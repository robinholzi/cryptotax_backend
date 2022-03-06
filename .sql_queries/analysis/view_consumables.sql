create or replace view v_consumables as
select 
	consumable.id cid, consumable.datetime cdatetime, 
	consumable.type ctype, consumable.price cprice,
	
	ana.id anaid, ana.type anatype, ana.exchange_wallet exchange_wallet, -- analysed, fee and create/update hidden
	
	coalesce(buy.currency_id, deposit.currency_id, transfer.currency_id) currency, 
	consumable.amount amount,
	
	analysis.id analysis_id,
	analysis.algo algo, analysis.transfer_algo transfer_algo
	
from tax_analysis_analysisconsumable consumable
join tax_analysis_analysable ana
	on consumable.analysable_id = ana.id
join tax_analysis_portfolioanalysis analysis
	on analysis.id = ana.analysis_id
left outer join tax_analysis_analysisbuy buy
	on buy.transaction_id = ana.id
left outer join tax_analysis_analysisdeposit deposit
	on deposit.transaction_id = ana.id
left outer join tax_analysis_analysistransfer transfer
	-- TODO: store prices in transferconsumables
	on transfer.transaction_id = ana.id
