test <- function(arg){
	x <- rnorm(250,mean=0,sd=7)
	y <- rnorm(250,mean=7,sd=0.35)

	switch(arg,	
	"plot" = {png('/home/comrade/Projects/fimm/isbio/breeze/static/rplot.png'); plot(x,y); dev.off()},
	"hisg" = {png('/home/comrade/Projects/fimm/isbio/breeze/static/rplot.png'); hist(x,y,breaks = 45); dev.off()},
	"box"  = {png('/home/comrade/Projects/fimm/isbio/breeze/static/rplot.png'); boxplot(x,y); dev.off()}
	)
}

