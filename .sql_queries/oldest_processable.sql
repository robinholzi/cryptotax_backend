select * 
from tax_analysis_processabletransaction pt
where pt.cooldown_until is NULL or pt.cooldown_until < now()
order by pt.created asc
limit 1