create or replace view v_tax_analysis_analysissellconsumer_full as
select 
	id, consumer_id, amount, analysis_id, consumed_id, 
	exchange_wallet, consume_datetime, currency, sell_price, 
	realized_profit, taxable_realized_profit
from v_tax_analysis_analysisconsumer_full
where type='SO'