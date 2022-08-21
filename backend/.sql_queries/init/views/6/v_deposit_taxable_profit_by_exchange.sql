create or replace view v_deposit_taxable_profit_by_exchange as (
	select ana_id analysis_id, exchange_wallet, sum(taxableinbase) as profit_sum -- taxable=total
	from (
		select anadep.ana_id, (amount*price*taxable) taxableinbase, exchange_wallet
		from v_tax_analysis_analysabledeposit anadep
	) as sub
	group by ana_id, exchange_wallet
)