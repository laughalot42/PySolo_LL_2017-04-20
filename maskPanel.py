import wx                               # GUI controls
import os
import winsound
import wx.lib.masked as masked
from filebrowsebutton_LL import FileBrowseButton, DirBrowseButton
from wx.lib.masked import NumCtrl

import configurator as cfg
import videoMonitor as VM
import pysolovideoGlobals as gbl

# TODO: datetimes are not working.  they look fine on the maskpanel, but are wrong in the configuration
#                   they change randomly when unrelated statements are executed.
# TODO: preview panel too large for actual image
# TODO: removed live camera option.  tracking doesn't stop because camera doesn't stop.

class maskMakerPanel(wx.Panel):
    #
    # cfg settings won't change unless configuration is changed, which will kill this object
    # mon settings may change due to threading, so these settings will be assigned here and cfg_dict updated after any changes
    #

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, wx.ID_ANY, size=(640,480), name=gbl.mon_name)

        self.parent =           parent
        self.mon_ID =           gbl.mon_ID
        cfg.cfg_dict_to_nicknames()       # set all nicknames for this monitor.  use these so changes will be saved on page change.
        cfg.mon_dict_to_nicknames()
        self.start_datetime =   gbl.start_datetime
        self.mon_name =         gbl.mon_name
        self.preview_size =      gbl.preview_size
        self.preview_fps =       gbl.preview_fps
        self.line_thickness =    gbl.line_thickness
        self.source =           gbl.source
        self.monitors =         gbl.monitors
        self.data_folder =      gbl.data_folder
        self.source_type =      gbl.source_type
        self.source_fps =       gbl.source_fps
        self.issdmonitor =      gbl.issdmonitor
        self.track_type =       gbl.track_type
        self.track =            gbl.track
        self.mask_file =        gbl.mask_file

        self.widgets()
        self.binders()
        self.sizers()

    def widgets(self):

        # TODO: get coordinate values by clicking the mouse
        # TODO: add PySolo single ROI drawing

    # ------------------------------------------------------------------------------------------------------------ Title
        self.title = wx.StaticText(self, -1, "\n %s" % self.mon_name)  # title
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.title.SetFont(font)

    # -------------------------------------------------------------------------------------------- video display options
        self.previewPanel = VM.monitorPanel(self, mon_ID=self.mon_ID, panelType='preview', loop=True)

        self.previewSizeLabel = wx.StaticText(self, wx.ID_ANY, 'frame size =')           # ------ preview frame size
        self.previewSize = wx.TextCtrl (self, wx.ID_ANY, str(self.preview_size),
                                            style=wx.TE_PROCESS_ENTER, name='previewSize')

        self.previewFPSLabel = wx.StaticText(self, wx.ID_ANY, 'preview fps =')         # --------- preview video fps
        self.previewFPS = wx.TextCtrl(self, wx.ID_ANY, str(self.preview_fps),
                                              style=wx.TE_PROCESS_ENTER, name='previewFPS')

        self.lineThicknessLabel = wx.StaticText(self, wx.ID_ANY, 'ROI line thickness =')  # --------- preview ROI line thickness
        self.lineThickness = wx.TextCtrl(self, wx.ID_ANY, str(self.line_thickness),
                                              style=wx.TE_PROCESS_ENTER, name='lineThickness')

        # ---------------------------------------------------------------------------------------  Save Configuration Button
        self.btnSaveCfg = wx.Button(self, wx.ID_ANY, label='Save Configuration', size=(130, 25))
        if self.source != '':
            self.btnSaveCfg.Enable(True)  # don't allow save if no source is selected
        else:
            self.btnSaveCfg.Enable(False)

            # ---------------------------------------------------------------------------------------  Delete Monitor Button
        self.btnRemoveMonitor = wx.Button(self, wx.ID_ANY, label='Delete Monitor', size=(130, 25))
        if self.monitors == 1:  # don't allow last monitor to be deleted
            self.btnRemoveMonitor.Enable(False)
        else:
            self.btnRemoveMonitor.Enable(True)

        # -------------------------------------------------------------------------------------------------------- source
        self.txt_source = wx.StaticText(self, wx.ID_ANY, "Source:  ")
        if self.source is not None:
            self.currentSource = wx.TextCtrl(self, wx.ID_ANY, self.source, style=wx.TE_READONLY)  # get current source
        else:
            self.currentSource = wx.TextCtrl(self, wx.ID_ANY, 'None Selected', style=wx.TE_READONLY)  # get current source

            # -------------------------------------------------------------------------------  Webcam selection combobox
        #        if len(gbl.webcams_inuse) >= gbl.webcams:                          # only one webcam implemented at this time
        #            self.WebcamsList = ['No more webcams available.']
        #        else:
        #        self.WebcamsList = ['Webcam %s' % (int(w) + 1) for w in range(gbl.webcams)]
#        self.WebcamsList = ['Webcam 1']

        # ------------------------------------------------------------------------------------------- source options
        self.source_IDs = [wx.ID_ANY, wx.ID_ANY, wx.ID_ANY]
        self.sources = ['placeholder for webcams',
#                         (wx.ComboBox(self, id=self.source_IDs[0], choices=self.WebcamsList, name='sources0',  # webcam
#                                     style=wx.EXPAND | wx.CB_DROPDOWN | wx.CB_READONLY | wx.CB_SORT)),
                        (FileBrowseButton(self, id=self.source_IDs[1],  # video file
                                          name='sources1', buttonText='Browse',
                                          toolTip='Type filename or click browse to choose video file',
                                          dialogTitle='Choose a video file',
                                          startDirectory=self.data_folder,
                                          wildcard='*.*', style=wx.ALL, changeCallback=self.onChangeSource1)),
                        (DirBrowseButton(self, id=self.source_IDs[2], name='sources2',  # folder of images
                                         style=wx.DD_DIR_MUST_EXIST,
                                         startDirectory=self.data_folder, changeCallback=self.onChangeSource2))
                        ]

        # --------------------------------------------------------------------------------  source type radio buttons
#        self.rbs = [(wx.RadioButton(self, wx.ID_ANY, 'Camera', style=wx.RB_GROUP)),
        self.rbs = ['placeholder for camera radiobutton',
                    (wx.RadioButton(self, wx.ID_ANY, 'File')),
                    (wx.RadioButton(self, wx.ID_ANY, 'Folder'))
                    ]

        # ------------------------------------------------------------------------------------------------ mask file browser
        wildcard = 'PySolo Video mask file (*.msk)|*.msk|' \
                   'All files (*.*)|*.*'  # adding space in here will mess it up!

        if self.mask_file is None:
            startDirectory = self.data_folder  # Default directory for file dialog startup
            initialValue = 'None Selected'
        elif os.path.isfile(self.mask_file):
            startDirectory = os.path.split(self.mask_file)[0]  # Default directory for file dialog startup
            initialValue = self.mask_file
        else:
            startDirectory = self.data_folder  # Default directory for file dialog startup
            initialValue = 'None Selected'

        self.pickMaskBrowser = FileBrowseButton(self, id=wx.ID_ANY,
                                                labelText='Mask File:         ', buttonText='Browse',
                                                toolTip='Type filename or click browse to choose mask file',
                                                dialogTitle='Choose a mask file',
                                                startDirectory=startDirectory, initialValue=initialValue,
                                                wildcard=wildcard, style=wx.ALL,
                                                changeCallback=self.onMaskBrowse,
                                                name='pickMaskBrowser')

        # -------------------------------------------------------------------------------------------- output folder browser
        if self.data_folder is None:
            startDirectory = self.data_folder = gbl.cfg_path  # Default directory is config directory
        elif os.path.isdir(self.data_folder):
            startDirectory = self.data_folder               # Default directory from config file
        else:
            startDirectory = self.data_folder = gbl.cfg_path  # Default directory is config directory

        self.pickOutputBrowser = DirBrowseButton(self, id=wx.ID_ANY,
                                                 style=wx.TAB_TRAVERSAL,
                                                 labelText='Output Folder:  ',
                                                 dialogTitle='Choose an output folder',
                                                 startDirectory=self.data_folder,
                                                 value=gbl.data_folder,
                                                 changeCallback=self.onChangeOutput,
                                                 name='pickOutputBrowser')

   # ------------------------------------------------------------------------------------------------- video attributes
        self.sourceFPSLabel = wx.StaticText(self, wx.ID_ANY, 'Speed (fps) =')           # ---------------- source fps
        self.sourceFPS = wx.TextCtrl (self, wx.ID_ANY, str(self.source_fps),
                                              style=wx.TE_PROCESS_ENTER, name='sourceFPS')

        self.txtDate = wx.StaticText(self, wx.ID_ANY, "Date: ")                        # ---------------- start date
        self.startDate = wx.DatePickerCtrl(self, wx.ID_ANY, dt=self.start_datetime,
                                            style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY | wx.TE_PROCESS_ENTER, name='start_date')


        self.txtTime = wx.StaticText(self, wx.ID_ANY, 'Time (24-hr): ')                 # ---------------- start time
        self.btnSpin = wx.SpinButton(self, wx.ID_ANY, wx.DefaultPosition, (-1, 20), wx.SP_VERTICAL)
        starttime = gbl.wxdatetime2timestring(self.start_datetime)
        self.startTime = masked.TimeCtrl(self, wx.ID_ANY, value=starttime,
                                          name='time: \n24 hour control', fmt24hr=True,
                                          spinButton=self.btnSpin, style=wx.TE_PROCESS_ENTER)

        self.instruction = wx.StaticText(self, wx.ID_ANY,
                'Clicking on the video will change top left coordinate values.')
        """
    # ------------------------------------------------------------------------------------------------ activate tracking
        self.trackBox = wx.CheckBox(self, wx.ID_ANY, 'Activate Tracking')
        self.trackBox.Enable(True)
        self.trackBox.SetValue(str(self.track))

    # ---------------------------------------------------------------------------------------- sleep deprivation monitor
        self.isSDMonitor = wx.CheckBox(self, wx.ID_ANY, 'Sleep Deprivation Monitor')
        self.isSDMonitor.Enable(True)
        self.isSDMonitor.SetValue(str(self.issdmonitor))

    # ---------------------------------------------------------------------------------------------------- tracking type
        self.trackChoice = [(wx.RadioButton(self, wx.ID_ANY, 'Activity as distance traveled', style=wx.RB_GROUP)),
                            (wx.RadioButton(self, wx.ID_ANY, 'Activity as midline crossings count')),
                            (wx.RadioButton(self, wx.ID_ANY, 'Only position of flies'))]

        for count in range(0, len(self.trackChoice)):
            self.trackChoice[count].Enable(True)
            if self.trackType == count:
                self.trackChoice[count].SetValue(True)
            else:
                self.trackChoice[count].SetValue(False)
        """

        # -------------------------------------------------------------------------------------------- instructional diagram
        self.diagram = wx.Bitmap(os.path.join(gbl.exec_dir, 'maskmakerdiagram.bmp'), wx.BITMAP_TYPE_BMP)
        self.diagramctl = wx.StaticBitmap(self, -1, self.diagram)

        # --------------------------------------------------------------------------------------- ROI Coordinates Input Grid
        self.rowLabels = [wx.StaticText(self, -1, ' '),
                           wx.StaticText(self, -1, 'Number'),  # row labels
                           wx.StaticText(self, -1, 'Top Left'),
                           wx.StaticText(self, -1, 'Span'),
                           wx.StaticText(self, -1, 'Gap'),
                           wx.StaticText(self, -1, 'Tilt')
                           ]
        self.X = []
        self.Y = []
        self.X.append(wx.StaticText(self, wx.ID_ANY, "Columns (X)"))  # column header for columns
        self.Y.append(wx.StaticText(self, wx.ID_ANY, "Rows (Y)"))  # column header for rows
        for cnt in range(0, 5):
            self.X.append(NumCtrl(self, wx.ID_ANY, 0))
            self.Y.append(NumCtrl(self, wx.ID_ANY, 0))

        # ------------------------------------------------------------------------------------ mask generator & save buttons
        self.btnMaskGen = wx.Button(self, wx.ID_ANY, label="Generate Mask", size=(130, 25))
        self.btnMaskGen.Enable(True)

        self.btnSaveMask = wx.Button(self, wx.ID_ANY, label="Save Mask", size=(130, 25))
        self.btnSaveMask.Enable(True)

    def binders(self):  # -------------------------------------------------------------------------------- Event Binders

#        self.Bind(wx.EVT_RADIOBUTTON,       self.onChangeRb,            self.rbs[0])
        self.Bind(wx.EVT_RADIOBUTTON,       self.onChangeRb,            self.rbs[1])
        self.Bind(wx.EVT_RADIOBUTTON,       self.onChangeRb,            self.rbs[2])
#        self.Bind(wx.EVT_RADIOBUTTON,       self.onChangeTrackType,     self.trackChoice[0])
#        self.Bind(wx.EVT_RADIOBUTTON,       self.onChangeTrackType,     self.trackChoice[1])
#        self.Bind(wx.EVT_RADIOBUTTON,       self.onChangeTrackType,     self.trackChoice[2])
        self.Bind(wx.EVT_BUTTON,            self.onSaveCfg,             self.btnSaveCfg)
        self.Bind(wx.EVT_BUTTON,            self.onRemoveMonitor,       self.btnRemoveMonitor)
        self.Bind(wx.EVT_BUTTON,            self.onMaskGen,             self.btnMaskGen)
        self.Bind(wx.EVT_BUTTON,            self.onSaveMask,            self.btnSaveMask)
#        self.Bind(wx.EVT_COMBOBOX,          self.onChangeSource0,       self.sources[0])
        self.Bind(wx.EVT_TEXT_ENTER,        self.onChangeSource1,       self.sources[1])
        self.Bind(wx.EVT_TEXT_ENTER,        self.onChangeSource2,       self.sources[2])
        self.Bind(wx.EVT_TEXT_ENTER,        self.onChangeSourceFPS,     self.sourceFPS)
        self.Bind(wx.EVT_TEXT_ENTER,        self.onChangePreviewSize,   self.previewSize)
        self.Bind(wx.EVT_TEXT_ENTER,        self.onChangePreviewFPS,    self.previewFPS)
        self.Bind(wx.EVT_TEXT_ENTER,        self.onChangeLineThickness, self.lineThickness)
        self.Bind(wx.EVT_TEXT_ENTER,        self.onChangeOutput,        self.pickOutputBrowser)
        self.Bind(wx.EVT_TEXT_ENTER,        self.onMaskBrowse,          self.pickMaskBrowser)

        # date and time fields require special event handling
        self.startDate.Bind(wx.EVT_KEY_UP, self.whichKey)
        self.Bind(wx.EVT_NAVIGATION_KEY, self.whichField)

    def sizers(self):
        self.mainSizer              = wx.BoxSizer(wx.HORIZONTAL)                                #   Main
        self.right_Sizer              = wx.BoxSizer(wx.VERTICAL)                                #   |   right_
        self.sb_selectsource        = wx.StaticBox(self, wx.ID_ANY, 'Select Source')            #   |   |   source selection text
        self.sbSizer_selectsource   = wx.StaticBoxSizer(self.sb_selectsource, wx.VERTICAL)      #   |   |   select box
        self.sourceGridSizer        = wx.FlexGridSizer(5, 2, 2, 2)                              #   |   |   |   |   grid of rbs & sources
        self.sb_maskNoutput         = wx.StaticBox(self, wx.ID_ANY, '')                         #   |   |   monitor selection text
        self.sbSizer_maskNoutput    = wx.StaticBoxSizer(self.sb_maskNoutput, wx.VERTICAL)       #   |   |   |   select box
        self.maskBrowserSizer       = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   |   |   mask browser
        self.outputDirSizer         = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   |   |   output dir browser
        self.right_MiddleSizer        = wx.BoxSizer(wx.HORIZONTAL)                              #   |   |   right_ middle
        self.sb_timeSettings        = wx.StaticBox(self, wx.ID_ANY, 'Time Settings')            #   |   |   |   time settings text
        self.sbSizer_timeSettings   = wx.StaticBoxSizer(self.sb_timeSettings, wx.VERTICAL)      #   |   |   |   time settings box
        self.dt_Sizer               = wx.FlexGridSizer(3, 2, 2, 2)                              #   |   |   |   |   |   datetimefps widgets
#        self.sb_trackingParms       = wx.StaticBox(self, wx.ID_ANY, 'Tracking Parameters')     #   |   |   |   tracking parameters text
#        self.sbSizer_trackingParms  = wx.StaticBoxSizer(self.sb_trackingParms, wx.VERTICAL)    #   |   |   tracking parameters box
#        self.trackOptionsSizer      = wx.BoxSizer(wx.VERTICAL)                                 #   |   |   |   |   |   tracking options widgets
        self.calcbox_sizer          = wx.BoxSizer(wx.VERTICAL)                                  #   |   |   |   |   |   calculations widgets
        self.right_BottomSizer        = wx.BoxSizer(wx.HORIZONTAL)                              #   |   |   right_ bottom
        self.diagramSizer           = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   |   diagram
        self.tableSizer             = wx.FlexGridSizer(6, 3, 1, 5)                              #   |   |   |   table
        self.button_sizer           = wx.BoxSizer(wx.VERTICAL)                                  #   |   |   |   buttons column

        self.left_Sizer             = wx.BoxSizer(wx.VERTICAL)                                  #   |   left_
        self.titleSizer             = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   Monitor title
        self.saveNdeleteSizer       = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   save and delete buttons
        self.videoSizer             = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   video panel
        self.settingsSizer          = wx.BoxSizer(wx.HORIZONTAL)                                #   |   |   preview settings


        # ------------------------------------------------------------------------------ left_ Side  Video Preview Panel
        #                                      this sizer saves the spot in left_Sizer in case video is changed later
        self.videoSizer.Add(self.previewPanel,                          1, wx.ALL | wx.ALIGN_TOP | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)

        self.settingsSizer.AddSpacer(5)
        self.settingsSizer.Add(self.previewSizeLabel,                   0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewSize,                        0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.AddSpacer(5)
        self.settingsSizer.Add(self.previewFPSLabel,                    0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.previewFPS,                         0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.AddSpacer(5)
        self.settingsSizer.Add(self.lineThicknessLabel,                 0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.Add(self.lineThickness,                      0, wx.ALL | wx.EXPAND, 5)
        self.settingsSizer.AddSpacer(5)

        self.saveNdeleteSizer.Add(self.btnSaveCfg,                      1, wx.ALL, 5)
        self.saveNdeleteSizer.Add(self.btnRemoveMonitor,                1, wx.ALL, 5)


        self.left_Sizer.Add(self.title,                                 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 1)
        self.left_Sizer.Add(self.videoSizer,                            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        self.left_Sizer.Add(self.settingsSizer,                         0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        self.left_Sizer.Add(self.saveNdeleteSizer,                      0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND | wx.ALIGN_BOTTOM, 5)
# ------------------------------------------------------------------------------------------------------------right_ SIDE
    # -------------------------------------------------------------------------------------------- select source box

        self.sourceGridSizer.Add(self.txt_source,                       0, wx.ALL | wx.LEFT,     5)
        self.sourceGridSizer.Add(self.currentSource,                    1, wx.ALL | wx.EXPAND,   5)

        for count in range(1, len(self.rbs)):                   # -------- source 0 (webcams) is not being used
            self.sourceGridSizer.Add(self.rbs[count],                   0, wx.ALL | wx.LEFT | wx.ALIGN_CENTER_VERTICAL, 5)
            self.sourceGridSizer.Add(self.sources[count],               1, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 5)

        self.sbSizer_selectsource.Add(self.sourceGridSizer,             1, wx.ALL | wx.EXPAND,   5)

        # -------------------------------------------------------------------------- mask browser, output folder browser
        self.sbSizer_maskNoutput.Add(self.pickMaskBrowser,              1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)
        self.sbSizer_maskNoutput.Add(self.pickOutputBrowser,            1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 5)

        # --------------------------------------------------------------------------------- time, tracking, buttons row
        # ------------------------------------------------------------------------ date / time / fps grid
        self.dt_Sizer.Add(self.txtDate,                                 0, wx.ALL, 5)
        self.dt_Sizer.Add(self.startDate,                               0, wx.ALL, 5)

        self.dt_Sizer.Add(self.txtTime,                                 0, wx.ALL, 5)
        self.addWidgets(self.dt_Sizer, [self.startTime, self.btnSpin])

        self.dt_Sizer.Add(self.sourceFPSLabel,                          0, wx.ALL, 5)
        self.dt_Sizer.Add(self.sourceFPS,                               0, wx.ALL, 5)

        # fill video start date and time box
        self.sbSizer_timeSettings.Add(self.dt_Sizer,                    0, wx.ALL, 5)

        """
        # -------------------------------------------------------------------------------- tracking options
        self.trackOptionsSizer.Add(self.trackBox,                       0, wx.ALL | wx.ALIGN_LEFT, 5)
        self.trackOptionsSizer.Add(self.isSDMonitor,                    0, wx.ALL | wx.ALIGN_LEFT, 5)

        for count in range(0, len(self.trackChoice)):
            self.calcbox_sizer.Add(self.trackChoice[count],             0, wx.ALL | wx.ALIGN_LEFT, 5)
        self.trackOptionsSizer.Add(self.calcbox_sizer,                  0, wx.ALL | wx.ALIGN_LEFT, 5)

        # fill tracking box
        self.sbSizer_trackingParms.Add(self.trackOptionsSizer,          0, wx.ALL, 5)
        """

        # fill middle row
        self.right_MiddleSizer.Add(self.sbSizer_timeSettings,           2, wx.ALL | wx.EXPAND, 5)
#        self.right_MiddleSizer.Add(self.sbSizer_trackingParms,          2, wx.ALL | wx.EXPAND, 5)
        self.right_MiddleSizer.Add(self.instruction,                    2, wx.ALL | wx.ALIGN_BOTTOM, 5)
        # ---------------------------------------------------------------------------------------------- mask generator
        self.diagramSizer.Add(self.diagramctl,                          0, wx.ALL | wx.ALIGN_CENTER, 2)

        # -------------------------------------------------------------------- Apply each row to the table
        for row in range(0, len(self.rowLabels)):
            self.tableSizer.Add(self.rowLabels[row],                    1, wx.ALL | wx.EXPAND, 5)  # column headers
            self.tableSizer.Add(self.X[row],                            1, wx.ALL | wx.EXPAND, 5)  # X column entries
            self.tableSizer.Add(self.Y[row],                            1, wx.ALL | wx.EXPAND, 5)  # Y column entries

        # -------------------------------------------------------------------------------------- button column
        self.button_sizer.Add(self.btnMaskGen,                          1, wx.ALL, 5)
        self.button_sizer.Add(self.btnSaveMask,                         1, wx.ALL, 5)

        # fill right_ bottom
        self.right_BottomSizer.Add(self.diagramSizer,                   0, wx.ALL | wx.ALIGN_CENTER, 2)
        self.right_BottomSizer.Add(self.tableSizer,                     0, wx.ALL | wx.ALIGN_CENTER | wx.EXPAND, 2)
        self.right_BottomSizer.Add(self.button_sizer,                   1, wx.ALL | wx.ALIGN_BOTTOM, 5)

        self.right_Sizer.Add(self.sbSizer_selectsource,                 1, wx.ALL | wx.EXPAND,   5)
        self.right_Sizer.Add(self.sbSizer_maskNoutput,                  1, wx.ALL | wx.EXPAND,   5)
        self.right_Sizer.Add(self.right_MiddleSizer,                    1, wx.ALL | wx.EXPAND,   5)
        self.right_Sizer.Add(self.right_BottomSizer,                    1, wx.ALL | wx.EXPAND,   5)

   # ------------------------------------------------------------------------------------------- right_ & left_ sides
        self.mainSizer.Add(self.left_Sizer,                             1, wx.ALL | wx.ALIGN_RIGHT | wx.EXPAND, 2)
        self.mainSizer.Add(self.right_Sizer,                            1, wx.ALL | wx.ALIGN_LEFT | wx.EXPAND, 2)

        self.SetSizer(self.mainSizer)
        self.Layout()
        print('check')

    def addWidgets(self, mainSizer ,widgets):       # ---------------------------------------  used for datetime widgets

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        for widget in widgets:
            if isinstance(widget, wx.StaticText):
                sizer.Add(widget,                           0, wx.ALL | wx.CENTER, 1),
            else:
                sizer.Add(widget,                           0, wx.ALL, 1)
        mainSizer.Add(sizer)

    def onRemoveMonitor(self, event):  # ------------------------------------------------------   Remove current monitor

        if self.monitors < 1:                                                    # don't remove the last monitor
            self.TopLevelParent.SetStatusText('Cannot remove last monitor.')
            winsound.Beep(600, 200)
            return False

        old_mon = self.mon_ID                          # keep track of monitor to be removed

        gbl.cfg_dict.pop(old_mon)                         # delete monitor from dictionary; renumbers list automatically

#        if self.source[0:6] == 'Webcam':                  # if needed change global copy of number of webcams
#            gbl.webcams -= 1  # change number of webcams
#            gbl.webcams_inuse.remove(self.mon_name)       # remove name from webcam list

        # ------------------------------------------------------------------------ reset higher numbered monitors' names
        for mon_count in range(old_mon, self.monitors):
            gbl.cfg_dict[mon_count]['mon_name'] = 'Monitor%d' % (mon_count)  # change monitor names
#            if gbl.cfg_dict[mon_count]['source'][0:6] == 'Webcam':
#                gbl.cfg_dict[mon_count]['source'][0:6] = 'Webcam%d' % mon_count    # rename webcam    ->  only 1 webcam currently supported

        gbl.monitors -= 1  # ------------------------------------------------------ Change global settings
        if old_mon > gbl.monitors:          # change current monitor number only if last monitor was deleted
            self.mon_ID = old_mon - 1

        gbl.mon_ID = self.mon_ID

        cfg.cfg_nicknames_to_dicts()       # -------------------------- update config dictionary to change # of monitors
        cfg.mon_dict_to_nicknames()         # ------------------------------------------------- get new monitor settings

        self.parent.repaginate()            # this will delete the notebook pages and recreate the notebook

    def onSaveCfg(self, event):
        cfg.cfg_nicknames_to_dicts()  # -------------------------------------------------- update config dictionary
        r = self.TopLevelParent.config.cfgSaveAs(self)
        if r:                                                               # TODO: progress indicator of some sort?
            self.TopLevelParent.SetStatusText('Configuration saved.')
        else:
            self.TopLevelParent.SetStatusText('Configuration not saved.')
        winsound.Beep(600, 200)

    def clearVideo(self):
        # don't save nicknames, you don't know whose been using them
        # -------------------------------------------------------------------------------------- stop old monitor panel  TODO: Update mask & settings
        try:    # ------ object may have been deleted earlier
            self.previewPanel.keepPlaying = False
            self.previewPanel.playTimer.Stop()
            self.previewPanel.Hide()                            # don't destroy the panel
        except:
            print('preview panel can''t be cleared.')
            pass

        self.videoSizer.Clear()

        gbl.del_started_item(gbl.timersStarted, self.mon_ID)  ###### for debugging

    def refreshVideo(self):
        self.clearVideo()
        self.previewPanel = VM.monitorPanel(self, mon_ID=self.mon_ID, panelType='preview', loop=True)        # make new monitor panel

        self.previewPanel.PlayMonitor()
        self.videoSizer.Add(self.previewPanel, 1, wx.ALL | wx.ALIGN_CENTER, 5)
        self.previewPanel.playTimer.Start(1000 / float(self.previewFPS.GetValue()))
        gbl.numberOfTimers = gbl.numberOfTimers +1
        self.videoSizer.SetMinSize(self.previewPanel.size)
        self.SetSizer(self.mainSizer)
        self.Layout()

        gbl.timersStarted.append([self.mon_ID, 'preview panel'])                                                                  ###### debug

    def whichKey(self, event):
            code = event.GetKeyCode()
            event.Skip()
            if code == 370 or code == 13:
                lastkey = 'Return'
                self.whichField(event, lastkey)
                return
            if code == 47:
                lastkey = '/'
                self.whichField(event, lastkey)
                return

    def whichField(self, event, lastKey='Nav'):     # ------ distributes control to correct function after navitation key is pressed
        whichObject = event.EventObject
        whichObjectstr = str(whichObject)
        whichObjectstr = whichObjectstr[1:9]

        if lastKey == 'Nav':                        # -----------   command event was triggered
            if whichObjectstr == 'maskPane':
                self.onChangeDateTime(event, 'start_date', 'Tab')

            elif whichObjectstr == 'TimeCtrl':
                if event.IsFromTab():
                    self.onChangeDateTime(event, 'start_time', 'Tab')
                else:
                    self.onChangeDateTime(event, 'start_time', 'Return')

            elif event.EventObject.Name == 'previewSize':
                self.onChangePreviewSize(event)
            elif event.EventObject.Name == 'previewFPS':
                self.onChangePreviewFPS(event)
            elif event.EventObject.Name == 'sourceFPS':
                self.onChangeSourceFPS(event)
            elif event.EventObject.Name == 'lineThickness':
                self.onChangeLineThickness(event)
            elif event.EventObject.Name == 'pickOutputBrowser':
                self.onChangeOutput(event)
            elif event.EventObject.Name == 'pickMaskBrowser':
                self.onMaskBrowse(event)

            elif whichObjectstr == 'BaseMask':
                event.Skip()

        elif lastKey == 'Return':
            if whichObjectstr == 'wx._cont':
                self.onChangeDateTime(event, 'start_date', 'Return')

        elif lastKey == '/':
            self.onChangeDateTime(event, 'start_date', lastKey)

        else:
            self.onChangeDateTime(event, whichObjectstr, lastKey)

    def onChangeDateTime(self, event, whichCtrl, lastKey):

        try:      # ------ bug in wxDateTimePickerCtrl: m_date not in sync occurs if month not changed
            stdate = self.startDate.GetValue()
        except:
            stdate = self.start_datetime

        sttime = self.startTime.GetValue(as_wxTimeSpan=True)

        #  update all datetime values
        self.start_datetime = gbl.start_datetime = gbl.cfg_dict[self.mon_ID]['start_datetime'] = stdate.AddTS(sttime)


        # -------- navigation for date & time controls
        if   lastKey == 'Return' and whichCtrl == 'start_date':
            self.startTime.SetFocus()                                      # done with date, proceed to time
        elif lastKey == 'Return' and whichCtrl == 'start_time':
            self.sourceFPS.SetFocus()                                       # done with time, proceed to fps
        if   lastKey == 'Tab'    and whichCtrl == 'start_date':
            EVT_RIGHT = wx.KeyEvent(47)                         # '/' moves focus to right in datepickerctrl
            self.startDate.HandleAsNavigationKey(EVT_RIGHT)
            self.startDate.Layout()
        elif lastKey == 'Tab'    and whichCtrl == 'start_time':
            EVT_RIGHT = wx.KeyEvent(47)                         # '/' moves focus to right in datepickerctrl
            self.startTime.HandleAsNavigationKey(EVT_RIGHT)

        print('check')

    def onChangeSourceFPS(self, event):
        input = gbl.correctType(self.sourceFPS.GetValue(), 'source_fps')
        if not (type(input) == int or type(input) == float):
            input = self.source_fps                         # don't change the value if input wasn't a number
            self.sourceFPS.SetValue(input)

        gbl.cfg_dict[self.mon_ID]['source_fps'] = gbl.source_fps = gbl.source_fps = input        # update self & cfg_dict
        self.startDate.SetFocus()

    def onChangeTrackType(self, event):
        gbl.cfg_dict[self.mon_ID]['track_type'] = gbl.track_type = self.track_type = event.Selection         # update self & cfg_dict

    def onChangeRb(self, event):
        RbSelected = event.EventObject.Label
        if RbSelected == 'Camera':                                              # update self source_type
            self.source_type = 0
        elif RbSelected == 'File':
            self.source_type = 1
        elif RbSelected == 'Folder':
            self.source_type = 2
        else:
            print('Invalid RB number in maskPanel.py.')

        if self.sources[self.source_type].GetValue() != '':                     # update self sources
            self.source = self.sources[self.source_type].GetValue()

        self.currentSource.SetValue(self.source)                                # update currentSource field
        gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source                # update cfg_dict
        gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type                # update cfg_dict

        self.refreshVideo()

    def onChangeSource0(self, event):                   # TODO: get calling object from event & combine the three onChangeSource functions
#        if gbl.cfg_dict[self.mon_ID]['source_type'] == 0:                    # if it was a webcam, remove from list
#            gbl.webcams_inuse.remove('Monitor%d' % self.mon_ID)                 # only one webcam implemented at this time
#            gbl.webcams -= 1

        self.source_type = 0                                                    # update self source_type
        self.source = self.sources[self.source_type].GetValue()                 # update self source
#        gbl.webcams_inuse.append(self.mon_name)              # add this monitor to webcam list (only one webcam implemented at this time)
#        gbl.webcams += 1

        self.currentSource.SetValue(self.source)                                # update currentSource field
        self.rbs[0].SetValue(True)                                              # update RBs
        gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type             # update cfg_dict
        gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source

        self.refreshVideo()                                 # change video playback

    def onChangeSource1(self, event):
        possibleSource = event.EventObject.GetValue()                           # change source information
        if not os.path.isfile(possibleSource):
            self.sources[1].SetValue('')
            return                                      # do nothing if invalid filename was specified

#        if gbl.cfg_dict[self.mon_ID]['source_type'] == 0:                    # if it was a webcam, remove from list
#            gbl.webcams_inuse.remove('Monitor%d' % self.mon_ID)                 # only one webcam implemented at this time
#            gbl.webcams -= 1
        self.source_type = 1                                                    # update self source_type

        self.source = possibleSource                                            # update self source

        self.currentSource.SetValue(self.source)                                # upate currentSource field
        self.rbs[1].SetValue(True)                                              # update RBs
        gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type             # update cfg_dict
        gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source



        self.refreshVideo()

    def onChangeSource2(self, event):
        possibleSource = event.EventObject.GetValue()                           # change source information
        if not os.path.isdir(possibleSource):
            self.sources[2].SetValue('')
            return                                      # do nothing if invalid filename was specified

#        if gbl.cfg_dict[self.mon_ID]['source_type'] == 0:                   # if it was a webcam, remove from list
#            gbl.webcams_inuse.remove('Monitor%d' % self.mon_ID)               # only one webcam implemented at this time
#            gbl.webcams -= 1

        self.source_type = 2                                                    # update self source type

        self.source = possibleSource                                            # update self source

        self.currentSource.SetValue(self.source)                                # update currentSource field
        self.rbs[2].SetValue(True)                                              # update RBs
        gbl.cfg_dict[self.mon_ID]['source_type'] = gbl.source_type = self.source_type             # update cfg_dict
        gbl.cfg_dict[self.mon_ID]['source'] = gbl.source = self.source

        self.refreshVideo()

    def onChangePreviewSize(self, event):
        input = gbl.correctType(self.previewSize.GetValue(), 'preview_size')                          # keep this incase new value is invalid
        if type(input) != tuple:
            input = self.preview_size

        gbl.cfg_dict[self.mon_ID]['preview_size'] = gbl.preview_size = self.preview_size = input           # update self & cfg_dict

        self.refreshVideo()                                 # close and restart video playback
        self.previewFPS.SetFocus()

    def onChangePreviewFPS(self, event):
        input = gbl.correctType(self.previewFPS.GetValue(), 'preview_fps')
        if not (type(input) == int or type(input) == float):
            input = self.preview_fps                        # don't change the value if input wasn't a number

        gbl.cfg_dict[self.mon_ID]['preview_fps'] = gbl.preview_fps = self.preview_fps = input           # update self & cfg_dict

        self.refreshVideo()                                 # close and restart video playback
        self.lineThickness.SetFocus()

    def onChangeLineThickness(self, event):
        input = gbl.correctType(self.lineThickness.GetValue(), 'line_thickness')
        if not (type(input) == int  or type(input) == float):
            input = self.line_thickness                        # don't change the value if input wasn't a number

        gbl.cfg_dict[self.mon_ID]['line_thickness'] = gbl.line_thickness = self.line_thickness = input           # update self & cfg_dict

        self.refreshVideo()                                 # close and restart video playback
        self.previewSize.SetFocus()

    def onChangeOutput(self, event):   # --------------------------------------------------------- change output folder
        gbl.cfg_dict[self.mon_ID]['data_folder'] = gbl.data_folder = self.data_folder = self.pickOutputBrowser.GetValue()

    def onMaskBrowse(self, event):      # ------------------------------------------------------ change mask file & ROIs
        gbl.cfg_dict[self.mon_ID]['mask_file'] = gbl.mask_file = self.mask_file = self.pickMaskBrowser.GetValue()
        gbl.genmaskflag = False                             # ROIs need to be reread from the mask file

        self.refreshVideo()

    def onMaskGen(self, event):
        gbl.genmaskflag = True                              # ROIs need to be read from gbl.ROIs

        self.mask = []  # holds rows for output to a mask file
        self.ROIs = []  # holds tuples for drawing ROIs

        mask_dict = {}
        mask_keys = ['columns', 'x1', 'x_len', 'x_sep', 'x_tilt', 'rows', 'y1', 'y_len', 'y_sep', 'y_tilt']

        for count in range(0,5):
            mask_dict[mask_keys[count]] = int(self.X[count+1].GetValue())               # x column

        for count in range(5,10):
            mask_dict[mask_keys[count]] = int(self.Y[count-4].GetValue())               # y column

        ROI = 1  # counter; numbers the ROIs

        for row in range(0, int(mask_dict['rows'])):  # y-coordinates change through rows
            ax = mask_dict['x1'] + row * mask_dict['x_tilt']  # reset x-coordinate start of row
            bx = ax + mask_dict['x_len']
            cx = bx
            dx = ax
            if row == 0:
                ay = mask_dict['y1']
            else:
                ay = mask_dict['y1'] + row * (mask_dict['y_len'] + mask_dict['y_sep'])  # move down in y
            by = ay
            cy = ay + mask_dict['y_len']
            dy = cy
            for col in range(0, mask_dict['columns']):  # x-coordinates change through columns

                # ------------------------------------------------------------------------ create the mask coordinates
                if col == 0 and row == 0:
                    self.mask.append(  # for saving to mask file
                        '(lp1\n((I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\n' % (ax, ay, bx, by, cx, cy, dx, dy))
                else:
                    self.mask.append(
                        'ttp%d\na((I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\nt(I%d\nI%d\n' % (
                        ROI, ax, ay, bx, by, cx, cy, dx, dy))

                self.ROIs.append([(ax, ay), (bx, by), (cx, cy), (dx, dy), (ax, ay)])  # for immediate use

                ax = bx + mask_dict['x_sep']  # prepare for next time
                bx = ax + mask_dict['x_len']
                cx = bx
                dx = ax
                ay = ay + mask_dict['y_tilt']
                by = ay
                cy = ay + mask_dict['y_len']
                dy = cy
                ROI += 1

        self.mask.append('ttp%d\na.(lp1\nI1\n' % (ROI + 1))
        self.mask.append('aI1\n' * mask_dict['rows'] * (mask_dict['columns'] -1))
        self.mask.append('a.\n\n\n')

        self.refreshVideo()

    def onSaveMask(self, event):            # ---------------------------------------------------  Save new mask to file
        """
        Lets user select file and path where mask will be saved.
        """
        # set file types for find dialog
        wildcard = "PySolo Video config file (*.msk)|*.msk|" \
                   "All files (*.*)|*.*"  # adding space in here will mess it up!

        dlg = wx.FileDialog(self,
                            message="Save mask as file ...",
                            defaultDir=self.data_folder,
                            wildcard=wildcard,
                            style=(wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
                            )

        if not(dlg.ShowModal() == wx.ID_OK):                     # show the file browser window
            return False
        else:
            self.mask_file = dlg.GetPath()                   # get the path from the save dialog

            if os.path.isfile(self.mask_file):
                os.remove(self.mask_file)                    # get rid of old file before appending data

            with open(self.mask_file, 'a') as mask_file:
                for roi in self.mask:
                    mask_file.write(roi)                          # write to file line by line

        dlg.Destroy()
        mask_file.close()

        self.pickMaskBrowser.SetValue(self.mask_file)                # update the mask browser textctrl box

        self.refreshVideo()

    def onClearMask(self, event):
        self.ROIs = []
        gbl.genmaskflag = True
        cfg.mon_nicknames_to_dicts(self.mon_ID)
        self.refreshVideo()



# ------------------------------------------------------------------------------------------ Stand alone test code
#  insert other classes above and call them in mainFrame
#
class mainFrame(wx.Frame):

    def __init__(self, *args, **kwds):

        wx.Frame.__init__(self, *args, **kwds)

        config = cfg.Configuration(self)
        whole = maskMakerPanel(self)




        print('done.')

if __name__ == "__main__":

    app = wx.App()
    wx.InitAllImageHandlers()


    frame_1 = mainFrame(None, 0, "")           # Create the main window.
    app.SetTopWindow(frame_1)                   # Makes this window the main window
    frame_1.Show()                              # Shows the main window

    app.MainLoop()                              # Begin user interactions.

#
