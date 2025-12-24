#pragma rtGlobals=1		// Use modern global access method.

//Color tuner 
//Author: Keisuke Fukutani (2019)
//Modification: Ryotaro Nakazawa (2025)


Menu "VisARPES"
	"ColorTuner (RN)/2",  DuplicateCheckCTKF()	
End

Function DuplicateCheckCTKF()	
	//If the color tuner panel is already present (Panelname=ColorTunerKF), then do not create a new one, but just bring it to the front and set the active graph to the topmost graph
	if(FindListItem("ColorTunerKF", winlist("*",";", "WIN:64")) > -1) 
		
		//Print "Color Tuner is already present"
		Execute "FocusOnTopGraph1()"
		DoWindow/F 'ColorTunerKF'
		
	else //Color tuner is not present. Make the new one
		Execute "ColorChange()"
	Endif
End




//Create the color tuner panel/////////////////////////////////
Function ColorChange() : Panel
	
	//Define the variables to be used
	Variable/D/G UpperV 
	Variable/D/G LowerV
	String/G Colorname
	Variable/G ReverseColoring
	String/G ActiveGraph
	String/G ActiveWave
	Variable/D/G ActiveWaveMax
	Variable/D/G ActiveWaveMin
	Variable/D/G step
	
	//Identify the topmost graph and its 1st wave and store their names in ActiveGraph and ActiveWave, respectively
	String/G ActiveGraph = WinName(0,1)                
	String/G ActiveWave = ImageNameList("",";")    //Active wave is now the set of strings made of all the images in the topmost graph, separated by semicolon ;
	Variable p1p= StrSearch(Activewave,";",0)   //Store in p1p  the location of first semicolon ; 
	ActiveWave = ActiveWave[0,p1p-1]               //Store in activewave the string made from 0th character to p1p-1 th character. This effectively gets rid of the semicolon in the activewave string
	
	
	Execute "ExractColorInfo()"
	
	
	
	//Build the color tuner panel
	PauseUpdate; Silent 1		// building window...	
	NewPanel /N=ColorTunerKF   /W=(700,71,1011,200)  /K=1  as "Color Tuner (RN)"	//Note the flag /K=1 (no dialog when killing)
	DoUpdate/E=1 /W='Color tuner'
	ModifyPanel cbRGB=(65535,65535,65535)
	SetDrawLayer UserBack
	SetDrawEnv fillfgc= (56576,56576,56576)
	DrawRect 115,449,141,485
	SetDrawEnv xcoord= rel,ycoord= abs,linethick= 0,linefgc= (65280,0,0)
	DrawRect 0,242,1,327
	DrawText 2, 67 , "0%"
	DrawText 93, 67, "50%"
	DrawText 168, 67, "100%"
	TitleBox title0 variable=ActiveGraph, pos={9,3}
	
	
	
	
	//Create the controllers
	PopupMenu popup0, value="*COLORTABLEPOP*", proc = ChangeColorStyle,  mode = Whichlistitem(ColorName, ctablist())+1,  pos={0,100}
	SetVariable setvar0 title="Max.",size={80,20}, pos={200, 26},variable=UpperV, value=UpperV, proc = ChangeUpperV, live=1
	SetVariable setvar1 title="Min.",size={80,50}, pos={200, 70}, Variable=LowerV, value=LowerV, proc = ChangeLowerV, live=1
	Slider slider0 vert=0,side=1, variable=UpperV, proc=ChangeUpper, limits={ActiveWaveMin,ActiveWaveMax, step}, size={190,45}, pos={2,26}, tkLblRot=180, ticks=-10, value=UpperV, live=1
	Slider slider1 vert=0,side=2, variable=LowerV, proc=ChangeLower, limits={ActiveWaveMin,ActiveWaveMax, step}, size={190,45}, pos={2,70}, ticks=-10, value=LowerV, live=1
	PopupMenu popup1 value=ImageNameList("",";"), title="", popvalue = activewave, proc=ActiveWaveChange, pos = {75,3}   //Wave selection
	CheckBox check0 title="Reverse", pos={209, 103},variable=reversecoloring, proc=reversing
	Button button1 title="Auto",size={40,20}, pos={227,44}, proc=AutoScaleGraph, help={"this is help"}
		
	ControlUpdate/A
End
	
	







/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////





///////////////////////////////////////////////////////////////////////////////////////////////
Function FocusOnTopGraph1() 
	Variable/G UpperV 
	Variable/G LowerV
	String/G Colorname
	Variable/G LogScale
	String/G ActiveGraph
	String/G ActiveWave
	Variable/G ActiveWaveMax
	Variable/G ActiveWaveMin
	
	//Identify the topmost graph and its 1st wave and store their names in ActiveGraph and ActiveWave, respectively
	String/G ActiveGraph = WinName(0,1)                
	String/G ActiveWave = ImageNameList("",";")    //Active wave is now the set of strings made of all the images in the topmost graph, separated by semicolon ;
	Variable p1p= StrSearch(Activewave,";",0)   //Store in p1p  the location of first semicolon ; 
	ActiveWave = ActiveWave[0,p1p-1]               //Store in activewave the string made from 0th character to p1p-1 th character. This effectively gets rid of the semicolon in the activewave string
	
	
	Execute "ExractColorInfo()"
	
	
	PopupMenu popup1 value=ImageNameList("",";"), popvalue = activewave, win='ColorTunerKF'
	PopupMenu popup0,  mode = Whichlistitem(ColorName, ctablist())+1, win='ColorTunerKF'

	Variable step = (ActiveWaveMax - ActiveWaveMin)/200
	Slider slider0 limits={ActiveWaveMin, ActiveWaveMax, step}, win='ColorTunerKF'
	Slider slider1 limits={ActiveWaveMin, ActiveWaveMax, step}, win='ColorTunerKF'


End


//////////////////////////////////////////
//For the current ActiveWave, this function identifies its values of UpperV, LowerV, ColorName, LogScale, ActiveGraph, and ActiveWave and stores into each variable/string. ////
//////////////////////////////////////////

Function ExractColorInfo()

	Variable/G UpperV 
	Variable/G LowerV
	String/G Colorname
	Variable/G LogScale
	String/G ActiveGraph
	String/G ActiveWave
	Variable/G ActiveWaveMax
	Variable/G ActiveWaveMin
	wave w = ImageNameToWaveRef(Activegraph, activewave)
	
	
	ActiveWaveMax = wavemax(w)
	ActiveWaveMin = WaveMin(w)
	

	
	
	String ImageSettings = StringByKey("RECREATION:ctab",imageinfo(ActiveGraph,ActiveWave,0),"=", ";")
	Variable BracketOpen = StrSearch(Imagesettings,"{",0)
	Variable BracketClose = StrSearch(Imagesettings,"}",0)
	Variable FirstComma = StrSearch(Imagesettings,",",0)
	Variable SecondComma = StrSearch(Imagesettings,",",FirstComma+1)
	Variable ThirdComma = StrSearch(Imagesettings,",",SecondComma+1)
	
	String InitialLowerV =  ImageSettings[BracketOpen+1,FirstComma-1]
	//print "InitialLowerV = " + InitialLowerV
	String/G InitialUpperV =  ImageSettings[FirstComma+1,SecondComma-1]
	//print InitialUpperV
	
	String/G Colorname =  ImageSettings[SecondComma+1,ThirdComma-1]
	//print ColorName
	
	String/G ColorFlip = ImageSettings[ThirdComma+1, BracketClose-1]
	

	
	Variable/G ReverseColoring = Str2num(colorFlip)
	
		
	if(NumType(Str2num(InitialUpperV))==2)
		
		UpperV = ActiveWaveMax					// execute if condition is TRUE
		//print "ui"
	else
		UpperV = Str2num(InitialUpperV)	
		//Print "good"				// execute if condition is FALSE
	endif
	
	if(NumType(Str2num(InitialLowerV))==2)
		LowerV = ActiveWaveMin					// execute if condition is TRUE
	else
		LowerV = Str2num(InitialLowerV)	
		//Print "Great"				// execute if condition is FALSE
	endif


End

/////////////////////////////////////////////
///////////////////////////////////////////
////////////////////////////////////////







///Auto scale button//////////////////////////////
Function AutoScaleGraph(ctrlname) : ButtonControl
String ctrlName
String/G ColorName
String/G ActiveWave
String/G ActiveGraph
Variable/G ActiveWaveMax
Variable/G ActiveWaveMin
Variable/G UpperV
Variable/G LowerV
variable/G reversecoloring

ModifyImage/W=$activeGraph $ActiveWave ctab= {*,*,$colorname,reversecoloring}
UpperV = ActiveWaveMax
LowerV = ActiveWaveMin
Slider slider0 value=UpperV, win='ColorTunerKF'
Slider slider1 value=LowerV, win='ColorTunerKF'

ControlUpdate /A

End

/////////////////////////////////////////////





 Function  ActiveWaveChange(ctrlName,popNum,popStr) : PopupMenuControl
   String ctrlName
   Variable popNum
   String popStr
   String/G ActiveGraph
   String/G ActiveWave
   String/G ColorName
   variable/G reversecoloring

activewave = popstr

Execute "ExractColorInfo()"

	PopupMenu popup0,  mode = Whichlistitem(ColorName, ctablist())+1, win='ColorTunerKF'

	Variable minVal = wavemin($activewave)
	Variable maxVal = wavemax($activewave)
	Variable step = (maxVal - minVal)/400

	Slider slider0 limits={minVal, maxVal, step}, win='ColorTunerKF'
	Slider slider1 limits={minVal, maxVal, step}, win='ColorTunerKF'


End





 Function  ChangeColorStyle(ctrlName,popNum,popStr) : PopupMenuControl
 	String ctrlName
 	Variable popNum
 	String popStr
 	String/G colorname
 	String/G Activegraph
 	String/G ActiveWave
 	Variable/G UpperV
 	Variable/G LowerV
 	variable/G reversecoloring
  
  	ColorName = popstr

	//print colorname
	ModifyImage/W=$activeGraph $ActiveWave ctab= {LowerV,UpperV,$colorname,reversecoloring}


end





///////////////////////////////////////////////////
///////////////////////////////////////////



Function Changeupper(ctrlName,sliderValue,event) : SliderControl
	String ctrlName
	Variable sliderValue
	Variable event	// bit field: bit 0: value set, 1: mouse down, 2: mouse up, 3: mouse moved
	String/G Colorname
	Variable/G UpperV
	Variable/G LowerV
	String/G Activegraph
	String/G ActiveWave
	variable/G reversecoloring

	//DoWindow/F $Activegraph
	//print Activegraph
	ModifyImage/W=$activegraph $activewave ctab={LowerV,sliderValue,$colorname,reversecoloring}
	
	UpperV = SliderValue
	
	
End

	
Function ChangeLower(ctrlName,sliderValue,event) : SliderControl
	String ctrlName
	Variable sliderValue
	Variable event	// bit field: bit 0: value set, 1: mouse down, 2: mouse up, 3: mouse moved
	String/G Colorname
	Variable/G UpperV
	Variable/G LowerV
	String/G Activegraph
	String/G ActiveWave
	variable/G reversecoloring
	
	ModifyImage/W=$activegraph $activewave ctab= {sliderValue,UpperV,$colorname,reversecoloring}
	
	LowerV = Slidervalue
	
	
End


Function ChangeUpperV(ctrlName,varNum,varStr,varName) : SetVariableControl
	String ctrlName
	Variable varNum
	String varStr
	String varName
	String/G Colorname
	Variable/G UpperV
	Variable/G LowerV
	String/G Activegraph
	String/G ActiveWave
	variable/G reversecoloring

UpperV = varNum

ModifyImage/W=$activegraph $activewave ctab= {LowerV,UpperV,$colorname,reversecoloring}
	
	

End


Function ChangeLowerV(ctrlName,varNum,varStr,varName) : SetVariableControl
	String ctrlName
	Variable varNum
	String varStr
	String varName
	String/G Colorname
	Variable/G UpperV
	Variable/G LowerV
	String/G Activegraph
	String/G ActiveWave
	variable/G reversecoloring

LowerV = varNum

ModifyImage/W=$activegraph $activewave ctab= {LowerV,UpperV,$colorname,reversecoloring}
	
	

End



Function Reversing(ctrlName,checked) : CheckBoxControl
	String ctrlName
	Variable checked
	Variable reversecoloring
	String/G Activegraph
	String/G ActiveWave
	String/G Colorname
	Variable/G UpperV
	Variable/G LowerV

reverseColoring = checked

ModifyImage/W=$activeGraph $ActiveWave ctab= {LowerV,UpperV,$colorname,reversecoloring}


End