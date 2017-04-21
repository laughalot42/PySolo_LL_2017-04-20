import wx
import cv2, cv2.cv
import os
import numpy as np
import winsound
import configurator as cfg
import pysolovideoGlobals as gbl

# --------------------------------------------------------------------------------------------- for using a video camera
class realCam(object):                                  # don't use global variables for this object due to threading
    """
    realCam class will handle a webcam connected to the system
    """
    def __init__(self_realCam, mon_ID=gbl.mon_ID, fps=gbl.source_fps, devnum=0):
        self_realCam.mon_ID = mon_ID                                    # don't use gbl nicknames due to threading
        self_realCam.source = devnum                                    # source is the device number
        self_realCam.fps = fps

        self_realCam.currentFrame = 0
        self_realCam.loop = True                   # cameras don't really loop, and shouldn't stop

        # ----------------------------------------------------------------------------------- initialize the camera
        try:    # ------ may fail to start camera
            self_realCam.captureVideo = cv2.VideoCapture(self_realCam.source)      # only one camera (device 0) is supported
                                                                                # argument is required even though it's "unexpected"
            retrn, self_realCam.frame = self_realCam.captureVideo.read()
        except:
            self_realCam.captureVideo = None                          # capture failed
            gbl.statbar.SetStatusText('Real Cam capture failed.')
            winsound.Beep(600,200)
            return
        #  ----------------------------------------------------------------------------- preserve camera properties
        self_realCam.initialSize = self_realCam.getCamFrameSize()
        self_realCam.lastFrame = 0                                      # cameras don't have a last frame


    def getCamFrameSize(self_realCam):
        """
        Return real size
        """
        self_realCam.rows, self_realCam.cols, channels = self_realCam.frame.shape
        return int(self_realCam.cols), int(self_realCam.rows)

    def getImage(self_realCam):  # capture and prepare the next frame
        """
        for live cameras
        """
        try:    # ------ may fail to read frame
            retrn, self_realCam.frame = self_realCam.captureVideo.read()
        except:
            self_realCam.frame = None
            gbl.statbar.SetStatusText('Real Cam capture failed.')
            winsound.Beep(600, 200)

        self_realCam.currentFrame += 1          # there is no last frame
        return self_realCam.frame


# ----------------------------------------------------------------------------------------------- for using a video file
class virtualCamMovie(object):
    """
    A Virtual cam to be used to pick images from a movie (avi, mov)
    """
    def __init__(self_vMovie, mon_ID=gbl.mon_ID, fps=gbl.source_fps, source= gbl.source, loop=True):
        self_vMovie.mon_ID = mon_ID                            # don't use gbl nicknames after init due to threading
        self_vMovie.source = source
        self_vMovie.fps = fps

        self_vMovie.currentFrame = 0
        self_vMovie.loop = loop

        try:    # ------ video may not open
            self_vMovie.captureVideo = cv2.VideoCapture(self_vMovie.source)
            flag, self_vMovie.frame = self_vMovie.captureVideo.read()
        except:
            self_vMovie.captureVideo = None                                       # capture failed
            gbl.statbar.SetStatusText('Video Cam capture failed.')
            winsound.Beep(600, 200)
            return

        self_vMovie.initialSize = self_vMovie.getVideoCamSize()                         # frame size from video
        self_vMovie.lastFrame = self_vMovie.captureVideo.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)

    def getVideoCamSize(self_vMovie):
        try:    # ------ frame is sometimes a NoneType object
            self_vMovie.rows, self_vMovie.cols, channels = self_vMovie.frame.shape
            return int(self_vMovie.cols), int(self_vMovie.rows)
        except:
            gbl.statbar.SetStatusText('No video frame available in videoMonitor.py, getVideoCamSize')
            return 500, 500     # randomly chosen substitute values

    def getImage(self_vMovie):            # capture next frame from video file
        """
        for input from video file
        """
        if (self_vMovie.currentFrame >= self_vMovie.lastFrame) and self_vMovie.loop:   # reached end of file
            self_vMovie.currentFrame = 0
            self_vMovie.captureVideo = cv2.VideoCapture(self_vMovie.source)         # restart the video

        elif (self_vMovie.currentFrame >= self_vMovie.lastFrame) and not self_vMovie.loop:
            self_vMovie.frame = None
            gbl.statbar.SetStatusText('End of Video File.')
            winsound.Beep(600, 200)
            return
        else: pass

        try:    # ------ may fail to read frame
            flag, self_vMovie.frame = self_vMovie.captureVideo.read()
        except:
            self_vMovie.frame = None
            gbl.statbar.SetStatusText('Capture failed.')
            winsound.Beep(600, 200)
            return

        self_vMovie.currentFrame += 1
        return self_vMovie.frame

# ------------------------------------------------------------------------------------ for using a sequence of 2D images
class virtualCamFrames(object):
    """
    A Virtual cam to be used to pick images from a folder rather than a webcam
    Images are handled through PIL
    """
    def __init__(self_vFrames, mon_ID = gbl.mon_ID, fps= gbl.source_fps, source=gbl.source, loop=True):
        self_vFrames.mon_ID = mon_ID
        self_vFrames.source = source
        self_vFrames.fps = fps

        self_vFrames.currentFrame = 0
        self_vFrames.loop = loop

        # ------------------------------------------------------------------------------ initialize file manager
        self_vFrames.fileList = self_vFrames.__populateList__()

        self_vFrames.lastFrame = len(self_vFrames.fileList)
        if self_vFrames.lastFrame == 0:
            self_vFrames.captureVideo = None                                       # capture failed
            gbl.statbar.SetStatusText('No images in folder.')
            winsound.Beep(600, 200)
            return


        filepath = os.path.join(self_vFrames.source, self_vFrames.fileList[0])

        self_vFrames.frame = cv2.imread(filepath, cv2.cv.CV_LOAD_IMAGE_COLOR)

        self_vFrames.initialSize = self_vFrames.getFramesSize()

    def __populateList__(self_vFrames):
        """
        Populate the file list
        """
        fileList = []
        fileListTmp = os.listdir(self_vFrames.source)

        for fileName in fileListTmp:
            if '.tif' in fileName or '.jpg' in fileName:
                fileList.append(fileName)

        fileList.sort()
        return fileList

    def getFramesSize(self_vFrames):
        self_vFrames.rows, self_vFrames.cols, channels = self_vFrames.frame.shape
        return int(self_vFrames.cols), int(self_vFrames.rows)

    def getImage(self_vFrames):
        """
        for folder of 2D images
        """
        if self_vFrames.currentFrame >= self_vFrames.lastFrame and self_vFrames.loop:
            self_vFrames.currentFrame = 0                                      # loop if requested

        elif self_vFrames.currentFrame > self_vFrames.lastFrame and not self_vFrames.loop:
            self_vFrames.frame = None
            gbl.statbar.SetStatusText('End of File List.')
            winsound.Beep(600, 200)
            return

        try:    # ------ may fail to find files in folder
            filepath = os.path.join(self_vFrames.source, self_vFrames.fileList[self_vFrames.currentFrame])
            self_vFrames.frame = cv2.imread(filepath, cv2.cv.CV_LOAD_IMAGE_COLOR)
        except:
            self_vFrames.captureVideo = None                        # capture failed
            gbl.statbar.SetStatusText('Error loading file ' + self_vFrames.fileList[self_vFrames.currentFrame])
            winsound.Beep(600, 200)
            return

        self_vFrames.currentFrame += 1
        return self_vFrames.frame

# ------------------------------------------------------------------------------------------ generic video display panel
class monitorPanel(wx.Panel):                                       
    """
    One Panel to be used as thumbnail, or a preview panel
    Avoid gbl nicknames, except for cfg_dict and flags, in case this is called for a monitor that is not currently selected
    """
    def __init__( self_MP, parent, mon_ID=gbl.mon_ID, panelType='thumb', loop=True):

        self_MP.mon_ID = mon_ID
        self_MP.mon_name = gbl.cfg_dict[self_MP.mon_ID]['mon_name']
        self_MP.panelType = panelType     # ----------------------------------------------- panel attributes
        if panelType == 'preview':
            self_MP.size = gbl.cfg_dict[self_MP.mon_ID]['preview_size']
            self_MP.fps = gbl.cfg_dict[self_MP.mon_ID]['preview_fps']
        elif panelType == 'thumb':
            self_MP.size = gbl.cfg_dict[0]['thumb_size']
            self_MP.fps = gbl.cfg_dict[0]['thumb_fps']
        else:
            self_MP.size = (320,240)
            self_MP.fps = 1
            print('Unexpected panel type in class monitorPanel')

        wx.Panel.__init__(self_MP, parent, id=wx.ID_ANY, size=self_MP.size, name=self_MP.mon_name)

        self_MP.parent = parent
        self_MP.loop = loop
        self_MP.keepPlaying = False                               # flag to start and stop video playback
        self_MP.source = gbl.cfg_dict[self_MP.mon_ID]['source']   # ----------------------------------- video source
        self_MP.source_type = gbl.cfg_dict[self_MP.mon_ID]['source_type']
#        if self_MP.source_type == 0:     # get the device number if the panel source is a webcam
#            self_MP.source = 0

        if gbl.genmaskflag:
            self_MP.ROIs = self_MP.Parent.ROIs
        else:
            self_MP.mask_file = gbl.cfg_dict[self_MP.mon_ID]['mask_file']
            try:    # ------ mask file may be corrupt
                self_MP.ROIs = gbl.loadROIsfromMaskFile(self_MP.mask_file)
            except: self_MP.ROIs = []

        self_MP.line_thickness = gbl.cfg_dict[self_MP.mon_ID]['line_thickness']

        self_MP.interval = 1000/ self_MP.fps

        self_MP.widgetMaker()             # ------------------------------------------ panel widgets and sizers
        self_MP.sizers()
        self_MP.SetSize(self_MP.size)
        self_MP.SetMinSize(self_MP.GetSize())
        self_MP.SetBackgroundColour('#A9A9A9')
        self_MP.allowEditing = False

        # ---------------------------------------- use the sourcetype to create the correct type of object for capture
        if gbl.cfg_dict[self_MP.mon_ID]['source_type'] == 0:
            self_MP.captureVideo = realCam(self_MP.mon_ID, self_MP.fps, devnum=0)
        elif gbl.cfg_dict[self_MP.mon_ID]['source_type'] == 1:
            self_MP.captureVideo = virtualCamMovie(self_MP.mon_ID, self_MP.fps, self_MP.source, loop=self_MP.loop)
        elif gbl.cfg_dict[self_MP.mon_ID]['source_type'] == 2:
            self_MP.captureVideo = virtualCamFrames(self_MP.mon_ID, self_MP.fps, self_MP.source, loop=self_MP.loop)

        self_MP.initialSize = (self_MP.initialCols, self_MP.initialRows) = self_MP.captureVideo.initialSize      # input frame size
        if self_MP.size > self_MP.captureVideo.initialSize:         # if size desired is bigger than input size
            self_MP.size = self_MP.captureVideo.initialSize         # reduce it to the input size
            if panelType == 'thumb':
                gbl.thumb_size = self_MP.size
            elif panelType == 'preview':
                gbl.preview_size = self_MP.size
            cfg.cfg_nicknames_to_dicts()

            self_MP.SetSize(self_MP.size)
            winsound.Beep(600,200)
            gbl.statbar.SetStatusText('Input frame size is only ' + str(self_MP.size))


        # mouse coordinates for mask panels only
        if gbl.mon_ID != 0:
            self_MP.Bind(wx.EVT_LEFT_UP, self_MP.onLeftUp)
        # ---------------------------------------------------------------------- create a timer that will play the video
        self_MP.Bind(wx.EVT_PAINT, self_MP.onPaint)
        self_MP.Bind(wx.EVT_TIMER, self_MP.onNextFrame)
        self_MP.playTimer = wx.Timer(self_MP, id=wx.ID_ANY)
        self_MP.numberOfTimers = gbl.numberOfTimers +1

    # ---------------------------------------------------------------------------------------------------------- Widgets
    def widgetMaker(self_MP):
        # --------------------------------------------------------------------- monitor number to display in corner
        monfont = wx.Font(25, wx.SWISS, wx.NORMAL, wx.NORMAL)
        self_MP.monDisplayNumber = wx.StaticText(self_MP, wx.ID_ANY, ' %s' % self_MP.mon_ID)
        self_MP.monDisplayNumber.SetFont(monfont)

    def sizers(self_MP):
        self_MP.numberSizer = wx.BoxSizer(wx.HORIZONTAL)
        self_MP.numberSizer.Add(self_MP.monDisplayNumber, 0, wx.ALIGN_LEFT | wx.ALIGN_TOP, 20)

        self_MP.SetSizer(self_MP.numberSizer)                       # just uncommented
        self_MP.Layout()

    def PlayMonitor(self_MP):

        try: self_MP.ROIs               # if there are no ROIs yet, make an empty list
        except: self_MP.ROIs = []

        if not gbl.genmaskflag or self_MP.ROIs == []:
            self_MP.ROIs = gbl.loadROIsfromMaskFile(gbl.mask_file)              # new ROIs are ready

        self_MP.ROIframe, self_MP.redmask = gbl.makeMaskFrames(self_MP.ROIs, self_MP.initialSize)  # creates overlay of ROIs with source dimensions

        # each of the 3 video input classes has a "getImage" function
        self_MP.frame = self_MP.captureVideo.getImage()

        # multiply element by element to leave zeros where lines will be drawn
        self_MP.frame2 = np.multiply(self_MP.frame.copy(), self_MP.ROIframe)

        # add redmask to frame to turn lines red
        self_MP.frame3 = np.add(self_MP.frame2.copy(), self_MP.redmask)

        self_MP.newframe = cv2.resize(self_MP.frame3.copy(), dsize=self_MP.size)

        self_MP.bmp = wx.BitmapFromBuffer(self_MP.size[0], self_MP.size[1], self_MP.newframe.tostring())

        self_MP.keepPlaying = True
        self_MP.Show()
        gbl.genmaskflag = False

    def onNextFrame(self_MP, evt):  # -------------------------------------------------- captures next frame
        self_MP.frame = self_MP.captureVideo.getImage()

        if self_MP.frame is None:
            gbl.statbar.SetStatusText('Reached end of file. Monitor %d'% gbl.mon_ID)
            self_MP.keepPlaying = False
            self_MP.playTimer.Stop()
            winsound.Beep(600,200)
            gbl.del_started_item(gbl.timersStarted, self_MP.mon_ID)                                                         ###### debug
            return


        frame2 = np.multiply(self_MP.frame.copy(), self_MP.ROIframe)  # apply mask (like PlayMonitor function)
        frame3 = np.add(frame2.copy(), self_MP.redmask)
        self_MP.newframe = cv2.resize(frame3.copy(), dsize=self_MP.size)        # resize the frame before copy from buffer
                                                                                # too large a frame will be corrupted

        try:    # ------ copy from buffer may fail
            self_MP.bmp.CopyFromBuffer(self_MP.newframe.tostring())  # copies data from buffer to bitmap
            self_MP.Refresh()  # triggers EVT_PAINT

        except:
            gbl.statbar.SetStatusText('Could not paint image.')
            self_MP.keepPlaying = False

    def onPaint(self_MP, evt):  # ---------------------------------------------- applies ROIs to image frame
        # BufferedPaintDC only works inside an event method.  ClientDC doesn't seem to do the job.

        try: self_MP.bmp    # ------ may have failed to create .bmp file
        except: pass
        else:
            thePanel = evt.GetEventObject()     # sometimes the event object is still not the right size.  Reset it just in case
            thePanel.SetSize(self_MP.size)
            dc = wx.BufferedPaintDC(thePanel)  # eventobject is a monitorPanel; create a buffered paint device context (DC)
            dc.DrawBitmap(self_MP.bmp, 0, 0, True)  # draw bitmap on the buffered DC

        evt.Skip()

    def onLeftUp(self, event):           # -------------------------- get mouse pointer coordinates of upper left corner
        print('wait here')

        (x_mouse, y_mouse) = event.GetPosition()
        x_source = x_mouse * self.initialSize[0] / self.size[0]
        y_source = y_mouse * self.initialSize[1] / self.size[1]

        self.parent.X[2].SetValue(x_source)
        self.parent.Y[2].SetValue(y_source)



# ------------------------------------------------------------------------------------------ Stand alone test code
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

        self.config = cfg.Configuration(self)
        thumbnailsize = gbl.cfg_dict[0]['size_thumb']
        thumb = monitorPanel(self, gbl.cfg_dict, 'thumb')

        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "", (10,10), (600,400))           # Create the main window.    id, title, pos, size, style, name
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#
