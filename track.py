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
import os
import cv2
import numpy as np
import pysolovideoGlobals as gbl
import configurator as cfg
import videoMonitor as VM
import math
from itertools import repeat  # generate tab-delimited zeroes to fill in extra columns
import winsound

# TODO: monitors are being tracked one at a time


class trackedMonitor(wx.Panel):                                    # TODO: why does this need to be a panel?  does it matter?
    def __init__(self, parent, mon_ID):
        self.mon_ID = gbl.mon_ID = mon_ID       # make sure the settings for this monitor are in the nicknames
        cfg.mon_dict_to_nicknames()
        self.mon_name = gbl.mon_name
        wx.Panel.__init__(self, parent, id=wx.ID_ANY, name=self.mon_name)

        # -------------------------------------------------------------------------------------------- source settings
        self.parent = parent
        self.loop = False                       # never loop tracking
        self.keepPlaying = False                # don't start yet
        self.source = gbl.source
        self.source_type = gbl.source_type
        self.devnum = 0                         # only one camera is currently supported
        self.fps = gbl.source_fps
        self.start_datetime = gbl.start_datetime
        self.mask_file = gbl.mask_file
        self.data_folder = gbl.data_folder
        self.outputprefix = os.path.join(self.data_folder, self.mon_name)     # path to folder where output will be saved
        self.console = self.consolePanel(parent, size=gbl.thumb_size)                         # the output console


        # ---------------------------------------- use the sourcetype to create the correct type of object for capture
        if self.source_type == 0:
            self.captureMovie = VM.realCam(self.mon_ID, 1, devnum=0)
        elif self.source_type == 1:
            self.captureMovie = VM.virtualCamMovie(self.mon_ID, 1, self.source, loop=False)
        elif self.source_type == 2:
            self.captureMovie = VM.virtualCamFrames(self.mon_ID, 1, self.source, loop=False)

        (self.cols, self.rows) = self.size = self.captureMovie.initialSize

        self.ROIs = gbl.loadROIsfromMaskFile(self.mask_file)  # -----------------------------------------------------ROIs

    class consolePanel(
        wx.TextCtrl):  # ------------------------------------------------ redirect sysout to scrolled textctrl
        def __init__(self, parent, size=(200, 200)):  # parent is the cfgPanel
            self.mon_ID = gbl.mon_ID  # keep track of which monitor this console is for
            style = wx.TE_MULTILINE | wx.TE_RICH | wx.TE_AUTO_SCROLL | wx.HSCROLL | wx.VSCROLL | wx.TE_READONLY
            wx.TextCtrl.__init__(self, parent, wx.ID_ANY, size=size, style=style, name=gbl.mon_name)

        def writemsg(self, message):
            self.AppendText(message + '\n')

    def getCoordsArray(self):
        keepgoing = True
        fly_coords = []                                 # table of coordinates of flies in each ROI for each frame
        frameCount = 0
        # ------------------------------------------------ make 2D array of fly coordinates for every ROI in every frame
        while keepgoing:                     # goes through WHOLE video
            # each of the 3 video input classes has a "getImage" function.
            # CaptureMovie is either webcam, video, or a folder
            frame = self.captureMovie.getImage()                # get image
            frameCount = frameCount + 1
            self.parent.trackedConsoles[self.mon_ID].writemsg('monitor %d, frame %d' % (self.mon_ID, frameCount))
            self.parent.trackedConsoles[self.mon_ID].SetFocus()
            if frame is not None:
                bw_image = self.prepImage(frame)                    # convert image to B&W and reduce noise
                fly_coords.append(self.getFrameFlyCoords(bw_image)) # append coordinates for every ROI in this frame
            else:
                keepgoing = False

        return fly_coords

    def calcDistances(self, fly_coords):
        # ------------------------------------------------------- in one minute increments, tabulate the distances moved
        # AFTER whole video is finished, do calculations
        distByMinute = []  # this is the tracking data we're producing
        self.previousFrame = fly_coords[0]
        for frameCount in range(0, len(fly_coords), int(60 * self.fps)):  # for each one minute interval
            subsetCoordinates = fly_coords[
                                frameCount:(frameCount + int(60 * self.fps))]  # get distance value for each ROI
            distByMinute.append(
                self.getDistances(subsetCoordinates, frameCount))  # append to array of distance calculations

        return distByMinute

    def startTrack(self, show_raw_diff=False, drawPath=True):  # ---------------------------------------- begin tracking
        """
        Each frame is compared against the moving average
        take an opencv frame as input and return an array of distances moved per minute for each ROI
        """

        gbl.statbar.SetStatusText('Tracking started: ' + self.mon_name)

        fly_coords = self.getCoordsArray()                       # finds coordinates of flies in each ROI in each frame
        distByMinute = self.calcDistances(fly_coords)            # calculates distance each fly travelled in each minute
        outputArrays = self.colSplit32(distByMinute)             # splits data into 32 ROI groups

        self.outputprefix = self.checkFilenames(len(outputArrays))      # prevents overwriting of files

        for batch in range(0, len(outputArrays)):                  # output the files
            outputfile = self.outputprefix + str(batch + 1) + '.txt'  # create a filename for saving

            f_out = open(outputfile, 'a')
            for rownum in range(0, len(outputArrays[batch])):
                f_out.write(outputArrays[batch][rownum])       # save "part" to the file in tab delimited format
                self.parent.trackedConsoles[self.mon_ID].writemsg(outputArrays[batch][rownum])
                self.parent.trackedConsoles[self.mon_ID].SetFocus()
            f_out.close()

            filename = os.path.split(self.outputprefix)[1]

        if filename == '':
            gbl.statbar.SetStatusText('Cancelled.')
        else:
            gbl.statbar.SetStatusText('Done. Output file names start with:  ' + filename)

        self.parent.trackedConsoles[self.mon_ID].writemsg('Acquisition of Monitor %d is finished.' % self.mon_ID)
        self.parent.trackedConsoles[self.mon_ID].SetFocus()

    def colSplit32(self, array):
        oneMinute = wx.TimeSpan(0,1,0,0)
        rownum = 1
        parts = []
        for rowdata in array:                           # determine how many files are needed
            if rownum == 1:
                numofParts = int(math.ceil((len(rowdata)-10)/32.0))         # number of separate files needed
                for num in range(0, numofParts):
                    parts.append([])                            # create an empty list for each file to be created

                realdatetime = self.start_datetime              # get the date and time for this row of data
            else:
                realdatetime = realdatetime.AddTS(oneMinute)


            prefix = str(rownum) + '\t' + realdatetime.Format('%d %b %y')           # column 0 is the row number, column 1 is the date
            prefix = prefix + '\t' + realdatetime.Format('%H:%M:%S')                # column 2 is the time
            prefix = prefix + '\t1\t1\t0\t0\t0\t0\t0'                               # next 7 columns are not used but DAMFileScan110X does not take 0000000 or 1111111


            for batch in range(0, numofParts):               # add 32 columns to each part
                datastring = prefix
                startcol = batch * 32
                endcol = startcol + 32
#                datastring = ("\t%d" % number for number in rowdata[startcol: endcol])
                for number in rowdata[startcol:endcol]:
                    datastring = datastring + '\t%d' % number

                parts[batch].append(datastring + '\n')            # append all of the rows to list "parts[batch]"

            rownum = rownum +1

        if len(rowdata) != numofParts * 32:                    # need to fill empty columns with zeroes
            morecols = (numofParts * 32) - len(rowdata)
            for rownum in range(0, len(parts[numofParts - 1])):
                parts[numofParts - 1][rownum] = parts[numofParts - 1][rownum][0:-1] + \
                                                '\t' + '\t'.join(list(repeat('0', morecols))) + '\n'
        return parts

    def tryNewName(self):
        defaultDir = os.path.split(self.outputprefix)[0]
        wildcard = "File Prefix |*.txt|" \
                       "All files (*.*)|*.*"

        dlg = wx.FileDialog(self.parent,
                            message="Choose a different output prefix for Monitor %d ..." % self.mon_ID,
                            defaultDir=defaultDir, wildcard=wildcard, style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:  # show the file browser window
            self.outputprefix = dlg.GetPath()[0:-4]  # get the filepath & name from the save dialog, don't use extension
        else:
            self.outputprefix = ''

        dlg.Destroy()
        return self.outputprefix

    def checkFilenames(self, numofParts):       # ----------------------------- gets valid output name and avoids overwriting
        goodname = False
        if not os.path.isdir(os.path.split(self.outputprefix)[0]):          # ------ directory must exist
            self.outputprefix = self.tryNewName()

        while not goodname:                                     # test to see if files will be overwritten
            goodname = True     # assume name is good until proven otherwise
            for batch in range(0, numofParts):                             # ------ check for each output file
                outputfile = self.outputprefix + str(batch + 1) + '.txt'  # create a filename for saving

                if goodname  and  os.path.isfile(outputfile):
                    gbl.statbar.SetStatusText('Avoid overwrite: File -> ' + outputfile + ' <- already exists.')
                    winsound.Beep(600, 200)
                    goodname = False

            if not goodname:
                self.outputprefix = self.tryNewName()       # ask for a new prefix

        return self.outputprefix

    def getDistances(self, coords, currentFrame):   # ------------------------- tabulates distance travelled by each fly
        totalDists = np.zeros(len(self.ROIs), dtype=int)     # tabulation of distances travelled in each ROI throughout video
        theseDists = np.zeros(len(self.ROIs))          # array of distances travelled between 2 frames for each ROI

        for thisFrame in coords:
            d_squareds = np.square(np.subtract(self.previousFrame, thisFrame))  # (x1-x2)^2, (y1-y2)^2 for each element

            for roiNum in range(0, len(d_squareds)):        # iterate through the ROIs, calculating distances
                theseDists[roiNum] = np.sqrt(d_squareds[roiNum][0] + d_squareds[roiNum][1])  # d = sqrt(x^2 + y^2)

            totalDists = totalDists + theseDists   # adds these distances to the running tab

            self.previousFrame = thisFrame                  # store for comparison with next frame
            currentFrame = currentFrame +1                  # keeps track of actual frame number in whole video

        return totalDists

    def prepImage(self, frame):
        frame = cv2.GaussianBlur(frame, (3, 3), 0)  # ----------blurs edges, aperture width 3, aperture height 0
        grey_image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # remove color & collapse to 2D array

        retvalue, bw_image = cv2.threshold(grey_image, 75, 255,
                                           cv2.THRESH_BINARY)  # convert to black & white   # TODO:  best threshold values?  was 20,255
        bw_image = cv2.morphologyEx(bw_image, cv2.MORPH_OPEN, (3, 3))  # remove noise

        """
        # ------------------------------------------------------------------------------------------------------------------------------ debug
        mini_image = cv2.resize(bw_image, (600, 600))
        cv2.imshow('mini', mini_image)
        cv2.waitKey(0)
        """
        return bw_image

    def getFrameFlyCoords(self,bw_image):             # returns an array of fly coordinates for one frame
        fliesInFrame = []
        for ROI in self.ROIs:                               # locate the fly in each ROI
            ROIimg = bw_image[ROI[0][1]:ROI[2][1],ROI[0][0]:ROI[2][0]]    # make a mini-image of the ROI
            """
# ------------------------------------------------------------------------------------------------------------------------------ debug
            cv2.imshow('ROIimg', ROIimg)
            cv2.waitKey(0)
            """
            fliesInFrame.append(self.getFlyCoords(ROIimg))        # determines coordinates of center of fly in ROI

        return fliesInFrame

    def getFlyCoords(self, ROIimg):             # returns coordinates of a single fly
        contours, hierarchy = cv2.findContours(ROIimg, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)  # find contours

        if len(contours) == 1:
            fly_rect = cv2.boundingRect(
                contours[0])  # coordinates (x, y, w, h) of a rectangle around the outside of the contour
        elif len(contours) > 1:
            rect_areas = []  # list of areas of the bounding boxes for one ROI
            rect_list = []  # list of coordinates of bounding rectangles for one ROI
            for contour in contours:  # find the second largest bounding box
                # get bounding rectangles and choose largest one
                rect_list.append(
                    cv2.boundingRect(contour))  # coordinates (x, y, w, h) of a rectangle around the outside of the contour
                rect_areas.append(rect_list[-1][2] * rect_list[-1][3])  # area of the rectangle

            fly_idx = max([idx for idx, value in enumerate(rect_areas)])  # use largest bounding box for fly
            fly_rect = rect_list[fly_idx]
        else:
            fly_rect = (0, 0, 0, 0)  # no contours found - there is no fly

        if fly_rect[2] * fly_rect[3] > 4000:  # blob is too big to be a fly or no contours found
            fly_rect = (0, 0, 0, 0)

        # use center of rectangle as center of fly.  tracking will not account for turning in place
        return ((fly_rect[0] + fly_rect[2] / 2),     # x-coordinate
                 (fly_rect[1] + fly_rect[3] / 2))  # y-coordinate




# ------------------------------------------------------------------------------------------ Stand alone test code
#  insert other classes above and call them in mainFrame
#

class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, None, id=wx.ID_ANY, size=(1000,200))



        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#

