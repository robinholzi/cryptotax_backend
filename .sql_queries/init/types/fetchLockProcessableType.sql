
-- UNUSED
-- UNUSED
-- UNUSED

drop function if exists fetch_and_lock_processable; -- depends on type
drop type if exists fetchLockProcessableReturnType;

create type fetchLockProcessableReturnType as ( 
   type varchar, 
   ptid integer, 
   sub_id integer, 
   ana_id integer, 
   datetime timestamp with time zone, 
   fee double precision, 
   fee_currency varchar,
   cooldown_until timestamp with time zone, 
   created timestamp with time zone, 
   exchange_wallet varchar, 

   order_from_currency varchar,
   order_from_amount double precision,
   order_to_currency varchar,
   order_to_amount double precision,
	
   deposit_buy_datetime timestamp with time zone,
   deposit_type varchar,
   deposit_currency varchar,
   deposit_amount double precision,
   deposit_taxable double precision,
	
   transfer_from_exchange_wallet varchar,
   transfer_currency varchar,
   transfer_amount double precision,
	
   base_currency_id varchar
);
