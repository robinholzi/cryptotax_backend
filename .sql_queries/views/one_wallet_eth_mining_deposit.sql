select d.amount, d.datetime
from v_tax_analysis_analysabledeposit d
where taxable > 0
and currency_id = 'ETH'
and d.exchange_wallet = 'Polygon: 0xa22add47a83879DbfD6a8468F6f9468FC98F72f9'