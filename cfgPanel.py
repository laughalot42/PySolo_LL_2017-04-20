#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pvg_acquire.py
#
#       Copyright 2011 Giorgio Gilestro <giorgio@gilest.ro>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#
#

__author__ = "Giorgio Gilestro <giorgio@gilest.ro>"
__version__ = "$Revision: 1.0 $"
__date__ = "$Date: 2011/08/16 21:57:19 $"
__copyright__ = "Copyright (c) 2011 Giorgio Gilestro"
__license__ = "Python"

#       Revisions by Caitlin Laughrey and Loretta E Laughrey in 2016.

import os
import wx
import wx.grid as gridlib
import winsound
import subprocess                       # for DAMFileScan110X

import pysolovideoGlobals as gbl
import configurator as cfg
import scrollingWindow as SW
from wx.lib.newevent import NewCommandEvent
ThumbnailClickedEvt, EVT_THUMBNAIL_CLICKED = wx.lib.newevent.NewCommandEvent()

# TODO: stop acquisition button leads to never-never-land
# TODO: scrollbars disappear on return to cfg panel after resizing thumbnails
# TODO: scrollbars disappear after add monitor
# TODO: scrollbars disappear after change configuration
# TODO: scrollbars disappear after using View Monitors button
# TODO: cannot select size or fps fields after resize until going to another page and returning
# TODO: monitor numbers misplaced upon returning to cfg panel

class cfgPanel(wx.Panel):

    def __init__(self, parent, size=(800,200)):

        wx.Panel.__init__(self, parent, size=size, name='cfgPanel')
        self.parent = parent
        self.mon_ID = 0                                    # the config page has mon_ID[0]
        cfg.cfg_dict_to_nicknames()

        self.makeWidgets()                          # start, stop, and browse buttons
        self.binders()
        self.sizers()                            # Set sizers

    def makeWidgets(self):    # --------------------------------------------------------------------- create the widgets
        self.cfgBrowseWidget()                                  # browse to find another config file
        self.tableWidget()                                      # display table of config information
        self.btnsWidget()                                       # buttons
        self.videosWidget()                                     # video thumbnails for each monitor in a scrolled window
        self.settingsWidget()                                   # adjust thumbnail size and playback rate

    def cfgBrowseWidget(self):
        self.pickCFGtxt = wx.StaticText(self, wx.ID_ANY, 'Configuration File: ')
        self.pickCFGfile = wx.TextCtrl(self, wx.ID_ANY, size=(700,25), style=wx.TE_PROCESS_ENTER, name='cfgname')
        self.pickCFGfile.SetValue(self.TopLevelParent.config.filePathName)
        self.pickBrowseBtn = wx.Button(self, wx.ID_ANY, size=(130,25), label='Browse')
        self.pickBrowseBtn.Enable(True)

    def tableWidget(self):
        # --------------------------------------------------------------------------------------------- create the table
        self.colLabels = ['Monitor', 'Track type', 'Track', 'Source', 'Mask File', 'Output Prefix']

        self.cfgTable = gridlib.Grid(self)
        self.cfgTable.CreateGrid(gbl.monitors, len(self.colLabels))
        self.cfgTable.SetRowLabelSize(0)                                    # no need to show row numbers
        self.cfgTable.EnableEditing(False)                                  # user should not make changes here         TODO: allow changes from cfgTable?
        for colnum in range(0, len(self.colLabels)):
            self.cfgTable.SetColLabelValue(colnum, self.colLabels[colnum])  # apply labels to columns

        self.fillTable()                 # fill the table using config info

    def btnsWidget(self):
        # ----------------------------------------------------------------------------------------------------- buttons
        self.btnAddMonitor = wx.Button(self, wx.ID_ANY, size=(130,25), label='Add Monitor')
        self.btnAddMonitor.Enable(True)

        self.btnSaveCfg = wx.Button(self, wx.ID_ANY, size=(130,25), label='Save Configuration')
        self.btnSaveCfg.Enable(True)

        self.btnStart = wx.Button(self, wx.ID_ANY, size=(130,25), label='Start Acquisition')
        self.btnStart.Enable(True)

#        self.btnStop = wx.Button(self, wx.ID_ANY, size=(130,25), label='Stop Acquisition')
#        self.btnStop.Enable(True)

        self.btnDAMFS = wx.Button(self, wx.ID_ANY, size=(130,25), label='DAMFileScan110X')                 # start DAMFileScan110X
        self.btnDAMFS.Enable(True)

        self.btnVideos = wx.Button(self, wx.ID_ANY, size=(130,25), label='View Monitors')
        self.btnVideos.Enable(True)

#        self.btnSCAMP = wx.Button(self, wx.ID_ANY, size=(130,25), label='SCAMP')                 # start DAMFileScan110X
#        self.btnSCAMP.Enable(True)

    def videosWidget(self):
        # ----------------------------------------------------------------------------------------- scrolled thumbnails
        self.scrolledThumbs = SW.scrollingWindow(self)      # INITIAL CALL to create scrolling window with sizers to contain thumbnails

    def settingsWidget(self):
        # ------------------------------------------------------------------------------------  monitor display options
        self.thumbSizeTxt = wx.StaticText(self, wx.ID_ANY, 'Thumbnail Size:')
        self.thumbSize = wx.TextCtrl (self, wx.ID_ANY, str(gbl.thumb_size), style=wx.TE_PROCESS_ENTER)

        self.thumbFPSTxt = wx.StaticText(self, wx.ID_ANY, 'Thumbnail FPS:')
        self.thumbFPS = wx.TextCtrl (self, wx.ID_ANY, str(gbl.thumb_fps), style=wx.TE_PROCESS_ENTER)

    def binders(self):      # ---------------------------------------------------------------------------------- binders
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeCfgFile,   self.pickCFGfile)           # change configuration
        self.Bind(wx.EVT_BUTTON,        self.onBrowseCfgFile,   self.pickBrowseBtn)         # change configuration
        self.Bind(wx.EVT_BUTTON,        self.onAddMonitor,      self.btnAddMonitor)         # add monitor
        self.Bind(wx.EVT_BUTTON,        self.onStartAcquisition,self.btnStart)              # start data acquisition
#        self.Bind(wx.EVT_BUTTON,        self.onStopAcquisition, self.btnStop)               # stop data acquisition
        self.Bind(wx.EVT_BUTTON,        self.onSaveCfg,         self.btnSaveCfg)            # save configuration
        self.Bind(wx.EVT_BUTTON,        self.onDAMFileScan110X, self.btnDAMFS)              # start binning pgm
#        self.Bind(wx.EVT_BUTTON,        self.onSCAMP,           self.btnSCAMP)              # start SCAMP pgm
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeThumbFPS,  self.thumbFPS)              # update thumbnail FPS
        self.Bind(wx.EVT_TEXT_ENTER,    self.onChangeThumbSize, self.thumbSize)             # update thumbnail size
        self.Bind(wx.EVT_BUTTON,        self.onMonitorVideos,   self.btnVideos)             # switch to monitors view

    def sizers(self):  # ----------------------------------------------------------------------------------- sizers
        self.cfgPanelSizer  = wx.BoxSizer(wx.VERTICAL)          # covers whole page
        self.upperSizer     = wx.BoxSizer(wx.HORIZONTAL)        # config table, browser, and buttons
        self.pickCFGsizer   = wx.BoxSizer(wx.HORIZONTAL)        # config browser
        self.tableSizer     = wx.BoxSizer(wx.VERTICAL)          # for browse button and config table
        self.btnSizer       = wx.BoxSizer(wx.VERTICAL)          # for button controls
        self.lowerSizer     = wx.BoxSizer(wx.VERTICAL)          # scrolled windows and settings
        self.scrolledSizer  = wx.BoxSizer(wx.HORIZONTAL)        # scrolling window of thumbnails
        self.settingsSizer  = wx.BoxSizer(wx.HORIZONTAL)        # fps and size settings

    # ------------------------------------------------------------------------------------ browser control and table
        self.pickCFGsizer.Add(self.pickCFGtxt,      0, wx.ALIGN_LEFT, 2)
        self.pickCFGsizer.Add(self.pickCFGfile,     0, wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.pickCFGsizer.Add(self.pickBrowseBtn,   0, wx.ALIGN_RIGHT, 2)

        self.tableSizer.Add(self.pickCFGsizer,      0, wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.tableSizer.Add(self.cfgTable,          1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 2)

    # ------------------------------------------------------------------------------------------------------ buttons
        self.btnSizer.Add(self.btnSaveCfg,          1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnAddMonitor,       1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnStart,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
#        self.btnSizer.Add(self.btnStop,             1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnVideos,           1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.btnSizer.Add(self.btnDAMFS,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
#        self.btnSizer.Add(self.btnSCAMP,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)

    # ---------------------------------------------------------------------------------------------------- upper sizer
        self.upperSizer.AddSpacer(40)
        self.upperSizer.Add(self.tableSizer,        0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 2)
        self.upperSizer.Add(self.btnSizer,          0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_TOP, 2)

    # ---------------------------------------------------------------------------------------- scrolling window sizer
        self.scrolledSizer.Add(self.scrolledThumbs,    1, wx.ALL | wx.ALIGN_CENTER, 2)

    # ---------------------------------------------------------------------------------------------- settings sizer
        self.settingsSizer.Add(self.thumbSizeTxt,       0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.Add(self.thumbSize,          0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.AddSpacer(5)
        self.settingsSizer.Add(self.thumbFPSTxt,        0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.Add(self.thumbFPS,           0, wx.ALL | wx.EXPAND, 2)
        self.settingsSizer.AddSpacer(5)

    # ----------------------------------------------------------------------------------------------------- lower sizer
        self.lowerSizer.Add(self.scrolledSizer,    1, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.lowerSizer.AddSpacer(50)

        self.lowerSizer.Add(self.settingsSizer,     0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 2)

    # --------------------------------------------------------------------------------------------- main panel sizer
        self.cfgPanelSizer.Add(self.upperSizer,        1, wx.ALL | wx.EXPAND | wx.ALIGN_TOP | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.cfgPanelSizer.Add(self.lowerSizer,        1, wx.ALL | wx.EXPAND | wx.ALIGN_BOTTOM | wx.ALIGN_CENTER_HORIZONTAL, 2)

        self.SetSizer(self.cfgPanelSizer)
        self.Layout()

    def onAddMonitor(self, event):      # ---------------------------------------------------------------    Add monitor
        """
        adds a monitor to the list 

        more than 9 monitors creates issues due to differences between alphabetical and numerical sorting.
            Avoiding problems by not allowing more than 9 monitors.
        """
        cfg.cfg_nicknames_to_dicts()            # -------------------------------------------- save current cfg settings

        if gbl.monitors >= 9:                               # no more than 9 monitors allowed
            self.TopLevelParent.SetStatusText('Too many monitors.  Cannot add another.')
            winsound.Beep(600, 200)
            return False

        # -------------------------------------------------------------------- put new monitor settings in gbl nicknames
        gbl.cfg_dict.append({})                          # add a dictionary to the cfg_dict list
        cfg.cfg_dict_to_nicknames()

        gbl.monitors += 1                                # increase the number of monitors
        gbl.mon_ID = gbl.monitors                        # update the current mon_ID
        gbl.mon_name = 'Monitor%d' % gbl.mon_ID          # update the monitor name

#        if gbl.source_type == 0:                         # create new webcam name if this is a webcam
#            gbl.webcams_inuse.append(gbl.mon_name)       # only one webcam is supported, but multiple monitors can use it
#            gbl.webcams += 1
#            gbl.source = 'Webcam%d' % gbl.webcams
#            gbl.source = 'Webcam1'                      # only one webcam is supported, but multiple monitors can use it

        cfg.cfg_nicknames_to_dicts()    # ---------------------------------- save new configuration settings to cfg_dict
        cfg.mon_nicknames_to_dicts(gbl.mon_ID)  # ----------------------------------------- apply new monitor settings to cfg_dict

        # --------------------------------------------------------------------------------- add monitor page to notebook
        self.parent.addMonitorPage()

        gbl.mon_ID = gbl.cfg_dict[0]['monitors']
        cfg.mon_dict_to_nicknames()
        self.Parent.notebookPages[0].fillTable()                 # update the configuration table
        self.scrolledThumbs.refreshThumbGrid()                   # create the thumbnail window

#        self.SetSizerAndFit(self.cfgPanelSizer)
#        self.Layout()

        gbl.mon_ID = 0

    def onSaveCfg(self, event):
        cfg.cfg_nicknames_to_dicts()        #  save any new settings to dictionary
        if gbl.mon_ID != 0:
            cfg.mon_nicknames_to_dicts(gbl.mon_ID)

        r = self.TopLevelParent.config.cfgSaveAs(self)
        if r:                                                                                                   #       TODO: progress indicator of some sort?
            self.TopLevelParent.SetStatusText('Configuration saved.')
            winsound.Beep(600,200)
        else:
            self.TopLevelParent.SetStatusText('Configuration not saved.')
            winsound.Beep(600,200)

    def fillTable(self):      # --------------------------------------- use cfg dictionary to fill in table
        currentrows = self.cfgTable.GetNumberRows()                 # clear the grid & resize to fit new configuration
        self.cfgTable.AppendRows(gbl.monitors, updateLabels=False)                  # add new rows to end
        self.cfgTable.DeleteRows(0, currentrows, updateLabels=False)                  # deletes old rows from beginning

        oldMonID = gbl.mon_ID
        for gbl.mon_ID in range(1, gbl.monitors +1):
            #        columns are: 'Monitor', 'Track type', 'Track', 'Source', 'Mask', 'Output'
            #       row numbers are 0-indexed
            cfg.mon_dict_to_nicknames()                     # get this monitor's settings

            # ----------------------------------------------------------------- table uses 0-indexing in following steps
            self.cfgTable.SetCellValue(gbl.mon_ID -1,       0, gbl.mon_name)
            self.cfgTable.SetCellAlignment(gbl.mon_ID -1,   0,  wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

            if gbl.track_type == 0: track_typeTxt = 'Distance'                                              # track type
            elif gbl.track_type == 1: track_typeTxt = 'Virtual BM'
            elif gbl.track_type == 2: track_typeTxt = 'Position'
            else:
                print('track_type is out of range')
                track_typeTxt = 'None'
            self.cfgTable.SetCellValue(gbl.mon_ID -1,       1, track_typeTxt)
            self.cfgTable.SetCellAlignment(gbl.mon_ID -1,   1, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

            self.cfgTable.SetCellValue(gbl.mon_ID -1,       2, str(gbl.track))                                  # track
            self.cfgTable.SetCellAlignment(gbl.mon_ID -1,   2, wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)

            if gbl.source is not None:
                self.cfgTable.SetCellValue(gbl.mon_ID -1,       3, gbl.source)                                  # source
            else:
                self.cfgTable.SetCellValue(gbl.mon_ID -1,       3, 'None Selected')


            if gbl.mask_file is not None:
                self.cfgTable.SetCellValue(gbl.mon_ID -1,    4, os.path.split(gbl.mask_file)[1])          # mask_file
            else:
                self.cfgTable.SetCellValue(gbl.mon_ID - 1,   4, 'None Selected')

            if gbl.data_folder is not None:
                outfile = os.path.join(gbl.data_folder, gbl.mon_name)                                   # output file name
                self.cfgTable.SetCellValue(gbl.mon_ID - 1, 5, outfile)
            else:
                self.cfgTable.SetCellValue(gbl.mon_ID - 1,   4, 'None Selected')


        gbl.mon_ID = oldMonID
        if gbl.mon_ID != 0:
            cfg.mon_dict_to_nicknames()
        self.cfgTable.AutoSize()                    # cell size based on contents
        self.Layout()

    def onChangeThumbFPS(self, event):
        input = gbl.correctType(self.thumbFPS.GetValue(), 'thumb_fps')
        if not (type(input) == int or type(input) == float):
            input = gbl.thumb_fps                         # don't change the value if input wasn't a number
            self.thumbSize.SetValue(input)

        gbl.cfg_dict[self.mon_ID]['thumb_fps'] = gbl.thumb_fps = input
        cfg.cfg_nicknames_to_dicts()
        self.scrolledThumbs.refreshThumbGrid()              # refresh thumbnails
        self.thumbSize.SetFocus()

    def onChangeThumbSize(self, event):
        input = gbl.correctType(self.thumbSize.GetValue(), 'thumb_size')
        if type(input) != tuple:
            input = gbl.preview_size
            self.thumbSize.SetValue(input)

        gbl.cfg_dict[self.mon_ID]['thumb_size'] = gbl.thumb_size = input           # update self & cfg_dict
        cfg.cfg_nicknames_to_dicts()
        try:
            self.scrolledThumbs.thumbPanels[1].monitorPanel
            self.scrolledThumbs.refreshThumbGrid()              # refresh thumbnails
        except:
            self.scrolledThumbs.thumbPanels[1].trackedMonitor
            self.scrolledThumbs[0].refreshConsoleGrid()              # refresh consoles

        self.thumbFPS.SetFocus()

    def onBrowseCfgFile(self, event):
        cfg.cfg_nicknames_to_dicts()

        answer = self.TopLevelParent.config.wantToSave()        # save this config before loading new one?
        if answer == wx.ID_YES:
            self.TopLevelParent.config.cfgSaveAs(self)                  # yes -> save cfg file
        elif answer == wx.ID_CANCEL:
            return                                                  # cancel -> don't save & don't change cfg
        else:
            pass                                                    # no -> don't save, load new cfg

        # ----------------------------------------------------------------------------- select a different config file
        wildcard = "PySolo Video config file (*.cfg)|*.cfg|" \
                   "All files (*.*)|*.*"  # adding space in here will mess it up!

        dlg = wx.FileDialog(self,
                            message = "Select Configuration File ...",
                            defaultDir = gbl.cfg_path,
                            wildcard = wildcard,
                            style = (wx.FD_OPEN)
                            )

        # load new configuration file
        if dlg.ShowModal() == wx.ID_OK:  # show the file browser window
            self.filePathName = dlg.GetPath()  # get the path from the save dialog
        else:
            winsound.Beep(600,200)
            gbl.statbar.SetStatusText('Config file selection failed in cfgPanel.')
            return

        self.changeConfig()

    def onChangeCfgFile(self, event):       # ---------------------------------------  new config file selected by text
        cfg.cfg_nicknames_to_dicts()

        answer = self.TopLevelParent.config.wantToSave()            # ask about saving configuration
        if answer == wx.ID_YES:
            self.TopLevelParent.config.cfgSaveAs(self)                  # do save
        elif answer == wx.ID_CANCEL:
            return                                                      # cancel changing cfg file
        else:
            pass                                                        # proceed without saving

        self.filePathName = self.TopLevelParent.config.cfgGetFilePathName(self, possiblePathName=self.pickCFGfile.GetValue())   # make sure file exists

        self.changeConfig()

    def changeConfig(self):
        gbl.cfg_dict = [gbl.cfg_dict[0], gbl.cfg_dict[1]]       # remove all but monitors 1 from dictionary

        self.GrandParent.config.loadConfigFile(self.filePathName)
        gbl.mon_ID = 1
        cfg.cfg_dict_to_nicknames()
        cfg.mon_dict_to_nicknames()

        self.fillTable()                                        # put new configuration into the table
#        self.scrolledThumbs.refreshThumbGrid()                  # create the thumbnail window
        self.parent.repaginate()                                # add monitor pages to notebook & end on config page
        self.pickCFGfile.SetValue(self.filePathName)

    def onStartAcquisition(self, event=None):
        """
        replace scrolled thumbnails with progress windows
        start tracking
        """
        gbl.statbar.SetStatusText('Tracking %d Monitors' % gbl.monitors)
        self.acquiring = True
        self.scrolledThumbs.refreshConsoleGrid()          # replace thumbnails with progress consoles and start tracking

    """
    def onStopAcquisition(self, event=None):
        gbl.statbar.SetStatusText('Stopped tracking.')
        winsound.Beep(600,200)
        self.acquiring = False
        for gbl.mon_ID in range(1, gbl.monitors+1):
            self.scrolledThumbs.thumbPanels[gbl.mon_ID].trackedMonitor.keepPlaying = False
            gbl.threadsStarted = gbl.threadsStart -1
    """

    def onMonitorVideos(self, event):
        self.Parent.notebookPages[0].scrolledThumbs.refreshThumbGrid()      # recreate scrolling window with sizers to contain thumbnails

    def onDAMFileScan110X(self, event):

        cmd = os.path.join(os.getcwd(), 'DAMFileScan110X', 'DAMFileScan110.exe')
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        process.wait()

    """
    def onSCAMP(self, event):
    """

# ------------------------------------------------------------------------------------------ Stand alone test code
#  insert other classes above and call them in mainFrame
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, None, id=wx.ID_ANY, size=(1000,200))

        config = cfg.Configuration(self, gbl.cfg_path)
        frame_acq = cfgPanel(self)  # Create the main window.
        app.SetTopWindow(frame_acq)

        print('done.')


if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#

