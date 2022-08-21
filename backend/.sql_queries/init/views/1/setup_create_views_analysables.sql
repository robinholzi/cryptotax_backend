create or replace view v_tax_analysis_analysablebuy as
select
	ana.id aid, ab.id abid, ana.analysis_id ana_id,
	ana.type, ana.datetime datetime,
	fee, ana.created created,
	exchange_wallet, analysed,
	ab.currency_id, ab.amount, ab.price
from tax_analysis_analysisbuy ab
	join tax_analysis_analysable ana
		on ab.transaction_id = ana.id
	join tax_analysis_portfolioanalysis a
		on a.id=ana.analysis_id
	where a.failed = False
;

create or replace view v_tax_analysis_analysablesell as
select
	ana.id aid, asell.id asellid, ana.analysis_id ana_id,
	ana.type, ana.datetime datetime, 
	fee, ana.created created,
	exchange_wallet, analysed,
	asell.currency_id, asell.amount, asell.price
from tax_analysis_analysissell asell
	join tax_analysis_analysable ana
		on asell.transaction_id = ana.id
	join tax_analysis_portfolioanalysis a
		on a.id=ana.analysis_id
	where a.failed = False
;
		
create or replace view v_tax_analysis_analysabledeposit as
select 
	ana.id aid, ad.id asellid, ana.analysis_id ana_id,
	ana.type, ana.datetime datetime, ad.type as deposit_type,
	fee, ana.created created,
	exchange_wallet, analysed,
	ad.currency_id, ad.buy_datetime,
	ad.amount, ad.price, ad.taxable
from tax_analysis_analysisdeposit ad
	join tax_analysis_analysable ana
		on ad.transaction_id = ana.id
	join tax_analysis_portfolioanalysis a
		on a.id=ana.analysis_id
	where a.failed = False
;

create or replace view v_tax_analysis_analysabletransfer as
select 
	ana.id aid, atrans.id asellid, ana.analysis_id ana_id,
	ana.type, ana.datetime datetime,
	fee, ana.created created,
	exchange_wallet,
	atrans.from_exchange_wallet, 
	atrans.currency_id, atrans.amount
from tax_analysis_analysistransfer atrans
	join tax_analysis_analysable ana
		on atrans.transaction_id = ana.id
	join tax_analysis_portfolioanalysis a
		on a.id=ana.analysis_id
	where a.failed = False
;

		