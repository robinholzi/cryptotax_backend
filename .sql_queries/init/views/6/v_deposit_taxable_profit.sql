create or replace view v_deposit_taxable_profit as (
	select analysis_id, sum(profit_sum) as profit_sum -- taxable=total
	from v_deposit_taxable_profit_by_currency
	group by analysis_id
)