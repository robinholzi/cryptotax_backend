
-- UNUSED
-- UNUSED
-- UNUSED

CREATE OR REPLACE FUNCTION fetch_and_lock_processable() 
RETURNS fetchLockProcessableReturnType AS $$
declare  
  selectedResult fetchLockProcessableReturnType %rowtype; 
begin

with merged as (
	(
		select 
			'O' as type,
			ptid, poid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
			from_currency_id order_from_currency_id, from_amount order_from_amount,
			to_currency_id order_to_currency, to_amount order_to_amount,
			null as deposit_buy_datetime, null as deposit_type, null as deposit_currency, null as deposit_amount, null as deposit_taxable, -- placeholder for deposit
			null as transfer_from_exchange_wallet, null as transfer_currency, 0 as transfer_amount -- placeholder for transfer
		from v_tax_analysis_processableoder
	) union (
		select 
			'D',
			ptid, pdid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
			null, null, null, null, -- placeholder for deposit
			buy_datetime, type, currency_id, amount, taxable,
			null, null, null -- placeholder for deposit
		from v_tax_analysis_processabledeposit
	) union (
		select 
			'T',
			ptaid ptid, ptfid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
			null, null, null, null, -- placeholder for order
			null, null, null, null, null, -- placeholder for deposit
			from_exchange_wallet, currency_id, amount 
		from v_tax_analysis_processabletransfer
	)
),


selected as (
	select * 
-- 		
	from merged
	where cooldown_until is NULL or cooldown_until < now()
	order by created asc
	limit 1
)


select into selectedResult s.*, a.base_currency_id
from selected s
join tax_analysis_portfolioanalysis a
on s.ana_id=a.id;

return selectedResult;
end;
$$ LANGUAGE plpgsql;