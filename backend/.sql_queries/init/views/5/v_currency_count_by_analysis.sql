create or replace view v_currency_count_by_analysis as 
select ana.id, (
	select count(distinct(currency)) as currencies
	from (
	(select tmp.from_currency_id as currency from v_tax_analysis_processableoder tmp where tmp.ana_id=ana.id)
	union
	(select tmp.to_currency_id from v_tax_analysis_processableoder tmp where tmp.ana_id=ana.id)
	union
	(select tmp.currency_id from v_tax_analysis_processabledeposit tmp where tmp.ana_id=ana.id)
	union
	(select tmp.currency_id from v_tax_analysis_processabletransfer tmp where tmp.ana_id=ana.id)
	union
	(select tmp.fee_currency_id from tax_analysis_processabletransaction tmp where tmp.analysis_id=ana.id)
	union
		------------------------------
	(select tmp.currency_id from v_tax_analysis_analysablebuy tmp where tmp.ana_id=ana.id)
	union
	(select tmp.currency_id from v_tax_analysis_analysablesell tmp where tmp.ana_id=ana.id)
	union
	(select tmp.currency_id from v_tax_analysis_analysabledeposit tmp where tmp.ana_id=ana.id)
	union
	(select tmp.currency_id from v_tax_analysis_analysabletransfer tmp where tmp.ana_id=ana.id)
	union
	(select tmp.base_currency_id from tax_analysis_portfolioanalysis tmp where tmp.id=ana.id)
	) tmp
) 
from tax_analysis_portfolioanalysis ana