create or replace view v_profits_by_currency as (
    select a.id as analysis_id, dep.currency_id,
    (	0
        + coalesce(sum(dep.profit_sum), 0)
        + coalesce(sum(sel.sum_realized_profit), 0)
    ) as sum_realized_profit, -- deposit_profit_sum + sell_profit_sum
    GREATEST( -- deposit_profit_sum + sell_profit_sum - fees
        0.0,
        coalesce(sum(dep.profit_sum), 0)
        + coalesce(sum(sel.sum_taxable_realized_profit), 0)
        - coalesce(sum(fees.fee_sum), 0)
    ) as sum_taxable_realized_profit
    from tax_analysis_portfolioanalysis a
    left outer join v_deposit_taxable_profit_by_currency dep on dep.analysis_id = a.id
    left outer join v_sell_profits_by_currency sel on sel.analysis_id = a.id and dep.currency_id = sel.currency_id
    left outer join v_fees_by_currency fees on fees.analysis_id = a.id and sel.currency_id = fees.currency_id
    group by a.id, dep.currency_id
    having not dep.currency_id is NULL
);
