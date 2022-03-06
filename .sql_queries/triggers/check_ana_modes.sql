CREATE TRIGGER trigger_check_update_analysis_mode
AFTER INSERT ON tax_analysis_analysable
    FOR EACH ROW
EXECUTE PROCEDURE update_analysis_modes();