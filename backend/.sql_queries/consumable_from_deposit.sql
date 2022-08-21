with selected as (
	select d.id depid, ana.id anaid, analysis.id analysisid, type, exchange_wallet
	from tax_analysis_analysisdeposit d
		join tax_analysis_analysable ana on d.transaction_id=ana.id
		join tax_analysis_portfolioanalysis analysis on ana.analysis_id=analysis.id
	where d.id=190
		and ana.analysed=False
		and analysis.mode='A'
		and analysis.cooldown_until > now() -- cooldown still active
),

updated as (
	update tax_analysis_portfolioanalysis
	set cooldown_until=null
	where id=all (
		select s.analysisid
		from selected s
	) and not empty (select * from selected)
)

update tax_analysis_analysable
set analysed=True
where id=all (
	select s.anaid
	from selected s
) and not empty (select * from selected);