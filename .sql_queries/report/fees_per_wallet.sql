select exchange_wallet, sum(fee)
from tax_analysis_analysable
where analysis_id=20
group by exchange_wallet