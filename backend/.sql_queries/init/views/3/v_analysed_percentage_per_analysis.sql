create or replace view v_analysed_percentage_per_analysis as
select tmp.*, (num_analysed/(
	case when (num_unanalysed+num_analysed+0.0)=0
	then 1 else (num_unanalysed+num_analysed+0.0) end
)) done 
from (
	select 
		id, 
		(
			select count(ansub.id)
			from tax_analysis_analysable ansub
			where ansub.analysis_id=ana.id
				and ansub.analysed=True
		) as num_analysed, 
		(
			(
				select count(proc.id)
				from tax_analysis_processabletransaction proc
				where proc.analysis_id=ana.id
			) 
			+ 
			(
				select count(ansub.id)
				from tax_analysis_analysable ansub
				where ansub.analysis_id=ana.id
					and ansub.analysed=False
			)
		) as num_unanalysed
	from tax_analysis_portfolioanalysis ana
) as tmp