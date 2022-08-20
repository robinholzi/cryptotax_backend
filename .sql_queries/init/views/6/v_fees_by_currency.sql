create or replace view v_fees_by_currency as (
    select analysis_id, currency as currency_id, sum(fee) as fee_sum
    from v_tax_analysis_analysables_full
    group by analysis_id, currency
)