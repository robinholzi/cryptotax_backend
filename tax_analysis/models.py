from django.db import models

from portfolio.models import Portfolio, TransactionType, Transaction, Currency, BaseCurrency


# TODO create analysis object in atomic transaction with processables

# TODO slipperage tolerance (ignore small error)


class AnalysisMode(models.TextChoices):
    BUY_ORDER = 'P', 'PROCESSING'
    SELL_ORDER = 'A', 'ANALYSING'
    TRANSFER = 'F', 'FINISHED'


class PortfolioAnalysis(models.Model):
    portfolio = models.ForeignKey(Portfolio, null=False, on_delete=models.CASCADE)

    base_currency = models.ForeignKey(BaseCurrency, null=False, blank=False, on_delete=models.DO_NOTHING)

    updated = models.DateTimeField('updated', auto_now=True)
    created = models.DateTimeField('created', auto_now_add=True)

    mode = models.CharField(max_length=2,
                            choices=AnalysisMode.choices)

    # only for analysis step (not processable-step)
    cooldown_until = models.DateTimeField('cooldown_until', blank=True,
                                          null=True)  # if crawling error: delay for some time

    failed = models.BooleanField('failed', default=False)

    def __str__(self):
        return f'PortfolioAnalysis ({self.portfolio} - {self.created})'


class PortfolioAnalysisReport(models.Model):
    analysis = models.OneToOneField(PortfolioAnalysis, null=False, on_delete=models.CASCADE)
    title = models.TextField('title', blank=True, null=True)

    error_message = models.TextField('error_message', blank=True, null=True, default=None)

    taxable_profit_sum = models.FloatField('taxable_profit_sum', null=False, blank=False, default=0)  # brutto
    fee_sum = models.FloatField('fee_sum', null=False, blank=False, default=0)  # werbungskosten
    # net tax: can be calculated by: tax_sum-fee_sum

    updated = models.DateTimeField('updated', auto_now=True)
    created = models.DateTimeField('created', auto_now_add=True)

    def __str__(self):
        return f'PortfolioAnalysisReport ({self.created}-{self.title})'


"""
transaction containing:
- swaps (not in respect to base currency)

- if 
"""


class ProcessableTransaction(models.Model):
    analysis = models.ForeignKey(PortfolioAnalysis, null=False, on_delete=models.CASCADE)
    datetime = models.DateTimeField('datetime', null=False, blank=False)

    type = models.CharField(max_length=4,
                            choices=TransactionType.choices)

    exchange_wallet = models.TextField('exchange_wallet', blank=True, null=True)

    fee = models.FloatField('fee', blank=False, null=False, default=0)
    fee_currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.DO_NOTHING)

    # only used during copy transaction from portfolio space -> analysis processing space
    # (in order to insert orders with correct ProcessableTransaction.id) in second instruction
    # SHOULD NOT BE USED / LOOKED AT AFTER INITIAL TRANSACTION
    portfolio_transaction = models.ForeignKey(Transaction,
                                              blank=True, null=True, default=None, on_delete=models.SET_NULL)

    cooldown_until = models.DateTimeField('cooldown_until', blank=True,
                                          null=True)  # if crawling error: delay for some time
    updated = models.DateTimeField('updated', auto_now=True)  # last looked at
    created = models.DateTimeField('created', auto_now_add=True)  # task insertion

    def __str__(self):
        return f'ProcessableTransaction'


class ProcessableOrder(models.Model):
    transaction = models.OneToOneField(ProcessableTransaction, null=False, on_delete=models.CASCADE)

    from_amount = models.FloatField('from_amount', blank=False, null=False, default=0)
    from_currency = models.ForeignKey(Currency, related_name='processable_order_from_currency', blank=True, null=True,
                                      on_delete=models.DO_NOTHING)

    to_amount = models.FloatField('to_amount', blank=False, null=False, default=0)
    to_currency = models.ForeignKey(Currency, related_name='processable_order_to_currency', blank=True, null=True,
                                    on_delete=models.DO_NOTHING)

    def __str__(self):
        return f'ProcessableTransaction'


class ProcessableDeposit(models.Model):
    transaction = models.OneToOneField(ProcessableTransaction, null=False, on_delete=models.CASCADE)

    amount = models.FloatField('amount', blank=False, null=False, default=0)
    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.DO_NOTHING)
    taxable = models.FloatField('taxable', blank=False, null=False, default=0)  # normalized percentage (0,1)

    def __str__(self):
        return f'ProcessableDeposit'


class ProcessableTransfer(models.Model):
    transaction = models.OneToOneField(ProcessableTransaction, null=False, on_delete=models.CASCADE)

    from_exchange_wallet = models.TextField('from_exchange_wallet', blank=True, null=True)

    amount = models.FloatField('amount', blank=False, null=False, default=0)
    currency = models.ForeignKey(Currency, blank=True, null=True, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f'ProcessableTransfer'


class AnalysableType(models.TextChoices):
    BUY_ORDER = 'BO', 'BuyOrder'
    SELL_ORDER = 'SO', 'SellOrder'
    TRANSFER = 'T', 'Transfer'
    DEPOSIT = 'D', 'Deposit'


class Analysable(models.Model):
    analysis = models.ForeignKey(PortfolioAnalysis, null=False, on_delete=models.CASCADE)
    datetime = models.DateTimeField('datetime', null=False, blank=False)

    type = models.CharField(max_length=4,
                            choices=AnalysableType.choices)

    exchange_wallet = models.TextField('exchange_wallet', blank=True, null=True)

    # in respect to base currency (amount of base)
    fee = models.FloatField('fee', blank=False, null=False, default=0)

    analysed = models.BooleanField('analysed', default=False, null=False)

    updated = models.DateTimeField('updated', auto_now=True)  # last looked at
    created = models.DateTimeField('created', auto_now_add=True)  # task insertion

    def __str__(self):
        return f'Analysable'


class AnalysisBuy(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)

    # bought asset
    currency = models.ForeignKey(Currency, blank=False, null=False, on_delete=models.DO_NOTHING)

    # number of bought asset
    amount = models.FloatField('amount', blank=False, null=False)

    # in respect to base currency (cost of one unit of bought unit)
    price = models.FloatField('price', blank=False, null=False, default=0)

    def __str__(self):
        return f'AnalysisBuy'


class ConsumableType(models.TextChoices):
    BUY_ORDER = 'BO', 'BuyOrder'
    TRANSFER = 'T', 'Transfer'
    DEPOSIT = 'D', 'Deposit'


class AnalysisConsumable(models.Model):
    analysis = models.ForeignKey(PortfolioAnalysis, null=False, on_delete=models.CASCADE)

    type = models.CharField(max_length=4,
                            choices=ConsumableType.choices)

    exchange_wallet = models.TextField('exchange_wallet', blank=True, null=True)

    def __str__(self):
        return f'AnalysisConsumable'


class AnalysisSell(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)

    # sold asset
    currency = models.ForeignKey(Currency, blank=False, null=False, on_delete=models.DO_NOTHING)

    # number of sold asset
    amount = models.FloatField('amount', blank=False, null=False)

    # in respect to base currency (cost of one unit of sold unit)
    price = models.FloatField('price', blank=False, null=False, default=0)

    def __str__(self):
        return f'AnalysisSell'


class AnalysisDeposit(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)

    # deposited asset
    currency = models.ForeignKey(Currency, blank=False, null=False, on_delete=models.DO_NOTHING)

    # number of deposited asset
    amount = models.FloatField('amount', blank=False, null=False)

    # in respect to base currency (cost of one unit of bought unit)
    price = models.FloatField('price', blank=False, null=False, default=0)

    taxable = models.FloatField('taxable', blank=False, null=False, default=0)  # normalized percentage (0,1)

    def __str__(self):
        return f'AnalysisDeposit'


class AnalysisTransfer(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)

    from_exchange_wallet = models.TextField('from_exchange_wallet', blank=True, null=True)

    # transferred asset
    currency = models.ForeignKey(Currency, blank=False, null=False, on_delete=models.DO_NOTHING)

    # number of transferred asset
    amount = models.FloatField('amount', blank=False, null=False)

    def __str__(self):
        return f'AnalysisTransfer'


class ConsumerType(models.TextChoices):
    SELL_ORDER = 'SO', 'SellOrder'
    TRANSFER = 'T', 'Transfer'


# may not be instantiated (abstract)
class AnalysisConsumer(models.Model):
    analysis = models.ForeignKey(PortfolioAnalysis, null=False, on_delete=models.CASCADE)

    consumed = models.OneToOneField(AnalysisConsumable, null=False, on_delete=models.CASCADE)

    type = models.CharField(max_length=4,
                            choices=ConsumerType.choices)

    # id of either AnalysisSell or AnalysisTransfer
    consumer = models.PositiveIntegerField('consumer_id', null=False, blank=False)

    # number of accounted asset
    amount = models.FloatField('amount', blank=False, null=False)

    def __str__(self):
        return f'AnalysisConsumer'


class AnalysisSellConsumer(models.Model):
    parent = models.OneToOneField(AnalysisConsumer, null=False, on_delete=models.CASCADE)
    consumer = models.OneToOneField(AnalysisSell, null=False, on_delete=models.CASCADE)

    # realized profit which this consumption causes (in base currency) -> basis for tax calculation
    realized_profit = models.FloatField('realized_profit', blank=False, null=False, default=0)


class AnalysisTransferConsumer(models.Model):
    parent = models.OneToOneField(AnalysisConsumer, null=False, on_delete=models.CASCADE)
    consumer = models.OneToOneField(AnalysisTransfer, null=False, on_delete=models.CASCADE)

# SQL QUERIES: select oldest process tasks which are park of an active (not failed, no portfolioreport), analysis
# TODO: gebühren als werbungskosten
