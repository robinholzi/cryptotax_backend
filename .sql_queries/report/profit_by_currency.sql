select 
	c.currency, 
	sum(c.realized_profit) sum_realized_profit,
	sum(c.taxable_realized_profit) sum_taxable_realized_profit
from v_tax_analysis_analysisconsumer_full c
where 
	c.type='SO'
	and c.analysis_id = 33

group by c.currency
order by c.currency asc