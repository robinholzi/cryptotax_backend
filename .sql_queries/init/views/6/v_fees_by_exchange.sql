create or replace view v_fees_by_exchange as (
	select analysis_id, exchange_wallet, sum(fee) as fee_sum
	from tax_analysis_analysable
	group by analysis_id, exchange_wallet
)