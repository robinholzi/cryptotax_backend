create or replace function create_init_portfolio_analysis (
	portfolio_id int, title varchar,
	base_currency_id varchar, 
	algo varchar, transfer_algo varchar, 
	untaxed_allowance decimal, 
	mining_tax_method varchar, mining_deposit_profit_rate decimal, 
	cross_wallet_sells boolean, taxable_period_days integer) 
	returns integer AS
$$
declare
	ret_val integer;

BEGIN -- transaction
	
   assert (portfolio_id > 0 and not (portfolio_id  is NULL)), 'portfolio id invalid!';
   
-- [Analysis]===================================================

	insert into tax_analysis_portfolioanalysis 
	(portfolio_id, title,
	 	base_currency_id, 
		algo, transfer_algo, 
		untaxed_allowance, 
		mining_tax_method, mining_deposit_profit_rate, 
		cross_wallet_sells, taxable_period_days
	) values (
		portfolio_id, title,
		base_currency_id, 
		algo, transfer_algo, 
		untaxed_allowance, 
		mining_tax_method, mining_deposit_profit_rate, 
		cross_wallet_sells, taxable_period_days
	);

-- [Orders]=====================================================
	
	with inserted as (
		insert into tax_analysis_processabletransaction (
			analysis_id, type, exchange_wallet, fee_currency_id, 
		 	fee, portfolio_transaction_id, datetime
		)
		select (
			select currval('tax_analysis_portfolioanalysis_id_seq')
		), 'O', exchange_wallet, fee_currency_id, fee, tid, datetime 
		from v_portfolio_order_full
		where pid = portfolio_id
		order by oid

		RETURNING id processable_tid, portfolio_transaction_id tid
	)

	-- insert orders into order table according to tid from transaction insert above
	INSERT INTO tax_analysis_processableorder (
		transaction_id, from_currency_id, from_amount, to_currency_id, to_amount)
	SELECT 
		i.processable_tid, 
		pof.from_currency_id, pof.from_amount, 
		pof.to_currency_id, pof.to_amount
	FROM inserted i join v_portfolio_order_full pof 
		on pof.tid=i.tid;

-- [Deposit]=====================================================

	with inserted as (
		insert into tax_analysis_processabletransaction (
			analysis_id, type, exchange_wallet, fee_currency_id, fee, 
			portfolio_transaction_id, datetime
		)
		select (
			select currval('tax_analysis_portfolioanalysis_id_seq')
		), 'D', exchange_wallet, fee_currency_id, fee, tid, datetime
		from v_portfolio_deposit_full
		where pid = portfolio_id
		order by did

		RETURNING id processable_tid, portfolio_transaction_id tid
	)

	-- insert deposits into deposit table according to tid from transaction insert above
	INSERT INTO tax_analysis_processabledeposit (
		transaction_id, buy_datetime, currency_id, amount, taxable, type)
	SELECT 
		i.processable_tid, 
		pdf.buy_datetime, pdf.currency_id, 
		pdf.amount, pdf.taxable, pdf.type
	FROM inserted i join v_portfolio_deposit_full pdf 
		on pdf.tid=i.tid;
	
-- [Transfer]=====================================================

	with inserted as (
		insert into tax_analysis_processabletransaction (
			analysis_id, type, exchange_wallet, fee_currency_id, fee, 
			portfolio_transaction_id, datetime
		)
		select (
			select currval('tax_analysis_portfolioanalysis_id_seq')
		), 'T', exchange_wallet, fee_currency_id, fee, taid, datetime
		from v_portfolio_transfer_full
		where pid = portfolio_id
		order by tfid

		RETURNING id processable_taid, portfolio_transaction_id taid
	)

	-- insert transfers into transfer table according to tid from transaction insert above
	INSERT INTO tax_analysis_processabletransfer (
		transaction_id, from_exchange_wallet, currency_id, amount)
	SELECT 
		i.processable_taid, 
		ptf.from_exchange_wallet,
		ptf.currency_id, ptf.amount
	FROM inserted i join v_portfolio_transfer_full ptf 
		on ptf.taid=i.taid;

-- ===============================================================

	RETURN currval('tax_analysis_portfolioanalysis_id_seq');

-- COMMIT; functions automatically transactions
end;
$$ 
language plpgsql;
