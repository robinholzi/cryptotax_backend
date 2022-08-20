import datetime
from typing import Optional

from django.db import (
    IntegrityError,
    connection,
    transaction,
)
from django.db.utils import DatabaseErrorWrapper

from portfolio.models import Currency
from tax_analysis.models import (
    Analysable,
    AnalysisAlgorithm,
    AnalysisBuy,
    AnalysisDeposit,
    AnalysisSell,
    AnalysisTransfer,
    ProcessableDeposit,
    ProcessableOrder,
    ProcessableTransaction,
    ProcessableTransfer,
)


@transaction.atomic
def create_analysis(
    portfolio_id: int,
    title: str,
    base_currency: Currency,
    algo: str,
    transfer_algo: str,
    untaxed_allowance: float,
    mining_tax_method: str,
    mining_deposit_profit_rate: float,
    cross_wallet_sells: bool,
    taxable_period_days: int,
) -> Optional[int]:
    query_str = """
        select create_init_portfolio_analysis
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    query_str,
                    [
                        portfolio_id,
                        title,
                        base_currency.tag,
                        algo,
                        transfer_algo,
                        untaxed_allowance,
                        mining_tax_method,
                        mining_deposit_profit_rate,
                        cross_wallet_sells,
                        taxable_period_days,
                    ],
                )
                raw_fetched = cursor.fetchall()

                if len(raw_fetched) == 0:
                    return None

                for raw in raw_fetched:
                    return int(raw[0])

                return None

    except IntegrityError as ie:
        print(">>?", ie)
        raise DatabaseErrorWrapper("Analysis creation not successful.")


# page_no: 1-based
@transaction.atomic
def query_portfolio_analysis_list(
    portfolio_id: int, pagesize: int, page_no: int = 1
) -> list[dict]:
    pagesize = max(5, min(200, pagesize))
    page_no = max(0, page_no)

    query_str = """
        select ana.id, ana.title, ana.created, ana.mode, ana.failed, ana.algo, ana.transfer_algo, ana.base_currency_id,
        ((select count(distinct(pt.id)) from tax_analysis_processabletransaction pt where pt.analysis_id=ana.id)
         +(select count(distinct(ta.id)) from tax_analysis_analysable ta where ta.analysis_id=ana.id)) as txs,

        (select currencies from v_currency_count_by_analysis vcc where vcc.id=ana.id),
        (select wallets from v_wallet_count_by_analysis vwc where vwc.id=ana.id),

        anarep.taxable_profit_sum as taxable_profit,
        anarep.realized_profit_sum as realized_profit,
        anarep.fee_sum as fees,
        (ppa.done + apa.done)/2.0 as progress,
        case when anarep.id is NULL then 'processing...' else anarep.error_message end
        from tax_analysis_portfolioanalysis ana
        left outer join tax_analysis_portfolioanalysisreport anarep ON anarep.analysis_id = ana.id
        join v_processed_percentage_per_analysis ppa ON ppa.id=ana.id
        join v_analysed_percentage_per_analysis apa ON apa.id=ana.id
        where ana.portfolio_id=%s
        order by ana.id
        limit %s
        offset %s;
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    query_str, [portfolio_id, pagesize, (page_no - 1) * pagesize]
                )

                analysis_list = []

                for raw in cursor.fetchall():
                    analysis_list.append(
                        {
                            "ana_id": raw[0],
                            "title": raw[1],
                            "created": raw[2],
                            "mode": raw[3],
                            "failed": raw[4],
                            "algo": raw[5],
                            "transfer_algo": raw[6],
                            "base_currency": raw[7],
                            "txs": raw[8],
                            "currencies": raw[9],
                            "wallets": raw[10],
                            "taxable_profit": raw[11],
                            "realized_profit": raw[12],
                            "fee_sum": raw[13],
                            "progress": raw[14],
                            "msg": raw[15],
                        }
                    )

                return analysis_list

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Analysis list query failed.")


def query_portfolio_analysis_number(portfolio_id: int) -> int:
    query_str = """
        select count(ana.id)
        from tax_analysis_portfolioanalysis ana
        where ana.portfolio_id=%s
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [portfolio_id])

                for raw in cursor.fetchall():
                    return int(raw[0])

                raise Exception("Illegal State!")

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Analysis number query failed.")


@transaction.atomic
def query_result_detail(analysis_id: int) -> Optional[dict]:
    query_str = """
        select ((select count(distinct(pt.id)) from tax_analysis_processabletransaction pt where pt.analysis_id=ana.id)
         +(select count(distinct(ta.id)) from tax_analysis_analysable ta where ta.analysis_id=ana.id)) as txs,
        (select currencies from v_currency_count_by_analysis vcc where vcc.id=ana.id) as currencies,
        (select wallets from v_wallet_count_by_analysis vwc where vwc.id=ana.id) as exchanges,
        anarep.taxable_profit_sum as taxable_profit,
        anarep.realized_profit_sum as realized_profit,
        dp.profit_sum as deposit_profit,
        sp.sum_realized_profit as sell_profit,
        anarep.fee_sum as fees,
        (ppa.done + apa.done)/2.0 as progress,
        case when anarep.id is NULL then 'processing...' else anarep.error_message end
        from tax_analysis_portfolioanalysis ana
        left outer join tax_analysis_portfolioanalysisreport anarep ON anarep.analysis_id = ana.id
        left outer join v_deposit_taxable_profit dp on dp.analysis_id = ana.id
        left outer join v_sell_profits sp on sp.analysis_id = ana.id
        join v_processed_percentage_per_analysis ppa ON ppa.id=ana.id
        join v_analysed_percentage_per_analysis apa ON apa.id=ana.id
        where ana.id=%s;
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str, [analysis_id])

                for raw in cursor.fetchall():
                    return {
                        "txs": raw[0],
                        "currencies": raw[1],
                        "exchanges": raw[2],
                        "taxable_profit": raw[3],
                        "realized_profit": raw[4],
                        "deposit_profit": raw[5],
                        "sell_profit": raw[6],
                        "fee_sum": raw[7],
                        "progress": raw[8],
                        "msg": raw[9],
                    }

                return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("query_result_detail not successful.")


@transaction.atomic
def query_profit_by_currency(analysis_id: int) -> list[dict]:
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from v_profit_by_currency
                    where analysis_id=%s
                """,
                    [analysis_id],
                )
                li = []
                for raw in cursor.fetchall():
                    li.append(
                        {
                            "currency": raw[1],
                            "realized_profit": raw[2],
                            "taxable_profit": raw[3],
                        }
                    )
                return li

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("query_profit_by_currency query not successful.")


@transaction.atomic
def query_profit_by_exchange(analysis_id: int) -> list[dict]:
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from v_profits_by_exchange
                    where analysis_id=%s
                """,
                    [analysis_id],
                )
                li = []
                for raw in cursor.fetchall():
                    li.append(
                        {
                            "exchange_wallet": raw[1],
                            "realized_profit": raw[2],
                            "taxable_profit": raw[3],
                        }
                    )
                return li

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("query_profit_by_exchange query not successful.")


@transaction.atomic
def query_sell_profit_by_currency(analysis_id: int) -> list[dict]:
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from v_sell_profits_by_currency
                    where analysis_id=%s
                """,
                    [analysis_id],
                )
                li = []
                for raw in cursor.fetchall():
                    li.append(
                        {
                            "currency": raw[1],
                            "realized_profit": raw[2],
                            "taxable_profit": raw[3],
                        }
                    )
                return li

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper(
            "query_sell_profit_by_currency query not successful."
        )


@transaction.atomic
def query_sell_profit_by_exchange(analysis_id: int) -> list[dict]:
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from v_sell_profits_by_exchange
                    where analysis_id=%s
                """,
                    [analysis_id],
                )
                li = []
                for raw in cursor.fetchall():
                    li.append(
                        {
                            "exchange_wallet": raw[1],
                            "realized_profit": raw[2],
                            "taxable_profit": raw[3],
                        }
                    )
                return li

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper(
            "query_sell_profit_by_exchange query not successful."
        )


@transaction.atomic
def query_fees_by_currency(analysis_id: int) -> list[dict]:
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from v_fees_by_currency
                    where analysis_id=%s
                """,
                    [analysis_id],
                )
                li = []
                for raw in cursor.fetchall():
                    li.append(
                        {
                            "currency": raw[1],
                            "fee_sum": raw[2],
                        }
                    )
                return li

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("query_fees_by_currency query not successful.")


@transaction.atomic
def query_fees_by_exchange(analysis_id: int) -> list[dict]:
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select * from v_fees_by_exchange
                    where analysis_id=%s
                """,
                    [analysis_id],
                )
                li = []
                for raw in cursor.fetchall():
                    li.append(
                        {
                            "exchange_wallet": raw[1],
                            "fee_sum": raw[2],
                        }
                    )
                return li

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("query_fees_by_exchange query not successful.")


@transaction.atomic
def fetch_processable() -> Optional[dict]:
    query_str = """
        with merged as (
        (
            select
                'O' as type,
                ptid, poid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
                from_currency_id order_from_currency_id, from_amount order_from_amount,
                to_currency_id order_to_currency, to_amount order_to_amount,
                null as deposit_buy_datetime, null as deposit_type, null as deposit_currency,
                null as deposit_amount, null as deposit_taxable, -- placeholder for deposit
                null as transfer_from_exchange_wallet, null as transfer_currency,
                0 as transfer_amount -- placeholder for transfer
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
                ptaid ptid, ptfid sub_id, ana_id, datetime, fee, fee_currency_id,
                cooldown_until, created, exchange_wallet,
                null, null, null, null, -- placeholder for order
                null, null, null, null, null, -- placeholder for deposit
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
            set cooldown_until = CURRENT_TIMESTAMP + INTERVAL '50 second'
            where id=all(select ptid from selected)
                and not (id is null)
                and exists (select * from selected)
        )

        select s.*, a.base_currency_id
        from selected s
        join tax_analysis_portfolioanalysis a
        on s.ana_id=a.id;
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str)
                rawFetched = cursor.fetchall()
                print("rawFetched: ", rawFetched)

                if len(rawFetched) == 0:
                    return None

                for raw in rawFetched:
                    return {
                        "type": raw[0],
                        "ptid": raw[1],
                        "sub_id": raw[2],
                        "ana_id": raw[3],
                        "datetime": raw[4],
                        "fee": raw[5],
                        "fee_currency": raw[6],
                        "cooldown_until": raw[7],  # analysis cooldown (not tx)
                        "created": raw[8],
                        "exchange_wallet": raw[9],
                        "order_from_currency": raw[10],
                        "order_from_amount": raw[11],
                        "order_to_currency": raw[12],
                        "order_to_amount": raw[13],
                        "deposit_buy_datetime": raw[14],
                        "deposit_type": raw[15],
                        "deposit_currency": raw[16],
                        "deposit_amount": raw[17],
                        "deposit_taxable": raw[18],
                        "transfer_from_exchange_wallet": raw[19],
                        "transfer_currency": raw[20],
                        "transfer_amount": raw[21],
                        "base_currency_id": raw[22],
                    }

                return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("fetch_processable not successful.")


@transaction.atomic
def create_buy_order_from_processable_order(
    processable: ProcessableTransaction,
    processable_order: ProcessableOrder,
    analysable: Analysable,
    buy: AnalysisBuy,
) -> None:
    try:
        with transaction.atomic():
            processable_order.delete()
            processable.delete()
            analysable.save()
            buy.save()

    except IntegrityError:  # TODO try catch within decorator
        raise DatabaseErrorWrapper(
            "create_buy_order_from_processable_order not successful."
        )


@transaction.atomic
def create_sell_order_from_processable_order(
    processable: ProcessableTransaction,
    processable_order: ProcessableOrder,
    analysable: Analysable,
    sell: AnalysisSell,
) -> None:
    try:
        with transaction.atomic():
            processable_order.delete()
            processable.delete()
            analysable.save()
            sell.save()

    except IntegrityError:  # TODO try catch within decorator
        raise DatabaseErrorWrapper(
            "create_sell_order_from_processable_order not successful."
        )


@transaction.atomic
def create_buy_and_sell_order_from_processable_order(
    processable: ProcessableTransaction,
    processable_order: ProcessableOrder,
    analysableSell: Analysable,
    sell: AnalysisSell,
    analysableBuy: Analysable,
    buy: AnalysisBuy,
) -> None:
    try:
        with transaction.atomic():
            processable_order.delete()
            processable.delete()
            analysableSell.save()
            analysableBuy.save()
            sell.save()
            buy.save()

    except IntegrityError:  # TODO try catch within decorator
        raise DatabaseErrorWrapper(
            "create_buy_and_sell_order_from_processable_order not successful."
        )


@transaction.atomic
def create_transfer_from_processable_transfer(
    processable: ProcessableTransaction,
    processable_transfer: ProcessableTransfer,
    analysable: Analysable,
    transfer: AnalysisTransfer,
) -> None:
    try:
        with transaction.atomic():
            processable_transfer.delete()
            processable.delete()
            analysable.save()
            transfer.save()

    except IntegrityError:  # TODO try catch within decorator
        raise DatabaseErrorWrapper(
            "create_transfer_from_processable_transfer not successful."
        )


@transaction.atomic
def create_deposit_from_processable_deposit(
    processable: ProcessableTransaction,
    processable_deposit: ProcessableDeposit,
    analysable: Analysable,
    transfer: AnalysisDeposit,
) -> None:
    try:
        with transaction.atomic():
            processable_deposit.delete()
            processable.delete()
            analysable.save()
            transfer.save()

    except IntegrityError:  # TODO try catch within decorator
        raise DatabaseErrorWrapper(
            "create_deposit_from_processable_deposit not successful."
        )


@transaction.atomic
def allocate_analyzable() -> Optional[dict]:
    print("allocate_analyzable:")
    query_str = """
        with selected as (
            select
                coalesce(buy.id, sell.id, deposit.id, transfer.id) sub_id,
                ana.*,
                coalesce(buy.currency_id, sell.currency_id, deposit.currency_id, transfer.currency_id) currency,
                -- for all types
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
                analysis.taxable_period_days taxable_period_days

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
            set cooldown_until = CURRENT_TIMESTAMP + INTERVAL '50 second'
            where id=all(select analysis_id from selected)
                and not (id is null)
                and exists (select * from selected)
        )

        select * from selected;
    """

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(query_str)
                rawFetched = cursor.fetchall()

                if len(rawFetched) == 0:
                    return None

                for raw in rawFetched:
                    return {
                        "sub_id": raw[0],
                        "type": raw[1],
                        "tid": raw[2],
                        "analysis_id": raw[3],
                        "datetime": raw[4],
                        "analysed": raw[5],
                        "fee": raw[6],
                        "exchange_wallet": raw[7],
                        "algo": raw[8],
                        "transfer_algo": raw[9],
                        "taxable_period": raw[10],
                        "currency": raw[11],  # for all types
                        "amount": raw[12],  # for all types
                        "buy_sell_deposit_price": raw[13],  # buy/sell/deposit
                        "deposit_buy_datetime": raw[14],
                        "deposit_taxable": raw[15],
                        "transfer_from_exchange_wallet": raw[16],
                    }

                return None

    except IntegrityError:  # TODO try catch within decorator
        raise DatabaseErrorWrapper("allocate_analyzable not successful.")


@transaction.atomic
def consumable_from_buy_order(buy_order_id: int) -> bool:
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
def consumable_from_deposit(deposit_id: int) -> bool:
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
    analysis_id: int,
    exchange_wallet: str,
    currency: str,
    algo: AnalysisAlgorithm,
    error_tolerance: float = 0.0000000000001,
) -> Optional[dict]:
    print("fetch_next_consumable")

    # fifo: lowest date first
    # worst: lowest price first
    asc_desc = "asc"

    # highest date first
    # or highest price first
    if algo == AnalysisAlgorithm.ALGO_LIFO or algo == AnalysisAlgorithm.ALGO_OPTIMAL:
        asc_desc = "desc"

    # fifo, lifo
    order_by_attr = "consumable.cdatetime"

    # best, worst
    if algo == AnalysisAlgorithm.ALGO_OPTIMAL or algo == AnalysisAlgorithm.ALGO_WORST:
        order_by_attr = "consumable.cprice"

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
                print(
                    "fetch_next_consumable: ",
                    str(analysis_id),
                    str(exchange_wallet),
                    str(currency),
                )
                cursor.execute(
                    query_str,
                    [
                        str(analysis_id),
                        str(exchange_wallet),
                        str(currency),
                        str(error_tolerance),
                    ],
                )
                rawFetched = cursor.fetchall()
                print("fetch_next_consumable res: ", rawFetched)

                if len(rawFetched) == 0:
                    print("fetch_next_consumable: query was empty")
                    # TODO error handling
                    raise IntegrityError("fetch_next_consumable: query was empty")

                for raw in rawFetched:
                    return {
                        "id": raw[0],
                        "datetime": raw[1],
                        "type": raw[2],
                        "price": raw[3],
                        "amount": raw[4],
                        "consumed": raw[5],
                    }

                print("unknown error")
                return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("fetch_next_consumable not successful.")


@transaction.atomic
def fetch_already_allocated_sum(analysable_id: int) -> Optional[float]:
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
                    return float(raw[0])

                return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("fetch_already_allocated_sum not successful.")


@transaction.atomic
def analysable_already_done(analysable_id: int) -> None:
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
def consume_sell(
    analysis_id: int,
    analysable_id: int,
    consumed_id: int,
    consumed_amount: float,
    realized_profit: float,
    taxable_realized_profit: float,
    finished: bool,
) -> None:
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
                cursor.execute(
                    query_str,
                    [
                        str(analysis_id),
                        str(consumed_id),
                        str(analysable_id),
                        str(consumed_amount),
                        str(analysable_id),
                        str(realized_profit),
                        str(taxable_realized_profit),
                    ],
                )
                return

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("consume_sell not successful.")


def consume_transfer(
    analysis_id: int,
    analysable_id: int,
    consumed_id: int,
    consumed_amount: float,
    buy_datetime: datetime.datetime,
    buy_price: float,
    finished: bool,
) -> None:
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
                cursor.execute(
                    query_str,
                    [
                        str(analysis_id),
                        str(consumed_id),
                        str(analysable_id),
                        str(consumed_amount),
                        str(analysable_id),
                        str(buy_datetime),
                        str(buy_price),
                        str(consumed_amount),
                        str(analysable_id),
                    ],
                )
                return

    except IntegrityError as ie:
        print("consume_sell failed: ", ie)
        raise DatabaseErrorWrapper("consume_sell not successful.")


# todo fetch comsumed amount and calc difference:
# IMPORTANT: check if analysis object locked or everything atomic
# if locked: ensure that after cooldown commit isn't possible anymore
