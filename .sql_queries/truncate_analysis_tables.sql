-- truncate tax_analysis_portfolioanalysis CASCADE

-- select * 
-- from v_portfolio_deposit_full t --join portfolio_transaction t ON t.id = d.transaction_id


-- select * 
-- from tax_analysis_processabledeposit

select * 
from create_init_portfolio_analysis(1)

-- drop view v_portfolio_transfer_full
