select distinct (currency)
from (

	(select from_currency_id currency from v_portfolio_order_full)

) temp
order by currency asc