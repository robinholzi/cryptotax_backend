import datetime

from django.db import IntegrityError, transaction
from django.db import connection
from django.db.utils import DatabaseErrorWrapper

from portfolio.models import Order, Deposit, Transfer
from tax_analysis.models import Analysable, AnalysisBuy, AnalysisSell, ProcessableTransaction, ProcessableOrder, \
    ProcessableTransfer, AnalysisTransfer, ProcessableDeposit, AnalysisDeposit, AnalysisAlgorithm


@transaction.atomic
def save_orders_transactions(orders: list[Order]):
    try:
        with transaction.atomic():
            for order in orders:
                order.transaction.save()
                order.save()
    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Order/Transaction creation not successful.")


@transaction.atomic
def save_deposits_transactions(deposits: list[Deposit]):
    try:
        with transaction.atomic():
            for deposit in deposits:
                deposit.transaction.save()
                deposit.save()
    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Deposit/Transaction creation not successful.")


@transaction.atomic
def save_transfers_transactions(transfers: list[Transfer]):
    try:
        with transaction.atomic():
            for transfer in transfers:
                transfer.transaction.save()
                transfer.save()
    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Deposit/Transaction creation not successful.")


@transaction.atomic
def fetch_processable():
    query_str = """
        with merged as (
        (
            select 
                'O' as type,
                ptid, poid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
                from_currency_id order_from_currency_id, from_amount order_from_amount,
                to_currency_id order_to_currency, to_amount order_to_amount,
                null as deposit_buy_datetime, null as deposit_currency, null as deposit_amount, null as deposit_taxable, -- placeholder for deposit
                null as transfer_from_exchange_wallet, null as transfer_currency, 0 as transfer_amount -- placeholder for transfer
            from v_tax_analysis_processableoder
        ) union (
            select 
                'D',
                ptid, pdid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
                null, null, null, null, -- placeholder for deposit
                buy_datetime, currency_id, amount, taxable,
                null, null, null -- placeholder for deposit
            from v_tax_analysis_processabledeposit
        ) union (
            select 
                'T',
                ptaid ptid, ptfid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
                null, null, null, null, -- placeholder for order
                null, null, null, null, -- placeholder for deposit
                from_exchange_wallet, currency_id, amount 
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
            set cooldown_until=%s
            where id=all(select ptid from selected) 
                and not (id is null)
                and exists (select * from selected)
        )
        
        select s.*, a.base_currency_id
        from selected s
        join tax_analysis_portfolioanalysis a
        on s.ana_id=a.id;
    """

    reserve_until = datetime.datetime.now(tz=datetime.timezone.utc) + \
                    datetime.timedelta(minutes=2)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [reserve_until.isoformat()])
                rawFetched = cursor.fetchall()

                if len(rawFetched) == 0:
                    return None

                for raw in rawFetched:
                    return {
                        'type': raw[0],
                        'ptid': raw[1],
                        'sub_id': raw[2],
                        'ana_id': raw[3],
                        'datetime': raw[4],
                        'fee': raw[5],
                        'fee_currency': raw[6],
                        'cooldown_until': raw[7],
                        'created': raw[8],
                        'exchange_wallet': raw[9],

                        'order_from_currency': raw[10],
                        'order_from_amount': raw[11],
                        'order_to_currency': raw[12],
                        'order_to_amount': raw[13],

                        'deposit_buy_datetime': raw[14],
                        'deposit_currency': raw[15],
                        'deposit_amount': raw[16],
                        'deposit_taxable': raw[17],

                        'transfer_from_exchange_wallet': raw[18],
                        'transfer_currency': raw[19],
                        'transfer_amount': raw[20],

                        'base_currency_id': raw[21],
                    }

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Community creation not successful.")


@transaction.atomic
def create_buy_order_from_processable_order(
        processable: ProcessableTransaction,
        processable_order: ProcessableOrder,
        analysable: Analysable, buy: AnalysisBuy):
    try:
        with transaction.atomic():
            processable_order.delete()
            processable.delete()
            analysable.save()
            buy.save()

    except IntegrityError as ie:
        print("Excp1: ", ie)
        raise DatabaseErrorWrapper("create_buy_order_from_processable_order not successful.")


@transaction.atomic
def create_sell_order_from_processable_order(
        processable: ProcessableTransaction,
        processable_order: ProcessableOrder,
        analysable: Analysable, sell: AnalysisSell):
    try:
        with transaction.atomic():
            processable_order.delete()
            processable.delete()
            analysable.save()
            sell.save()

    except IntegrityError as ie:
        print("Excp2: ", ie)
        raise DatabaseErrorWrapper("create_sell_order_from_processable_order not successful.")


@transaction.atomic
def create_buy_and_sell_order_from_processable_order(
        processable: ProcessableTransaction,
        processable_order: ProcessableOrder,
        analysableSell: Analysable, sell: AnalysisSell,
        analysableBuy: Analysable, buy: AnalysisBuy):
    try:
        with transaction.atomic():
            processable_order.delete()
            processable.delete()
            analysableSell.save()
            analysableBuy.save()
            sell.save()
            buy.save()

    except IntegrityError as ie:
        print("Excp3: ", ie)
        raise DatabaseErrorWrapper("create_buy_and_sell_order_from_processable_order not successful.")


@transaction.atomic
def create_transfer_from_processable_transfer(
        processable: ProcessableTransaction,
        processable_transfer: ProcessableTransfer,
        analysable: Analysable, transfer: AnalysisTransfer):
    try:
        with transaction.atomic():
            processable_transfer.delete()
            processable.delete()
            analysable.save()
            transfer.save()

    except IntegrityError as ie:
        print("Excp4: ", ie)
        raise DatabaseErrorWrapper("create_transfer_from_processable_transfer not successful.")


@transaction.atomic
def create_deposit_from_processable_deposit(
        processable: ProcessableTransaction,
        processable_deposit: ProcessableDeposit,
        analysable: Analysable, transfer: AnalysisDeposit):
    try:
        with transaction.atomic():
            processable_deposit.delete()
            processable.delete()
            analysable.save()
            transfer.save()

    except IntegrityError as ie:
        print("Excp4: ", ie)
        raise DatabaseErrorWrapper("create_deposit_from_processable_deposit not successful.")


@transaction.atomic
def allocate_analyzable():
    print("allocate_analyzable:")
    query_str = """
        with selected as (
            select 
                coalesce(buy.id, sell.id, deposit.id, transfer.id) sub_id, 
                ana.*, 
                coalesce(buy.currency_id, sell.currency_id, deposit.currency_id, transfer.currency_id) currency, -- for all types
                coalesce(buy.amount, sell.amount, deposit.amount, transfer.amount) amount, -- for all types
                coalesce(buy.price, sell.price, deposit.price) buy_sell_deposit_price,  -- buy/sell/deposit
                deposit.buy_datetime deposit_buy_datetime, 
				deposit.taxable deposit_taxable, 
                transfer.from_exchange_wallet transfer_from_exchange_wallet
        
            from (
            select 
                ana.type,
                ana.id as tid, ana.analysis_id, ana.datetime, ana.analysed,
                ana.fee, ana.exchange_wallet, 
                analysis.algo algo, analysis.transfer_algo transfer_algo,
                analysis.taxable_period taxable_period
        
            from tax_analysis_analysable ana
                join tax_analysis_portfolioanalysis analysis
                    on ana.analysis_id = analysis.id
            where ana.analysed=False 
                and analysis.failed=False
                and analysis.mode='A'
                and (analysis.cooldown_until is null or analysis.cooldown_until<=now())
        
                -- no earlier (by datetime) unanalysed analysable in whole analysis
                and not exists (
                    select * 
                    from tax_analysis_analysable ana2
                    where 
                        ana2.analysis_id=analysis.id -- from same analysis
                        and ana2.id!=ana.id -- no same analysable
                        and ana2.datetime < ana.datetime -- came earlier (by datetime)
                        and not ana2.analysed -- not yet analysed
                )
        
            -- order viable analysables by creation date (to be fair across different analysises)
            order by ana.created asc
            limit 1
            ) as ana
            -- join buys, sells, transfers & deposits: one has to be joinable!
            left outer join tax_analysis_analysisbuy buy on buy.transaction_id=ana.tid
            left outer join tax_analysis_analysissell sell on sell.transaction_id=ana.tid 
            left outer join tax_analysis_analysisdeposit deposit on deposit.transaction_id=ana.tid 
            left outer join tax_analysis_analysistransfer transfer on transfer.transaction_id=ana.tid 
        ),
        
        updated as (
            update tax_analysis_portfolioanalysis 
            set cooldown_until= %s
            where id=all(select analysis_id from selected) 
                and not (id is null)
                and exists (select * from selected)
        )
        
        select * from selected;
    """

    reserve_until = datetime.datetime.now(tz=datetime.timezone.utc) + \
                    datetime.timedelta(seconds=30)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [reserve_until.isoformat()])
                rawFetched = cursor.fetchall()

                if len(rawFetched) == 0:
                    return None

                for raw in rawFetched:
                    return {
                        'sub_id': raw[0],
                        'type': raw[1],
                        'tid': raw[2],
                        'analysis_id': raw[3],
                        'datetime': raw[4],
                        'analysed': raw[5],
                        'fee': raw[6],
                        'exchange_wallet': raw[7],
                        'algo': raw[8],
                        'transfer_algo': raw[9],
                        'taxable_period': raw[10],

                        'currency': raw[11],  # for all types
                        'amount': raw[12],  # for all types
                        'buy_sell_deposit_price': raw[13],  # buy/sell/deposit
                        'deposit_buy_datetime': raw[14],
                        'deposit_taxable': raw[15],
                        'transfer_from_exchange_wallet': raw[16]
                    }

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Community creation not successful.")


@transaction.atomic
def consumable_from_buy_order(buy_order_id: int):
    print("consumable_from_buy_order:")
    query_str = """
        with selected as (
            select b.id buyid, ana.id anaid, b.amount amount, analysis.id analysisid, ana.datetime, b.price
            from tax_analysis_analysisbuy b
                join tax_analysis_analysable ana on b.transaction_id=ana.id
                join tax_analysis_portfolioanalysis analysis on ana.analysis_id=analysis.id
            where b.id=%s
                and ana.analysed=False
                and analysis.mode='A' 
                and analysis.cooldown_until > now() -- cooldown still active
        ),
        inserted as (
            insert into tax_analysis_analysisconsumable (analysable_id, datetime, type, price, amount)
            select anaid, datetime, 'BO', price, amount
            from selected
        ),
        
        updated as (
            update tax_analysis_portfolioanalysis
            set cooldown_until=null
            where id=all (
                select s.analysisid
                from selected s
            ) and exists (select * from selected)
        )
        
        update tax_analysis_analysable
        set analysed=True
        where id=all (
            select s.anaid
            from selected s
        ) and exists (select * from selected);
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [str(buy_order_id)])
                return True

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("consumable_from_buy_order not successful.")


@transaction.atomic
def consumable_from_deposit(deposit_id: int):
    print("consumable_from_deposit: ", deposit_id)
    query_str = """
        with selected as (
            select d.id depid, ana.id anaid, d.amount amount, analysis.id analysisid, d.buy_datetime, d.price
            from tax_analysis_analysisdeposit d
                join tax_analysis_analysable ana on d.transaction_id=ana.id
                join tax_analysis_portfolioanalysis analysis on ana.analysis_id=analysis.id
            where d.id=%s
                and ana.analysed=False
                and analysis.mode='A'
                and analysis.cooldown_until > now() -- cooldown still active
        ),
        
        inserted as (
            insert into tax_analysis_analysisconsumable (analysable_id, datetime, type, price, amount)
            select anaid, buy_datetime, 'D', price, amount
            from selected
        ),
        
        updated as (
            update tax_analysis_portfolioanalysis
            set cooldown_until=null
            where id=all (
                select s.analysisid
                from selected s
            ) and exists (select * from selected)
        )
        
        update tax_analysis_analysable
        set analysed=True
        where id=all (
            select s.anaid
            from selected s
        ) and exists (select * from selected);
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [str(deposit_id)])
                return True

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("consumable_from_deposit not successful.")


# TODO optimal strategy: allocate first: long term (tax free) holdings
@transaction.atomic
def fetch_next_consumable(
        analysis_id: int, exchange_wallet: str, currency: str,
        algo, error_tolerance: float = 0.0000000000001):
    print("fetch_next_consumable")

    # fifo: lowest date first
    # worst: lowest price first
    asc_desc = 'asc'

    # highest date first
    # or highest price first
    if algo == AnalysisAlgorithm.ALGO_LIFO or \
            algo == AnalysisAlgorithm.ALGO_OPTIMAL:
        asc_desc = 'desc'

    # fifo, lifo
    order_by_attr = 'consumable.cdatetime'

    # best, worst
    if algo == AnalysisAlgorithm.ALGO_OPTIMAL or \
            algo == AnalysisAlgorithm.ALGO_WORST:
        order_by_attr = 'consumable.cprice'

    query_str = f"""
    select 
        consumable.cid, consumable.cdatetime, 
        consumable.ctype, consumable.cprice,
        consumable.amount, -- total consumable
        coalesce(sum(consumer.amount),0) consumed
    from v_consumables_balance consumable
        left outer join tax_analysis_analysisconsumer consumer
            ON consumer.consumed_id = consumable.cid
    where 
        consumable.analysis_id=%s
        and consumable.exchange_wallet=%s
        and consumable.currency=%s
        
    group by 
        consumable.cid, consumable.ctype,
        consumable.cid, consumable.cdatetime, 
        consumable.ctype, consumable.cprice,
        consumable.amount
        
    having (consumable.amount - coalesce(sum(consumer.amount), 0)) > %s
    -- TODO error tolerance
    
     -- after transfer the amount has later date than the buy order
    order by {order_by_attr} {asc_desc}
    limit 1
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                print("fetch_next_consumable: ",
                      str(analysis_id),
                      str(exchange_wallet),
                      str(currency)
                      )
                cursor.execute(query_str, [
                    str(analysis_id),
                    str(exchange_wallet),
                    str(currency),
                    str(error_tolerance)
                ])
                rawFetched = cursor.fetchall()
                print("fetch_next_consumable res: ", rawFetched)

                if len(rawFetched) == 0:
                    print("fetch_next_consumable: query was empty")
                    # TODO error handling
                    raise IntegrityError("fetch_next_consumable: query was empty")

                for raw in rawFetched:
                    return {
                        'id': raw[0],
                        'datetime': raw[1],
                        'type': raw[2],
                        'price': raw[3],
                        'amount': raw[4],
                        'consumed': raw[5],
                    }

                print("unknown error")
                return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("fetch_next_consumable not successful.")


@transaction.atomic
def fetch_already_allocated_sum(analysable_id: int):
    print("fetch_already_allocated_sum:")
    query_str = """
        select coalesce(sum(amount), 0)
        from tax_analysis_analysisconsumer comsumer
        where consumer_id = %s -- analysable
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [str(analysable_id)])
                rawFetched = cursor.fetchall()

                if len(rawFetched) == 0:
                    return None

                for raw in rawFetched:
                    return raw[0]

                return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("fetch_already_allocated_sum not successful.")


@transaction.atomic
def analysable_already_done(analysable_id: int):
    print("analysable_already_done:")
    query_str = """
        with selected as (
            select ana.id anaid, analysis.id analysisid
            from tax_analysis_analysable ana
                join tax_analysis_portfolioanalysis analysis on ana.analysis_id=analysis.id
            where ana.id=%s
                and ana.analysed=False
                and analysis.mode='A' 
                and analysis.cooldown_until > now() -- cooldown still active
        ),

        updated as (
            update tax_analysis_portfolioanalysis
            set cooldown_until=null
            where id=all (
                select s.analysisid
                from selected s
            ) and exists (select * from selected)
        )
        
        update tax_analysis_analysable
        set analysed=True
        where id=all (
            select s.anaid
            from selected s
        ) and exists (select * from selected);
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [str(analysable_id)])
                return

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("fetch_already_allocated_sum not successful.")


# TODO check weather consumed amount is correct
def consume_sell(analysis_id: int, analysable_id: int, consumed_id: int, consumed_amount: float,
                 realized_profit: float, taxable_realized_profit: float, finished: bool):
    print("consume_sell:")
    analysed_part = "update tax_analysis_analysable set analysed=True where false"
    if finished:
        analysed_part = """
            update tax_analysis_analysable
            set analysed=True
            where id=all (
                select s.anaid
                from selected s
            ) and exists (select * from selected)
        """

    query_str = f"""
    insert into tax_analysis_analysisconsumer (analysis_id, consumed_id, type, consumer_id, amount)
    values (%s, %s, 'SO', %s, %s);
    
    with selected as (
        select s.id sellid, ana.id anaid, s.amount amount, analysis.id analysisid, type, exchange_wallet
        from tax_analysis_analysissell s
            join tax_analysis_analysable ana on s.transaction_id=ana.id
            join tax_analysis_portfolioanalysis analysis on ana.analysis_id=analysis.id
        where ana.id=%s
            and ana.analysed=False
            and analysis.mode='A' 
            and analysis.cooldown_until > now() -- cooldown still active
    ),
    inserted2 as (
        insert into tax_analysis_analysissellconsumer (parent_id, realized_profit, taxable_realized_profit)
        select (
            select currval('tax_analysis_analysisconsumer_id_seq')
        ), %s, %s
        from selected
        where exists (select * from selected) or not exists (select * from selected)  
        -- do nothing, just use inserted to force sequentiality?
    ),
    updated as (
        update tax_analysis_portfolioanalysis
        set cooldown_until=null
        where id=all (
            select s.analysisid
            from selected s
        ) and exists (select * from selected)
    )
    
    {analysed_part}
    ;
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [
                    str(analysis_id),
                    str(consumed_id),
                    str(analysable_id),
                    str(consumed_amount),

                    str(analysable_id),

                    str(realized_profit),
                    str(taxable_realized_profit)
                ])
                return

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("consume_sell not successful.")


def consume_transfer(analysis_id: int, analysable_id: int, consumed_id: int, consumed_amount: float,
                     buy_datetime: datetime, buy_price: float, finished: bool):
    print("consume_transfer:")
    analysed_part = "update tax_analysis_analysable set analysed=True where false"
    if finished:
        analysed_part = """
            update tax_analysis_analysable
            set analysed=True
            where id=all (
                select s.anaid
                from selected s
            ) and exists (select * from selected)
        """

    select_query = """
        with selected as (
            select t.id transferid, ana.id anaid, t.amount amount, analysis.id analysisid, type, exchange_wallet
            from tax_analysis_analysistransfer t
                join tax_analysis_analysable ana on t.transaction_id=ana.id
                join tax_analysis_portfolioanalysis analysis on ana.analysis_id=analysis.id
            where ana.id=%s
                and ana.analysed=False
                and analysis.mode='A' 
                and analysis.cooldown_until > now() -- cooldown still active
        )
    """

    query_str = f"""
    insert into tax_analysis_analysisconsumer (analysis_id, consumed_id, type, consumer_id, amount)
    values (%s, %s, 'T', %s, %s);
    
    {select_query}
    
    insert into tax_analysis_analysisconsumable (analysable_id, datetime, type, price, amount)
    select  anaid, %s, 'T', %s, %s
    from selected
    limit 1;

    {select_query},
    
    inserted3 as (
        insert into tax_analysis_analysistransferconsumer (parent_id, created_consumable_id)
        select 
            (select currval('tax_analysis_analysisconsumer_id_seq')), 
            (select currval('tax_analysis_analysisconsumable_id_seq'))
    ),
    
    updated as (
        update tax_analysis_portfolioanalysis
        set cooldown_until=null
        where id=all (
            select s.analysisid
            from selected s
        ) and exists (select * from selected)
    )

    {analysed_part}
    ;
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [
                    str(analysis_id),
                    str(consumed_id),
                    str(analysable_id),
                    str(consumed_amount),

                    str(analysable_id),

                    str(buy_datetime),
                    str(buy_price),
                    str(consumed_amount),

                    str(analysable_id),
                ])
                return

    except IntegrityError as ie:
        print("consume_sell failed: ", ie)
        raise DatabaseErrorWrapper("consume_sell not successful.")

# todo fetch comsumed amount and calc difference:
# IMPORTANT: check if analysis object locked or everything atomic
# if locked: ensure that after cooldown commit isn't possible anymore
