# ALGORITHM
import datetime

from portfolio.models import transaction_type_from_char, Transaction, Order, BaseCurrency, Currency, Transfer, Deposit
from tax_analysis.analysis_worker.price_crawler import fetch_price
from tax_analysis.db import fetch_processable, create_sell_order_from_processable_order, \
    create_buy_order_from_processable_order, create_buy_and_sell_order_from_processable_order, \
    create_transfer_from_processable_transfer, create_deposit_from_processable_deposit

import requests

# TODO periodic analysis worker: delete processables & analysables of failed analysises
from tax_analysis.models import Analysable, AnalysisBuy, AnalysableType, AnalysisSell, ProcessableOrder, \
    ProcessableTransaction, ProcessableTransfer, AnalysisTransfer, ProcessableDeposit, AnalysisDeposit

""""
{
    'type': 'O'|'D'|'T', 
    'ptid': 656, 
    'sub_id': 505, 
    'fee': 9.557e-05, 
    'fee_currency': 'BNB', 
    'cooldown_until': None, 
    'created': datetime.datetime(2021, 12, 16, 23, 32, 12, 491880, tzinfo=datetime.timezone.utc), 
    'order_from_currency': 'EUR', 
    'order_from_amount': 30.0, 
    'order_to_currency': 'ADA', 
    'order_to_amount': 30.0, 
    'deposit_currency': None, 
    'deposit_amount': None, 
    'deposit_taxable': None, 
    'transfer_from_exchange_wallet': None, 
    'transfer_currency': None, 
    'transfer_amount': 0.0
}
"""
def processable_worker():
    print("dispatching processable_worker...")
    # cur = Currency.objects.get(tag="BTC")
    # base = BaseCurrency.objects.get(tag="EUR")
    # print("price:", fetch_price(cur, base, datetime.date(year=2020, month=12, day=12)))

    processable_map = fetch_processable()
    if processable_map is None:
        print("No processable found...")
        return

    try:
        trans_type = transaction_type_from_char(processable_map.get('type'))
        trans_datetime = datetime.datetime.fromisoformat(str(processable_map.get('datetime')))
        trans_fee = float(processable_map.get('fee'))
        trans_fee_cur_tag = str(processable_map.get('fee_currency'))
        trans_base_cur_tag = str(processable_map.get('base_currency_id'))
        trans_processable_tid = int(processable_map.get('ptid'))
        trans_sub_id = int(processable_map.get('sub_id'))

        processable_transaction = ProcessableTransaction.objects.get(id=trans_processable_tid)

        trans_analysis_id = int(processable_map.get('ana_id'))
        trans_exchange_wallet = processable_map.get('exchange_wallet')

        fee_currency = Currency.objects.get(tag=trans_fee_cur_tag)
        base_currency = BaseCurrency.objects.get(tag=trans_base_cur_tag)

        _final_fee_in_base = 0
        if trans_fee != 0 and trans_fee_cur_tag != "NONE":
            _final_fee_in_base = trans_fee * fetch_price(fee_currency, base_currency, trans_datetime)

        print("fee (", trans_fee_cur_tag, "->", trans_base_cur_tag, ")=", trans_fee, " -> ", _final_fee_in_base)

        if trans_type == Order:
            _order_from_currency = str(processable_map.get('order_from_currency'))
            _order_from_amount = str(processable_map.get('order_from_amount'))
            _order_to_currency = str(processable_map.get('order_to_currency'))
            _order_to_amount = str(processable_map.get('order_to_amount'))
            processable_order = ProcessableOrder.objects.get(id=trans_sub_id)

            print("order (", _order_from_currency, "->", _order_to_currency, ")=", _order_from_amount, " -> ",
                  _order_to_amount)

            print(_order_from_currency, _order_from_amount, _order_to_currency, _order_to_amount)

            order_from_currency = Currency.objects.get(tag=_order_from_currency)
            order_to_currency = Currency.objects.get(tag=_order_to_currency)

            if base_currency.tag == order_from_currency.tag:
                # from=analysis base -> buy order in respect to base
                # ------------------------------------------------------------------------
                order_from_currency = BaseCurrency.objects.get(tag=_order_from_currency)
                _final_price = fetch_price(order_to_currency, order_from_currency, trans_datetime)
                _analysable = Analysable(
                    analysis_id=trans_analysis_id,
                    datetime=trans_datetime,
                    type=AnalysableType.BUY_ORDER,
                    exchange_wallet=trans_exchange_wallet,
                    fee=_final_fee_in_base
                )
                create_buy_order_from_processable_order(
                    processable_transaction,
                    processable_order,
                    _analysable,
                    AnalysisBuy(
                        transaction=_analysable,
                        currency_id=order_to_currency.tag,
                        amount=_order_to_amount,
                        price=_final_price
                    )
                )
                return
                # ------------------------------------------------------------------------

            elif base_currency.tag == order_to_currency.tag:
                # to=analysis base -> sell order in respect to base
                # ------------------------------------------------------------------------
                order_to_currency = BaseCurrency.objects.get(tag=_order_to_currency)
                _final_price = fetch_price(order_from_currency, order_to_currency, trans_datetime)
                _analysable = Analysable(
                    analysis_id=trans_analysis_id,
                    datetime=trans_datetime,
                    type=AnalysableType.SELL_ORDER,
                    exchange_wallet=trans_exchange_wallet,
                    fee=_final_fee_in_base
                )
                create_sell_order_from_processable_order(
                    processable_transaction,
                    processable_order,
                    _analysable,
                    AnalysisSell(
                        transaction=_analysable,
                        currency_id=order_from_currency.tag,
                        amount=_order_from_amount,
                        price=_final_price
                    )
                )
                return
                # ------------------------------------------------------------------------

            else:  # two not base currencies -> swap -> create buy and sell analysis
                from_price_in_base = fetch_price(order_from_currency, base_currency, trans_datetime)
                to_price_in_base = fetch_price(order_to_currency, base_currency, trans_datetime)

                # sell ------------------------------------
                #
                _sell_analysable = Analysable(
                    analysis_id=trans_analysis_id,
                    datetime=trans_datetime,
                    type=AnalysableType.SELL_ORDER,
                    exchange_wallet=trans_exchange_wallet,
                    fee=_final_fee_in_base
                )
                _sell_order = AnalysisSell(
                    transaction=_sell_analysable,
                    currency_id=order_from_currency.tag,
                    amount=_order_from_amount,
                    price=from_price_in_base
                )
                # -----------------------------------------
                # buy -------------------------------------
                _buy_analysable = Analysable(
                    analysis_id=trans_analysis_id,
                    datetime=trans_datetime + datetime.timedelta(milliseconds=10),  # +10ms for causality
                    type=AnalysableType.BUY_ORDER,
                    exchange_wallet=trans_exchange_wallet,
                    fee=_final_fee_in_base
                )
                _buy_order = AnalysisBuy(
                    transaction=_buy_analysable,
                    currency_id=order_to_currency.tag,
                    amount=_order_to_amount,
                    price=to_price_in_base
                )
                # -----------------------------------------

                create_buy_and_sell_order_from_processable_order(
                    processable_transaction,
                    processable_order,
                    _sell_analysable, _sell_order,
                    _buy_analysable, _buy_order
                )
                return

        elif trans_type == Transfer:
            _transfer_from_exchange_wallet = str(processable_map.get('transfer_from_exchange_wallet'))
            _transfer_currency = str(processable_map.get('transfer_currency'))
            _transfer_amount = float(processable_map.get('transfer_amount'))
            processable_transfer = ProcessableTransfer.objects.get(id=trans_sub_id)
            currency = Currency.objects.get(id=_transfer_currency)

            _analysable = Analysable(
                analysis_id=trans_analysis_id,
                datetime=trans_datetime,
                type=AnalysableType.TRANSFER,
                exchange_wallet=trans_exchange_wallet,
                fee=_final_fee_in_base
            )

            create_transfer_from_processable_transfer(
                processable_transaction,
                processable_transfer,
                _analysable,
                AnalysisTransfer(
                    transaction=_analysable,
                    from_exchange_wallet=_transfer_from_exchange_wallet,
                    currency=currency.tag,
                    amount=_transfer_amount
                )
            )
            return

        elif trans_type == Deposit:
            _deposit_currency = str(processable_map.get('transfer_currency'))
            _deposit_amount = float(processable_map.get('transfer_amount'))
            _deposit_taxable = float(processable_map.get('transfer_amount'))
            processable_deposit = ProcessableDeposit.objects.get(id=trans_sub_id)
            currency = Currency.objects.get(id=_deposit_currency)

            price = fetch_price(currency, base_currency, trans_datetime)

            _analysable = Analysable(
                analysis_id=trans_analysis_id,
                datetime=trans_datetime,
                type=AnalysableType.DEPOSIT,
                exchange_wallet=trans_exchange_wallet,
                fee=_final_fee_in_base
            )

            create_deposit_from_processable_deposit(
                processable_transaction,
                processable_deposit,
                _analysable,
                AnalysisDeposit(
                    transaction=_analysable,
                    currency=currency.tag,
                    amount=_deposit_amount,
                    price=price,
                    taxable=_deposit_taxable
                )
            )
            return

        else:
            raise NotImplementedError

    except Exception as ex:
        print("ERROR:", ex)
        return
