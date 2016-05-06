require( Nozzle.R1 )
path <- "$loc" # WARNING : USE AT YOUR OWN RISK, may be overwriten by tag code.
setwd("$loc")

report_name <- "$report_name"
# define a function for exception handler
failed_fun_print <- function(section_name, error_report){
	Error_report_par  <- newParagraph("<br>", asStrong( "Error Log Details: " ),"<br><br>",asCode(paste(error_report,collapse="")));
	section_name      <- addTo( section_name, newParagraph( "This section FAILED! Contact the development team... " ), Error_report_par )
	return (section_name)
}

$project_parameters
$pipeline_config

REPORT <- newCustomReport(report_name)
$tags

# Render the report to a file
writeReport( REPORT, filename=toString("$dochtml"))
# system("chmod -R 770 .")
system("touch r_done")

