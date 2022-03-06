
"""
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

    'subid': 10,
    'type': 'BO'|'SO'|'D'|'T',
    'tid': 34,
    'analysis_id': 12,
    'datetime': datetime.datetime(2021, 12, 16, 23, 32, 12, 491880, tzinfo=datetime.timezone.utc),
    'analysed': false,
    'fee': 1.2, # in respect to base
    'cooldown_until': None,
    'exchange_wallet': 'Binance',

    'currency': 'BNB',  # for all types
    'amount': 0.134,  # for all types
    'buy_sell_deposit_price': 410.03,  # buy/sell/deposit (in respect to base)
    'deposit_taxable': 1.0,
    'transfer_from_exchange_wallet': 'Kraken'
}
"""
import datetime

from tax_analysis.db.processing_analysis import allocate_analyzable, consumable_from_buy_order, \
    fetch_already_allocated_sum, analysable_already_done, fetch_next_consumable, consume_sell, consumable_from_deposit, \
    consume_transfer
from tax_analysis.models import AnalysableType, analysable_type_from_char, algorithm_from_char


def analysis_worker():
    print("dispatching processable_worker...")
    # cur = Currency.objects.get(tag="BTC")
    # base = BaseCurrency.objects.get(tag="EUR")
    # print("price:", fetch_price(cur, base, datetime.date(year=2020, month=12, day=12)))

    analysable_map = allocate_analyzable()
    if analysable_map is None:
        print("No analysable found...")
        return

    try:
        ana_type = analysable_type_from_char(analysable_map.get('type'))
        ana_tid = int(analysable_map.get('tid'))
        ana_sub_id = int(analysable_map.get('sub_id'))
        analysis_id = int(analysable_map.get('analysis_id'))
        ana_datetime = datetime.datetime.fromisoformat(str(analysable_map.get('datetime')))
        ana_fee = float(analysable_map.get('fee'))
        ana_exchange_wallet = str(analysable_map.get('exchange_wallet'))

        # for transfer/sell logic
        ana_algo = algorithm_from_char(str(analysable_map.get('algo')))
        ana_transfer_algo = algorithm_from_char(str(analysable_map.get('transfer_algo')))
        ana_taxable_period = analysable_map.get('taxable_period')

        print("ana_tid: ", ana_tid)
        print("analysis_id: ", analysis_id)
        print("ana_type: ", ana_type)
        print("ana_taxable_period: ", ana_taxable_period)

        if ana_type == AnalysableType.BUY_ORDER:
            print("BUY_ORDER: ")
            return consumable_from_buy_order(ana_sub_id)

        elif ana_type == AnalysableType.SELL_ORDER:
            print("SELL_ORDER: ")
            currency_id = str(analysable_map.get('currency'))
            sell_price = float(analysable_map.get('buy_sell_deposit_price'))
            amount = float(analysable_map.get('amount'))
            amount_already_consumed = float(fetch_already_allocated_sum(ana_tid))
            amount_needed = amount - amount_already_consumed

            print("amount_already_consumed, amount_needed, amount: ",
                  amount_already_consumed, amount_needed, amount)

            TOLERANCE = 0.0000000000001  # TODO
            if abs(amount_needed) <= TOLERANCE:
                return analysable_already_done(ana_tid)

            next_consumable = fetch_next_consumable(
                analysis_id, ana_exchange_wallet, currency_id,
                ana_algo,
                TOLERANCE
            )

            print("next_consumable: ", next_consumable)
            consumed_id = int(next_consumable.get('id'))
            buy_datetime = datetime.datetime.fromisoformat(str(next_consumable.get('datetime', 0.0)))
            total_amount = float(next_consumable.get('amount', 0.0))
            already_consumed = float(next_consumable.get('consumed', 0.0))
            buy_price = float(next_consumable.get('price', 0.0))
            unconsumed_amount = total_amount - already_consumed

            print('unconsumed_amount: ', unconsumed_amount)
            consumption_amount = max(min(amount_needed, unconsumed_amount), 0)
            print('consumption_amount: ', consumption_amount)

            finished = abs(consumption_amount - amount_needed) <= TOLERANCE

            # payout amount - buy in amount (in base currency)
            realized_profit = consumption_amount * (sell_price-buy_price)
            taxable_realized_profit = 0

            # hold period = sell datetime - buy datetime
            # do not use tax-free period for losses
            if (realized_profit < 0) \
                    or ana_taxable_period is None \
                    or (ana_datetime-buy_datetime) < ana_taxable_period:
                # taxable
                print("---> taxable! ")
                taxable_realized_profit = realized_profit

            # raise Exception("TODO undo last consumption in db")
            return consume_sell(
                analysis_id,
                ana_tid,
                consumed_id,
                consumption_amount,

                realized_profit,
                taxable_realized_profit,

                finished
            )

        elif ana_type == AnalysableType.DEPOSIT:
            print("DEPOSIT: ")
            return consumable_from_deposit(ana_sub_id)

        elif ana_type == AnalysableType.TRANSFER:
            print("TRANSFER: ")
            currency_id = str(analysable_map.get('currency'))
            amount = float(analysable_map.get('amount'))
            amount_already_consumed = float(fetch_already_allocated_sum(ana_tid))
            amount_needed = amount - amount_already_consumed
            from_exchange_wallet = str(analysable_map.get('transfer_from_exchange_wallet'))

            print("amount_already_consumed, amount_needed, amount: ",
                  amount_already_consumed, amount_needed, amount)

            TOLERANCE = 0.0000000000001  # TODO
            if abs(amount_needed) <= TOLERANCE:
                return analysable_already_done(ana_tid)

            # Transfers do not cause profit realization
            next_consumable = fetch_next_consumable(
                analysis_id, from_exchange_wallet, currency_id, ana_algo,
                TOLERANCE
            )
            # TODO query empty?

            consumed_id = int(next_consumable.get('id'))
            buy_datetime = datetime.datetime.fromisoformat(str(next_consumable.get('datetime', 0.0)))
            total_amount = float(next_consumable.get('amount', 0.0))
            already_consumed = float(next_consumable.get('consumed', 0.0))
            buy_price = float(next_consumable.get('price', 0.0))
            unconsumed_amount = total_amount - already_consumed

            print('unconsumed_amount: ', unconsumed_amount)
            consumption_amount = max(min(amount_needed, unconsumed_amount), 0)
            print('consumption_amount: ', consumption_amount)

            finished = abs(amount_needed - unconsumed_amount) <= TOLERANCE

            return consume_transfer(
                analysis_id,
                ana_tid,
                consumed_id,
                consumption_amount,
                buy_datetime,
                buy_price,

                finished
            )

        else:
            raise NotImplementedError()

    except Exception as ex:
        print("Exception:", ex)
        return

# TODO calculate profit via price

# TODO deposit: taxable at deposit & long term kursgewinn tax
# TODO: steuerfrei wenn über gewisse zeit alt

# TODO deposits: payin date & virtual buy date (problem with sorting compatibility with other types)
# (fifo nach payin order virtual buy?)

# transfer nach payin order virtual buy

# maybe extra datetime field for consumable needed
# (buy/transfer/deposit can set different dates according to their logic)

# TODO document behavior of deposits and transfers with fifo (what will be taken: payin or buyin)
