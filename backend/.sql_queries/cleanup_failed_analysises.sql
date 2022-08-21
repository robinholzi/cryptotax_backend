create or replace function cleanup_failed_analysises()
returns BOOLEAN
as

$$
declare
	ret_val BOOLEAN;

BEGIN -- transaction

	-- processables ---------------------------------

	delete from tax_analysis_processableorder x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_processabletransaction ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.transaction_id
		and a.failed=True
	);

	delete from tax_analysis_processabledeposit x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_processabletransaction ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.transaction_id
		and a.failed=True
	);

	delete from tax_analysis_processabletransfer x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_processabletransaction ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.transaction_id
		and a.failed=True
	);

	delete from tax_analysis_processabletransaction ta
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
	where
		a.id=ta.analysis_id 
		and a.failed=True
	);

	-- analysables ---------------------------------
	
	delete from tax_analysis_analysistransferconsumer x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_analysisconsumer  c 
		on c.analysis_id = a.id
	where 
		c.id = x.parent_id
		and a.failed=True
	);

	delete from tax_analysis_analysissellconsumer x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_analysisconsumer  c 
		on c.analysis_id = a.id
	where 
		c.id = x.parent_id
		and a.failed=True
	);

	delete from tax_analysis_analysisconsumer x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
	where 
		a.id = x.analysis_id
		and a.failed=True
	);
	
	
	

	delete from tax_analysis_analysisconsumable x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_analysable  ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.analysable_id
		and a.failed=True
	);

	delete from tax_analysis_analysisbuy x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_analysable  ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.transaction_id
		and a.failed=True
	);

	delete from tax_analysis_analysissell x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_analysable ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.transaction_id
		and a.failed=True
	);

	delete from tax_analysis_analysistransfer x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_analysable ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.transaction_id
		and a.failed=True
	);

	delete from tax_analysis_analysisdeposit x
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
		join tax_analysis_analysable ta 
		on ta.analysis_id = a.id
	where 
		ta.id = x.transaction_id
		and a.failed=True
	);

	delete from tax_analysis_analysable ta
	where exists (
	select *
	from tax_analysis_portfolioanalysis a
	where
		a.id=ta.analysis_id 
		and a.failed=True
	);
	
	-- todo consumers

	return true;
end;
$$ 
language plpgsql;
