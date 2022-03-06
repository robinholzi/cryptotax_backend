from django.urls import path, include

from portfolio.views import create_order_list, create_deposit_list, create_transfer_list, portfolio_list_my, \
    portfolio_create, portfolio_update, portfolio_delete, portfolio_details, portfolio_list_reports, portfolio_list_txs, \
    portfolio_report_create, portfolio_report_delete, portfolio_report_detail

urlpatterns = [

    # portfolio reports
    path('<int:pid>/reports/list/', portfolio_list_reports, name="reports_list"),
    path('<int:pid>/report/create/', portfolio_report_create, name="report_create"),
    path('<int:pid>/report/<int:rid>/delete/', portfolio_report_delete, name="report_delete"),
    path('<int:pid>/report/<int:rid>/detail/', portfolio_report_detail, name="report_detail"),
    # TODO: CRUD


    # portfolio transactions
    path('<int:pid>/txs/list/', portfolio_list_txs, name="portfolio_details"),
    # TODO: CRUD
    path('order/create/', create_order_list, name="create_order_list"),
    path('deposit/create/', create_deposit_list, name="create_deposit_list"),
    path('transfer/create/', create_transfer_list, name="create_transfer_list"),

    # portfolio management
    path('delete/', portfolio_delete, name="portfolio_delete"),
    path('list/my/', portfolio_list_my, name="portfolio_list_my"),
    path('create/', portfolio_create, name="portfolio_create"),
    path('<int:pid>/detail/', portfolio_details, name="portfolio_details"),
    path('<int:pid>/update/', portfolio_update, name="portfolio_update"),
]
