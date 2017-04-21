
import wx
import threading
import configurator as cfg
import videoMonitor as VM
import track
import pysolovideoGlobals as gbl
from wx.lib.newevent import NewCommandEvent
ThumbnailClickedEvt, EVT_THUMBNAIL_CLICKED = wx.lib.newevent.NewCommandEvent()

# TODO:  Stop Acquisition button leads to never-never-land


# ------------------------------------------------------------------------- creates a thread that plays a videoMonitor
class videoThread (threading.Thread):                       # threading speeds up video processing
    def __init__(self, monitorPanel, name):
        threading.Thread.__init__(self)
        self.monitorPanel = monitorPanel                            # the video panel to be played in the panel
        self.name = name

    def start(self):
        self.monitorPanel.PlayMonitor()                             # start playing the video
        gbl.threadsStarted.append((gbl.mon_ID, ' video'))                                                                      ###### for debugging

class trackingThread (threading.Thread):        #----------------------- creates a Thread that processes the video input
    def __init__(self, parent, trackedMonitor, mon_ID):
        threading.Thread.__init__(self)
        self.trackedMonitor = trackedMonitor                # the tracking object
        self.mon_ID = mon_ID
        self.name = gbl.cfg_dict[self.mon_ID]['mon_name']

    def start(self):
        self.trackedMonitor.startTrack()
        gbl.threadsStarted.append((gbl.mon_ID, ' tracking'))                                                                    ###### for debugging


class scrollingWindow(wx.ScrolledWindow):     # ---------------------- contails a list of thumbnails in a scrolled window
    def __init__(self, parent):
        """
        Thumbs may be videoMonitor panels or console panels.  They are contained in the self.thumbPanels list
        and are mutually exclusive.
        """
        # -------------------------------------------------------------------------------------- Set up scrolling window
        self.parent = parent
        wx.ScrolledWindow.__init__(self, parent, wx.ID_ANY, size=(-1, 300))
        self.SetScrollbars(1, 1, 1, 1)
        self.SetScrollRate(10, 10)

        self.thumbGridSizer = wx.GridSizer(3, 3, 5, 5)

        self.thumbPanels = ['thumb panels']
        self.refreshThumbGrid()            # --------------------- put thumbnails in gridsizer and display in scrolled window
                                            # setsizer is done in calling program (cfgPanel)

    def clearThumbGrid(self):
        if len(self.thumbPanels) > 1:        # don't remove the 0th element
            for gbl.mon_ID in range(len(self.thumbPanels) -1, 0, -1):     # destroy old previewPanel objects or they will keep playing
                                                            # reverse order avoids issues with list renumbering
                self.thumbPanels[gbl.mon_ID]._Thread__stop()
                self.thumbPanels[gbl.mon_ID].monitorPanel.keepPlaying = False        # stop playing video                       ###### checks out 1,2,3
                self.thumbPanels[gbl.mon_ID].monitorPanel.playTimer.Stop()
                self.thumbPanels[gbl.mon_ID].monitorPanel.Hide()
                self.thumbPanels[gbl.mon_ID].monitorPanel.Destroy()         # prevents doubled up images & flickering
                del self.thumbPanels[gbl.mon_ID]                    # delete the objects from the list.

                gbl.del_started_item(gbl.threadsStarted, gbl.mon_ID)                                                        ###### for debugging
                gbl.del_started_item(gbl.timersStarted, gbl.mon_ID)                                                        ###### for debugging

        self.thumbGridSizer.Clear()                          # clear out gridsizer

    def refreshThumbGrid(self):  # -------------------------------------- Make array of thumbnails to populate the grid
        oldMonID = gbl.mon_ID
        try:    # ------ don't know if thumbnails or consoles are showing
            self.clearThumbGrid()
        except: pass
        try:    # ------ don't know if thumbnails or consoles are showing
            self.clearConsoleGrid()
        except:
            pass

        # --------------------------------------------- go through each monitor configuration and make a thumbnail panel
        for gbl.mon_ID in range(1, gbl.monitors + 1):
            cfg.mon_dict_to_nicknames()

            # create thread with thumbnail panel and add to grid
            self.thumbPanels.append(videoThread(VM.monitorPanel(self, mon_ID=gbl.mon_ID, panelType='thumb', loop=True),             ###### checks out 1, 2, 3
                                               gbl.mon_name))

            interval = self.thumbPanels[gbl.mon_ID].monitorPanel.interval
            self.thumbPanels[gbl.mon_ID].start()
            self.thumbPanels[gbl.mon_ID].monitorPanel.playTimer.Start(interval)
            self.thumbGridSizer.Add(self.thumbPanels[gbl.mon_ID].monitorPanel, 1, wx.ALIGN_CENTER_HORIZONTAL, 5)
            gbl.timersStarted.append([gbl.mon_ID, 'thumb panel'])                                                                 ###### debug

        self.SetSizerAndFit(self.thumbGridSizer)
        self.Layout()                                   # rearranges thumbnails into grid           # setscrollbars has no effect here

        gbl.mon_ID = oldMonID                          # go back to same page we came from
        if gbl.mon_ID != 0:
            cfg.mon_dict_to_nicknames()


    def clearConsoleGrid(self):
        if len(self.thumbPanels) > 1:        # don't remove the 0th element
            maxcount = len(self.thumbPanels) -1
            for mon_count in range(maxcount, 0, -1):     # destroy old previewPanel objects or they will keep playing
                                                            # reverse order avoids issues with list renumbering
#                self.thumbPanels[mon_count].trackedMonitor.keepPlaying = False        # no video
#                self.thumbPanels[mon_count].thumbPanels.console.playTimer.Stop()       # timers aren't needed for consoles
                self.trackedConsoles[mon_count].Hide()
                self.trackedConsoles[mon_count].Destroy()                                      # prevents doubled up panels and flickering
                self.thumbPanels[mon_count]._Thread__stop()
                del self.thumbPanels[mon_count]                    # delete the objects from the list.
                del self.trackedConsoles[mon_count]                # delete the objects from the list.
                del self.trackedMonitors[mon_count]                # delete the objects from the list.

            gbl.del_started_item(gbl.threadsStarted, gbl.mon_ID)                                                        ###### for debugging
            gbl.del_started_item(gbl.timersStarted, gbl.mon_ID)                                                        ###### for debugging

        self.thumbGridSizer.Clear()                          # clear out gridsizer

    def refreshConsoleGrid(self):  # ------------------------------------- Make array of thumbnails to populate the grid
        oldMon_ID = gbl.mon_ID

        try:    # ------ don't know if thumbnails or consoles are showing
            self.clearThumbGrid()
        except: pass
        try:    # ------ don't know if thumbnails or consoles are showing
            self.clearConsoleGrid()
        except:
            pass

        # --------------------------------------------- go through each monitor configuration and make a thumbnail panel
        self.trackedMonitors = ['tracked monitors']
        self.trackedConsoles = ['consoles']
        for gbl.mon_ID in range(1, gbl.monitors + 1):
            cfg.mon_dict_to_nicknames()  # load monitor parameters to globals

            # create thread with tracked monitor and scroll panel and add to grid
            self.trackedMonitors.append(track.trackedMonitor(self, gbl.mon_ID))
            self.trackedConsoles.append(self.trackedMonitors[gbl.mon_ID].console)
            self.thumbPanels.append(trackingThread(self, self.trackedMonitors[gbl.mon_ID], gbl.mon_ID))  # create tracked object

            self.thumbGridSizer.Add(self.trackedConsoles[gbl.mon_ID], 1, wx.ALIGN_CENTER_HORIZONTAL, 5) # add console to scrolled window

        self.SetSizerAndFit(self.thumbGridSizer)                                  # did not fix all thumbs in one place
        self.Parent.Layout()

        for gbl.mon_ID in range(1, gbl.monitors + 1):
            self.thumbPanels[gbl.mon_ID].start()  # start tracking after grid sizer is completely set

        gbl.mon_ID = oldMon_ID              # go back to the page we came from
        if gbl.mon_ID != 0:
            cfg.mon_dict_to_nicknames()

    def ignoreEvent(self, event):
        event.skip()
# ------------------------------------------------------------------------------------------ Stand alone test code

#  insert other classes above and call them in mainFrame
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

        whatsit = scrollingWindow(self)

        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.


