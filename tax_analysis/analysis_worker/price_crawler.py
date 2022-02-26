
import datetime
import json

from portfolio.models import BaseCurrency, Currency

import requests

from tax_analysis.models import CurrencyPriceCache


def fetch_price(
        currency: Currency,
        base_currency: BaseCurrency,
        dt: datetime.datetime):

    if currency.tag == base_currency.tag:
        return 1

    cache = CurrencyPriceCache.objects.filter(
        currency=currency,
        base=base_currency,
        date__exact=dt.date())

    if cache.exists():
        return float(cache.first().price)

    try:
        result_price = -1.0
        if currency.coingecko_name is not None:
            # first is real crypto -> normal coingecko request

            url = f"https://api.coingecko.com/api/v3/coins/{currency.coingecko_name}/history?date={dt.day}-{dt.month}-{dt.year}&vs_currencies={base_currency.coingecko_name}"
            print("url: ", url)
            result = requests.get(url)
            print("result: ", result.content)
            # data.market_data.current_price

            res_obj = result.json()
            market_data = res_obj['market_data']['current_price']

            result_price = float(market_data[base_currency.coingecko_name.lower()])

        else:  # currency is fiat
            currency_equiv = BaseCurrency.objects.get(tag=currency.tag)
            base_currency_equiv = Currency.objects.get(tag=base_currency.tag)
            if base_currency_equiv.coingecko_name is None:  # e.g. EUR/USD
                # base is real fiat -> exchange
                url = f"https://api.exchangerate.host/{dt.year}-{dt.month}-{dt.day}?base={currency_equiv.exchange_host_name}&symbols={base_currency.exchange_host_name}&places=40"
                print("url: ", url)
                result = requests.get(url)
                res_obj = result.json()
                rates = res_obj['rates']

                result_price = float(rates[base_currency.exchange_host_name.upper()])

            else:  # e.g. EUR/BTC
                # base is coin -> use coingecko
                url = f"https://api.coingecko.com/api/v3/coins/{base_currency_equiv.coingecko_name}/history?date={dt.day}-{dt.month}-{dt.year}&vs_currencies={currency.coingecko_name}"
                print("url: ", url)
                result = requests.get(url)
                print("result: ", result.content)
                # data.market_data.current_price

                res_obj = result.json()
                market_data = res_obj['market_data']['current_price']

                result_price =  1.0 / float(market_data[currency_equiv.coingecko_name.lower()])

        if currency.coingecko_name is None:
            print("++--10")
            raise Exception("invalid pair!")

        if result_price >= 0:
            CurrencyPriceCache(
                currency=currency,
                base=base_currency,
                date=dt.date(),
                price=result_price
            ).save()
            return result_price
        raise Exception

    except Exception as ex:
        print("error >> ", ex)
        raise ex
