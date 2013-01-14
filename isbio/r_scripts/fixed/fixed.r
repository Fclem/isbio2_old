
testfunc <- function(arg1){
	x <- c(1,3,6,9,12)
	y <- c(1.5,2,7,8,15)
	x2 <- c(0.5, 3, 5, 8, 12)
	y2 <- c(0.8, 1, 2, 4, 6)

	myline.fit <- lm(y ~ x)

	png('/home/comrade/Desktop/rplot.png')
	plot(x,y, xlab="x axis", ylab="y axis", main="my plot", ylim=c(0,20), xlim=c(0,20), pch=15, col="blue")	
	if (arg1) {
	    abline(myline.fit)
	    points(x2, y2, pch=16, col="green")
	}
	dev.off()	
}



