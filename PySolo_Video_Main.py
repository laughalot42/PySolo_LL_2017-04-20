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

import wx
from win32api import GetSystemMetrics
import wx.lib.inspection

import pysolovideoGlobals as gbl
import configurator as cfg
import cfgPanel
import maskPanel

# ------------------------------------------------------------------------------------------------------  Main Notebook
class mainNotebook(wx.Notebook):
    """
    The main notebook containing all the panels for data displaying and analysis
    """

    def __init__(self, parent):

        wx.Notebook.__init__(self, parent, id=wx.ID_ANY, style=wx.NB_LEFT, name='NotebookNameStr') # initialize notebook

        self.notebookPages = []

        self.notebookPages.append(cfgPanel.cfgPanel(self))          # -----configuration page is element 0
        cfg.cfg_dict_to_nicknames()                                     # load configuration parameters into globals
        self.AddPage(self.notebookPages[0], 'Configuration')

        for gbl.mon_ID in range(1, gbl.monitors+1):                       # monitor pages are numbered by monitor number
            cfg.mon_dict_to_nicknames()                                   # load monitor configuration into globals
            self.addMonitorPage()                                         # add monitor page to notebook

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)
        self.Layout()

        gbl.mon_ID = 0             # set mon_ID to zero which is configuration page

    def addMonitorPage(self):
        self.notebookPages.append(maskPanel.maskMakerPanel(self))       # make the monitor page
        self.AddPage(self.notebookPages[gbl.mon_ID], gbl.mon_name)      # add to notebook

    def onPageChanged(self, event):                             # ----- directs event related page changes to onGoToPage
        page_num = event.GetSelection()
        self.onGoToPage(page_num)

    def onGoToPage(self, page_num):  # --------------------------------------------- for changing pages without an event
        gbl.statbar.SetStatusText(' ')
        old_ID = gbl.mon_ID

        if old_ID != 0:     # ------------------------------------------------------------------ leaving a monitor page
            cfg.mon_nicknames_to_dicts(old_ID)                  # save any changes made to the monitor
            self.notebookPages[old_ID].clearVideo()             # remove video and timer

        if old_ID == 0:  # ---------------------------------------------------------- leaving the configuration page
            cfg.cfg_nicknames_to_dicts()  # save any new changes to config parameters

            try:   # ------ don't know if thumbnails or console are showing
                self.notebookPages[0].scrolledThumbs.clearThumbGrid()       # remove all thumbnails, timers, and threads
            except: pass
            try:   # ------ don't know if thumbnails or console are showing
                self.notebookPages[0].scrolledThumbs.clearConsoleGrid()       # remove all thumbnails, timers, and threads
            except: pass

        # -------------------------------------------------------------------------------- update to the new page number
        gbl.mon_ID = page_num

        if page_num == 0:         # -------------------------------------------------------- going to configuration page
            cfg.cfg_dict_to_nicknames()                         # load configuration page parameters
            self.notebookPages[0].fillTable()                   # update the configuration table
            self.notebookPages[0].scrolledThumbs.refreshThumbGrid()    # update and start the thumbnails window
#            self.notebookPages[0].scrolledThumbs.SetScrollbars(1,1,1,1)                                                # does not restore scrollbars
#            self.Layout()

        else:          # ---------------------------------------------------------------------- going to a monitor page
            if gbl.mon_ID != 0:
                cfg.mon_dict_to_nicknames()                 # update nicknames to values for the selected monitor

            self.notebookPages[gbl.mon_ID].previewPanel.parent.refreshVideo()                              # start video

        self.notebookPages[0].scrolledThumbs.EnableScrolling(1, 1)
        self.notebookPages[0].Layout()

        print('check')

    def repaginate(self):     # -------------------------------------- update notebook after number of pages has changed
        # page 0 (config page) will not be affected except for thumbnails               # then go to configuration page

        # -------------------------------------------------------------------- delete each page from notebook (except 0)
        self.Unbind(wx.EVT_NOTEBOOK_PAGE_CHANGED)                   # prevent page changing while deleting pages
        for gbl.mon_ID in range(len(self.notebookPages)-1, 0, -1):
            self.notebookPages[gbl.mon_ID].clearVideo()      # stop & remove video, timer, and thread for monitor pages
#            self.notebookPages.pop(gbl.mon_ID)               # remove page from list of pages
            del self.notebookPages[gbl.mon_ID]               # remove page from list of pages
            self.DeletePage(gbl.mon_ID)                      # remove page from notebook object

        # ---------------------------------------------------- stop configuration page thumbnail and console timers
        try:    # ------ don't know if thumbnails or console are showing
            self.notebookPages[0].scrolledThumbs.clearThumbGrid()
        except: pass
        try:    # ------ don't know if thumbnails or console are showing
            self.notebookPages[0].scrolledThumbs.clearConsoleGrid()
        except: pass

        # ------------------------------------------------------------------------------------- recreate notebook pages
        cfg.cfg_dict_to_nicknames()                  # load configuration parameters into globals
        self.notebookPages[0].scrolledThumbs.thumbPanels = ['videoMonitors']  # initiate a new thumbnail list; element 0 identifies type of list

        # ----------------------------------------------------------------------------------- add back each monitor page
        for gbl.mon_ID in range(1, gbl.monitors+1):                 # monitor pages are numbered by monitor number
            cfg.mon_dict_to_nicknames()                                   # load monitor configuration into globals
            self.addMonitorPage()                                         # add monitor page to notebook

        self.notebookPages[0].fillTable()                                # update the configuration table
        self.notebookPages[0].scrolledThumbs.refreshThumbGrid()               # update the scrolled thumbs window

        gbl.mon_ID = 0          # ------------------------------------------------------------ go to configuration page
        cfg.cfg_dict_to_nicknames()
        self.SetSelection(gbl.mon_ID)
        self.Layout()

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onPageChanged)     # restore binding

class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.config = cfg.Configuration(self)                   # let user select a configuration to load before starting

        gbl.statbar = wx.StatusBar(self, wx.ID_ANY)  # status bar
        self.SetStatusBar(gbl.statbar)
        gbl.statbar.SetStatusText('Status Bar')

        self.theNotebook = mainNotebook(self)

        self.__set_properties("pySolo Video", 0.95)  # set title and frame/screen ratio
        self.__do_layout()

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.theNotebook, 1, wx.EXPAND, 0)
        self.SetSizer(mainSizer)
        self.Layout()


        print('done.')

    # -------------------------------------------------------------------------------------- Set window properties
    def __set_properties(self, window_title, size_ratio):
        """
        Set the title of the main window.
        Set the size of the main window relative to the size of the user's display.
        Center the window on the screen.


        Get screen_width & screen_height:   Screen resolution information
              Allows all object sizes to be sized relative to the display.
        """
        screen_width = GetSystemMetrics(0)  # get the screen resolution of this monitor
        screen_height = GetSystemMetrics(1)

        # begin wxGlade: mainFrame.__set_properties
        self.SetTitle(window_title)  # set window title
        self.SetSize((screen_width * size_ratio,
                      screen_height * size_ratio))  # set size of window
        self.Center()  # center the window

#        self.Maximize(True)                            # issues with scrolledwindow?

        # %%                                                  Put notebook in window.

    def __do_layout(self):
        """
        Puts a notebook in the main window.
        """
#        self.videoNotebook = mainNotebook(self)

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.theNotebook, 1, wx.EXPAND, 0)
        self.SetSizer(mainSizer)


# ------------------------------------------------------------------------------------- Main Program
if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()

    frame_1 = mainFrame(None, -1, '')           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    wx.lib.inspection.InspectionTool().Show()

    app.MainLoop()                              # Begin user interactions.


