create or replace view v_tax_analysis_analysables_full as
select 
	coalesce(buy.id, sell.id, deposit.id, transfer.id) sub_id, 
	ana.*, 
	coalesce(buy.currency_id, sell.currency_id, deposit.currency_id, transfer.currency_id) currency, -- for all types
	coalesce(buy.amount, sell.amount, deposit.amount, transfer.amount) amount, -- for all types
	coalesce(buy.price, sell.price, deposit.price) buy_sell_deposit_price,  -- buy/sell/deposit
	deposit.buy_datetime deposit_buy_datetime, 
	deposit.taxable deposit_taxable, 
	transfer.from_exchange_wallet transfer_from_exchange_wallet
from tax_analysis_analysable ana
	join tax_analysis_portfolioanalysis analysis ON analysis.id = ana.analysis_id 
	left outer join tax_analysis_analysisbuy buy ON buy.transaction_id = ana.id
	left outer join tax_analysis_analysissell sell ON sell.transaction_id = ana.id
	left outer join tax_analysis_analysisdeposit deposit ON deposit.transaction_id = ana.id
	left outer join tax_analysis_analysistransfer transfer ON transfer.transaction_id = ana.id
	
order by ana.datetime