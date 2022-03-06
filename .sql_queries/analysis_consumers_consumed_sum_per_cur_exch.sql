select t1.exchange_wallet, t2.currency, t1.sum_ consumed_sum, t2.sum_ sell_sum, (t1.sum_-t2.sum_) diff

from (
select exchange_wallet, currency, sum(sold_amount) sum_
from v_detailed_sell_report
where analysis_id=20
group by exchange_wallet, currency
order by exchange_wallet, currency
) t1 
join 
(
select exchange_wallet, currency_id as currency, sum(amount) sum_
from v_tax_analysis_analysablesell
where ana_id=20
group by exchange_wallet, currency_id
order by exchange_wallet, currency_id
) t2 on (
	t1.exchange_wallet=t2.exchange_wallet
	and t1.currency=t2.currency
)