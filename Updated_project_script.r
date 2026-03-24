####### ROUGH WORKING SCRIPT FOR PROJECT ######
#### Run once for women; again for men ####
rm(list = ls())
wd <- '~/Documents/projects/aarhus/data/'
setwd(wd)
source('util_fun.R')
library(tm)
library(NLP)
library(openNLP)
library(quanteda)
library(syuzhet)
library(tm)
library(qdap)
library(plyr)
library(slam)
library(dplyr)
library(rJava)

### Import text files from Project Gutenberg ####

## Scrape web links from html ##
filename.v = '~/Path/to/html'
html.v <- scan(filename.v, what = 'character', sep='\n', encoding = 'UTF-8')
m <- regexpr("www.gutenberg.org/ebooks/\\d+", html.v, perl=TRUE)
links = regmatches(html.v, m)
links
ddir = '~/Path/to/directory'
dir.create(ddir)

## Scrape file location from URL ##
url <- c(links)
nums <- gsub(".*\\.org/ebooks/","",url) 
nums <- sort(nums)
print(nums)

##loop for all URLs ##
for (num in nums){
  tryCatch({
    address <- paste("http://gutenberg.pglaf.org/cache/epub/", num, "/pg", num,'.txt', sep="")
    filename <- paste(num, '.txt', sep="")
    path <- paste(ddir, filename)
    download.file(address, destfile=path)
  }, error=function(e){cat("ERROR :",conditionMessage(e), "\n")})
}
text.word.l <- maketext(files.v,input.dir)
texttitle.l <- gsub("\\..*","",files.v)

### Clean metadata and tokenize ####

## import directory ##
input.dir <- '~/Documents/projects/aarhus/data/children/men/'
files.v <- dir(path = input.dir, pattern='.*txt')

## tokenize texts in directory ##
maketext <- function(files,directory){
  text.word.l <- list() 
  for(i in 1:length(files)){ 
    text.v <- scan(paste(directory, files[i], sep="/"), what="character", sep="\n") 
    lines <- as.list(text.v)
    start.v <- grep(pattern = "\\*\\*\\*", text.v, perl=TRUE)[1]
    end.v <- grep(pattern = "\\*\\*\\*", text.v, perl=TRUE)[2]
    metadata.v <- text.v[c(1:start.v,end.v:length(text.v))]# create metadata variable
    textlines.v <- text.v[(start.v+2):(end.v-2)]
    text.lower.v <- tolower(textlines.v) # casefolding
    text.words.v <- strsplit(text.lower.v, "\\W") # tokenize
    text.words.v <- unlist(text.words.v) # transform list to vector
    text.words.v <- text.words.v[which(text.words.v!="")] # remove blanks
    text.word.l[[files[i]]] <- text.words.v # update list
  }
  return(text.word.l)
}  
text.word.l <- maketext(files.v,input.dir)
texttitle.l <- gsub("\\..*","",files.v)

###### NER #######
###############################################
#### THIS SECTION IS NOT COMPLETE ############
##############################################
###options(mc.cores=1)
filenames.v <- Sys.glob("~/Documents/projects/aarhus/data/children/men/*.txt")
basename(filenames.v)

texts.l <- filenames.v %>%
  lapply(readLines) %>%
  lapply(paste0, collapse = " ") %>%
  lapply(as.String)
names(texts.l) <- gsub("\\..*","",basename(filenames.v))
str(texts.l, max.level = 1)
class(texts.l)
class(texts.l[[1]])

# annotation 
entity.an <- function(doc, pipeline) {
  annotations <- annotate(doc, pipeline)
  AnnotatedPlainTextDocument(doc, annotations)
}

# second argument for entity.an
pipelineanno <- list(
  Maxent_Sent_Token_Annotator(),
  Maxent_Word_Token_Annotator(),
  Maxent_Entity_Annotator(kind = "person"),
  Maxent_Entity_Annotator(kind = "location")
)

synop_annotated <- texts.l %>% 
  lapply(entity.an, pipelineanno)

person.l <- synop_annotated %>%
  lapply(entities, kind = "person") 
location.l <- synop_annotated %>%
  lapply(entities, kind = "location") 

### Location analysis
n1 <- location.l %>% sapply(length)
n2 <- location.l %>% lapply(unique) %>% sapply(length)
N <- synop_annotated %>% lapply(words) %>% sapply(length)
locationratio.v <- n1/N # relative frequency of location
uniqueratio.v <- n1/n2 # average use of locations

# plot relative importance of location
names(locationratio.v) <- gsub('\\..*',"",names(locationratio.v))
barplot(locationratio.v, main = 'Location Entities', xlab = 'Book', ylab = 'Relative frequency')


############################################
######## END INCOMPLETE SECTION ############
#############################################

#### Sentiment Analysis ###
## sentiment for each document ##

# slice text in n bins #
slice_text <- function(text,bin){
  sliced.text.l <- split(text, cut(1:length(text),bin))
}
text.l <- maketext(files.v,input.dir)
names(text.l) <- gsub("\\..*","",files.v)
text.l <- unlist(lapply(text.l,slice_text,2), recursive=FALSE)# why could slice size matter?
text.v <- gsub("\\..*","",names(text.l))

# create corpus from slices #
library(tm)
text.cor <- Corpus(VectorSource(lapply(text.l, paste, collapse = " ")))

# clean and filter #
text.cor <- tm_map(text.cor, removeNumbers)
text.cor <- tm_map(text.cor, removeWords, stopwords("english"))
text.cor <- tm_map(text.cor, stripWhitespace)

# sentiment for each document #
afinncorpus <- function(corpus){
  sent <- rep(0,length(corpus))
  for(i in 1:length(corpus)){
    sent[i] <- get_sentiment(paste(corpus[[i]]$content, collapse = " "),method = 'afinn')
  }
  return(sent)
}
text.v <-afinncorpus(text.cor)
summary(text.v)
dev.new(); barplot(sent.v, main="Sentiments - ", horiz=TRUE)

### LDA ###
## create document term matrix ##
text.dtm <- DocumentTermMatrix(text.cor)
print(text.dtm)
text.dtm <- docsparse(2,text.dtm)
print(text.dtm)
summary(col_sums(text.dtm))

# prune dtm #
prune <- function(dtm,mx){
  mx <- ceiling(dim(dtm)[1]*mx)
  dtm <- dtm[,slam::col_sums(as.matrix(dtm) > 0) < mx]
  return(dtm)
}
text.dtm <- prune(text.dtm,.75)# try other levels of pruning
summary(col_sums(text.dtm))

# train topic model based latent dirichlet allocation #
library(topicmodels) # Based on Blei's code
ls('package:topicmodels') # show functions in library
k = 10 # number of topics
seed <- 1234
mdl1 <- LDA(text.dtm, k = k, method = 'VEM', control = list(seed = seed))
## unpacking the model

# quick & dirty #
terms(mdl1,10)
topics(mdl1,2)

# proportions parameter
alpha <- mdl1@alpha
print(alpha)
# lexicon
lexicon <- mdl1@terms
head(lexicon)

# topics' word distribution (these estimate are only semi-meaningful)
topicword.mat <- mdl1@beta
dim(topicword.mat)
terms(mdl1,10)# print the 10 most likely terms within each topic

# documents' topic distribution
doctopic.mat <- mdl1@gamma
dim(doctopic.mat)
doctopic.mat[1,]# topic saturation of document 1
row_sums(doctopic.mat)[1]
# plot document distribution
barplot(doctopic.mat[1,])
library(ggplot2)
dev.new()

i = 6 # document number to plot
dt.df <- data.frame(x = 1:length(doctopic.mat[i,]), y = doctopic.mat[i,])
ggplot(data = dt.df, aes(x = x, y = y)) +
  geom_bar(stat = "identity", colour ="#FF9999")+
  theme_minimal() +
  scale_x_discrete('Topic', breaks = 1:k, limits = as.character(1:k)) +
  ylab("Document weight") +
  labs(title = paste(text.dtm$dimnames$Docs[i]))


# calculate posteriors for words within each topic
mdl1post.l <- posterior(mdl1, text.dtm)
str(mdl1post.l)
# topic 1
tmp <- sort(mdl1post.l$terms[4,], decreasing = T)# word posteriors for each topic p(w|k)=ϕkw
# and now the obligatory topic word cloud
library(wordcloud); require(RColorBrewer)
pal2 <- brewer.pal(8,"Dark2")
dev.new()
wordcloud(names(tmp[1:20]),tmp[1:30], scale=c(8,.2), random.order=FALSE, rot.per=.15, colors=pal2)

# perplexity
# model evaluation
perplexity(mdl1)
perplexity(mdl1,thom.dtm)

### estimate number of topics (optimal k estimation) - BE CAREFUL! ###
k = 100
#progress.bar <- create_progress_bar("text")
#progress.bar$init(k)
best.mdl <- list()
perplex.mat <- matrix(0,k-1,2)
for(i in 2:k){
  best.mdl[[i-1]] <- LDA(books.dtm, i)
  print(paste('k =',i, sep = ' '))
  #progress.bar$step()
}

# unpack model
# ten most likely terms in each topic
terms(best.mdl[[18]],10)

# two dominant topics for all documents
top2 <- topics(best.mdl[[18]],2)
colnames(top2) <- filenames
print(top2)

##### NER #######
filenames.v <- Sys.glob("~/Documents/projects/aarhus/data/children/men/*.txt")# wildcard expansion
filenames.v <- filenames.v[c(60,61,57)]# Synoptic Gospels
basename(filenames.v)
# piping through the documents
texts.l <- filenames.v %>%
  lapply(readLines) %>%
  lapply(paste0, collapse = " ") %>%
  lapply(as.String)
names(texts.l) <- gsub("\\..*","",basename(filenames.v))
# list of strings
str(texts.l, max.level = 1)
class(texts.l)
class(texts.l[[1]])
# annotation 
entity.an <- function(doc, pipeline) {
  annotations <- annotate(doc, pipeline)
  AnnotatedPlainTextDocument(doc, annotations)
}

# second argument for entity.an
pipelineanno <- list(
  Maxent_Sent_Token_Annotator(),
  Maxent_Word_Token_Annotator(),
  Maxent_Entity_Annotator(kind = "person"),
  Maxent_Entity_Annotator(kind = "location")
)

synop_annotated <- texts.l %>% 
  lapply(entity.an, pipelineanno)

person.l <- synop_annotated %>%
  lapply(entities, kind = 'person') 
location.l <- synop_annotated %>%
  lapply(entities, kind = 'location') 

n1 <- location.l %>% sapply(length)
n2 <- location.l %>% lapply(unique) %>% sapply(length)
N <- synop_annotated %>% lapply(words) %>% sapply(length)
locationratio.v <- n1/N # relative frequency of location
uniqueratio.v <- n1/n2 # average use of locations
# plot relative importance of location
names(locationratio.v) <- gsub('\\..*',"",names(locationratio.v))
barplot(locationratio.v, main = 'Location Entities', xlab = 'Book', ylab = 'Relative frequency')