from django.urls import path, include

from portfolio.views import create_order_list, create_deposit_list, create_transfer_list, portfolio_list_my, \
    portfolio_create, portfolio_update, portfolio_delete, portfolio_details, portfolio_list_reports, portfolio_list_txs

urlpatterns = [

    # portfolio reports/transactions
    path('<pid>/reports/list/', portfolio_list_reports, name="portfolio_details"),
    path('<pid>/txs/list/', portfolio_list_txs, name="portfolio_details"),

    # portfolio management
    path('delete/', portfolio_delete, name="portfolio_delete"),
    path('list/my/', portfolio_list_my, name="portfolio_list_my"),
    path('create/', portfolio_create, name="portfolio_create"),
    path('<pid>/detail/', portfolio_details, name="portfolio_details"),
    path('<pid>/update/', portfolio_update, name="portfolio_update"),

    path('order/create/', create_order_list, name="create_order_list"),
    path('deposit/create/', create_deposit_list, name="create_deposit_list"),
    path('transfer/create/', create_transfer_list, name="create_transfer_list"),
]
