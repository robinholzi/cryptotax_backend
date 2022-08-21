from math import ceil
from typing import Any

import dateutil.parser
from django.core.paginator import Paginator
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils import json

from portfolio.db import (
    query_number_portfolios_of_user,
    query_portfolio_of_user_by_id,
    query_portfolios_of_user,
)
from portfolio.models import (
    BaseCurrency,
    Currency,
    Deposit,
    Order,
    Portfolio,
    Transaction,
    Transfer,
)
from tax_analysis.db.order_management import (
    save_deposits_transactions,
    save_orders_transactions,
    save_transfers_transactions,
)
from tax_analysis.db.processing_analysis import (
    query_fees_by_currency,
    query_fees_by_exchange,
    query_portfolio_analysis_list,
    query_portfolio_analysis_number,
    query_profit_by_currency,
    query_profit_by_exchange,
    query_result_detail,
    query_sell_profit_by_currency,
    query_sell_profit_by_exchange,
)
from tax_analysis.models import PortfolioAnalysis
from tax_analysis.report_serializer import PortfolioReportCreateSerializer
from utils.auth.decorators import ensure_authenticated_user
from utils.exceptions.exception_handlers import exception_handler
from utils.response_wrappers import (
    error_response,
    success_response,
)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_list_my(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        raw_page_size = int(request.GET.get("page_size", "30"))
        raw_page_no = int(request.GET.get("page_no", "1"))
    except KeyError:
        return error_response(400, 1, "page_size or page_no GET params malformed!")

    page_size = max(5, min(200, raw_page_size))
    page_no = max(1, raw_page_no)

    portfolios = query_portfolios_of_user(request.user.id, page_size, page_no)
    number_portfolios = query_number_portfolios_of_user(request.user.id)
    return success_response(
        200,
        0,
        "portfolios retrieved successfully.",
        data={
            "page_size": page_size,
            "number_pages": ceil(float(number_portfolios) / page_size),
            "number_portfolios": number_portfolios,
            "portfolios": portfolios,
        },
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_details(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    portfolio_query = Portfolio.objects.filter(id=pid)
    if not portfolio_query.exists():
        return error_response(400, 1, "portfolio does not exist!")

    portfolio = portfolio_query.first()
    if portfolio.user.id != request.user.id:
        return error_response(401, 1, "you are not allowed to edit this portfolio!")

    portfolio = query_portfolio_of_user_by_id(request.user.id, pid)
    return success_response(200, 0, "portfolio retrieved successfully.", data=portfolio)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_create(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        title = request.GET.get("title", None)
        if title is None or len(str(title)) < 4:
            return error_response(400, 2, "title argument has to have length >=4!")

        # TODO: limit portfolios per user

        if Portfolio.objects.filter(user_id=request.user.id, title=title).exists():
            return error_response(
                400, 2, "You already have a portfolio with that name!"
            )

        new_portfolio = Portfolio(user=request.user, title=title)
        new_portfolio.save()

        return success_response(
            200, 0, "created portfolio successfully.", data={"id": new_portfolio.id}
        )

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


@api_view(["PUT"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_update(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        portfolio_query = Portfolio.objects.filter(id=pid)
        if not portfolio_query.exists():
            return error_response(400, 1, "portfolio does not exist!")

        portfolio = portfolio_query.first()
        if portfolio.user.id != request.user.id:
            return error_response(401, 1, "you are not allowed to edit this portfolio!")

        title = request.GET.get("title", None)
        if title is None or len(str(title)) < 4:
            return error_response(400, 2, "title argument has to have length >=4!")

        portfolio.title = title
        portfolio.save()

        return success_response(
            200, 0, "updated portfolio successfully.", data={"id": portfolio.id}
        )

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_delete(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        pid_list_raw = request.GET.get("pids", "[]")
        pid_list = json.loads(pid_list_raw)

        deleted_ids = []

        for pid in pid_list:
            try:
                portfolio_query = Portfolio.objects.filter(id=pid)
                if not portfolio_query.exists():
                    continue

                portfolio = portfolio_query.first()
                if portfolio.user.id != request.user.id:
                    return error_response(
                        401, 1, "you are not allowed to edit this portfolio!"
                    )

                portfolio.delete()
                deleted_ids.append(pid)

            except Exception as ex:
                print(ex)

        return success_response(
            200, 0, "deleted portfolios successfully.", data={"ids": deleted_ids}
        )

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


# [Reports] @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_list_reports(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        # TODO abstract in reusable method -> decorator
        pquery = Portfolio.objects.filter(id=pid)
        if not pquery.exists():
            return error_response(400, 0, "portfolio does not exist.")

        portfolio = pquery.first()

        if portfolio.user.id != request.user.id:
            return error_response(401, 1, "you are not allowed to edit this portfolio!")

        try:
            raw_page_size = int(request.GET.get("page_size", "30"))
            raw_page_no = int(request.GET.get("page_no", "1"))
        except KeyError:
            return error_response(400, 1, "page_size or page_no GET params malformed!")

        page_size = max(5, min(200, raw_page_size))
        page_no = max(1, raw_page_no)

        reports = query_portfolio_analysis_list(portfolio.id, page_size, page_no)
        number_reports = query_portfolio_analysis_number(portfolio.id)
        return success_response(
            200,
            0,
            "portfolios retrieved successfully.",
            data={
                "page_size": page_size,
                "number_pages": ceil(float(number_reports) / page_size),
                "number_reports": number_reports,
                "reports": reports,
            },
        )
    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.")


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_report_create(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    serializer = PortfolioReportCreateSerializer(
        uid=request.user.id, pid=pid, data=request.POST
    )
    try:
        if serializer.is_valid():
            return success_response(
                200,
                0,
                "analysis created.",
                data={"id": serializer.create(serializer.validated_data)},
            )
        else:
            return error_response(
                400, 0, "failed to instantiate analysis!", data=serializer.errors
            )
    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.")


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_report_delete(
    request: Request, rid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        pquery = PortfolioAnalysis.objects.filter(id=rid)
        if not pquery.exists():
            return error_response(400, 0, "report analysis does not exist.")

        analysis = pquery.first()

        if analysis.portfolio.user.id != request.user.id:
            return error_response(401, 1, "you are not allowed to edit this analysis!")

        analysis.delete()
        return success_response(200, 0, "analysis deleted successfully.")
    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.")


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_reports_delete(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        rid_list_raw = request.GET.get("rids", "[]")
        rid_list = json.loads(rid_list_raw)

        deleted_ids = []

        for rid in rid_list:
            try:
                report_query = PortfolioAnalysis.objects.filter(id=rid)
                if not report_query.exists():
                    continue

                report = report_query.first()
                if report.portfolio.user.id != request.user.id:
                    return error_response(
                        401, 1, "you are not allowed to edit this report!"
                    )

                report.delete()
                deleted_ids.append(rid)

            except Exception as ex:
                print(ex)

        return success_response(
            200, 0, "deleted reports successfully.", data={"ids": deleted_ids}
        )

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


# TODO steuerlast nach jahr gruppieren
# TODO download link for mapping excel (extra endpoint)
# TODO realized profit in respect to coin

# TODO!!!!!! only return statiscal data when report generation is finished (also frontend check)
# TODO!!!!!! only return statiscal data when report generation is finished (also frontend check)
# TODO!!!!!! only return statiscal data when report generation is finished (also frontend check)
# TODO!!!!!! only return statiscal data when report generation is finished (also frontend check)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_report_detail(
    request: Request, rid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        pquery = PortfolioAnalysis.objects.filter(id=rid)
        if not pquery.exists():
            return error_response(400, 0, "report analysis does not exist.")

        analysis = pquery.first()

        if analysis.portfolio.user.id != request.user.id:
            return error_response(401, 1, "you are not allowed to view this analysis!")

        data = query_result_detail(analysis.id)
        if data is None:
            return error_response(500, 1, "internal error. querying failed.")

        # TODO by coin / by wallet / by year & wallet / by year & coin

        profits_by_currency = query_profit_by_currency(analysis.id)
        profits_by_exchange = query_profit_by_exchange(analysis.id)
        sell_profits_by_currency = query_sell_profit_by_currency(analysis.id)
        sell_profits_by_exchange = query_sell_profit_by_exchange(analysis.id)
        fees_by_currency = query_fees_by_currency(analysis.id)
        fees_by_exchange = query_fees_by_exchange(analysis.id)

        return success_response(
            200,
            0,
            "analysis retrieved successfully.",
            data={
                "portfolio_id": analysis.portfolio_id,
                "ana_id": analysis.id,
                "title": analysis.title,
                "created": analysis.created,
                "mode": analysis.mode,
                "failed": analysis.failed,
                "algo": analysis.algo,
                "transfer_algo": analysis.transfer_algo,
                "base_currency": analysis.base_currency_id,
                "mining_tax_method": analysis.mining_tax_method,
                "mining_deposit_profit_rate": analysis.mining_deposit_profit_rate,
                "taxable_period_days": analysis.taxable_period_days,
                "txs": data["txs"],
                "currencies": data["currencies"],
                "exchanges": data["exchanges"],
                "taxable_profit": data["taxable_profit"],
                "realized_profit": data["realized_profit"],
                "deposit_profit": data["deposit_profit"],
                "sell_profit": data["sell_profit"],
                "fee_sum": data["fee_sum"],
                "progress": data["progress"],
                "msg": data["msg"],
                "profits_by_currency": profits_by_currency,
                "profits_by_exchange": profits_by_exchange,
                "sell_profits_by_currency": sell_profits_by_currency,
                "sell_profits_by_exchange": sell_profits_by_exchange,
                "fees_by_currency": fees_by_currency,
                "fees_by_exchange": fees_by_exchange,
            },
        )
    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.")


# [Transactions] @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_list_orders(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        # TODO abstract in reusable method -> decorator
        pquery = Portfolio.objects.filter(id=pid)
        if not pquery.exists():
            return error_response(400, 0, "portfolio does not exist.")

        portfolio = pquery.first()

        if portfolio.user.id != request.user.id:
            return error_response(401, 1, "you are not allowed to view this portfolio!")

        try:
            raw_page_size = int(request.GET.get("page_size", "30"))
            raw_page_no = int(request.GET.get("page_no", "1"))
        except KeyError:
            return error_response(400, 1, "page_size or page_no GET params malformed!")

        page_size = max(5, min(200, raw_page_size))
        page_no = max(1, raw_page_no)

        txs_query = Order.objects.filter(transaction__portfolio=pid).order_by(
            "-transaction__datetime"
        )
        order_paginator = Paginator(txs_query, page_size)
        orders = []
        object_list = order_paginator.page(page_no).object_list
        for order_obj in object_list:
            orders.append(
                {
                    "tid": order_obj.transaction_id,
                    "oid": order_obj.id,
                    "from_currency": order_obj.from_currency_id,
                    "from_amount": order_obj.from_amount,
                    "to_currency": order_obj.to_currency_id,
                    "to_amount": order_obj.to_amount,
                    "datetime": order_obj.transaction.datetime,
                    "exchange_wallet": order_obj.transaction.exchange_wallet,
                    "fee_currency": order_obj.transaction.fee_currency_id,
                    "fee": order_obj.transaction.fee,
                }
            )

        num_txs = txs_query.count()
        return success_response(
            200,
            0,
            "transaction list retrieved successfully.",
            data={
                "page_size": page_size,  # TODO unused
                "number_pages": ceil(float(num_txs) / page_size),  # TODO unused
                "number_txs": num_txs,
                "txs": orders,
            },
        )
    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.")


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@exception_handler()
@ensure_authenticated_user
def portfolio_list_deposits(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    # TODO abstract in reusable method -> decorator
    pquery = Portfolio.objects.filter(id=pid)
    if not pquery.exists():
        return error_response(400, 0, "portfolio does not exist.")

    portfolio = pquery.first()

    if portfolio.user.id != request.user.id:
        return error_response(401, 1, "you are not allowed to view this portfolio!")

    try:
        raw_page_size = int(request.GET.get("page_size", "30"))
        raw_page_no = int(request.GET.get("page_no", "1"))
    except KeyError:
        return error_response(400, 1, "page_size or page_no GET params malformed!")

    page_size = max(5, min(200, raw_page_size))
    page_no = max(1, raw_page_no)

    txs_query = Deposit.objects.filter(transaction__portfolio=pid).order_by(
        "-transaction__datetime"
    )
    deposit_paginator = Paginator(txs_query, page_size)
    deposits = []
    object_list = deposit_paginator.page(page_no).object_list
    for deposit_obj in object_list:
        deposits.append(
            {
                "tid": deposit_obj.transaction_id,
                "did": deposit_obj.id,
                "currency": deposit_obj.currency_id,
                "amount": deposit_obj.amount,
                "buy_datetime": deposit_obj.buy_datetime,
                "taxable": deposit_obj.taxable,
                "type": deposit_obj.type,
                "datetime": deposit_obj.transaction.datetime,
                "exchange_wallet": deposit_obj.transaction.exchange_wallet,
                "fee_currency": deposit_obj.transaction.fee_currency_id,
                "fee": deposit_obj.transaction.fee,
            }
        )

    num_txs = txs_query.count()
    return success_response(
        200,
        0,
        "transaction list retrieved successfully.",
        data={
            "page_size": page_size,  # TODO unused
            "number_pages": ceil(float(num_txs) / page_size),  # TODO unused
            "number_txs": num_txs,
            "txs": deposits,
        },
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@exception_handler()
@ensure_authenticated_user
def portfolio_list_transfers(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    # TODO abstract in reusable method -> decorator
    pquery = Portfolio.objects.filter(id=pid)
    if not pquery.exists():
        return error_response(400, 0, "portfolio does not exist.")

    portfolio = pquery.first()

    if portfolio.user.id != request.user.id:
        return error_response(401, 1, "you are not allowed to view this portfolio!")

    try:
        raw_page_size = int(request.GET.get("page_size", "30"))
        raw_page_no = int(request.GET.get("page_no", "1"))
    except KeyError:
        return error_response(400, 1, "page_size or page_no GET params malformed!")

    page_size = max(5, min(200, raw_page_size))
    page_no = max(1, raw_page_no)

    # TODO paging
    txs_query = Transfer.objects.filter(transaction__portfolio=pid).order_by(
        "-transaction__datetime"
    )
    transfer_paginator = Paginator(txs_query, page_size)
    transfers = []
    object_list = transfer_paginator.page(page_no).object_list
    for transfer_obj in object_list:
        transfers.append(
            {
                "taid": transfer_obj.transaction_id,
                "tfid": transfer_obj.id,
                "currency": transfer_obj.currency_id,
                "amount": transfer_obj.amount,
                "from_exchange_wallet": transfer_obj.from_exchange_wallet,
                "datetime": transfer_obj.transaction.datetime,
                "exchange_wallet": transfer_obj.transaction.exchange_wallet,
                "fee_currency": transfer_obj.transaction.fee_currency_id,
                "fee": transfer_obj.transaction.fee,
            }
        )

    num_txs = txs_query.count()
    return success_response(
        200,
        0,
        "transaction list retrieved successfully.",
        data={
            "page_size": page_size,  # TODO unused
            "number_pages": ceil(float(num_txs) / page_size),  # TODO unused
            "number_txs": num_txs,
            "txs": transfers,
        },
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def create_order_list(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    orders = []

    # TODO abstract in reusable method -> decorator
    pquery = Portfolio.objects.filter(id=pid)
    if not pquery.exists():
        return error_response(400, 0, "portfolio does not exist.")

    portfolio = pquery.first()

    # TODO improve ownership (multi owner)?
    if portfolio.user.id != request.user.id:
        return error_response(401, 1, "you are not allowed to access this portfolio!")

    try:
        req_data = json.loads(request.body)
        req_orders = list(req_data)

        for reqmap in req_orders:
            _datetime = dateutil.parser.isoparse(str(reqmap["datetime"]))
            _exchange_wallet = str(reqmap.get("exchange_wallet", None))

            _fee = float(reqmap.get("fee", None))
            _fee_currency = str(reqmap.get("fee_currency", None)).upper()

            _from_amount = float(reqmap.get("from_amount", None))
            _from_currency = str(reqmap.get("from_currency", None)).upper()

            _to_amount = float(reqmap.get("to_amount", None))
            _to_currency = str(reqmap.get("to_currency", None)).upper()

            transact = Transaction()
            order = Order()
            order.transaction = transact

            transact.portfolio_id = pid
            transact.datetime = _datetime
            transact.type = "O"
            transact.exchange_wallet = _exchange_wallet

            if _fee_currency != "NONE":
                transact.fee = _fee
                transact.fee_currency_id = _fee_currency

            if _from_currency != "NONE":
                formcurquery = Currency.objects.filter(tag=_from_currency)
                if not formcurquery.exists():
                    print("reqmap: ", reqmap)
                    return error_response(
                        400,
                        2,
                        "invalid currency.",
                        message=f"The currency '{_from_currency}' does not exist!'",
                    )
                from_cur = formcurquery.first()
            else:
                raise ValueError("from_currency must not be empty!")

            if _to_currency != "NONE":
                formcurquery = Currency.objects.filter(tag=_to_currency)
                if not formcurquery.exists():
                    print("reqmap: ", reqmap)
                    return error_response(
                        400,
                        2,
                        "invalid currency.",
                        message=f"The currency '{_to_currency}' does not exist!'",
                    )
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
        return success_response(200, 0, "orders created successfully.")

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def create_deposit_list(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    deposits = []

    # TODO abstract in reusable method -> decorator
    pquery = Portfolio.objects.filter(id=pid)
    if not pquery.exists():
        return error_response(400, 0, "portfolio does not exist.")

    portfolio = pquery.first()

    # TODO improve ownership (multi owner)?
    if portfolio.user.id != request.user.id:
        return error_response(401, 1, "you are not allowed to access this portfolio!")

    try:
        req_data = json.loads(request.body)
        req_deposits = list(req_data)

        for reqmap in req_deposits:
            _datetime = dateutil.parser.isoparse(str(reqmap["datetime"]))
            _exchange_wallet = str(reqmap.get("exchange_wallet", None))

            _fee = float(reqmap.get("fee", None))
            _fee_currency = str(reqmap.get("fee_currency", None)).upper()

            _deposit_type = reqmap["type"]
            if _deposit_type not in ["G", "C", "POW", "CI"]:
                return error_response(
                    400, 2, "deposit type must be either 'G', 'C', 'POW' or 'CI'."
                )

            _buy_datetime_str = reqmap["buy_datetime"]
            _buy_datetime = (
                _datetime
                if (_buy_datetime_str is None or len(_buy_datetime_str) == 0)
                else dateutil.parser.isoparse(str(_buy_datetime_str))
            )

            _amount = float(reqmap.get("amount", None))
            _currency = str(reqmap.get("currency", None)).upper()
            _taxable = float(reqmap.get("taxable", None))

            # TRANSACTION
            transact = Transaction()
            deposit = Deposit()
            deposit.transaction = transact

            transact.portfolio_id = pid
            transact.datetime = _datetime
            transact.type = "G"
            transact.exchange_wallet = _exchange_wallet

            if _fee_currency != "NONE":
                transact.fee = _fee
                transact.fee_currency_id = _fee_currency

            # DEPOSIT
            if _currency != "NONE":
                curquery = Currency.objects.filter(tag=_currency)
                if not curquery.exists():
                    return error_response(
                        400,
                        3,
                        "invalid currency.",
                        message=f"The currency '{_currency}' does not exist!'",
                    )
                currency = curquery.first()
            else:
                raise ValueError("from_currency must not be empty!")

            deposit.type = _deposit_type
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
        return success_response(200, 0, "deposits created successfully.")

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def create_transfer_list(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    transfers = []

    # TODO abstract in reusable method -> decorator
    pquery = Portfolio.objects.filter(id=pid)
    if not pquery.exists():
        return error_response(400, 0, "portfolio does not exist.")

    portfolio = pquery.first()

    # TODO improve ownership (multi owner)?
    if portfolio.user.id != request.user.id:
        return error_response(401, 1, "you are not allowed to access this portfolio!")

    try:
        req_data = json.loads(request.body)
        req_transfers = list(req_data)

        for reqmap in req_transfers:
            _datetime = dateutil.parser.isoparse(str(reqmap["datetime"]))
            _exchange_wallet = str(reqmap.get("exchange_wallet", None))

            _fee = float(reqmap.get("fee", None))
            _fee_currency = str(reqmap.get("fee_currency", None)).upper()

            _from_exchange_wallet = str(reqmap.get("from_exchange_wallet", None))
            _amount = float(reqmap.get("amount", None))
            _currency = str(reqmap.get("currency", None)).upper()

            # TRANSACTION
            transact = Transaction()
            transfer = Transfer()
            transfer.transaction = transact

            transact.portfolio_id = pid
            transact.datetime = _datetime
            transact.type = "T"
            transact.exchange_wallet = _exchange_wallet

            if _fee_currency != "NONE":
                transact.fee = _fee
                transact.fee_currency_id = _fee_currency

            # TRANSFER
            currency = None
            if _currency != "NONE":
                curquery = Currency.objects.filter(tag=_currency)
                if not curquery.exists():
                    return error_response(
                        400,
                        2,
                        "invalid currency.",
                        message=f"The currency '{_currency}' does not exist!'",
                    )
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
        return success_response(200, 0, "transfers created successfully.")

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


@api_view(["DELETE"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_txs_delete(
    request: Request, pid: int, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        # TODO abstract in reusable method -> decorator
        pquery = Portfolio.objects.filter(id=pid)
        if not pquery.exists():
            return error_response(400, 0, "portfolio does not exist.")

        portfolio = pquery.first()

        if portfolio.user.id != request.user.id:
            return error_response(401, 1, "you are not allowed to view this portfolio!")

        # ----
        tid_list_raw = request.GET.get("tids", "[]")
        tid_list = json.loads(tid_list_raw)

        deleted_ids = []
        # ----

        for tid in tid_list:
            try:
                tx_query = Transaction.objects.filter(id=tid)
                if not tx_query.exists():
                    continue

                tx = tx_query.first()
                if tx.portfolio_id != portfolio.id:
                    return error_response(
                        401,
                        1,
                        "At least 1 transaction wasn't part of the portfolio you specified!",
                    )

                tx.delete()
                deleted_ids.append(tid)

            except Exception as ex:
                print(ex)

        return success_response(
            200, 0, "deleted txs successfully.", data={"ids": deleted_ids}
        )

    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )


# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@ensure_authenticated_user
def portfolio_currencies(
    request: Request, *args: tuple[Any, ...], **kwargs: tuple[Any, ...]
) -> Response:
    try:
        currencies = (
            BaseCurrency.objects.all()
            .order_by("-market_cap")
            .values_list("tag", flat=True)
        )
        return success_response(
            200, 0, "currencies retrieved successfully.", data=currencies
        )
    except Exception as ex:
        print(ex)
        return error_response(
            500,
            0,
            "internal error.",
        )
