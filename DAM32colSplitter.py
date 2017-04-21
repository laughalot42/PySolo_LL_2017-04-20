# wx.lib.filebrowsebutton.FileBrowseButton()

import wx
import os
import csv
import math
from wx.lib.filebrowsebutton import FileBrowseButton
#from filebrowsebutton import FileBrowseButton, DirBrowseButton
from itertools import repeat  # generate tab-delimited zeroes to fill in extra columns
import wx.lib.inspection
import wx.lib.masked as masked
import winsound

class mainPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=(600,300))

        self.parent = parent
        self.gui()

    def gui(self):

        self.inputfile = FileBrowseButton(self, id=wx.ID_ANY,
                                labelText='Input File', buttonText='Browse',
                                startDirectory='C:\Users\labadmin\Desktop\OptoGenetics\Data_Folder',
                                toolTip='Type filename or click browse to choose input file',
                                dialogTitle='Choose an input file',
                                size=(300, -1),
                                fileMask='*.*', fileMode=wx.ALL, name='input browse button')

#        self.outputPrompt = wx.StaticText(self, wx.ID_ANY, "Output File Prefix: ")
#        self.outputfile = wx.TextCtrl(self, wx.ID_ANY, name='outputprefix')

        self.datePrompt = wx.StaticText(self, wx.ID_ANY, "Start Date: ")
        self.startDate = wx.DatePickerCtrl(self, wx.ID_ANY, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)

        self.timePrompt = wx.StaticText(self, wx.ID_ANY, "Start Time: ")
        self.spinbtn = wx.SpinButton(self, wx.ID_ANY, wx.DefaultPosition, (-1, 20), wx.SP_VERTICAL)
        self.startTime = masked.TimeCtrl(self, wx.ID_ANY,
                                          name='time: \n24 hour control', fmt24hr=True,
                                          spinButton=self.spinbtn)

#        self.fpsPrompt = wx.StaticText(self, wx.ID_ANY, "Frame Rate (fps): ")
#        self.fps = wx.TextCtrl(self, wx.ID_ANY)

        self.startBtn =  wx.Button(self, wx.ID_STOP, label="Start")

        self.statusbar = wx.wx.TextCtrl(self, wx.ID_ANY, size=(1000,20), value="", style=wx.TE_READONLY)

        self.Bind(wx.EVT_BUTTON, self.onStart, self.startBtn)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
#        spacerSizer = wx.BoxSizer(wx.HORIZONTAL)
        inSizer = wx.BoxSizer(wx.HORIZONTAL)
        outSizer = wx.BoxSizer(wx.HORIZONTAL)
        dateSizer = wx.BoxSizer(wx.HORIZONTAL)
        timeSizer = wx.BoxSizer(wx.HORIZONTAL)
#        fpsSizer = wx.BoxSizer(wx.HORIZONTAL)

        inSizer.Add(self.inputfile, 1, wx.LEFT | wx.EXPAND, 10)

#        outSizer.Add(self.outputPrompt, 0, wx.LEFT, 10)
#        outSizer.Add(self.outputfile, 0, wx.LEFT, 10)

        dateSizer.Add(self.datePrompt, 0, wx.LEFT | wx.EXPAND, 10)
        dateSizer.Add(self.startDate, 0, wx.LEFT | wx.EXPAND, 10)

#        timeSizer.AddSpacer(8)
        timeSizer.Add(self.timePrompt, 0, wx.LEFT | wx.EXPAND, 10)
        timeSizer.Add(self.startTime, 0, wx.LEFT | wx.EXPAND, 7)
        timeSizer.Add(self.spinbtn, 0, wx.LEFT | wx.EXPAND, 4)
#        self.addWidgets(timeSizer, [self.timePrompt, self.startTime, self.spinbtn])
#        timeSizer.Add(self.startTime, 0, wx.LEFT, 10)

#        fpsSizer.Add(self.fpsPrompt, 0, wx.LEFT | wx.EXPAND, 10)
#        fpsSizer.Add(self.fps, 0, wx.LEFT | wx.EXPAND, 10)


        mainSizer.Add(inSizer, 0, wx.LEFT | wx.EXPAND, 10)
        mainSizer.Add(outSizer, 0, wx.LEFT | wx.EXPAND, 10)
        mainSizer.Add(dateSizer, 0, wx.LEFT | wx.EXPAND, 10)
        mainSizer.Add(timeSizer, 0, wx.LEFT | wx.EXPAND, 10)
#        mainSizer.Add(fpsSizer, 0, wx.LEFT | wx.EXPAND, 10)
        mainSizer.Add(self.startBtn, 0, wx.CENTER, 10)
        mainSizer.AddSpacer(20)
        mainSizer.Add(self.statusbar, 0, wx.CENTER | wx.EXPAND, 10)
        mainSizer.AddSpacer(20)
        self.SetSizer(mainSizer)

    """
    def addWidgets(self, mainSizer ,widgets):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        for widget in widgets:
            if isinstance(widget, wx.StaticText):
                sizer.Add(widget, 0, wx.ALL | wx.EXPAND, 2),
            else:
                sizer.Add(widget, 0, wx.ALL | wx.EXPAND, 2)
        mainSizer.Add(sizer)
    """

    def onStart(self, event):
        self.startBtn.Enable(False)
        self.colSplit32()

    def colSplit32(self):
        parts = []
        inputfile = self.inputfile.GetValue()
        self.outputprefix = os.path.split(inputfile)[1][0:-4]

        if self.outputprefix != '':
            with open(inputfile, 'rb') as f_in:
                input_tsv = csv.reader(f_in, delimiter='\t')

                self.interval = wx.TimeSpan(0,1,0)         # one minute of data per row of output

                for rowdata in input_tsv:                           # determine how many files are needed
                    rownum = int(rowdata[0])
                    if rownum == 1:
                        self.numofParts = int(math.ceil((len(rowdata)-10)/32.0))         # number of separate files needed
                        for num in range(0, self.numofParts):
                            parts.append([])                            # create a list of data for each file to be created

                        # fix the date and time
                        realdatetime = self.startDate.Value + self.startTime.GetValue(as_wxTimeSpan=True)
                        self.outputprefix = self.noOverwrite()

                    else:
                        realdatetime = realdatetime + self.interval


                    rowdata[1] = realdatetime.Format('%d %b %y')           # column 1 is the date
                    rowdata[2] = realdatetime.Format('%H:%M:%S')           # column 2 is the time

                    prefix = '\t'.join(rowdata[0:10])  # first 10 columns are part of each file


                    for batch in range(0, self.numofParts):  # add 32 columns to each part
                        startcol = 10 + batch * 32
                        endcol = startcol + 32
                        parts[batch].append(prefix + '\t' + '\t'.join(
                            rowdata[startcol: endcol]) + '\n')  # append all of the rows to list "part[batch]"

                if len(rowdata) != self.numofParts * 32 + 10:                    # need to fill empty columns with zeroes
                    morecols = (self.numofParts * 32 + 10) - input_tsv.__sizeof__()
                    for rownum in range(0, len(parts[self.numofParts - 1])):
                        parts[self.numofParts - 1][rownum] = parts[self.numofParts - 1][rownum][0:-1] + \
                                                        '\t' + '\t'.join(list(repeat('0', morecols))) + '\n'


                for batch in range(0, self.numofParts):
                    outputfile = self.outputprefix + str(batch + 1) + '.txt'  # create a filename for saving

                    f_out = open(outputfile, 'a')
                    for rownum in range(0, len(parts[batch])):
                        f_out.write(parts[batch][rownum])  # save "part" to the file in tab delimited format

            f_in.close()
            f_out.close()

            filename = os.path.split(self.outputprefix)[1]

        if filename == '':
            self.statusbar.SetValue('Cancelled.')
            self.startBtn.Enable(True)
        else:
            self.statusbar.SetValue('Done. Output file names start with:  ' + filename)
            self.startBtn.Enable(True)


    def noOverwrite(self):

        goodname = False  # avoid possibility of file overwrite
        while not goodname:
            goodname = True  # change to false if there's a problem                           
            for batch in range(0, self.numofParts):  # check for each output file                 
                outputfile = self.outputprefix + str(batch + 1) + '.txt'  # create a filename for saving
                if os.path.isfile(outputfile) and goodname == True:
                    self.statusbar.SetValue('Avoid overwrite: File -> ' + outputfile + ' <- already exists.')
                    winsound.Beep(600, 200)
                    goodname = False  # no more files will be tested and while loop continues

                    wildcard = "Monitor File Prefix (*.txt)|*.txt|" \
                               "All files (*.*)|*.*"  # adding space in here will mess it up!

                    dlg = wx.FileDialog(self.parent,
                                        message="Choose a different output prefix ...",
                                        wildcard=wildcard,
                                        style=wx.SAVE,
                                        )

                    if dlg.ShowModal() == wx.ID_OK:  # show the file browser window
                        self.outputprefix = dlg.GetPath()[0:-4]  # get the filepath & name from the save dialog, don't use extension
                    else:
                        self.outputprefix = ''
                        goodname = True                     # stop looking for an output prefix name
                        break

                    dlg.Destroy()
        return self.outputprefix

class mainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        kwds["size"] = (600,300)
        kwds["pos"] = (400,50)

        wx.Frame.__init__(self, *args, **kwds)

        myPanel = mainPanel(self)

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  Main Program

if __name__ == "__main__":
    app = wx.App()
    wx.InitAllImageHandlers()

    frame_1 = mainFrame(None, -1, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()                              # Begin user interactions.
