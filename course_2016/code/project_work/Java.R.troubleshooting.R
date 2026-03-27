#If you are working on a mac and still having trouble with your Java there are some things you are try to trouble shoot. I tried to explain this as straightforward as possible. Hope this helps you resolve any issues! Please let me know if this works or if you have questions about how I explained it.

#you can check the environment path for Java and your R libraries by entering these codes into the R console at anytime:

Sys.getenv('R_LIBS_USER')
#should read out: <home-directory>/Library/R/3.3 (your version of R)/library/
Sys.getenv("JAVA_HOME")
#should be similar to this, depending on your version of Java: Library/Java/JavaVirtualMachines/jdk1.8.0_101.jdk/Contents/Home/
Sys.getenv("LD_LIBRARY_PATH")
#should be similar this: /Library/Java/JavaVirtualMachines/jdk1.8.0_101.jdk/Contents/Home/jre/lib/server/

#If the JAVA_HOME comes back "", then you definitely need to do some of the steps below and maybe install updated Xcode and git. 
#If LD_LIBRARY_PATH returns strange symbols too, then you also need to do below steps.

#If you can install rJava then run this code and try to see what it says and if/where you have an error message:

install.packages("rJava") #if you need to install it
library(rJava)
.jinit()#if you get an error message at this point and it talks about locating Java so used "" instead, then see below for things to try.

.jcall("java/lang/System", "S", "getProperty", "java.runtime.version") #this should point to the run.time version of Java your computer points to. make sure it's at least 1.7 or 1.8 if not then, even if you can instal RWeka and other programs successfully, they probably have errors when you try to use functions from then...SO... try this below

#for issue with Java pointing to the wrong version, at .jcall():

#open a Terminal on your mac and you probably need to enter: 

cd /

#when you type into the Terminal and hit enter: 

ls

#you should be able to see 'Applications' as an option in that directory.
#If so then type: 

cd Applications

#then once you are in the Applications directory (if you are in Applicatiosn and enter ls, then you will see all of the programs on your computer with the .app extension, including an R.app). Either way, use cd and ls commands to find your location and this locations in the Terminal...then in your Terminal, type into terminal and hit enter: 

sudo R CMD javareconf

#you should see variables like JAVA_HOME scroll through and those variables below it filled out with varying paths. If this looks good then restart R, try the Sys.getenv commands to see if the path has finally updated...if so then reinstall rJava and run the rJava commans above. If good, then try installing and loading packages like RWeka and testing them out with examples from class.

#If when you enter the sudo R CMD javareconf, and you only have JAVA_HOME path filled out but no others in the output from this comman, and you also see error messages in it, then you might have a different problem then just reconfiguring your java in R. see below:

#If you had an error message with .jinit() in R, and/or in the Terminal you do not have the javareconf run correctly then try manually updating/installing onto your computer the latest version of Xcode and git. Xcode comes from apple, and the dev store (free)

#once you have updated your Xcode and git versions on your computer, then try restarting your computer and repeating steps in the Terminal again (get to Applications directory and then enterin the sudo R CMD javareconf). If this has a better result, then open R and try to check settings with the Sys.getenv functions and reinstall rJava, and then use the code up top to check the run.time Java used. Then try installing RWeka or openNLP and see if they install correctly and find examples to test RWeka

#If you have questions about these steps then please ask! I also find just trying these steps and restarting the computer and restarting R, and reinstalling packages each time, is helpful. ALSO, when doing this and installing packages, do it directly through the R console, not hte RStudio GUI easy paths. This does seem to make a difference, for some people.

#Hope you find this helpful! Good luck!


