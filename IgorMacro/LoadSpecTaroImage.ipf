#pragma TextEncoding = "UTF-8"
#pragma rtGlobals=3		// Use modern global access method and strict wave access.

//Author: Keisuke Fukutani (2021)
//Modification: Ryotaro Nakazawa (2025)
//This macro can be used to load multiple 2D data in .txt format created by A1 (MBS) software into Igor at once.
//Compile and execute "Load A1 data" under VisARPES menu and select one or more A1 text files to load them all.
//It is highly recommended, although not required, that the files names do not start with a number or special character to avoid malfunctions 
//IMPORTANT: This macro assumes that the files starts with all the metadata 


//Create the Load A1 data menu in VisARPES 
Menu "VisARPES"
"Load SpecTaro Image/1", Load_SpectrumAnalyzerData()
End

//Function starts

Function/S Load_SpectrumAnalyzerData()

//Define the variables
    Variable refNum
    String message = "Select one or more 'Spectrum Analyzer image files' of to be loaded"
    String outputPaths
    String fileFilters = "Data Files (*.txt,*.dat,*.csv):.txt,.dat,.csv;"
    fileFilters += "All Files:.*;"
	


    Open /D /R /MULT=1 /F=fileFilters /M=message refNum  //Open the dialog which prompts user to select one or more files
    outputPaths = S_fileName  //Store in the OutputPaths the names of all the selected files in the format of "FolderPath:File1 \r File2 \r File3 \r ..." which was created in S-FileName by Open command.
 
    if (strlen(outputPaths) == 0) //Check if any file was selected. If not, print cancelled.
        Print "Cancelled"
    else
        
    	Variable numFilesSelected = ItemsInList(outputPaths, "\r") //Store the number of files selected by the user 
        
        
        
   	  Variable i  //Running index for each file
        
    	 for(i=0; i<numFilesSelected; i+=1) //Start the loading process for each file to be loaded
            
            String columnInfo
            String path = StringFromList(i, outputPaths, "\r")      //Get the full path to the filename including extension
            String FolderPath = ParseFilePath(1, path, ":", 1, 0)   //Get the path to the folder where the file is located (no file name)
            Newpath/O pathx, FolderPath                             //Make the folder path into path variable
            String Fname = ParseFilePath(0, path, ":", 1, 0)        //Get the filename in the folder (no folder path)
            String wName = ParseFilePath(3, path, ":", 0, 0)        //Get just the filename with extention removed
            //wName = CleanupName(wName, 0)                         //Uncomment this feature if the liberal name (e.g. filename starting with number or special character) to be cleaned up
            
            
    
           
            //===　For the i-th file, start reading the texts in the file line by line and store all of them in "NoteInfo"=========================
            String filename = FName
            
            
          Open/R/P=pathx refnum as filename 
          Variable lineNumber, len
        	 String noteinfo = ""
          String buffer
          Variable angleInc
          Variable angleMin
          Variable angleMax
          lineNumber = 0
          
          
          do
             FReadLine refnum, buffer
             len = strlen(buffer)
             if (len == 0)
             	break
             endif
             //Printf "Line number %d: %s", lineNumber, buffer
             
             noteinfo += buffer
             
             
             if(stringmatch(buffer, "*Y Step*")) //Extract Angle increment
             
             	angleInc = str2num(stringFromList(1, buffer, "\t"))
             
             endif
             
             if(stringmatch(buffer, "*Y Min*")) //Extract Angle minimum
             
             	angleMin = str2num(stringFromList(1, buffer, "\t"))
             
             endif
             
             if(stringmatch(buffer, "*Y Max*")) //Extract Angle maximum
             
             	angleMax = str2num(stringFromList(1, buffer, "\t"))
             
             endif






             if(grepstring(buffer, "DATA:")) //Find which linenumber in the text file the word "DATA:" appears
          
             	//print "The data is located at: ", linenumber
             	break   // Here we find the line number in the txt file where the word "DATA:" appears. A1 txt file contains all the numerical data after "DATA:"
             endif
             
             
             
             if (CmpStr(buffer[len-1],"\r") != 0) 
					Printf "\r"
             endif
          	
             lineNumber += 1
          while(1)
             
            Close refNum
            //================================
            

            sprintf columnInfo, "N='%s';", wName
        
           

           
           //Now load the file into igor by telling it the actual numerical data are listed from the linenumber+1 by tab as delimiters 
            LoadWave/D/J/M/K=0/V={"\t","$",0,0}/L={0,linenumber+1,0,0,0} /U={0,1,0,0} /B=columnInfo path
            
            //Append to the loaded wave the note information from the A1 text files (every text that precedes the numerical data)
            Note $wname, noteinfo
  
            
           setscale/P y, AngleMin, AngleInc, $wname
           
    
            
            
            // Add commands here to load the actual waves.  An example command
            // is included below but you will need to modify it depending on how
            // the data you are loading is organized.
            //LoadWave/A/D/J/W/K=0/V={" "," $",0,0}/L={0,2,0,0,0} path
            
				// Image表示            
            	Display;DelayUpdate
				AppendImage $wname
				
				// 軸の向き		
				ModifyGraph swapXY=1
				SetAxis/A/R right
				SetAxis/A/R left
				// そのた軸設定
				ModifyGraph gfSize=18
				ModifyGraph mirror=2
				ModifyGraph standoff(bottom)=0
				ModifyGraph standoff(left)=0
				// label name
				Label bottom "\\f02k\\f00\\B∥\\M (Å\\S-1\\M)"
				Label left "Binding Energy (eV)"
				// intensity color
				ModifyImage $wname ctab= {*,*,YellowHot,0}
				
				//ColorTnner表示。
				DuplicateCheckCTKF()	
            
            
        endfor
    endif
       

   return outputPaths      // Will be empty if user canceled


End
