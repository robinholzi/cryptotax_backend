create or replace function reserve_oldest_processable (reserve_until timestamptz) 
returns table(
	_type text,
	_ptid bigint,
	_sub_id bigint,
	_fee double precision,
	_fee_currency text,
	_cooldown_until timestamptz,
	_created timestamptz,
	
	_order_from_currency text,
	_order_from_amount double precision,
	_order_to_currency text,
	_order_to_amount double precision,
	
	deposit_currency text,
	deposit_amount double precision,
	deposit_taxable double precision,
	transfer_from_exchange_wallet text,
	transfer_currency text,
	transfer_amount double precision
)
as
$$

BEGIN -- transaction

-- CREATE TEMP TABLE selected (
-- 	_type text,
-- 	_ptid bigint,
-- 	_sub_id bigint,
-- 	_fee double precision,
-- 	_fee_currency text,
-- 	_cooldown_until timestamptz,
-- 	_created timestamptz,

-- 	_order_from_currency text,
-- 	_order_from_amount double precision,
-- 	_order_to_currency text,
-- 	_order_to_amount double precision,

-- 	deposit_currency text,
-- 	deposit_amount double precision,
-- 	deposit_taxable double precision,
-- 	transfer_from_exchange_wallet text,
-- 	transfer_currency text,
-- 	transfer_amount double precision
-- );

assert not(reserve_until is null), "reserve_until must not be null!";
assert (reserve_until between now() and (now() + interval '2 hours')), 
	"reserve_until must lie (max. 2h) in the future!";

return query
	with merged as (
	(
		select 
			'O' as type,
			ptid, poid sub_id, fee, fee_currency, cooldown_until, created,
			from_currency order_from_currency, from_amount order_from_amount,
			to_currency order_to_currency, to_amount order_to_amount,
			null as deposit_currency, null as deposit_amount, null as deposit_taxable, -- placeholder for deposit
			null as transfer_from_exchange_wallet, null as transfer_currency, 0 as transfer_amount -- placeholder for deposit
		from v_tax_analysis_processableoder
	) union (
		select 
			'D',
			ptid, pdid sub_id, fee, fee_currency, cooldown_until, created,
			null, null, null, null, -- placeholder for deposit
			currency, amount, taxable,
			null, null, null -- placeholder for deposit
		from v_tax_analysis_processabledeposit
	) union (
		select 
			'T',
			ptaid ptid, ptfid sub_id, fee, fee_currency, cooldown_until, created,
			null, null, null, null, -- placeholder for order
			null, null, null, -- placeholder for deposit
			from_exchange_wallet, currency, amount 
		from v_tax_analysis_processabletransfer
	)
	),

	selected as (
		select * 
-- 		into selected
		from merged
	 	where cooldown_until is NULL or cooldown_until < now()
	 	order by created asc
		limit 1
	),
	
 	updated as (
 		update tax_analysis_processabletransaction 
 		set cooldown_until=reserve_until
  		where id=all(select ptid from selected) 
  			and not (id is null)
  			and exists (select * from selected)
 	)
	
	select * from selected;
	
-- return query
-- 	select * from selected;

end;
$$ 
language plpgsql;