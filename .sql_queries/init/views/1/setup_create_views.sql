create or replace view v_portfolio_order_full as
select 
	t.id tid, o.id oid, t.portfolio_id pid, 
	o.from_currency_id, o.from_amount, 
	o.to_currency_id, o.to_amount, 
	t.datetime, t.exchange_wallet, 
	t.fee_currency_id, t.fee
from portfolio_order o 
	join portfolio_transaction t ON t.id = o.transaction_id;

create or replace view v_portfolio_deposit_full as
select 
	t.id tid, d.id did, t.portfolio_id pid, 
	d.buy_datetime,
	d.currency_id, d.type,
	d.amount, d.taxable,
	t.datetime, t.exchange_wallet, 
	t.fee_currency_id, t.fee
from portfolio_deposit d 
	join portfolio_transaction t ON t.id = d.transaction_id;

create or replace view v_portfolio_transfer_full as
select 
	ta.id taid, tf.id tfid, ta.portfolio_id pid, 
	tf.currency_id, tf.amount, 
	tf.from_exchange_wallet, 
	ta.datetime, ta.exchange_wallet, 
	ta.fee_currency_id, ta.fee
from portfolio_transfer tf 
	join portfolio_transaction ta ON ta.id = tf.transaction_id;