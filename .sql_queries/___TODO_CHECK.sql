select *
from v_tax_analysis_analysablebuy
where currency_id='XLM' and ana_id=22;

-- TODO select * from sells & MANUAL WORST & BEST CASE CALC CHCEK (139.73 euro profit?)

select * from v_detailed_sell_report
where analysis_id=22 and currency='XLM'