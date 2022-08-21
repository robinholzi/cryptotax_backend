-- unused, untested!!!!!!!!!!!!!!!!!
create or replace view v_consumable_balance_and_consumed as  
select 
        consumable.cid, consumable.cdatetime, 
        consumable.ctype, consumable.cprice,
        consumable.amount, -- total consumable
        coalesce(sum(consumer.amount),0) consumed,
		consumable.analysis_id, consumable.currency, 
		consumable.exchange_wallet
    from v_consumables_balance consumable
        left outer join tax_analysis_analysisconsumer consumer
            ON consumer.consumed_id = consumable.cid
        
    group by 
        consumable.cid, consumable.ctype,
        consumable.cid, consumable.cdatetime, 
        consumable.ctype, consumable.cprice,
        consumable.amount,
		consumable.analysis_id, consumable.currency, 
		consumable.exchange_wallet
    
     -- after transfer the amount has later date than the buy order
    order by consumable.cdatetime asc  -- fifo