
BEGIN; -- transaction

with selected as (
	select 
		coalesce(buy.id, sell.id, deposit.id, transfer.id) subid, 
		ana.*, 
		coalesce(buy.currency_id, sell.currency_id, deposit.currency_id, transfer.currency_id) currency, -- for all types
		coalesce(buy.amount, sell.amount, deposit.amount, transfer.amount) amount, -- for all types
		coalesce(buy.price, sell.price, deposit.price) buy_sell_deposit_price,  -- buy/sell/deposit
		deposit.taxable deposit_taxable, 
		transfer.from_exchange_wallet tranfer_from_exchange_wallet

	from (
	select 
		ana.type,
		ana.id as tid, ana.analysis_id, ana.datetime, ana.analysed,
		ana.fee, ana.exchange_wallet

	from tax_analysis_analysable ana
		join tax_analysis_portfolioanalysis analysis
			on ana.analysis_id = analysis.id
	where ana.analysed=False 
		and analysis.failed=False
		and analysis.mode='A'
		and (analysis.cooldown_until is null or analysis.cooldown_until<=now())

		-- no earlier (by datetime) unanalysed analysable in whole analysis
		and not exists (
			select * 
			from tax_analysis_analysable ana2
			where 
				ana2.analysis_id=analysis.id -- from same analysis
				and ana2.id!=ana.id -- no same analysable
				and ana2.datetime < ana.datetime -- came earlier (by datetime)
		)

	-- order viable analysables by creation date (to be fair across different analysises)
	order by ana.created asc
	limit 1
	) as ana
	-- join buys, sells, transfers & deposits: one has to be joinable!
	left outer join tax_analysis_analysisbuy buy on buy.transaction_id=ana.tid
	left outer join tax_analysis_analysissell sell on sell.transaction_id=ana.tid 
	left outer join tax_analysis_analysisdeposit deposit on deposit.transaction_id=ana.tid 
	left outer join tax_analysis_analysistransfer transfer on transfer.transaction_id=ana.tid 
),

updated as (
	update tax_analysis_portfolioanalysis 
	set cooldown_until= now() -- TODO: reserve_until
	where id=all(select analysis_id from selected) 
		and not (id is null)
		and exists (select * from selected)
)

select * from selected;

commit;