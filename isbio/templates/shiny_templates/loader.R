#Load the QC data Excel file. 
file_name <- paste("$QC_dsrt_tbl",sep="/") 
if (file.exists(file_name)) {
	QC_dsrt_tbl <- readWorksheetFromFile(file_name, sheet=1, header = TRUE)
}

#Extract the clinical data
file_name <- paste("$Clindata_dsrt_tbl",sep="/") 
if (file.exists(file_name)) {
	Clindata_dsrt_tbl <- readWorksheetFromFile(file_name, sheet=3, header = TRUE)
	samples <- colnames(Clindata_dsrt_tbl)[3:c(grep("Mechanism.Targets",colnames(Clindata_dsrt_tbl))-2)]
}
