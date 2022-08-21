create or replace view v_tax_analysis_processableoder as
select 
	pt.id ptid, po.id poid, pt.analysis_id ana_id,
	pt.datetime datetime,
	fee, fee_currency_id, pt.created created,
	exchange_wallet,
	pt.cooldown_until, 
	po.from_currency_id, po.from_amount, 
	po.to_currency_id, po.to_amount
from tax_analysis_processableorder po
	join tax_analysis_processabletransaction pt
		on po.transaction_id = pt.id
	join tax_analysis_portfolioanalysis a
		on a.id=pt.analysis_id
	where a.failed = False
;
		
create or replace view v_tax_analysis_processabledeposit as
select 
	pt.id ptid, pd.id pdid, pt.analysis_id ana_id,
	pt.datetime datetime, pt.type,
	fee, fee_currency_id, pt.created created,
	exchange_wallet,
	pt.cooldown_until, 
	pd.currency_id, pd.buy_datetime,
	pd.amount, pd.taxable
from tax_analysis_processabledeposit pd
	join tax_analysis_processabletransaction pt
		on pd.transaction_id = pt.id
	join tax_analysis_portfolioanalysis a
		on a.id=pt.analysis_id
	where a.failed = False
;

create or replace view v_tax_analysis_processabletransfer as
select 
	pta.id ptaid, ptf.id ptfid, pta.analysis_id ana_id,
	pta.datetime datetime,
	fee, fee_currency_id, pta.created created,
	exchange_wallet,
	pta.cooldown_until, 
	ptf.from_exchange_wallet, 
	ptf.currency_id, ptf.amount
from tax_analysis_processabletransfer ptf
	join tax_analysis_processabletransaction pta
		on ptf.transaction_id = pta.id
	join tax_analysis_portfolioanalysis a
		on a.id=pta.analysis_id
	where a.failed = False
;	
		