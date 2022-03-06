create or replace view v_consumables_balance as
select 
	consumable.*,
	coalesce(sum(consumer.amount),0) consumed
from v_consumables consumable
	left outer join tax_analysis_analysisconsumer consumer
		ON consumer.consumed_id = consumable.cid
group by 
	consumable.cid, consumable.cdatetime, 
	consumable.ctype, consumable.cprice, 
	
	consumable.anaid, consumable.anatype, 
	consumable.exchange_wallet, 
	consumable.currency, consumable.amount, 
	
	consumable.analysis_id, consumable.algo, consumable.transfer_algo