create or replace view v_consumers_satisfied_amounts as
select 
		ana."id",
		ana."type", 
		ana."analysed",
		ana."analysis_id", 
		ana."datetime", 
		ana."exchange_wallet", 
		ana."fee", 
		coalesce(sell.id, transfer.id) sub_id, 
		coalesce(sell.currency_id, transfer.currency_id) currency,
		coalesce(sell.amount, transfer.amount) amount,
		transfer.from_exchange_wallet transfer_from_exchange_wallet,
		coalesce (sum(consumer.amount), 0) consumed
from tax_analysis_analysable ana
	left outer join tax_analysis_analysissell sell on sell.transaction_id=ana.id 
	left outer join tax_analysis_analysistransfer transfer on transfer.transaction_id=ana.id 
	
	left outer join tax_analysis_analysisconsumer consumer ON consumer.consumer_id = ana.id

where ana."type"='T' or ana."type"='SO'
group by 
		ana."id",
		ana."type", 
		ana."analysed",
		ana."analysis_id", 
		ana."datetime", 
		ana."exchange_wallet", 
		ana."fee",
		
		sell.id, transfer.id,
		sell.currency_id, transfer.currency_id,
		sell.amount, transfer.amount,
		transfer.from_exchange_wallet
		
order by ana.datetime