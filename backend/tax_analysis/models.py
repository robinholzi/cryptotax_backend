from django.db import models

from portfolio.models import (
    BaseCurrency,
    Currency,
    DepositTyp,
    Portfolio,
    Transaction,
    TransactionType,
)

# TODO slipperage tolerance (ignore small error)


class AnalysisMode(models.TextChoices):
    PROCESSING = "P", "PROCESSING"
    ANALYSING = "A", "ANALYSING"
    FINISHED = "F", "FINISHED"


class AnalysisAlgorithm(models.TextChoices):
    ALGO_FIFO = "FIFO", "ALGO_FIFO"
    ALGO_LIFO = "LIFO", "ALGO_LIFO"
    ALGO_OPTIMAL = (
        "OPT",
        "ALGO_OPTIMAL",
    )  # consume highest price first (to keep realized profit low)
    ALGO_WORST = "WRST", "ALGO_WORST"  # consume lowest price first


class MiningTaxMethod(models.TextChoices):
    # tax mined coins on deposit with certain percentage, afterwards only gains taxable
    ON_DEPOSIT_AND_GAINS = "D&G", "ON_DEPOSIT_AND_GAINS"

    # tax mined coins on deposit with certain percentage, afterwards tax free gains
    ON_DEPOSIT_AND_NOT_GAINS = "D&NG", "ON_DEPOSIT_AND_NOT_GAINS"

    # only tax sell by 100% of coins are gains (= buy at price 0)
    NOT_ON_DEPOSIT_AND_FULL_GAINS = "ND&FG", "NOT_ON_DEPOSIT_AND_FULL_GAINS"

    # no crypto taxation
    NOT_ON_DEPOSIT_AND_NOT_GAINS = "ND&NG", "NOT_ON_DEPOSIT_AND_NOT_GAINS"


def algorithm_from_char(c: str) -> tuple[str, str]:
    if c == "FIFO":
        return AnalysisAlgorithm.ALGO_FIFO
    if c == "LIFO":
        return AnalysisAlgorithm.ALGO_LIFO
    if c == "OPT":
        return AnalysisAlgorithm.ALGO_OPTIMAL
    if c == "WRST":
        return AnalysisAlgorithm.ALGO_WORST
    raise NotImplementedError


class PortfolioAnalysis(models.Model):
    portfolio = models.ForeignKey(Portfolio, null=False, on_delete=models.CASCADE)
    title = models.TextField("title", blank=True, null=True)

    # settings ------------------------------------------------------------------------

    base_currency = models.ForeignKey(
        BaseCurrency, null=False, blank=False, on_delete=models.DO_NOTHING
    )

    algo = models.CharField(max_length=5, choices=AnalysisAlgorithm.choices)
    transfer_algo = models.CharField(max_length=5, choices=AnalysisAlgorithm.choices)

    # tax settings ++++++++++++++++++++++++++++++
    # allowance from which onward profits have to be taxed
    untaxed_allowance = models.FloatField("untaxed_allowance", default=0, null=None)

    mining_tax_method = models.CharField(
        max_length=10,
        choices=MiningTaxMethod.choices,
        default=MiningTaxMethod.ON_DEPOSIT_AND_GAINS,
    )

    # percentage of deposit which is considers (and summed up) as profit
    mining_deposit_profit_rate = models.FloatField(
        "mining_deposit_profit_rate", default=1.0, null=False
    )

    # TODO: unimplemented
    cross_wallet_sells = models.BooleanField(
        "cross_wallet_sells", null=False, default=False
    )

    # null = Infinity (never tax free)
    # 0 always tax free -> just calculate profits
    taxable_period_days = models.IntegerField(
        "taxable_period_days", null=True, blank=True, default=None
    )

    # for processing (initialized by default) -----------------------------------------

    mode = models.CharField(
        max_length=2, choices=AnalysisMode.choices, default=AnalysisMode.PROCESSING
    )

    # only for analysis step (not processable-step)
    cooldown_until = models.DateTimeField(
        "cooldown_until", blank=True, null=True, default=None
    )  # if crawling error: delay for some time

    failed = models.BooleanField("failed", default=False)

    # ---------------------------------------------------------------------------------

    updated = models.DateTimeField("updated", auto_now=True)
    created = models.DateTimeField("created", auto_now_add=True)

    def __str__(self) -> str:
        return f"PortfolioAnalysis ({self.portfolio} - {self.created})"


class CurrencyPriceCache(models.Model):
    currency = models.ForeignKey(
        Currency, null=False, blank=False, on_delete=models.CASCADE
    )
    base = models.ForeignKey(
        BaseCurrency, null=False, blank=False, on_delete=models.CASCADE
    )
    date = models.DateField("date", null=False, blank=False)
    price = models.FloatField("price", null=False, blank=False)


class PortfolioAnalysisReport(models.Model):
    analysis = models.OneToOneField(
        PortfolioAnalysis, null=False, on_delete=models.CASCADE
    )

    error_message = models.TextField(
        "error_message", blank=True, null=True, default=None
    )

    realized_profit_sum = models.FloatField(
        "taxable_profit_sum", null=False, blank=False, default=0
    )  # brutto
    taxable_profit_sum = models.FloatField(
        "taxable_profit_sum", null=False, blank=False, default=0
    )  # brutto
    fee_sum = models.FloatField(
        "fee_sum", null=False, blank=False, default=0
    )  # werbungskosten
    # net tax: can be calculated by: tax_sum-fee_sum

    updated = models.DateTimeField("updated", auto_now=True)
    created = models.DateTimeField("created", auto_now_add=True)

    def __str__(self) -> str:
        return f"PortfolioAnalysisReport ({self.created}-{self.title})"


"""
transaction containing:
- swaps (not in respect to base currency)
"""


class ProcessableTransaction(models.Model):
    analysis = models.ForeignKey(
        PortfolioAnalysis, null=False, on_delete=models.CASCADE
    )
    datetime = models.DateTimeField("datetime", null=False, blank=False)

    type = models.CharField(max_length=4, choices=TransactionType.choices)

    exchange_wallet = models.TextField("exchange_wallet", blank=True, null=True)

    fee = models.FloatField("fee", blank=False, null=False, default=0)
    fee_currency = models.ForeignKey(
        Currency, blank=True, null=True, on_delete=models.DO_NOTHING
    )

    # only used during copy transaction from portfolio space -> analysis processing space
    # (in order to insert orders with correct ProcessableTransaction.id) in second instruction
    # SHOULD NOT BE USED / LOOKED AT AFTER INITIAL TRANSACTION
    portfolio_transaction = models.ForeignKey(
        Transaction, blank=True, null=True, default=None, on_delete=models.SET_NULL
    )

    cooldown_until = models.DateTimeField(
        "cooldown_until", blank=True, null=True
    )  # if crawling error: delay for some time
    updated = models.DateTimeField("updated", auto_now=True)  # last looked at
    created = models.DateTimeField("created", auto_now_add=True)  # task insertion

    def __str__(self) -> str:
        return "ProcessableTransaction"


class ProcessableOrder(models.Model):
    transaction = models.OneToOneField(
        ProcessableTransaction, null=False, on_delete=models.CASCADE
    )

    from_amount = models.FloatField("from_amount", blank=False, null=False, default=0)
    from_currency = models.ForeignKey(
        Currency,
        related_name="processable_order_from_currency",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )

    to_amount = models.FloatField("to_amount", blank=False, null=False, default=0)
    to_currency = models.ForeignKey(
        Currency,
        related_name="processable_order_to_currency",
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
    )

    def __str__(self) -> str:
        return "ProcessableTransaction"


class ProcessableDeposit(models.Model):
    transaction = models.OneToOneField(
        ProcessableTransaction, null=False, on_delete=models.CASCADE
    )
    type = models.CharField(
        choices=DepositTyp.choices, null=False, max_length=8, default=DepositTyp.DEFAULT
    )

    buy_datetime = models.DateTimeField("buy_datetime", null=False, blank=False)
    amount = models.FloatField("amount", blank=False, null=False, default=0)
    currency = models.ForeignKey(
        Currency, blank=True, null=True, on_delete=models.DO_NOTHING
    )

    # used iff DepositType == CUSTOM_RATE
    taxable = models.FloatField(
        "taxable", blank=False, null=False, default=0
    )  # normalized percentage (0,1)

    def __str__(self) -> str:
        return "ProcessableDeposit"


class ProcessableTransfer(models.Model):
    transaction = models.OneToOneField(
        ProcessableTransaction, null=False, on_delete=models.CASCADE
    )

    from_exchange_wallet = models.TextField(
        "from_exchange_wallet", blank=True, null=True
    )

    amount = models.FloatField("amount", blank=False, null=False, default=0)
    currency = models.ForeignKey(
        Currency, blank=True, null=True, on_delete=models.DO_NOTHING
    )

    def __str__(self) -> str:
        return "ProcessableTransfer"


class AnalysableType(models.TextChoices):
    BUY_ORDER = "BO", "BuyOrder"
    SELL_ORDER = "SO", "SellOrder"
    TRANSFER = "T", "Transfer"
    DEPOSIT = "D", "Deposit"


def analysable_type_from_char(c: str) -> tuple[str, str]:
    if c == "BO":
        return AnalysableType.BUY_ORDER
    if c == "SO":
        return AnalysableType.SELL_ORDER
    if c == "T":
        return AnalysableType.TRANSFER
    if c == "D":
        return AnalysableType.DEPOSIT
    raise NotImplementedError


class Analysable(models.Model):
    analysis = models.ForeignKey(
        PortfolioAnalysis, null=False, on_delete=models.CASCADE
    )
    datetime = models.DateTimeField("datetime", null=False, blank=False)

    type = models.CharField(max_length=4, choices=AnalysableType.choices)

    exchange_wallet = models.TextField("exchange_wallet", blank=True, null=True)

    # in respect to base currency (amount of base)
    fee = models.FloatField("fee", blank=False, null=False, default=0)

    analysed = models.BooleanField("analysed", default=False, null=False)

    updated = models.DateTimeField("updated", auto_now=True)  # last looked at
    created = models.DateTimeField("created", auto_now_add=True)  # task insertion

    def __str__(self) -> str:
        return "Analysable"


class AnalysisBuy(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)

    # bought asset
    currency = models.ForeignKey(
        Currency, blank=False, null=False, on_delete=models.DO_NOTHING
    )

    # number of bought asset
    amount = models.FloatField("amount", blank=False, null=False)

    # in respect to base currency (cost of one unit of bought unit)
    price = models.FloatField("price", blank=False, null=False, default=0)

    def __str__(self) -> str:
        return "AnalysisBuy"


class ConsumableType(models.TextChoices):
    BUY_ORDER = "BO", "BuyOrder"
    TRANSFER = "T", "Transfer"
    DEPOSIT = "D", "Deposit"


class AnalysisConsumable(models.Model):
    analysable = models.ForeignKey(Analysable, null=False, on_delete=models.CASCADE)

    datetime = models.DateTimeField("datetime", null=False, blank=False)

    type = models.CharField(max_length=4, choices=ConsumableType.choices)

    # in respect to base currency (cost of one unit of bought unit)
    price = models.FloatField("price", blank=False, null=False)

    # since transfers can cause fractional consumers with different prices
    # we also neeed amount here (for deposits & buyorders the same as in analysable)
    amount = models.FloatField("amount", blank=False, null=False)

    def __str__(self) -> str:
        return "AnalysisConsumable"


class AnalysisSell(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)

    # sold asset
    currency = models.ForeignKey(
        Currency, blank=False, null=False, on_delete=models.DO_NOTHING
    )

    # number of sold asset
    amount = models.FloatField("amount", blank=False, null=False)

    # in respect to base currency (cost of one unit of sold unit)
    price = models.FloatField("price", blank=False, null=False, default=0)

    def __str__(self) -> str:
        return "AnalysisSell"


class AnalysisDeposit(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)
    type = models.CharField(
        choices=DepositTyp.choices, null=False, max_length=8, default=DepositTyp.DEFAULT
    )

    buy_datetime = models.DateTimeField("buy_datetime", null=False, blank=False)

    # deposited asset
    currency = models.ForeignKey(
        Currency, blank=False, null=False, on_delete=models.DO_NOTHING
    )

    # number of deposited asset
    amount = models.FloatField("amount", blank=False, null=False)

    # in respect to base currency (cost of one unit of bought unit)
    price = models.FloatField("price", blank=False, null=False, default=0)

    # tax rate at deposit (not long term capital gain tax)
    # used iff DepositType == CUSTOM_RATE
    taxable = models.FloatField(
        "taxable", blank=False, null=False, default=0
    )  # normalized percentage (0,1)

    # absolute taxable = price * taxable

    def __str__(self) -> str:
        return "AnalysisDeposit"


class AnalysisTransfer(models.Model):
    transaction = models.OneToOneField(Analysable, null=False, on_delete=models.CASCADE)

    from_exchange_wallet = models.TextField(
        "from_exchange_wallet", blank=True, null=True
    )

    # transferred asset
    currency = models.ForeignKey(
        Currency, blank=False, null=False, on_delete=models.DO_NOTHING
    )

    # number of transferred asset
    amount = models.FloatField("amount", blank=False, null=False)

    def __str__(self) -> str:
        return "AnalysisTransfer"


class ConsumerType(models.TextChoices):
    SELL_ORDER = "SO", "SellOrder"
    TRANSFER = "T", "Transfer"


# may not be instantiated (abstract)
class AnalysisConsumer(models.Model):
    analysis = models.ForeignKey(
        PortfolioAnalysis, null=False, on_delete=models.CASCADE
    )

    consumed = models.ForeignKey(
        AnalysisConsumable, null=False, on_delete=models.CASCADE
    )

    type = models.CharField(max_length=4, choices=ConsumerType.choices)

    # id of either AnalysisSell's or AnalysisTransfer's parent Analysable
    consumer = models.ForeignKey(
        Analysable, null=False, blank=False, on_delete=models.CASCADE
    )

    # number of accounted asset
    amount = models.FloatField("amount", blank=False, null=False)

    def __str__(self) -> str:
        return "AnalysisConsumer"


class AnalysisSellConsumer(models.Model):
    parent = models.OneToOneField(
        AnalysisConsumer, null=False, on_delete=models.CASCADE
    )

    # realized profit which this consumption causes (in base currency) -> basis for tax calculation
    realized_profit = models.FloatField(
        "realized_profit", blank=False, null=False, default=0
    )
    taxable_realized_profit = models.FloatField(
        "taxable_realized_profit", blank=False, null=False, default=0
    )


class AnalysisTransferConsumer(models.Model):
    parent = models.OneToOneField(
        AnalysisConsumer, null=False, on_delete=models.CASCADE
    )

    # consumable which was created from transfer
    created_consumable = models.OneToOneField(
        AnalysisConsumable, null=False, on_delete=models.CASCADE
    )


# SQL QUERIES: select oldest process tasks which are park of an active (not failed, no portfolioreport), analysis
# TODO: gebühren als werbungskosten

# net profit: sell profits + deposit profits
