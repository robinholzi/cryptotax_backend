create function update_analysis_modes()
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
	update tax_analysis_portfolioanalysis
	set mode = 'F'
	where -- exists better than join for delete statements
		tax_analysis_portfolioanalysis.failed=False
		and tax_analysis_portfolioanalysis.mode = 'A'
		and not exists (
			select *
			from tax_analysis_analysable ana
			where ana.analysis_id = tax_analysis_portfolioanalysis.id
	);

	-- -----------------------------------------------------------------------------------------------------
	-- [Finished->genResult] -------------------------------------------------------------------------------
	
	    -- title: default - based on portfolio name & hash/id?
		-- error_message
		-- tax_sum: by queryies: sum up all taxes from consumers in current analysis (easy)
		-- fee_sum: by queries: sum up all fees in analysables in current analysis (easy)
		
		-- TODO
		
	-- -----------------------------------------------------------------------------------------------------

	return NULL;
end;
$emp_audit$
language plpgsql;
