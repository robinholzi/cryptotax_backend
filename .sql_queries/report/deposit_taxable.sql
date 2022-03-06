select currency_id, sum(taxableinbase)
from (
select (amount*price*taxable) taxableinbase, currency_id
from tax_analysis_analysisdeposit
) as sub
group by currency_id

-- todo only one analysis