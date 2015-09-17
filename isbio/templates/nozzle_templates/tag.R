
if(!exists("section_name")){
	section_name <- report_name
}
if(exists("section_body")){
	new_section <- newSection( section_name )
	tag_section <- tryCatch({section_body(new_section)}, error = function(e){ failed_fun_print(new_section,e) })
	REPORT <- addTo( REPORT, tag_section )
}

# <------- end of header -------->
##### END OF TAG #####

setwd(path)
