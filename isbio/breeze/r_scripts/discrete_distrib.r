require(stats)

png('/home/comrade/Projects/fimm/isbio/breeze/static/dp.png')
plot(table(rpois(100, 5)), type = "h", col = "red", lwd = 10, main = "rpois(100, lambda = 5)")
dev.off()
