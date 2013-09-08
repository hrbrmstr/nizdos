#
# nizdos-quick.R
#
# Copyright (c) 2013 Bob Rudis (@hrbrmtr) bob@rudis.net
#
# MIT License
#
# quick/small example of how to extract the Nest data we're storing then
# summarize and plot it
#

library(RMongo)
library(reshape2)
library(ggplot2)
library(gridExtra)
library(scales)

# Connect to mongo
nest <- mongoDbConnect('nest')

# setup and execute query
query <- dbGetQuery(nest, 'readings', "", skip=0, limit=0)
readings <- query[c('date', 'temp', 'humid')]

# convert date string to date/time
readings$date <- as.POSIXct(gsub(" UTC","",readings$date),format="%a %b %d %H:%M:%S %Y", tz="UTC")

# take a quick look at the data
summary(readings)

# setup chart readings colors
nestTempCol <- "#7B3294"
nestHumidCol <- "#008837"
nestColRange <- c(nestTempCol,nestHumidCol)

# setup temperature plot
gg <- ggplot(data=readings, aes(x=date))
gg <- gg + geom_line(aes(y=temp), color=nestTempCol)
gg <- gg + scale_x_datetime(breaks = date_breaks("1 day"), minor_breaks=NULL)
gg <- gg + labs(x="", y="Temperature (°F)")
gg <- gg + theme_bw()

# setup humidity plot
gg1 <- ggplot(data=readings, aes(x=date))
gg1 <- gg1 + geom_line(aes(y=humid), color=nestHumidCol)
gg1 <- gg1 + scale_x_datetime(breaks = date_breaks("1 day"), minor_breaks=NULL)
gg1 <- gg1 + labs(x="Time", y="Humidity (%)")
gg1 <- gg1 + theme_bw()

# setup boxplot of both readings
melted.readings <- melt(readings, id.vars=c("date"))
gg2 <- ggplot(data=melted.readings, aes(variable, value))
gg2 <- gg2 + geom_boxplot(color=nestColRange)
gg2 <- gg2 + labs(x="Reading",y="Value Range")
gg2 <- gg2 + theme_bw()

# save it out to a file
png("nest-quick.png",width=600,height=300)
grid.arrange(arrangeGrob(gg, gg1, ncol=1), gg2, ncol=2, widths=c(1.75,1))
dev.off()

