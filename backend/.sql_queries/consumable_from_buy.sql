with selected as (
	select b.id buyid, ana.id anaid, analysis.id analysisid, type, exchange_wallet
	from tax_analysis_analysisbuy b
		join tax_analysis_analysable ana on b.transaction_id=ana.id
		join tax_analysis_portfolioanalysis analysis on ana.analysis_id=analysis.id
	where b.id=190
		and ana.analysed=False
		and analysis.mode='A' 
		and analysis.cooldown_until > now() -- cooldown still active
),
inserted as (
	insert into tax_analysis_analysisconsumable (analysable_id, type, exchange_wallet)
	select anaid, 'BO', exchange_wallet
	from selected
),

updated as (
	update tax_analysis_portfolioanalysis
	set cooldown_until=null
	where id=all (
		select s.analysisid
		from selected s
	) and exists (select * from selected)
)

update tax_analysis_analysable
set analysed=True
where id=all (
	select s.anaid
	from selected s
) and exists (select * from selected);