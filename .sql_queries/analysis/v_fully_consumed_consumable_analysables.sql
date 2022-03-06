create or replace view v_fully_consumed_consumable_analysables as
select ana.*, 
	coalesce (buy.amount, transfer.amount) amount,
	coalesce (buy.currency_id, transfer.currency_id) currency_id
from tax_analysis_analysable ana
	left outer join tax_analysis_analysisbuy buy ON buy.transaction_id = ana.id
	left outer join tax_analysis_analysistransfer transfer ON transfer.transaction_id = ana.id
	
where (ana.type='BO' or ana.type='T')
	and ana.analysed=True
	
-- WRONG SEMANTICS!