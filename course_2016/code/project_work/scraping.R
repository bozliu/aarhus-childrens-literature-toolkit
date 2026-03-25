
##### Script for importing text files from Project Gutenberg ######
#### Firstly, go to Project Gutenberg website. Right click on 'Children's Lit Bookshelf' and right click. Select 'View page source'. Save the html document'

### How to scrape web links from html ###

# Import the above html document as a vector called 'filename.v'
filename.v = '~/Path/to/html/'
# Scan 'filename.v' and past all the characters to 'html.v'
html.v <- scan(filename.v, what = 'character', sep='\n', encoding = 'UTF-8')

## Go through 'html.v' and look for all instances of a string of characters with the format 'www.gutenberg.org/ebooks/' followed by any string of numbers.
# Paste all of these strings of numbers to 'm'. This gives us the individual file extensions which link to the Gutenberg texts.
m <- regexpr("www.gutenberg.org/ebooks/\\d+", html.v, perl=TRUE)

## Take all of those instances you found above, extract them from 'html.v' and paste it to 'links'. This gathers all the extensions into a single vector.
links = regmatches(html.v, m)

## Create new directory to work in
ddir = '~/Path/to/directory'
dir.create(ddir)

## Combine all of the links in 'Links' above and paste to 'url'. This is not strictly necessary but I think it makes things easier to follow
url <- c(links)
## Extract all of the numbers from 'url'. This extracts all of the file extensions from the Gutenberg urls. Again, this is not strictly necessary but I think it makes things easier to follow.
nums <- gsub(".*\\.org/ebooks/","",url)
## Re-order these numbers so they are in order rather than randomly arranged. Once more, this is just for ease.
nums <- sort(nums)

## This is a loop. This means that the program will go through all of the vector 'nums' that we created above, one after the other. Each number is pasted to to the end of the http extension.
## This web address is a mirror of Project Gutenberg, which allows us to download all of the texts without the download limit. Good news!
## This loop also contains an error function. If they script tries to download a text and it isn't there, an error is returned. This stops the programme crashing if it cannot locate a file.
for (num in nums){
  tryCatch({
    address <- paste("http://gutenberg.pglaf.org/cache/epub/", num, "/pg", num,'.txt', sep="")
    filename <- paste(num, '.txt', sep="")
    path <- paste(ddir, filename)
    download.file(address, destfile=path)
  }, error=function(e){cat("ERROR :",conditionMessage(e), "\n")})
}
## Create a list of each of these newly downloaded texts
text.word.l <- maketext(files.v,input.dir)
## Create a list of 'titles'. In this case, the titles are the numbers of the url extensions for each of the files.
texttitle.l <- gsub("\\..*","",files.v)
