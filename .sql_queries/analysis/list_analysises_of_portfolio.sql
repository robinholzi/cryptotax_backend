select ana.id, ana.title, ana.created, ana.mode, ana.failed, ana.algo, ana.transfer_algo, ana.base_currency_id,
((select count(distinct(pt.id)) from tax_analysis_processabletransaction pt where pt.analysis_id=ana.id)
 +(select count(distinct(ta.id)) from tax_analysis_analysable ta where ta.analysis_id=ana.id)) as txs,
anarep.taxable_profit_sum as taxable_profit,
anarep.realized_profit_sum as realized_taxable_profit,
anarep.fee_sum as fees,
(ppa.done + apa.done)/2.0 as progress,
case when anarep.id is NULL then 'processing...' else anarep.error_message end
from tax_analysis_portfolioanalysis ana
left outer join tax_analysis_portfolioanalysisreport anarep ON anarep.analysis_id = ana.id
join v_processed_percentage_per_analysis ppa ON ppa.id=ana.id
join v_analysed_percentage_per_analysis apa ON apa.id=ana.id
where ana.portfolio_id=8 -- TODO
order by ana.id
limit 15
offset 0;