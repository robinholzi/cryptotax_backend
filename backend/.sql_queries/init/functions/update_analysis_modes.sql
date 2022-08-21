create or replace function update_analysis_modes()
returns trigger
as
$emp_audit$

BEGIN -- transaction

	-- checks als unfailed analysises in mode 'Processing' or 'Analysing'
	
	-- if not objects left to work on: 
	-- finished: (Processing->Analysing), (Analysing->Finished)
	
	-- [Processing->Analysing] -----------------------------------------------------------------------------
	
	-- find all analysises which are not failed, are in processing state and have no processables any more
	update tax_analysis_portfolioanalysis
	set mode = 'A'
	where -- exists better than join for delete statements
		tax_analysis_portfolioanalysis.failed=False
		and tax_analysis_portfolioanalysis.mode = 'P'
		and not exists (
			select *
			from tax_analysis_processabletransaction pt
			where pt.analysis_id = tax_analysis_portfolioanalysis.id
	);
	
	-- [Analysing->Finished] -------------------------------------------------------------------------------
	
	-- find all analysises which are not failed, are in processing state and have no processables any more
	with finishedAnalysises(id) as (
		select a.id
		from tax_analysis_portfolioanalysis a
		where
			a.failed=False
			and a.mode = 'A'
			and not exists (
				select *
				from tax_analysis_analysable ana
				where ana.analysis_id = a.id
				and ana.analysed = False
		)
	),
	inserted as (
		insert into tax_analysis_portfolioanalysisreport (
			analysis_id,
			error_message,
			fee_sum,
			realized_profit_sum,
			taxable_profit_sum
		) 
		select fa.id, NULL, 
		(select tf.sum from v_total_fees tf where tf.analysis_id = fa.id),
		profits.sum_realized_profit,
		profits.sum_taxable_realized_profit
		from finishedAnalysises fa
		join v_profits profits on profits.analysis_id = fa.id
	)
	
	update tax_analysis_portfolioanalysis
	set mode = 'F'
	where tax_analysis_portfolioanalysis.id in (select id from finishedAnalysises);

	return NULL;
end;
$emp_audit$
language plpgsql;
