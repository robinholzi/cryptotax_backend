create or replace view v_deposit_taxable_profit_by_currency as (
	select ana_id analysis_id, currency_id, sum(taxableinbase) as profit_sum -- taxable=total
	from (
		select anadep.ana_id, (amount*price*taxable) taxableinbase, currency_id
		from v_tax_analysis_analysabledeposit anadep
	) as sub
	group by ana_id, currency_id
)