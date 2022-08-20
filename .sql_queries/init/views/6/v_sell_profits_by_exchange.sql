create or replace view v_sell_profits_by_exchange as (
	select a.id as analysis_id, sell.exchange_wallet,
		sum(realized_profit) as sum_realized_profit,
		sum(taxable_realized_profit) as sum_taxable_realized_profit
	from v_tax_analysis_analysissellconsumer_full sell
	join tax_analysis_portfolioanalysis a on sell.analysis_id = a.id
	group by a.id, sell.exchange_wallet, a.untaxed_allowance
)