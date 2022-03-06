create or replace view v_processed_percentage_per_analysis as
select tmp.*, (num_processed/(
	case when (num_unprocessed+num_processed+0.0)=0
	then 1 else (num_unprocessed+num_processed+0.0) end
)) done 
from (
	select 
		id, 
		(
			select count(ansub.id)
			from tax_analysis_analysable ansub
			where ansub.analysis_id=ana.id
		) as num_processed, 
		(
			select count(proc.id)
			from tax_analysis_processabletransaction proc
			where proc.analysis_id=ana.id
		) as num_unprocessed
	from tax_analysis_portfolioanalysis ana
) as tmp