create or replace view v_detailed_sell_report as
select 
	consumer.analysis_id, 
	consumer.id consumer_id,
	consumable.exchange_wallet exchange_wallet,
	consumer.currency currency,
	consumer.amount sold_amount,
	consumable.cdatetime buy_datetime,
	consumer.consume_datetime sell_datetime,
	consumable.cprice buy_price,
	consumer.sell_price sell_price,
	consumer.realized_profit realized_profit,
	consumer.taxable_realized_profit taxable_realized_profit,
	consumable.cid consumable_id
	
from v_tax_analysis_analysissellconsumer_full consumer
	join v_consumables_balance consumable on consumer.consumed_id=consumable.cid