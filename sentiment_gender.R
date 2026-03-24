#### Sentiment Analysis ###

rm(list = ls())
wd <- '~/Path/to/Working/Directory'
input.dir <- '~/Path/to/gendered/corpus'
files.v <- dir(path = input.dir, pattern='.*txt')
setwd(wd)
source('util_fun.R')

## sentiment for each document ##

# Slice text into bins -- this separates each text into two parts.
## This is for reasons of efficiency, etc.
slice_text <- function(text,bin){
  sliced.text.l <- split(text, cut(1:length(text),bin))
}
text.l <- maketext(files.v,input.dir)  # NB - this requires the maketext function, defined in the t_models script.
names(text.l) <- gsub("\\..*","",files.v) # the regex here says basically, 'take any file of any name in the input directory'
text.l <- unlist(lapply(text.l,slice_text,2), recursive=FALSE) # split these into two and make a list of slices
text.v <- gsub("\\..*","",names(text.l)) # Turn this list back into character vector

# Create corpus from slices #
library(tm)
text.cor <- Corpus(VectorSource(lapply(text.l, paste, collapse = " ")))

# Clean and filter corpus #
text.cor <- tm_map(text.cor, removeNumbers) # Remove all numbers from corpus
text.cor <- tm_map(text.cor, removeWords, stopwords("english"))  # remove all words on stopword list from corpus -- long
text.cor <- tm_map(text.cor, stripWhitespace) # Remove all extra whitespace from corpus

# This functions provides an overall sentiment score for each text in the corpus#
## Again, we are using the AFINN sentiment scores but other options are available.

afinncorpus <- function(corpus){
  sent <- rep(0,length(corpus))
  for(i in 1:length(corpus)){
    sent[i] <- get_sentiment(paste(corpus[[i]]$content, collapse = " "),method = 'afinn')
  }
  return(sent)
}
text.v <-afinncorpus(text.cor)  # Perform afinncorpus function on text.cor. Return value as text.v
summary(text.v)  # See summary in console
dev.new(); barplot(sent.v, main="Sentiments in ---- ", horiz=TRUE) # Print barplot summary.

# You could go further here and use ggplot2 to present nicer visuals.
## Similarly, you could dig around with the numbers here in more depth. 