from math import ceil
from typing import Optional

from django.db import (
    IntegrityError,
    connection,
    transaction,
)
from django.db.utils import DatabaseErrorWrapper


@transaction.atomic
def query_portfolios_of_user(user_id: int, page_size: int, page_no: int) -> list[dict]:
    page_size = max(1, page_size)
    offset = max(0, page_size * (max(0, page_no) - 1))
    try:
        query_str = """
            select p.id, p.title, (
            select count(distinct(t.id)) from portfolio_transaction t where p.id=t.portfolio_id
            ) as transactions, (
            select count(distinct(t.exchange_wallet)) from portfolio_transaction t where p.id=t.portfolio_id
            ) as exchanges, (
            select count(distinct(r.id))
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            ) as reports, (
            select r.realized_profit_sum
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            order by r.created desc
            limit 1
            ) as latest_report_profit, (
            select a.base_currency_id
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            order by r.created desc
            limit 1
            ) as latest_report_currency, (
            select r.created
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            order by r.created desc
            limit 1
            ) as latest_report_date
            from portfolio_portfolio p
            where p.user_id=%s
            order by p.id asc
            limit %s
            offset %s
        """

        with connection.cursor() as cursor:
            cursor.execute(query_str, [user_id, page_size, offset])
            res = cursor.fetchall()
            portfolios = []
            for r in res:
                portfolios.append(
                    {
                        "id": r[0],
                        "title": r[1],
                        "transactions": r[2],
                        "exchanges": r[3],
                        "reports": r[4],
                        "latest_report_profit": r[5],
                        "latest_report_currency": r[6],
                        "latest_report_date": r[7],
                    }
                )

            return portfolios

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Portfolios query creation not successful.")


@transaction.atomic
def query_number_portfolios_of_user(user_id: int) -> int:
    try:
        query_str = """
            select count(p.id)
            from portfolio_portfolio p
            where p.user_id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(query_str, [user_id])
            res = cursor.fetchall()
            for r in res:
                return int(r[0])

            raise IntegrityError("Illegal state!")

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Portfolios query creation not successful.")


def query_number_pages_portfolios_of_user(user_id: int, page_size: int) -> int:
    page_size = max(1, page_size)
    return ceil(float(query_number_portfolios_of_user(user_id)) / page_size)


@transaction.atomic
def query_portfolio_of_user_by_id(user_id: int, pid: int) -> Optional[dict]:
    try:
        query_str = """
            select p.id, p.title, (
            select count(distinct(t.id)) from portfolio_transaction t where p.id=t.portfolio_id
            ) as transactions, (
            select count(distinct(t.exchange_wallet)) from portfolio_transaction t where p.id=t.portfolio_id
            ) as exchanges, (
            select count(distinct(r.id))
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            ) as reports, (
            select r.realized_profit_sum
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            order by r.created desc
            limit 1
            ) as latest_report_profit, (
            select a.base_currency_id
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            order by r.created desc
            limit 1
            ) as latest_report_currency, (
            select r.created
            from tax_analysis_portfolioanalysis a
            join tax_analysis_portfolioanalysisreport r on r.analysis_id=a.id
            where p.id=a.portfolio_id
            order by r.created desc
            limit 1
            ) as latest_report_date
            from portfolio_portfolio p
            where p.user_id=%s
            and p.id=%s
        """

        with connection.cursor() as cursor:
            cursor.execute(query_str, [user_id, pid])
            res = cursor.fetchall()
            for r in res:
                return {
                    "id": r[0],
                    "title": r[1],
                    "transactions": r[2],
                    "exchanges": r[3],
                    "reports": r[4],
                    "latest_report_profit": r[5],
                    "latest_report_currency": r[6],
                    "latest_report_date": r[7],
                }

            return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Portfolio query creation not successful.")
