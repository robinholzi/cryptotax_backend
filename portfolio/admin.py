from django.contrib import admin

from portfolio.models import (
    Deposit,
    Order,
    Portfolio,
    Transaction,
    Transfer,
)

admin.site.register(Portfolio)
admin.site.register(Transaction)
admin.site.register(Order)
admin.site.register(Transfer)
admin.site.register(Deposit)
