create or replace view v_wallet_count_by_analysis as  
select ana.id, (
	select count(distinct(wallet)) as wallets
	from (
	(select tmp.from_exchange_wallet as wallet from v_tax_analysis_processabletransfer tmp where tmp.ana_id=ana.id)
	union
	(select tmp.exchange_wallet from tax_analysis_processabletransaction tmp where tmp.analysis_id=ana.id)
	union
		------------------------------
	(select tmp.exchange_wallet from tax_analysis_analysable tmp where tmp.analysis_id=ana.id)
	union
	(select tmp.from_exchange_wallet from v_tax_analysis_analysabletransfer tmp where tmp.ana_id=ana.id)
	) tmp
)
from tax_analysis_portfolioanalysis ana