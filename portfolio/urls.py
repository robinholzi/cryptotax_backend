from django.urls import path

from portfolio.views import (
    create_deposit_list,
    create_order_list,
    create_transfer_list,
    portfolio_create,
    portfolio_currencies,
    portfolio_delete,
    portfolio_details,
    portfolio_list_deposits,
    portfolio_list_my,
    portfolio_list_orders,
    portfolio_list_reports,
    portfolio_list_transfers,
    portfolio_report_create,
    portfolio_report_delete,
    portfolio_report_detail,
    portfolio_reports_delete,
    portfolio_txs_delete,
    portfolio_update,
)

urlpatterns = [
    # portfolio reports
    path("<int:pid>/reports/list/", portfolio_list_reports, name="reports_list"),
    path("<int:pid>/report/create/", portfolio_report_create, name="report_create"),
    path(
        "<int:pid>/report/<int:rid>/delete/",
        portfolio_report_delete,
        name="report_delete",
    ),
    path("<int:pid>/reports/delete/", portfolio_reports_delete, name="reports_delete"),
    path(
        "<int:pid>/report/<int:rid>/detail/",
        portfolio_report_detail,
        name="report_detail",
    ),
    # TODO: CRUD
    # portfolio transactions
    path("<int:pid>/orders/list/", portfolio_list_orders, name="portfolio_list_orders"),
    path(
        "<int:pid>/deposits/list/",
        portfolio_list_deposits,
        name="portfolio_list_deposits",
    ),
    path(
        "<int:pid>/transfers/list/",
        portfolio_list_transfers,
        name="portfolio_list_transfers",
    ),
    # TODO: CRUD
    path("<int:pid>/orders/create/", create_order_list, name="create_order_list"),
    path("<int:pid>/deposits/create/", create_deposit_list, name="create_deposit_list"),
    path(
        "<int:pid>/transfers/create/", create_transfer_list, name="create_transfer_list"
    ),
    path("<int:pid>/txs/delete/", portfolio_txs_delete, name="create_transfer_list"),
    # portfolio management
    path("delete/", portfolio_delete, name="portfolio_delete"),
    path("list/my/", portfolio_list_my, name="portfolio_list_my"),
    path("create/", portfolio_create, name="portfolio_create"),
    path("<int:pid>/detail/", portfolio_details, name="portfolio_details"),
    path("<int:pid>/update/", portfolio_update, name="portfolio_update"),
    # generic
    path("currencies/", portfolio_currencies, name="portfolio_currencies"),
]
