import datetime

from django.db import IntegrityError, transaction
from django.db import connection
from django.db.utils import DatabaseErrorWrapper

from tax_analysis.models import Analysable, AnalysisBuy, AnalysisSell, ProcessableTransaction, ProcessableOrder, \
    ProcessableTransfer, AnalysisTransfer, ProcessableDeposit, AnalysisDeposit


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
                null as deposit_currency, null as deposit_amount, null as deposit_taxable, -- placeholder for deposit
                null as transfer_from_exchange_wallet, null as transfer_currency, 0 as transfer_amount -- placeholder for deposit
            from v_tax_analysis_processableoder
        ) union (
            select 
                'D',
                ptid, pdid sub_id, ana_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
                null, null, null, null, -- placeholder for deposit
                currency_id, amount, taxable,
                null, null, null -- placeholder for deposit
            from v_tax_analysis_processabledeposit
        ) union (
            select 
                'T',
                ptaid ptid, ana_id, ptfid sub_id, datetime, fee, fee_currency_id, cooldown_until, created, exchange_wallet,
                null, null, null, null, -- placeholder for order
                null, null, null, -- placeholder for deposit
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
                    datetime.timedelta(minutes=5)

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

                        'deposit_currency': raw[14],
                        'deposit_amount': raw[15],
                        'deposit_taxable': raw[16],

                        'transfer_from_exchange_wallet': raw[17],
                        'transfer_currency': raw[18],
                        'transfer_amount': raw[19],

                        'base_currency_id': raw[20],
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
