create or replace view v_fees as (
	select analysis_id, sum(fee)
	from tax_analysis_analysable
	group by analysis_id
)