create or replace view v_sell_profits as (
    select
        analysis_id,
        sum(sum_realized_profit) as sum_realized_profit,
        sum(sum_taxable_realized_profit) as sum_taxable_realized_profit
    from v_total_sell_profits_by_currency
    group by analysis_id
)