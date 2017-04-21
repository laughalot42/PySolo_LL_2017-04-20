""" Global Variable Declarations """

# previewPanels cannot be global because they must be assigned to their apecific panel

# ----------------------------------------------------------------------------   Imports
import numpy as np                      # for ROIs
import wx                               # GUI controls
import os                               # system controls
import cv2
import cv2.cv
from os.path import expanduser          # get user's home directory
import datetime                         # date and time handling functions
import sys
import cPickle
import winsound


exec_dir = sys.path[0]    # folder containing the scripts for this program


# -------------------------------------------------- nicknames for general configuration parameters
global monitors, \
    thumb_size, \
    thumb_fps, \
    cfg_path, \
    thumbPanels, \
    threadsStarted, \
    timersStarted, \
    trackers, \
    statbar

monitors = 1
# webcams = 1
thumb_size = (320,240)
thumb_fps = 5
cfg_path = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files')

thumbPanels = ['thumb panels']                  # list of thumbnail panels used in scrolled window on configuration page
                                                 # element 0 identifies the type of list
threadsStarted  = []              # list of threads started
timersStarted = []
trackers = []                       # list of trackers for acquiring data.  index does not match cfg_dict
                                                # since not all monitors are necessarily tracked
statbar = ''

# -------------------------------------------------- nicknames for monitor configuration for **current** mon_ID
global mon_ID, \
    mon_name, \
    source_type, \
    source, \
    source_fps, \
    preview_size, \
    preview_fps, \
    line_thickness, \
    issdmonitor, \
    start_datetime, \
    track, \
    track_type, \
    mask_file, \
    data_folder

mon_ID = 1   # always at least one monitor.  use it to initialize
mon_name = 'Monitor1'
source_type = 0
source = None
source_fps = 0.5
preview_size = (480, 480)
preview_fps = 1
line_thickness = 2
issdmonitor = False
start_datetime = wx.DateTime_Now()
track_type = 0
track = True
mask_file = None
data_folder = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files')

# --------------------------------------------------------------------- cfg_dict contains all configuration settings
global cfg_dict

cfg_dict = [{                                               # create the default config dictionary
        'monitors'      : monitors,                        # element 0 is the options dictionary
#        'webcams'       : webcams,                        # number of webcams available, not necessarily in use
        'thumb_size'    : thumb_size,
        'thumb_fps'     : thumb_fps,
        'cfg_path'      : cfg_path
        },
        {                                       # all additional elements are the monitor dictionaries (1-indexed)
        'mon_name'      : mon_name,                 # include one default monitor of a camera in default config
        'source_type'   : source_type,
        'source'        : source,
        'source_fps'    : source_fps,
        'preview_size'  : preview_size,
        'preview_fps'   : preview_fps,
        'issdmonitor'   : issdmonitor,
        'start_datetime': start_datetime,
        'track'         : track,
        'track_type'    : track_type,
        'mask_file'     : mask_file,
        'data_folder'   : data_folder,
        'line_thickness': line_thickness
        }]

# ------------------------------------------------------------------------------------ Timer Dictionary
global numberOfTimers

numberOfTimers = 0

# ------------------------------------------------------------------- miscellaneous globals
global ROIs, genmaskflag

ROIs = []               # temporary storage for ROIs
genmaskflag = False     # changes to true when new mask is created



# ---------------------------------------------------------------- functions needed by multiple classes

def correctType(r, key):
    """
    changes string r into appropriate type (int, datetime, tuple, etc.)
    """
#    theYear = gbl.start_datetime.GetCurrentYear()  # change the wx.DateTime year representation to 4 digits for datepickerctrl
#    gbl.start_datetime.SetYear(theYear)
#    self.start_date.SetValue(gbl.start_datetime)

    if key == 'start_datetime':  # order of conditional test is important! do this first!
        if type(r) == type(wx.DateTime.Now()):
            pass
        elif type(r) == type(''):  # string -> datetime value
            try:    # ------  string may not be decipherable
                r = string2wxdatetime(r)
            except:
                r = wx.DateTime.Now()
        elif type(r) == type(datetime.datetime.now()):
                r = pydatetime2wxdatetime(r)
        else:
            print('$$$$$$ could not interpret start_datetime value')
            r = wx.DateTime.Now()

        return r

    if r == 'None' or r is None:  # None type
        r = None
        return r

    # look for string characteristics to figure out what type they should be
    if r == 'True' or r == 'False':  # boolean
        if r == 'False':
            r = False
        elif r == 'True':
            r = True

        return r

    try:    # ------  test to see if the value is an integer
        int(r)
        return int(r)
    except:
        pass

    try:    # ------  test to see if the value is a floating point number
        float(r)
        return float(r)
    except:
        pass

    if ',' in r:  # tuple of two integers
        if not '(' in r:
            r = '(' + r + ')'
        r = tuple(r[1:-1].split(','))
        r = (int(r[0]), int(r[1]))

        return r

    return r  # all else has failed:  return as string

def loadROIsfromMaskFile(mask_file):      # ------------------------------------------------------ read Mask file

    if mask_file is None:
        ROIs = []
        return ROIs             # there is no mask file

    if os.path.isfile(mask_file):  # if mask file is there, try to load ROIs
        try:    # ------ mask file may be corrupt
            cf = open(mask_file, 'r')  # read mask file
            ROItuples = cPickle.load(cf)  # list of 4 tuple sets describing rectangles on the image
            cf.close()
        except:
            statbar.SetStatusText('Mask failed to load')
            winsound.Beep(600, 200)
            return False

    # ------------------------------------------------------------------------------------------ make gbl.ROIs
    ROIs = []
    for roi in ROItuples:  # complete each rectangle by adding first coordinate to end of list
        roiList = []  # clear for each rectangle
        for coordinate in roi:  # add each coordinate to the list for the rectangle
            roiList.append(coordinate)
        roiList.append(roi[0])
        ROIs.append(roiList)  # add the rectangle lists to the list of ROIs

    return ROIs

def makeMaskFrames(ROIs, size):

    # creates a transparent frame (2D)
    # draws the ROIs on the frame  &  returns the frame
    # mask

    # ---------------------------------------------------------------------------------------- create transparent frame
    npsize = (size[1], size[0])                     # opencv and np use opposite order
    mask_frame = np.ones(npsize, np.uint8)          # binary frame for creating mask

    if not ROIs: ROIs = []
    # ---------------------------------------------------------------------------------------- draw ROIs in red channel
    for roi in ROIs:
        for count in range(0, 4):
            cv2.line(mask_frame, roi[count], roi[count + 1], 0, line_thickness)        # zeros in regions that will be masked, ones in regions that won't

    mask = np.dstack((mask_frame, mask_frame, mask_frame))           # stacks 3 mask_frames so each color has ROIs that won't be covered by other colors
    mask = mask.astype(np.uint8)
    redmask = np.dstack(((1-mask_frame)*255, np.zeros(npsize, np.uint8), np.zeros(npsize, np.uint8)))   # applies mask to red only

    return mask, redmask

def pydatetime2wxdatetime(pydt):  # ---------------------- convert python datetime.datetime to wx.datetime
    dt_iso = pydt.isoformat()
    wxdt = wx.DateTime()
    wxdt.ParseISOCombined(dt_iso, sep='T')
    return wxdt

def string2wxdatetime(strdt):  # ---------------------------------------- convert string to wx.datetime
    wxdt = wx.DateTime()
    wxdt.ParseDateTime(strdt)

    chkYear = wxdt.GetYear()             # two-digit years will cause problems later.    # TODO: better way to handle 2-digit year problems?
    thisYear = wx.DateTime.Now()
    thisYear = thisYear.GetYear()
    if chkYear < 1900:
        if chkYear < (thisYear - 2000) :
            wxdt.SetYear(chkYear + 2000)
        else:
            wxdt.SetYear(chkYear + 1900)

    return wxdt                     ###### -1 year fixed

def wxdatetime2timestring(datetime):
    strdt = datetime.FormatISOTime()
    return strdt

def get_DateTime(date, time):   #---------------------------------- convert string date and string time to wx.datetime
    date = date.GetValue()
    time = time.GetValue(as_wxTimeSpan=True)
    wxdt = date.AddTS(time)
    return wxdt                                             # return changes the date!  ???


def del_started_item(theList, mon_ID):
    try:
        for count in range(0, len(theList)):
            if theList[count][0] == mon_ID:
                del theList[count]

            print('pause')                                                                                                              ###### debug
    except: pass