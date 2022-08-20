import os

from django.db import (
    IntegrityError,
    connection,
)
from django.db.utils import DatabaseErrorWrapper


def _run_init_query(query_path: str) -> None:
    """FOR VIEW & FUNCTION CREATION"""
    query_path = query_path.replace("\\", os.sep)
    query_path = query_path.replace("/", os.sep)
    PROJECT_PATH = os.path.abspath(os.path.dirname(__name__))
    file_path = PROJECT_PATH + os.sep + ".sql_queries" + os.sep + query_path

    with open(file_path, "r", encoding="utf-8") as infile:
        query_str = infile.read()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query_str)
                return

        except IntegrityError as ie:
            print(ie)
            raise DatabaseErrorWrapper("initialization transaction failed!")


def initialize_db() -> None:
    # initialize base views
    _run_init_query("init/views/1/setup_create_views.sql")
    _run_init_query("init/views/1/setup_create_views_analysables.sql")
    _run_init_query("init/views/1/setup_create_views_processable.sql")

    # init processing views
    _run_init_query("init/views/2/reserve_oldest_processable_transaction.sql")
    _run_init_query("init/views/2/reserve_oldest_processable.sql")
    _run_init_query("init/views/3/v_processed_percentage_per_analysis.sql")

    # init analysis views
    _run_init_query("init/views/3/v_fully_consumed_consumable_analysables.sql")
    _run_init_query("init/views/3/v_consumables.sql")
    _run_init_query("init/views/3/v_consumables_balance.sql")

    _run_init_query("init/views/3/v_tax_analysis_analysables_full.sql")
    _run_init_query("init/views/3/v_tax_analysis_analysisconsumer_full.sql")
    _run_init_query("init/views/3/v_tax_analysis_analysissellconsumer_full.sql")

    _run_init_query("init/views/3/v_consumable_balance_and_consumed.sql")
    _run_init_query("init/views/3/v_consumers_satisfied_amounts.sql")

    _run_init_query("init/views/3/v_analysed_percentage_per_analysis.sql")

    # init result views
    _run_init_query("init/views/5/v_currency_count_by_analysis.sql")
    _run_init_query("init/views/5/v_wallet_count_by_analysis.sql")

    _run_init_query("init/views/6/v_deposit_taxable_profit_by_currency.sql")
    _run_init_query("init/views/6/v_deposit_taxable_profit_by_exchange.sql")
    _run_init_query("init/views/6/v_deposit_taxable_profit.sql")

    _run_init_query("init/views/6/v_fees.sql")
    _run_init_query("init/views/6/v_fees_by_currency.sql")
    _run_init_query("init/views/6/v_fees_by_exchange.sql")

    _run_init_query("init/views/6/v_sell_profits.sql")
    _run_init_query("init/views/6/v_sell_profits_by_currency.sql")
    _run_init_query("init/views/6/v_sell_profits_by_exchange.sql")

    _run_init_query("init/views/6/v_profits.sql")
    _run_init_query("init/views/6/v_profits_by_currency.sql")
    _run_init_query("init/views/6/v_profits_by_exchange.sql")

    # types -------------------------------------------------------------

    # _run_init_query("init/types/fetchLockProcessableType.sql")

    # functions ---------------------------------------------------------

    _run_init_query("init/functions/create_analysis.sql")
    # _run_init_query("init/functions/fetch_and_lock_processable.sql")
    _run_init_query("init/functions/update_analysis_modes.sql")

    # triggers ----------------------------------------------------------

    _run_init_query("init/triggers/check_ana_modes.sql")

    # -------------------------------------------------------------------
