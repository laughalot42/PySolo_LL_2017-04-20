#   There are three types of configuration parameter storage used:
#       1. ConfigParser configuration file which is loaded into cfg_obj    - involves I/O to disk (slow)
#               cfg_Obj is handled in the Configuration Class
#       2. Configuration dictionary in the global gbl.cfg_dict list    - more convenient representation of whole configuration
#       3. Global variables  (gbl)    - easy to reference variables that don't affect the dictionary until applied
#


# ----------------------------------------------------------------------------   Imports
import wx                               # GUI controls
import os                               # system controls
from os.path import expanduser          # get user's home directory
import ConfigParser                     # configuration file handler
import wx.lib.newevent                  # mouse click event handling functions
import pysolovideoGlobals as gbl


# --------------------------------------------------------------------- configuration functions available to all modules
#   The following functions transfer values from one type of storage to another:



def cfg_nicknames_to_dicts():
    gbl.cfg_dict[0]['monitors'] = gbl.monitors
#    gbl.cfg_dict[0]['webcams'] = gbl.webcams
    gbl.cfg_dict[0]['thumb_size'] = gbl.thumb_size
    gbl.cfg_dict[0]['thumb_fps'] = gbl.thumb_fps
    gbl.cfg_dict[0]['cfg_path'] = gbl.cfg_path

def cfg_dict_to_nicknames():
    gbl.monitors = gbl.cfg_dict[0]['monitors']
#    gbl.webcams = gbl.cfg_dict[0]['webcams']
    gbl.thumb_size = gbl.cfg_dict[0]['thumb_size']
    gbl.thumb_fps = gbl.cfg_dict[0]['thumb_fps']
    gbl.cfg_path = gbl.cfg_dict[0]['cfg_path']

def mon_nicknames_to_dicts(mon_ID):
    gbl.cfg_dict[mon_ID]['mon_name'] = gbl.mon_name
    gbl.cfg_dict[mon_ID]['source_type'] = gbl.source_type
    gbl.cfg_dict[mon_ID]['source'] = gbl.source
    gbl.cfg_dict[mon_ID]['source_fps'] = gbl.source_fps
    gbl.cfg_dict[mon_ID]['preview_size'] = gbl.preview_size
    gbl.cfg_dict[mon_ID]['preview_fps'] = gbl.preview_fps
    gbl.cfg_dict[mon_ID]['line_thickness'] = gbl.line_thickness
    gbl.cfg_dict[mon_ID]['issdmonitor'] = gbl.issdmonitor
    gbl.cfg_dict[mon_ID]['start_datetime'] = gbl.start_datetime
    gbl.cfg_dict[mon_ID]['track'] = gbl.track
    gbl.cfg_dict[mon_ID]['track_type'] = gbl.track_type
    gbl.cfg_dict[mon_ID]['mask_file'] = gbl.mask_file
    gbl.cfg_dict[mon_ID]['data_folder'] = gbl.data_folder

def mon_dict_to_nicknames():                                                ###### received bad cfg_dict
    gbl.mon_name = gbl.cfg_dict[gbl.mon_ID]['mon_name']
    gbl.source_type = gbl.cfg_dict[gbl.mon_ID]['source_type']
    gbl.source = gbl.cfg_dict[gbl.mon_ID]['source']
    gbl.source_fps = gbl.cfg_dict[gbl.mon_ID]['source_fps']
    gbl.preview_size = gbl.cfg_dict[gbl.mon_ID]['preview_size']
    gbl.preview_fps = gbl.cfg_dict[gbl.mon_ID]['preview_fps']
    gbl.line_thickness = gbl.cfg_dict[gbl.mon_ID]['line_thickness']
    gbl.issdmonitor = gbl.cfg_dict[gbl.mon_ID]['issdmonitor']
    gbl.start_datetime = gbl.cfg_dict[gbl.mon_ID]['start_datetime']
    gbl.track = gbl.cfg_dict[gbl.mon_ID]['track']
    gbl.track_type = gbl.cfg_dict[gbl.mon_ID]['track_type']
    gbl.mask_file = gbl.cfg_dict[gbl.mon_ID]['mask_file']
    gbl.data_folder = gbl.cfg_dict[gbl.mon_ID]['data_folder']



# --------------------------------------------------------------------------------------------- Initialize Configuration
class Configuration(object):
    """
    Initiates program configuration
    Uses ConfigParser to store and retrieve


            options     section of configuration that pertains to program operation
            monitor#    section of configuration that pertains to video source #

        ----------  object attributes ---------------
            self.cfg_Obj       ConfigParser object
            cfg_dict       list of dictionaries containing all config parameters and their values, indexed on 'section, key'
                                    cfg_dict[0] contains options
                                    cfg_dict[n] where n is > 0 contains parameters for monitor n
            self.filePathName   the path and name of the configuration file
            self.opt_keys       list of configuration option keys
            self.mon_keys       list of configration monitor keys

        ----------  functions -----------------------
            cfgOpen()                       reads configuration file
            cfgSaveAs()                     gets file path and name from user and saves
            cfg_to_dicts()                  creates a configuration dictionary for quicker access to configuration parameters
            dict_to_cfg_obj()             saves dictionary to ConfigParser object
            getValue(section, key)          gets configuration value and converts it into the correct type
            setValue(section, key, value)   sets the value for a configuration parameter and updates dictionary
    """

    def __init__(self, parent, possiblePathName=None):
        """
        Initializes the configuration.
        """
        if possiblePathName is None:  possiblePathName = gbl.cfg_path
        self.parent = parent
        self.assignKeys()

    # ------------------------------------------------------ make sure the expected file exists or create a default file
        if possiblePathName == '' :
            self.defaultDir = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files') # define a default output directory
            possiblePathName = os.path.join(self.defaultDir, 'pysolo_video.cfg')    # and filename

        self.filePathName = self.cfgGetFilePathName(parent, possiblePathName)   # allow user to select a different configuration
                                                                                # cancelling will leave defaults in place

        if self.filePathName is not None:
            self.loadConfigFile(self.filePathName)              # load the configuration file
        else:
            self.filePathName = 'None Selected'
            self.cfg_Obj = ConfigParser.RawConfigParser()       # create a ConfigParser object for when it's time to save
            # just keep using the global variables until the user saves the file

    def assignKeys(self):        # -------------------------------------------------------------- configuration keywords

        self.opt_keys = ['monitors',        # number of monitors in the configuration
#                         'webcams',         # number of available webcams
                         'thumb_size',      # size to use for thumbnails
                         'thumb_fps',        # speed to use for thumbnails
                         'cfg_path']        # folder where configuration file is kept

        self.mon_keys = ['mon_name',        # name of monitor
                         'source_type',      # type of source (webcam = 0, video = 1, folder of images = 2)
                         'source',          # source file or webcam identifier
                         'source_fps',       # speed of video
                         'issdmonitor',     # is sleep deprivation monitor
                         'preview_size',    # size to use for full size video display
                         'preview_fps',     # speed to use for full size video display
                         'line_thickness',   # thickness of line around ROIs
                         'start_datetime',  # date and time experiment started
                         'track',           # track this monitor or not?
                         'track_type',       # type of tracking to be used
                         'mask_file',        # contains ROI coordinates
                         'data_folder']      # folder where output should be saved

    def cfgGetFilePathName(self, parent, possiblePathName=''):  # ----------------------------  get config file path & name
        """
        Lets user select or create a config file, and makes sure it is valid
        """
        # if directory or file name are invalid, start file dialog

        if not(os.path.isfile(possiblePathName)):

            wildcard = "PySolo Video config file (*.cfg)|*.cfg|" \
                       "All files (*.*)|*.*"  # adding space in here will mess it up!

            dlg = wx.FileDialog(parent,
                                message="Open configuration file ...",
                                defaultDir=gbl.cfg_path,
                                wildcard=wildcard,
                                style=wx.OPEN
                                )

            if dlg.ShowModal() == wx.ID_OK:                         # show the file browser window
                self.filePathName = dlg.GetPath()                   # get the filepath from the save dialog
            else:
                self.filePathName = None                            # no filename was selected

            dlg.Destroy()
        else:                                                   # supplied filename was valid so use it
            self.filePathName = possiblePathName

        if self.filePathName is not None:
            gbl.cfg_dict[0]['cfg_path'] = gbl.cfg_path = os.path.split(self.filePathName)[0]    # this file's path
        else:
            gbl.cfg_dict[0]['cfg_path'] = gbl.cfg_path = os.path.join(expanduser('~'), 'Documents', 'PySolo_Files')      # a default path

        return self.filePathName

    def dict_to_cfg_Obj(self):  # ----------------------------------------------- use dictionary to build cfg object
        """
        Creates ConfigParser object using cfg_dict values.
        """
        # update configuration object with current config dictionary
        if not self.cfg_Obj.has_section('Options'):  # make sure the options section exists in the cfg object
            self.cfg_Obj.add_section('Options')

        for key in self.opt_keys:  # add parameters to options section
            self.cfg_Obj.set('Options', key, gbl.cfg_dict[0][key])

        gbl.monitors = gbl.cfg_dict[0]['monitors']
        for gbl.mon_ID in range(1, gbl.monitors + 1):  # for each monitor make sure the monitor section exists in cfg_obj
            mon_dict_to_nicknames()
            if not self.cfg_Obj.has_section(gbl.cfg_dict[gbl.mon_ID]['mon_name']):
                self.cfg_Obj.add_section(gbl.cfg_dict[gbl.mon_ID]['mon_name'])

            for key in self.mon_keys:  # add parameters to this monitor section              ###################  - this is where date(2) = 1970
                self.cfg_Obj.set(gbl.cfg_dict[gbl.mon_ID]['mon_name'], key, gbl.cfg_dict[gbl.mon_ID][key])

    def cfg_to_dicts(self):  # ---------------------------------------  use config parser object to update dictionary
        """
        Create list of dictionaries from cfg for easier lookup of configuration info.
        First element [0] contains Options.
        Remaining element's indices indicate monitor number.
        """

#        gbl.webcams_inuse = []  # webcam names will be added to list and counted
        # ------------------------------------------------------------------------------------------------------ Options
        if not self.cfg_Obj.has_section('Options'):         # make sure the options section exists in the cfg object
            self.cfg_Obj.add_section('Options')

        for key in self.opt_keys:  # fill dictionary with project parameters
            if self.cfg_Obj.has_option('Options', key):         # otherwise just leave the dictionary option as is
                gbl.cfg_dict[0][key] = self.getValue('Options', key)

        # ----------------------------------------------------------------------------------------------------- Monitors
        gbl.monitors = gbl.cfg_dict[0]['monitors'] = len(self.cfg_Obj._sections) -1        # item 0 is options, not a monitor

        dictSize = len(gbl.cfg_dict)                        # need to add a new dictionaries for any new monitors
        if gbl.monitors >= dictSize:
            for gbl.mon_ID in range(dictSize, gbl.monitors + 1):
                gbl.cfg_dict.append({})

        # --------------------------------------------------------------------------------------- add values to cfg_dict
        for gbl.mon_ID in range(1, gbl.monitors + 1):       # update dictionary using cfg_object values
            gbl.mon_name = gbl.cfg_dict[gbl.mon_ID]['mon_name'] = 'Monitor%d' % gbl.mon_ID

            for key in self.mon_keys:
                if self.cfg_Obj.has_option(gbl.mon_name,key):
                    gbl.cfg_dict[gbl.mon_ID][key] = self.getValue(gbl.mon_name, key)  # copy config info into dictionary
                else:
                    gbl.cfg_dict[gbl.mon_ID][key] = 0               # if key not in cfg_obj, fill in with zero

#            if gbl.source[0:6] == 'Webcam':  # count the number of webcams
#                gbl.webcams_inuse.append(gbl.mon_name)
        print('check')
#        gbl.webcams = len(gbl.webcams_inuse)


    def loadConfigFile(self, filePathName=''):    # --------------------------------  Load config from file
        """ --------------------------------------------------------------------- create the ConfigParser object """
        self.filePathName = filePathName
        self.cfg_Obj = ConfigParser.RawConfigParser()               # create a ConfigParser object

        try:  # -------  file could be corrupted
            self.cfg_Obj.read(self.filePathName)               # read the selected configuration file
        except:                                             # otherwise just use the default config dictionary as is
            print('Invalid configuration file input.  Creating default.')
            self.dict_to_cfg_Obj()                       # apply the default configuration to the cfg object
            self.cfgSaveAs(self.parent)                         # save the cfg object to a cfg file

        self.cfg_to_dicts()                                # update the config dictionary from the config file

    def cfgSaveAs(self, parent):  # --------------------------------------------------------  Save config file
        """
        Dictionary should be up to date before calling this function.
        Lets user select file and path where configuration will be saved. Saves using ConfigParser .write()
        """
        for section in self.cfg_Obj.sections():      # delete all monitors from configuration object
            if section != 'Options':                        # keep the Options section
                self.cfg_Obj.remove_section(section)

        self.dict_to_cfg_Obj()                              # and recreate monitor sections from dictionary

        # get a filename for the configuration file
        wildcard = "PySolo Video config file (*.cfg)|*.cfg|" \
                   "All files (*.*)|*.*"  # adding space in here will mess it up!

        dlg = wx.FileDialog(parent,
                            message = "Save configuration as file ...",
                            defaultDir = gbl.cfg_path,
                            wildcard = wildcard,
                            style = (wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                            )

        # save configuration to selected file
        if dlg.ShowModal() == wx.ID_OK:  # show the file browser window
            self.filePathName = dlg.GetPath()  # get the path from the save dialog

            gbl.cfg_path = os.path.split(self.filePathName)[0]

            with open(self.filePathName, 'wb') as configfile:
                self.cfg_Obj.write(configfile)  # ConfigParser write to file

        else:
            return False  # failed to save configuration

        dlg.Destroy()
        configfile.close()

        return True

    def wantToSave(self):
        dlg = wx.MessageDialog(self.parent, 'Do you want to save the current configuration?',
                               style=wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION | wx.CENTRE)
        answer = dlg.ShowModal()
        dlg.Destroy()
        return answer


    def getValue(self, section, key):       # ------------- get cfg object string and convert into value of correct type
        """
        get value from config file based on section and keyword
        Do some sanity checking to return tuple, integer and strings, datetimes, as required.
        """
        if  not self.cfg_Obj.has_option(section, key):                       # does option exist?
            r = None
            return r

        r = self.cfg_Obj.get(section, key)

        r = gbl.correctType(r, key)

        return r

    def setValue(self, section, key, value):        # ---------------------------  add or change cfg value in dictionary
        """
        changes or adds a configuration value in config file
        """
        if not self.cfg_Obj.has_section(section):
            self.cfg_Obj.add_section(section)
        if not self.cfg_Obj.has_option(section, key):
            self.cfg_Obj.set(section, key)

        self.cfg_Obj.set(section, key, value)                   # get dictionary list index number from section name
        element_no = section[7:8]
        if element_no == '': element_no = '0'

        gbl.cfg_dict[int(element_no)][key] = value




# ------------------------------------------------------------------------------------------ Stand alone test code

class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

    # get configuration parameters and create dictionaries for each section
        config = Configuration(self)


        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.



