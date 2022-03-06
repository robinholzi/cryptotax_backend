create or replace view v_tax_analysis_analysisconsumer_full as
select 
	c.*,
	consumable.exchange_wallet, consumable.currency,
	ana.datetime consume_datetime,
	sc.realized_profit, sc.taxable_realized_profit,
	sell.price sell_price,
	tc.created_consumable_id
from tax_analysis_analysisconsumer c
	join tax_analysis_analysable ana on c.consumer_id=ana.id
	join v_consumables consumable on c.consumed_id=consumable.cid
	
	left outer join tax_analysis_analysissellconsumer sc ON sc.parent_id = c.id
	left outer join tax_analysis_analysistransferconsumer tc ON tc.parent_id = c.id
	
	left outer join tax_analysis_analysissell sell ON (sell.transaction_id = ana.id and ana."type"='SO')