from datetime import datetime
import dateutil.parser

from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.utils import json

from cryptotax_backend.utils import error_response, success
from portfolio.db import query_portfolios_of_user, query_portfolio_of_user_by_id
from portfolio.helper.rand import random_portfolio
from portfolio.models import Order, Transaction, Portfolio, Currency, Deposit, Transfer
from tax_analysis.db import save_orders_transactions, save_deposits_transactions, save_transfers_transactions
from utils.decorators import ensure_authenticated_user


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_list_my(request, *args, **kwargs):
    portfolios = query_portfolios_of_user(request.user.id)
    return success(200, 0, "portfolios retrieved successfully.", data=portfolios)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_details(request, pid, *args, **kwargs):
    portfolio_query = Portfolio.objects.filter(id=pid)
    if not portfolio_query.exists():
        return error_response(400, 1, "portfolio does not exist!")

    portfolio = portfolio_query.first()
    if portfolio.user.id != request.user.id:
        return error_response(401, 1, "you are not allowed to edit this portfolio!")

    portfolio = query_portfolio_of_user_by_id(request.user.id, pid)
    return success(200, 0, "portfolio retrieved successfully.", data=portfolio)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_create(request, *args, **kwargs):
    try:
        title = request.GET.get('title', None)
        print("request: ", title)
        if title is None or len(str(title)) < 4:
            return error_response(400, 2, "title argument has to have length >=4!")

        # TODO: limit portfolios per user

        if Portfolio.objects.filter(user_id=request.user.id, title=title).exists():
            return error_response(400, 2, "You already have a portfolio with that name!")

        new_portfolio = Portfolio(user=request.user, title=title)
        new_portfolio.save()

        return success(200, 0, "created portfolio successfully.", data={
            'id': new_portfolio.id
        })

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )


@api_view(['PUT'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_update(request, pid, *args, **kwargs):
    try:
        portfolio_query = Portfolio.objects.filter(id=pid)
        if not portfolio_query.exists():
            return error_response(400, 1, "portfolio does not exist!")

        portfolio = portfolio_query.first()
        if portfolio.user.id != request.user.id:
            return error_response(401, 1, "you are not allowed to edit this portfolio!")

        title = request.GET.get('title', None)
        if title is None or len(str(title)) < 4:
            return error_response(400, 2, "title argument has to have length >=4!")

        portfolio.title = title
        portfolio.save()

        return success(200, 0, "updated portfolio successfully.", data={
            'id': portfolio.id
        })

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_delete(request, *args, **kwargs):
    try:
        pid_list_raw = request.GET.get('pids', "[]")
        pid_list = json.loads(pid_list_raw)

        deleted_ids = []

        for pid in pid_list:
            try:
                portfolio_query = Portfolio.objects.filter(id=pid)
                if not portfolio_query.exists():
                    continue

                portfolio = portfolio_query.first()
                if portfolio.user.id != request.user.id:
                    return error_response(401, 1, "you are not allowed to edit this portfolio!")

                portfolio.delete()
                deleted_ids.append(pid)

            except Exception as ex:
                print(ex)

        return success(200, 0, "deleted portfolios successfully.", data={
            'ids': deleted_ids
        })

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )


# [Transactions] @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_list_reports(request, *args, **kwargs):
    portfolios = query_portfolios_of_user(request.user.id)
    return success(200, 0, "portfolios retrieved successfully.", data=portfolios)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_list_txs(request, *args, **kwargs):
    portfolios = query_portfolios_of_user(request.user.id)
    return success(200, 0, "portfolios retrieved successfully.", data=portfolios)


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def create_order_list(request, *args, **kwargs):
    orders = []

    portfolio_id = int(request.GET.get("portfolio_id", -1))
    if portfolio_id < 1:
        return error_response(400, 0, "cannot parse portfolio_id!")

    portfolio = Portfolio.objects.filter(id=portfolio_id)
    if not portfolio.exists():
        return error_response(400, 1, "portfolio_id not existing!")

    # TODO improve ownership (multi owner)?
    if portfolio.first().user.id != request.user.id:
        return error_response(401, 0, "not allowed to access this portfolio!")

    try:
        req_data = json.loads(request.body)
        req_orders = list(req_data)

        for reqmap in req_orders:
            _datetime = dateutil.parser.isoparse(str(reqmap['datetime']))
            _exchange_wallet = str(reqmap.get("exchange_wallet", None))

            _fee = float(reqmap.get('fee', None))
            _fee_currency = str(reqmap.get("fee_currency", None)).upper()

            _from_amount = float(reqmap.get('from_amount', None))
            _from_currency = str(reqmap.get('from_currency', None)).upper()

            _to_amount = float(reqmap.get('to_amount', None))
            _to_currency = str(reqmap.get('to_currency', None)).upper()

            transact = Transaction()
            order = Order()
            order.transaction = transact

            transact.portfolio_id = portfolio_id
            transact.datetime = _datetime
            transact.type = 'O'
            transact.exchange_wallet = _exchange_wallet

            if _fee_currency != "NONE":
                transact.fee = _fee
                transact.fee_currency_id = _fee_currency

            from_cur = None
            if _from_currency != "NONE":
                formcurquery = Currency.objects.filter(tag=_from_currency)
                if not formcurquery.exists():
                    return error_response(400, 2, "invalid currency.")
                from_cur = formcurquery.first()
            else:
                raise ValueError("from_currency must not be empty!")

            to_cur = None
            if _to_currency != "NONE":
                formcurquery = Currency.objects.filter(tag=_to_currency)
                if not formcurquery.exists():
                    return error_response(400, 2, "invalid currency.")
                to_cur = formcurquery.first()
            else:
                raise ValueError("from_currency must not be empty!")

            order.from_amount = _from_amount
            order.from_currency = from_cur

            order.to_amount = _to_amount
            order.to_currency = to_cur

            orders.append(order)

    except ValueError as err:
        print(err)
        return error_response(400, 5, "error parsing request data.")

    try:
        # check if topic exists
        save_orders_transactions(orders)
        return success(200, 0, "orders created successfully.")

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def create_deposit_list(request, *args, **kwargs):
    deposits = []

    portfolio_id = int(request.GET.get("portfolio_id", -1))
    if portfolio_id < 1:
        return error_response(400, 0, "cannot parse portfolio_id!")

    portfolio = Portfolio.objects.filter(id=portfolio_id)
    if not portfolio.exists():
        return error_response(400, 1, "portfolio_id not existing!")

    # TODO improve ownership (multi owner)?
    if portfolio.first().user.id != request.user.id:
        return error_response(401, 0, "not allowed to access this portfolio!")

    try:
        req_data = json.loads(request.body)
        req_deposits = list(req_data)

        for reqmap in req_deposits:
            _datetime = dateutil.parser.isoparse(str(reqmap['datetime']))
            _exchange_wallet = str(reqmap.get("exchange_wallet", None))

            _fee = float(reqmap.get('fee', None))
            _fee_currency = str(reqmap.get("fee_currency", None)).upper()

            _amount = float(reqmap.get('amount', None))
            _currency = str(reqmap.get('currency', None)).upper()
            _taxable = float(reqmap.get('taxable', None))

            _buy_datetime_str = reqmap['buy_datetime']
            _buy_datetime = _datetime \
                if (_buy_datetime_str is None or len(_buy_datetime_str) == 0) \
                else dateutil.parser.isoparse(str(_buy_datetime_str))

            # TRANSACTION

            transact = Transaction()
            deposit = Deposit()
            deposit.transaction = transact

            transact.portfolio_id = portfolio_id
            transact.datetime = _datetime
            transact.type = 'D'
            transact.exchange_wallet = _exchange_wallet

            if _fee_currency != "NONE":
                transact.fee = _fee
                transact.fee_currency_id = _fee_currency

            # DEPOSIT

            currency = None
            if _currency != "NONE":
                curquery = Currency.objects.filter(tag=_currency)
                if not curquery.exists():
                    return error_response(400, 2, "invalid currency.")
                currency = curquery.first()
            else:
                raise ValueError("from_currency must not be empty!")

            deposit.buy_datetime = _buy_datetime
            deposit.amount = _amount
            deposit.currency = currency
            deposit.taxable = _taxable

            deposits.append(deposit)

    except ValueError as err:
        print(err)
        return error_response(400, 5, "error parsing request data.")

    try:
        # check if topic exists
        save_deposits_transactions(deposits)
        return success(200, 0, "deposits created successfully.")

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def create_transfer_list(request, *args, **kwargs):
    transfers = []

    portfolio_id = int(request.GET.get("portfolio_id", -1))
    if portfolio_id < 1:
        return error_response(400, 0, "cannot parse portfolio_id!")

    portfolio = Portfolio.objects.filter(id=portfolio_id)
    if not portfolio.exists():
        return error_response(400, 1, "portfolio_id not existing!")

    # TODO improve ownership (multi owner)?
    if portfolio.first().user.id != request.user.id:
        return error_response(401, 0, "not allowed to access this portfolio!")

    try:
        req_data = json.loads(request.body)
        req_transfers = list(req_data)

        for reqmap in req_transfers:
            _datetime = dateutil.parser.isoparse(str(reqmap['datetime']))
            _exchange_wallet = str(reqmap.get("exchange_wallet", None))

            _fee = float(reqmap.get('fee', None))
            _fee_currency = str(reqmap.get("fee_currency", None)).upper()

            _from_exchange_wallet = str(reqmap.get('from_exchange_wallet', None))
            _amount = float(reqmap.get('amount', None))
            _currency = str(reqmap.get('currency', None)).upper()

            # TRANSACTION

            transact = Transaction()
            transfer = Transfer()
            transfer.transaction = transact

            transact.portfolio_id = portfolio_id
            transact.datetime = _datetime
            transact.type = 'T'
            transact.exchange_wallet = _exchange_wallet

            if _fee_currency != "NONE":
                transact.fee = _fee
                transact.fee_currency_id = _fee_currency

            # TRANSFER

            currency = None
            if _currency != "NONE":
                curquery = Currency.objects.filter(tag=_currency)
                if not curquery.exists():
                    return error_response(400, 2, "invalid currency.")
                currency = curquery.first()
            else:
                raise ValueError("from_currency must not be empty!")

            transfer.from_exchange_wallet = _from_exchange_wallet
            transfer.amount = _amount
            transfer.currency = currency

            transfers.append(transfer)

    except ValueError as err:
        print(err)
        return error_response(400, 5, "error parsing request data.")

    try:
        # check if topic exists
        save_transfers_transactions(transfers)
        return success(200, 0, "transfers created successfully.")

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )
