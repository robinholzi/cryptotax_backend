from django.db import (
    IntegrityError,
    transaction,
)
from django.db.utils import DatabaseErrorWrapper

from portfolio.models import (
    Deposit,
    Order,
    Transfer,
)


@transaction.atomic
def save_orders_transactions(orders: list[Order]) -> None:
    try:
        with transaction.atomic():
            for order in orders:
                order.transaction.save()
                order.save()
    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Order/Transaction creation not successful.")


@transaction.atomic
def save_deposits_transactions(deposits: list[Deposit]) -> None:
    try:
        with transaction.atomic():
            for deposit in deposits:
                deposit.transaction.save()
                deposit.save()
    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Deposit/Transaction creation not successful.")


@transaction.atomic
def save_transfers_transactions(transfers: list[Transfer]) -> None:
    try:
        with transaction.atomic():
            for transfer in transfers:
                transfer.transaction.save()
                transfer.save()
    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Deposit/Transaction creation not successful.")
