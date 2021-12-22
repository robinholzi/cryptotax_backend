from datetime import datetime
import dateutil.parser

from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.utils import json

from cryptotax_backend.utils import error_response, success
from portfolio.models import Order, Transaction, Portfolio, Currency
from utils.decorators import ensure_authenticated_user


# TODO CHECK ON INSERT THAT CURRENCIES EXIST!!!!!!!!!
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

        for ordermap in req_orders:
            _datetime = dateutil.parser.isoparse(str(ordermap['datetime']))
            _exchange_wallet = str(ordermap.get("exchange_wallet", None))

            _fee = float(ordermap.get('fee', None))
            _fee_currency = str(ordermap.get("fee_currency", None)).upper()

            _from_amount = float(ordermap.get('from_amount', None))
            _from_currency = str(ordermap.get('from_currency', None)).upper()

            _to_amount = float(ordermap.get('to_amount', None))
            _to_currency = str(ordermap.get('to_currency', None)).upper()

            transact = Transaction()
            order = Order()
            order.transaction = transact

            transact.portfolio_id = portfolio_id
            transact.datetime = _datetime
            transact.exchange_wallet = _exchange_wallet

            # TODO check that fee currency exists (and is resolvable)

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

            # ------------------------------------------
            if from_cur.coingecko_name is not None and to_cur.coingecko_name is not None:
                pass  # 2 non base currencies -> okay
            # ------------------------------------------

            # ------------------------------------------
            if (from_cur.coingecko_name is None and to_cur.coingecko_name is not None) or \
                    from_cur.coingecko_name is not None and to_cur.coingecko_name is None:
                pass  # 1 non base currencies -> okay
            # ------------------------------------------

            # ------------------------------------------
            if from_cur.coingecko_name is None and to_cur.coingecko_name is None:
                # 2 base currencies -> invalid
                return error_response(400, 2, "currency pair consists of 2 base currencies -> not yet supported.")
            # ------------------------------------------

            order.from_amount = _from_amount
            order.from_currency_id = from_cur

            order.to_amount = _to_amount
            order.to_currency_id = to_cur

            orders.append(order)

    except ValueError as err:
        print(err)
        return error_response(400, 5, "error parsing request data.")

    try:
        # check if topic exists
        for order in orders:
            order.transaction.save()
            order.save()

        return success(200, 0, "orders created successfully.")

    except Exception as ex:
        print(ex)
        return error_response(500, 0, "internal error.", )
