select 
	consumable.id, consumable.type, ana.datetime, 
	consumable.amount, -- total consumable
	coalesce(sum(consumer.amount),0) consumed
from tax_analysis_analysisconsumable consumable
	join tax_analysis_analysable ana 
		on ana.id=consumable.analysable_id
	join tax_analysis_portfolioanalysis analysis 
		on analysis.id=ana.analysis_id
	left outer join tax_analysis_analysisconsumer consumer
		ON consumer.consumed_id = consumable.id
where 
	analysis.id=6 -- TODO
	and consumable.exchange_wallet='Binance' -- TODO
		
group by consumable.id, ana.id, ana.datetime
having  (consumable.amount - coalesce(sum(consumer.amount),0)) > 0
-- TODO error tolerance

 -- after transfer the amount has later date than the buy order
order by ana.datetime asc  -- fifo
limit 1