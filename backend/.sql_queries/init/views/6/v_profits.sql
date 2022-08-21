create or replace view v_profits as (
	select a.id as analysis_id, 
	(coalesce(dep.profit_sum, 0) + coalesce(sel.sum_realized_profit, 0)) as sum_realized_profit, -- deposit_profit_sum + sell_profit_sum
	GREATEST( -- deposit_profit_sum + sell_profit_sum - fees - untaxed_allowance
		0.0,
		( coalesce(dep.profit_sum, 0)
		+ coalesce(sel.sum_taxable_realized_profit, 0)
		- coalesce(fees.sum, 0)
		- a.untaxed_allowance
		)
	) as sum_taxable_realized_profit
	from tax_analysis_portfolioanalysis a
	left outer join v_deposit_taxable_profit dep on dep.analysis_id = a.id
	left outer join v_total_sell_profits sel on sel.analysis_id = a.id
	left outer join v_total_fees fees on fees.analysis_id = a.id
)
