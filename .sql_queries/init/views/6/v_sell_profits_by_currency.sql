create or replace view v_sell_profits_by_currency as (
	select a.id as analysis_id, sell.currency as currency_id,
		sum(realized_profit) as sum_realized_profit,
		sum(taxable_realized_profit) as sum_taxable_realized_profit
	from v_tax_analysis_analysissellconsumer_full sell
	join tax_analysis_portfolioanalysis a on sell.analysis_id = a.id
	group by a.id, sell.currency, a.untaxed_allowance
)