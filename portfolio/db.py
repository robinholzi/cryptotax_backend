from django.db import IntegrityError, transaction, connection
from django.db.utils import DatabaseErrorWrapper


@transaction.atomic
def query_portfolios_of_user(user_id):
    try:
        query_str = f"""
            select p.id, p.title, (
            select count(t.id) from portfolio_transaction t where p.id=t.portfolio_id
            ) as transactions, (
            select count(t.exchange_wallet) from portfolio_transaction t where p.id=t.portfolio_id
            ) as exchanges, (
            select count(r.id) 
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
        """

        with connection.cursor() as cursor:
            cursor.execute(query_str, [user_id])
            res = cursor.fetchall()
            portfolios = []
            for r in res:
                portfolios.append({
                    'id': r[0],
                    'title': r[1],
                    'transactions': r[2],
                    'exchanges': r[3],
                    'reports': r[4],
                    'latest_report_profit': r[5],
                    'latest_report_currency': r[6],
                    'latest_report_date': r[7],
                })

            return portfolios

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Portfolios query creation not successful.")


@transaction.atomic
def query_portfolio_of_user_by_id(user_id, pid):
    try:
        query_str = f"""
            select p.id, p.title, (
            select count(t.id) from portfolio_transaction t where p.id=t.portfolio_id
            ) as transactions, (
            select count(t.exchange_wallet) from portfolio_transaction t where p.id=t.portfolio_id
            ) as exchanges, (
            select count(r.id) 
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
                    'id': r[0],
                    'title': r[1],
                    'transactions': r[2],
                    'exchanges': r[3],
                    'reports': r[4],
                    'latest_report_profit': r[5],
                    'latest_report_currency': r[6],
                    'latest_report_date': r[7],
                }

            return None

    except IntegrityError as ie:
        print(ie)
        raise DatabaseErrorWrapper("Portfolio query creation not successful.")
