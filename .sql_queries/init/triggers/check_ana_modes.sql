DROP TRIGGER IF EXISTS trigger_check_update_analysis_mode ON tax_analysis_analysable;
CREATE TRIGGER trigger_check_update_analysis_mode
AFTER INSERT OR UPDATE OR DELETE ON tax_analysis_analysable
FOR EACH ROW
EXECUTE PROCEDURE update_analysis_modes();