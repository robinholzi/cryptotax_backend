import datetime
import random

def random_portfolio():
    return {
        'title': f"Robin's Portfolio #{random.randint(1,100)}",
        'transactions': random.randint(1,10000),
        'exchanges': random.randint(1,9),
        'reports': random.randint(1,100),
        'latest_report_profit': random.uniform(0, 1000.0),
        'latest_report_date': datetime.datetime.now(),
    }