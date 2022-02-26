import datetime

from django.db import models

from user.models import CryptoTaxUser


class Portfolio(models.Model):
    user = models.ForeignKey(CryptoTaxUser, null=False, on_delete=models.CASCADE)
    title = models.TextField('title', blank=True, null=True)

    updated = models.DateTimeField('updated', auto_now=True)
    created = models.DateTimeField('created', auto_now_add=True)

    def __str__(self):
        return f'Portfolio ({self.user}-{self.title})'


class TransactionType(models.TextChoices):
    ORDER = 'O', 'Order'
    TRANSFER = 'T', 'Transfer'
    DEPOSIT = 'D', 'Deposit'


def transaction_type_from_char(c: str):
    if c == 'O':
        return TransactionType.ORDER
    if c == 'T':
        return TransactionType.TRANSFER
    if c == 'D':
        return TransactionType.DEPOSIT
    raise NotImplementedError


class Currency(models.Model):
    tag = models.CharField('tag', max_length=60, primary_key=True)
    coingecko_name = models.CharField('coingecko_name', max_length=150, blank=True, null=True)


class BaseCurrency(models.Model):
    tag = models.CharField('tag', max_length=60, primary_key=True)
    coingecko_name = models.CharField('coingecko_name', max_length=150, blank=False, null=False)
    exchange_host_name = models.CharField('exchange_host_name', max_length=150, blank=True, null=True)


class Transaction(models.Model):
    portfolio = models.ForeignKey(Portfolio, null=False, on_delete=models.CASCADE)
    datetime = models.DateTimeField('datetime', null=False, blank=False)

    type = models.CharField(max_length=4,
                            choices=TransactionType.choices,
                            null=False, blank=False)

    exchange_wallet = models.TextField('exchange_wallet', blank=True, null=True)

    fee = models.FloatField('fee', blank=False, null=False, default=0)
    fee_currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.SET_NULL)

    updated = models.DateTimeField('updated', auto_now=True)
    created = models.DateTimeField('created', auto_now_add=True)

    def __str__(self):
        return f'Transaction ({self.portfolio}-{self.title})'


class Order(models.Model):
    transaction = models.OneToOneField(Transaction, null=False, on_delete=models.CASCADE)

    from_amount = models.FloatField('from_amount', blank=False, null=False, default=0)
    from_currency = models.ForeignKey(Currency, related_name='order_from_currency', blank=True, null=True, on_delete=models.SET_NULL)

    to_amount = models.FloatField('to_amount', blank=False, null=False, default=0)
    to_currency = models.ForeignKey(Currency, related_name='order_to_currency', blank=True, null=True, on_delete=models.SET_NULL)


class Transfer(models.Model):
    transaction = models.OneToOneField(Transaction, null=False, on_delete=models.CASCADE)

    from_exchange_wallet = models.TextField('from_exchange_wallet', blank=True, null=True)

    amount = models.FloatField('amount', blank=False, null=False, default=0)
    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.SET_NULL)


class Deposit(models.Model):
    transaction = models.OneToOneField(Transaction, null=False, on_delete=models.CASCADE)

    buy_datetime = models.DateTimeField('buy_datetime', null=False, blank=False)
    amount = models.FloatField('amount', blank=False, null=False, default=0)
    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.SET_NULL)
    taxable = models.FloatField('taxable', blank=False, null=False, default=0)  # normalized percentage (0,1)

    # TODO buyin date
