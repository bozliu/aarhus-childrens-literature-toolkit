# Set wd
rm(list = ls())
wd <- 'Your/working/directory'
setwd(wd)
source('util_fun.R')

## import directory
input.dir <- '/Path/To/Input/Dir'
files.v <- dir(path = input.dir, pattern='.*txt')

# tokenize texts in directory
maketext <- function(files,directory){
  text.word.l <- list() 
  for(i in 1:length(files)){ 
    text.v <- scan(paste(directory, files[i], sep="/"), what="character", sep="\n") 
    lines <- as.list(text.v)
    start.v <- grep(pattern = "\\*\\*\\*", text.v, perl=TRUE)[1]
    end.v <- grep(pattern = "\\*\\*\\*", text.v, perl=TRUE)[2]
    metadata.v <- text.v[c(1:start.v,end.v:length(text.v))]# create metadata variable
    text.v <- paste(text.v) 
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