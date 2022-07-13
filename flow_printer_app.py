import os
import sys
import datetime
import numpy as np
# import random
import time
# import threading
import re
import warnings
import serial
from PIL import Image
# import pyvips
import pandas as pd
from pandas import DataFrame
from matplotlib.figure import Figure
# from matplotlib import cm
import matplotlib as mpl
import matplotlib.pyplot as plt
import pyqtgraph as pg
mpl.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QTimer, Qt, QThreadPool, QRunnable
from PyQt5.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget, QDesktopWidget
from simple_pyspin import Camera
from functools import partial
from playsound import playsound
# from collections import OrderedDict # this is used, not sure about the error
from pipython import GCSDevice, pitools
from pipython.gcscommands import GCSCommands as gcs


## import classes
import Start_up as su
import Graphic_display as gd
import Printer_canvas as pc
import Histogram as hc
import Print_thread as pt

class main_window(QtWidgets.QMainWindow):

    def __init__(self):
        super(main_window, self).__init__()
        self.setWindowIcon(QtGui.QIcon('cells.png'))
        app.setWindowIcon(QtGui.QIcon('cells.png'))
        self.gamma = 1
        self.zoom_factor = 1
        self.setup_main_window()
        self.setup_ui_text()
        self.actions()
        self.threadpool = QThreadPool()
        self.threadpool.setMaxThreadCount(10)
        try:
            self.pathname = 'C:/Users/sunyi/Desktop/gcode_generator/gcode'
            self.filenames = os.listdir(self.pathname)
        except:
            self.pathname = 'C:/Users/sunyi/Desktop'
            self.filenames = os.listdir(self.pathname)
        _filenames = []
        for i in range(len(self.filenames)):
            item = self.filenames[i]
            if '.gcode' in item:
                self.list_current_directory.addItem(item)
                _filenames.append(item)
        self.list_current_directory.setCurrentRow(0)
        os.chdir(self.pathname)
        self.filenames = _filenames
        if c_camera.cam:
            # refresh ui camera variables
            self.lineedit_analog_gain.setText(str(np.round(c_camera.cam.get_info('Gain')['value'],2))+' dB')
            self.lineedit_exposure.setText(str(np.round(c_camera.cam.get_info('ExposureTime')['value'],2))+' ms')
        self.take_image_start_time = time.time()
        return

    def closeEvent(self, event):
        try:
            c_camera.cam.stop() # Stop recording if camera caught on
        except:
            0
        if c_main_window.cbox_live.isChecked():
            c_camera.live_timer.stop()

        try:
            c_camera.cam.close()
            time.sleep(0.1)
        except:
            print('couldn''t close/clean up camera')

        try:
            c.laser_off()
            c.l.close()
            c.l.__del__()
            c.l = 0
            print('laser closed')
        except:
            0
            print('couldn''t close/clean up laser')

        try:
            c.z.SVO(1, False)
            c.z.CloseConnection()
            c.z = 0
            print('z stage close/clean')
        except:
            print('couldn''t close/clean up z stage')

        try:
            c.xy.SVO(1, False)
            c.xy.SVO(2, False)
            c.xy.CloseConnection()
            c.xy = 0
            print('xy stage close/clean')
        except:
            print('couldn''t close/clean up xy stage')
        time.sleep(0.1) # hang here - otherwise we get some pthread-mutex-assertion-error / glitch where threads dont shutdown properly
        app.quit()
        print('close event ran')
        print('close all controllers properly here: main window closeEvent')
        return

    def setup_main_window(self):
        self.setObjectName('main_window')
        self.resize(1349, 915)
        # self.setStyleSheet('color:#FFFFFF;\n'
# 'background-color: rgb(80,80,80);')
        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName('centralwidget')
        self.image_camera = QtWidgets.QLabel(self.centralwidget)
        self.image_camera.setGeometry(QtCore.QRect(345, 25, 958, 638))
        self.image_camera.setText('')
        self.image_camera.setScaledContents(True)
        self.image_camera.setObjectName('image_camera')
        ####pyqtgraph
        pg.setConfigOption("background", (236, 236, 236))
        pg.setConfigOption("foreground", "k")
        self.hist_flag1 = None
        self.hist_flag2 = None
        self.hist = pg.PlotWidget()
        self.setCentralWidget(self.hist)
        self.hist.setGeometry(QtCore.QRect(319, 670, 996, 200))
        self.hist.setObjectName('image_histogram')
        self.histogram_layout = QtWidgets.QVBoxLayout()
        self.histogram_layout.addWidget(self.hist)
        self.hist.setXRange(-1, 257)
        self.hist.setMouseEnabled(x=False, y=False)
        self.hist.showGrid(x=True, y=True, alpha = 0.5)
        # self.hist.hideAxis('left')
        # self.hist.hideLabel('bottom')
        self.hist.setLabel('left', text='')
        self.hist.setLabel('bottom', text='')
        self.hist.setLogMode(x=False, y=True)
        self.hist.plot([1,2,3,250], [0.5, 1, 3,0], pen = pg.mkPen('k', width = 3),alpha = 0.5, clear=True)


        ## previous
        self.image_histogram = hc.histogram_canvas()
        # self.setCentralWidget(self.image_histogram)
        # self.image_histogram.setGeometry(QtCore.QRect(319, 670, 996, 200))
        # self.image_histogram.setObjectName('image_histogram')
        # self.histogram_layout = QtWidgets.QVBoxLayout()
        # self.histogram_layout.addWidget(self.image_histogram)

        self.status_image = QtWidgets.QLabel(self.centralwidget)
        self.status_image.setGeometry(QtCore.QRect(709, 870, 571, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(True)
        self.status_image.setFont(font)
        self.status_image.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.status_image.setStyleSheet('color:#FFFFFF')
        self.status_image.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.status_image.setObjectName('status_image')
        self.status_current_directory = QtWidgets.QLabel(self.centralwidget)
        self.status_current_directory.setGeometry(QtCore.QRect(200, 665, 181, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(True)
        self.status_current_directory.setFont(font)
        self.status_current_directory.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.status_current_directory.setStyleSheet('color:#FFFFFF\n'
# '')
        self.status_current_directory.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.status_current_directory.setObjectName('status_current_directory')
        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setGeometry(QtCore.QRect(20, 650, 291, 16))
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName('line_2')
        self.list_current_directory = QtWidgets.QListWidget(self.centralwidget)
        self.list_current_directory.setGeometry(QtCore.QRect(20, 701, 291, 161))
        # self.list_current_directory.setStyleSheet('background-color: rgb(128,128,128);')
        self.list_current_directory.setObjectName('list_current_directory')
        font = QtGui.QFont()
        font.setPointSize(8)
        self.list_current_directory.setFont(font)
        self.btn_change_directory = QtWidgets.QPushButton(self.centralwidget)
        self.btn_change_directory.setGeometry(QtCore.QRect(20, 670, 80, 25))
        # self.btn_change_directory.setStyleSheet('color:#FFFFFF')
        self.btn_change_directory.setObjectName('btn_change_directory')
        self.tabs = QtWidgets.QTabWidget(self.centralwidget)
        self.tabs.setGeometry(QtCore.QRect(10, 10, 321, 641))
        self.tabs.setFocusPolicy(QtCore.Qt.TabFocus)
        # self.tabs.setStyleSheet('border-color: rgb(80, 80, 80);\n'
# 'selection-color: rgb(80, 80, 80);\n'
# 'alternate-background-color: rgb(80, 80, 80);\n'
# 'selection-color: rgb(128, 128, 128);\n'
# 'background-color: rgb(80,80, 80);\n'
# 'color:rgb(0, 0, 0);\n'
# '')
        self.tabs.setObjectName('tabs')
        self.camera_tab = QtWidgets.QWidget()
        self.camera_tab.setObjectName('camera_tab')
        self.btn_ROI_in = QtWidgets.QPushButton(self.camera_tab)
        self.btn_ROI_in.setGeometry(QtCore.QRect(5, 195, 80, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_ROI_in.sizePolicy().hasHeightForWidth())
        self.btn_ROI_in.setSizePolicy(sizePolicy)
        # self.btn_ROI_in.setStyleSheet('color:#FFFFFF;')
        self.btn_ROI_in.setAutoDefault(False)
        self.btn_ROI_in.setDefault(False)
        self.btn_ROI_in.setFlat(False)
        self.btn_ROI_in.setObjectName('btn_ROI_in')
        self.btn_ROI_out = QtWidgets.QPushButton(self.camera_tab)
        self.btn_ROI_out.setGeometry(QtCore.QRect(105, 195, 80, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_ROI_out.sizePolicy().hasHeightForWidth())
        self.btn_ROI_out.setSizePolicy(sizePolicy)
        # self.btn_ROI_out.setStyleSheet('color:#FFFFFF;')
        self.btn_ROI_out.setAutoDefault(False)
        self.btn_ROI_out.setDefault(False)
        self.btn_ROI_out.setFlat(False)
        self.btn_ROI_out.setObjectName('btn_ROI_out')
        self.btn_ROI_home = QtWidgets.QPushButton(self.camera_tab)
        self.btn_ROI_home.setGeometry(QtCore.QRect(195, 195, 80, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_ROI_home.sizePolicy().hasHeightForWidth())
        self.btn_ROI_home.setSizePolicy(sizePolicy)
        # self.btn_ROI_home.setStyleSheet('color:#FFFFFF;')
        self.btn_ROI_home.setAutoDefault(False)
        self.btn_ROI_home.setDefault(False)
        self.btn_ROI_home.setFlat(False)
        self.btn_ROI_home.setObjectName('btn_ROI_home')
        self.status_capture = QtWidgets.QLabel(self.camera_tab)
        self.status_capture = QtWidgets.QLabel(self.camera_tab)
        self.status_capture.setGeometry(QtCore.QRect(105, 35, 141, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(True)
        self.status_capture.setFont(font)
        # self.status_capture.setStyleSheet('color:#FFFFFF;')
        self.status_capture.setAlignment(QtCore.Qt.AlignCenter)
        self.status_capture.setObjectName('status_capture')
        self.lineedit_analog_gain = QtWidgets.QLineEdit(self.camera_tab)
        self.lineedit_analog_gain.setGeometry(QtCore.QRect(105, 105, 80, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_analog_gain.sizePolicy().hasHeightForWidth())
        self.lineedit_analog_gain.setSizePolicy(sizePolicy)
        # self.lineedit_analog_gain.setStyleSheet('background-color: rgb(128, 128, 128);')
        self.lineedit_analog_gain.setObjectName('lineedit_analog_gain')
        # self.cbox_target_FPS = QtWidgets.QCheckBox(self.camera_tab)
        # self.cbox_target_FPS.setGeometry(QtCore.QRect(205, 160, 80, 30))
        # sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.cbox_target_FPS.sizePolicy().hasHeightForWidth())
        # self.cbox_target_FPS.setSizePolicy(sizePolicy)
        # self.cbox_target_FPS.setAutoFillBackground(False)
        # self.cbox_target_FPS.setStyleSheet('color:#FFFFFF;')
        # self.cbox_target_FPS.setCheckable(True)
        # self.cbox_target_FPS.setTristate(False)
        # self.cbox_target_FPS.setObjectName('cbox_target_FPS')
        self.lineedit_exposure = QtWidgets.QLineEdit(self.camera_tab)
        self.lineedit_exposure.setGeometry(QtCore.QRect(105, 75, 80, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_exposure.sizePolicy().hasHeightForWidth())
        self.lineedit_exposure.setSizePolicy(sizePolicy)
        # self.lineedit_exposure.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_exposure.setObjectName('lineedit_exposure')
        self.label_target_FPS = QtWidgets.QLabel(self.camera_tab)
        self.label_target_FPS.setGeometry(QtCore.QRect(10, 160, 80, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(False)
        self.label_target_FPS.setFont(font)
        self.label_target_FPS.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.label_target_FPS.setStyleSheet('color:#FFFFFF;')
        self.label_target_FPS.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_target_FPS.setObjectName('label_target_FPS')
        self.combobox_binning = QtWidgets.QComboBox(self.camera_tab)
        self.combobox_binning.setGeometry(QtCore.QRect(103, 135, 84, 20))
        self.combobox_binning.setStyleSheet('text-align:center;')
        # self.combobox_binning.setStyleSheet('color:#FFFFFF;\n'
# 'selection-background-color: rgb(0,168,0);\n'
# 'background-color: rgb(128, 128, 128);\n'
# '')
        self.combobox_binning.setObjectName('combobox_binning')
        self.combobox_binning.addItem('')
        self.combobox_binning.addItem('')
        self.combobox_binning.addItem('')
        self.btn_snap = QtWidgets.QPushButton(self.camera_tab)
        self.btn_snap.setGeometry(QtCore.QRect(5, 10, 80, 25))
        # self.btn_snap.setStyleSheet('color:#FFFFFF;')
        self.btn_snap.setObjectName('btn_snap')
        self.cbox_exposure = QtWidgets.QCheckBox(self.camera_tab)
        self.cbox_exposure.setGeometry(QtCore.QRect(205, 70, 80, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbox_exposure.sizePolicy().hasHeightForWidth())
        self.cbox_exposure.setSizePolicy(sizePolicy)
        self.cbox_exposure.setAutoFillBackground(False)
        # self.cbox_exposure.setStyleSheet('color:#FFFFFF;')
        self.cbox_exposure.setCheckable(True)
        self.cbox_exposure.setTristate(False)
        self.cbox_exposure.setObjectName('cbox_exposure')
        self.cbox_analog_gain = QtWidgets.QCheckBox(self.camera_tab)
        self.cbox_analog_gain.setGeometry(QtCore.QRect(205, 100, 80, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbox_analog_gain.sizePolicy().hasHeightForWidth())
        self.cbox_analog_gain.setSizePolicy(sizePolicy)
        self.cbox_analog_gain.setAutoFillBackground(False)
        # self.cbox_analog_gain.setStyleSheet('color:#FFFFFF;')
        self.cbox_analog_gain.setCheckable(True)
        self.cbox_analog_gain.setTristate(False)
        self.cbox_analog_gain.setObjectName('cbox_analog_gain')
        self.lineedit_target_FPS = QtWidgets.QLineEdit(self.camera_tab)
        self.lineedit_target_FPS.setGeometry(QtCore.QRect(105, 165, 80, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_target_FPS.sizePolicy().hasHeightForWidth())
        self.lineedit_target_FPS.setSizePolicy(sizePolicy)
        # self.lineedit_target_FPS.setStyleSheet('background-color: rgb(128, 128, 128);')
        self.lineedit_target_FPS.setObjectName('lineedit_target_FPS')
        self.btn_save = QtWidgets.QPushButton(self.camera_tab)
        self.btn_save.setGeometry(QtCore.QRect(5, 40, 80, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_save.sizePolicy().hasHeightForWidth())
        self.btn_save.setSizePolicy(sizePolicy)
        # self.btn_save.setStyleSheet('color:#FFFFFF;')
        self.btn_save.setAutoDefault(False)
        self.btn_save.setDefault(False)
        self.btn_save.setFlat(False)
        self.btn_save.setObjectName('btn_save')
        self.label_camera_binning = QtWidgets.QLabel(self.camera_tab)
        self.label_camera_binning.setGeometry(QtCore.QRect(10, 130, 100, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(False)
        self.label_camera_binning.setFont(font)
        self.label_camera_binning.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.label_camera_binning.setStyleSheet('color:#FFFFFF;\n'
# '')
        self.label_camera_binning.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_camera_binning.setObjectName('label_camera_binning')
        self.btn_video = QtWidgets.QPushButton(self.camera_tab)
        self.btn_video.setGeometry(QtCore.QRect(105, 10, 80, 25))
        # self.btn_video.setStyleSheet('color:#FFFFFF;')
        self.btn_video.setObjectName('btn_video')
        self.cbox_live = QtWidgets.QCheckBox(self.camera_tab)
        self.cbox_live.setGeometry(QtCore.QRect(205, 5, 80, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbox_live.sizePolicy().hasHeightForWidth())
        self.cbox_live.setSizePolicy(sizePolicy)
        self.cbox_live.setAutoFillBackground(False)
        # self.cbox_live.setStyleSheet('color:#FFFFFF;')
        self.cbox_live.setCheckable(True)
        self.cbox_live.setTristate(False)
        self.cbox_live.setObjectName('cbox_live')
        self.label_analog_gain = QtWidgets.QLabel(self.camera_tab)
        self.label_analog_gain.setGeometry(QtCore.QRect(10, 100, 80, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(False)
        self.label_analog_gain.setFont(font)
        self.label_analog_gain.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.label_analog_gain.setStyleSheet('color:#FFFFFF;')
        self.label_analog_gain.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_analog_gain.setObjectName('label_analog_gain')
        self.label_exposure = QtWidgets.QLabel(self.camera_tab)
        self.label_exposure.setGeometry(QtCore.QRect(10, 70, 80, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(False)
        self.label_exposure.setFont(font)
        self.label_exposure.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.label_exposure.setStyleSheet('color:#FFFFFF;')
        self.label_exposure.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_exposure.setObjectName('label_exposure')
        self.line_1 = QtWidgets.QFrame(self.camera_tab)
        self.line_1.setGeometry(QtCore.QRect(10, 220, 261, 16))
        self.line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_1.setObjectName('line_1')
        self.lineedit_gamma = QtWidgets.QLineEdit(self.camera_tab)
        self.lineedit_gamma.setGeometry(QtCore.QRect(90, 235, 50, 25))
        # self.lineedit_gamma.setStyleSheet('background-color: rgb(128, 128, 128);')
        self.lineedit_gamma.setObjectName('lineedit_gamma')
        self.cbox_normalise = QtWidgets.QCheckBox(self.camera_tab)
        self.cbox_normalise.setGeometry(QtCore.QRect(10, 290, 131, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbox_normalise.sizePolicy().hasHeightForWidth())
        self.cbox_normalise.setSizePolicy(sizePolicy)
        self.cbox_normalise.setAutoFillBackground(False)
        # self.cbox_normalise.setStyleSheet('color:#FFFFFF;')
        self.cbox_normalise.setCheckable(True)
        self.cbox_normalise.setTristate(False)
        self.cbox_normalise.setObjectName('cbox_normalise')
        self.cbox_show_scalebar = QtWidgets.QCheckBox(self.camera_tab)
        self.cbox_show_scalebar.setGeometry(QtCore.QRect(10, 320, 131, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbox_show_scalebar.sizePolicy().hasHeightForWidth())
        self.cbox_show_scalebar.setSizePolicy(sizePolicy)
        self.cbox_show_scalebar.setAutoFillBackground(False)
        # self.cbox_show_scalebar.setStyleSheet('color:#FFFFFF;')
        self.cbox_show_scalebar.setCheckable(True)
        self.cbox_show_scalebar.setChecked(True)
        self.cbox_show_scalebar.setTristate(False)
        self.cbox_show_scalebar.setObjectName('cbox_show_scalebar')
        self.combobox_objective = QtWidgets.QComboBox(self.camera_tab)
        self.combobox_objective.setGeometry(QtCore.QRect(80, 410, 84, 25))
#         self.combobox_objective.setStyleSheet('color:#FFFFFF;\n'
# 'selection-background-color: rgb(0,168,0);\n'
# 'background-color: rgb(128, 128, 128);\n'
# '')
        self.combobox_objective.setObjectName('combobox_objective')
        self.combobox_objective.addItem('')
        self.combobox_objective.addItem('')
        self.combobox_objective.addItem('')
        self.combobox_objective.addItem('')
        self.combobox_objective.addItem('')
        self.combobox_colourmap = QtWidgets.QComboBox(self.camera_tab)
        self.combobox_colourmap.setGeometry(QtCore.QRect(80, 350, 84, 25))
#         self.combobox_colourmap.setStyleSheet('color:#FFFFFF;\n'
# 'selection-background-color: rgb(0,168,0);\n'
# 'background-color: rgb(128, 128, 128);\n'
# '')

        self.combobox_colourmap.setObjectName('combobox_colourmap')
        self.combobox_colourmap.addItem('')
        self.combobox_colourmap.addItem('')
        self.combobox_colourmap.addItem('')
        self.combobox_colourmap.addItem('')
        self.combobox_colourmap.addItem('')
        self.cbox_saturated = QtWidgets.QCheckBox(self.camera_tab)
        self.cbox_saturated.setGeometry(QtCore.QRect(10, 380, 131, 30))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbox_saturated.sizePolicy().hasHeightForWidth())
        self.cbox_saturated.setSizePolicy(sizePolicy)
        self.cbox_saturated.setAutoFillBackground(False)
        # self.cbox_saturated.setStyleSheet('color:#FFFFFF;')
        self.cbox_saturated.setCheckable(True)
        self.cbox_saturated.setChecked(True)
        self.cbox_saturated.setTristate(False)
        self.cbox_saturated.setObjectName('cbox_saturated')
        self.label_gamma = QtWidgets.QLabel(self.camera_tab)
        self.label_gamma.setGeometry(QtCore.QRect(15, 230, 51, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(False)
        self.label_gamma.setFont(font)
        self.label_gamma.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.label_gamma.setStyleSheet('color:#FFFFFF;')
        self.label_gamma.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_gamma.setObjectName('label_gamma')
        self.label_objective = QtWidgets.QLabel(self.camera_tab)
        self.label_objective.setGeometry(QtCore.QRect(10, 410, 61, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(False)
        self.label_objective.setFont(font)
        self.label_objective.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.label_objective.setStyleSheet('color:#FFFFFF;')
        self.label_objective.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_objective.setObjectName('label_objective')
        self.slider_gamma = QtWidgets.QSlider(self.camera_tab)
        self.slider_gamma.setGeometry(QtCore.QRect(10, 260, 131, 30))
        self.slider_gamma.setMaximum(200)
        self.slider_gamma.setSliderPosition(100)
        self.slider_gamma.setOrientation(QtCore.Qt.Horizontal)
        self.slider_gamma.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider_gamma.setTickInterval(5)
        self.slider_gamma.setObjectName('slider_gamma')
        self.label_colourmap = QtWidgets.QLabel(self.camera_tab)
        self.label_colourmap.setGeometry(QtCore.QRect(10, 350, 61, 30))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setItalic(False)
        self.label_colourmap.setFont(font)
        self.label_colourmap.setLayoutDirection(QtCore.Qt.LeftToRight)
        # self.label_colourmap.setStyleSheet('color:#FFFFFF;')
        self.label_colourmap.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_colourmap.setObjectName('label_colourmap')
        self.tabs.addTab(self.camera_tab, '')
        self.printer_tab = QtWidgets.QWidget()
        self.printer_tab.setObjectName('printer_tab')
        self.btn_print = QtWidgets.QPushButton(self.printer_tab)
        self.btn_print.setGeometry(QtCore.QRect(110, 10, 91, 25))
        # self.btn_print.setStyleSheet('color:#808080')
        self.btn_print.setObjectName('btn_print')
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)
        self.btn_print.setFont(font)
        self.image_printer_position_xy = pc.printer_canvas('xy') # c_main_window.image_printer_position_xy.update_plot
        self.verticalLayoutWidget = QtWidgets.QWidget(self.printer_tab)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(30, 260, 241, 241))
        self.verticalLayoutWidget.setObjectName('verticalLayoutWidget')
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName('verticalLayout')
        #### pyqtgraph
        self.graph_xy = pg.PlotWidget()
        self.verticalLayout.addWidget(self.graph_xy)
        self.graph_xy.setXRange(-10, 11)
        self.graph_xy.setYRange(-10, 11)
        self.graph_xy.showGrid(x=True, y=True, alpha=1)
        self.graph_xy.setMouseEnabled(x=False, y=False)
        self.xy_graph_plot = self.graph_xy.plot([c.p_xpos_current], [c.p_ypos_current], color=(255,0,0), symbol='o', clear=True, symbolBrush =(255, 0, 0))
        # self.verticalLayout.addWidget(self.image_printer_position_xy)
        self.image_printer_position_xz = pc.printer_canvas('xz')
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.printer_tab)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(30, 520, 241, 80))
        self.verticalLayoutWidget_2.setObjectName('verticalLayoutWidget_2')
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName('verticalLayout_2')
        ### PlotWidget
        self.graph_xz = pg.PlotWidget()
        self.verticalLayout_2.addWidget(self.graph_xz)
        self.graph_xz.setXRange(-10, 10)
        self.graph_xz.setYRange(-3, 3)
        self.graph_xz.showGrid(x=True, y=True, alpha=1)
        self.graph_xz.setMouseEnabled(x=False, y=False)
        self.xz_graph_plot = self.graph_xz.plot([c.p_xpos_current], [c.p_z_cent-c.p_zpos_current], color=(255,0,0), symbol='o', clear=True, symbolBrush =(255, 0, 0))
        print("x = " + str(c.p_xpos_current))
        print("y = " + str(c.p_ypos_current))
        print("z = " + str(c.p_z_cent-c.p_zpos_current))
        # self.verticalLayout_2.addWidget(self.image_printer_position_xz)
        self.btn_stop_print = QtWidgets.QPushButton(self.printer_tab)
        self.btn_stop_print.setGeometry(QtCore.QRect(20, 151, 181, 25))
        font = QtGui.QFont()
        font.setPointSize(11)
        font.setBold(True)
        font.setWeight(75)
        font.setKerning(True)
        self.btn_stop_print.setFont(font)
        # self.btn_stop_print.setStyleSheet('color: rgb(225, 0, 0);\n'
# 'background-color: rgb(120, 120, 120);')
        self.btn_stop_print.setObjectName('btn_stop_print')
        self.btn_pos_y = QtWidgets.QPushButton(self.printer_tab)
        self.btn_pos_y.setGeometry(QtCore.QRect(140, 240, 30, 20))
        # self.btn_pos_y.setStyleSheet('color:#FFFFFF;')
        self.btn_pos_y.setObjectName('btn_pos_y')
        self.label_status_y_num = QtWidgets.QLabel(self.printer_tab)
        self.label_status_y_num.setGeometry(QtCore.QRect(130, 600, 60, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_status_y_num.setFont(font)
        # self.label_status_y_num.setStyleSheet('color:#FFFFFF')
        self.label_status_y_num.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_status_y_num.setObjectName('label_status_y_num')
        self.btn_neg_y = QtWidgets.QPushButton(self.printer_tab)
        self.btn_neg_y.setGeometry(QtCore.QRect(140, 500, 30, 20))
        # self.btn_neg_y.setStyleSheet('color:#FFFFFF')
        self.btn_neg_y.setObjectName('btn_neg_y')
        self.label_status_x_num = QtWidgets.QLabel(self.printer_tab)
        self.label_status_x_num.setGeometry(QtCore.QRect(30, 600, 60, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_status_x_num.setFont(font)
#         self.label_status_x_num.setStyleSheet('color:#FFFFFF\n'
# '')
        self.label_status_x_num.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_status_x_num.setObjectName('label_status_x_num')
        self.btn_pos_z = QtWidgets.QPushButton(self.printer_tab)
        self.btn_pos_z.setGeometry(QtCore.QRect(270, 240, 30, 20))
        # self.btn_pos_z.setStyleSheet('color:#FFFFFF')
        self.btn_pos_z.setObjectName('btn_pos_z')
        self.btn_neg_z = QtWidgets.QPushButton(self.printer_tab)
        self.btn_neg_z.setGeometry(QtCore.QRect(0, 500, 30, 20))
        # self.btn_neg_z.setStyleSheet('color:#FFFFFF')
        self.btn_neg_z.setObjectName('btn_neg_z')
        self.btn_pos_x = QtWidgets.QPushButton(self.printer_tab)
        self.btn_pos_x.setGeometry(QtCore.QRect(270, 370, 30, 20))
        # self.btn_pos_x.setStyleSheet('color:#FFFFFF')
        self.btn_pos_x.setObjectName('btn_pos_x')
        self.btn_neg_x = QtWidgets.QPushButton(self.printer_tab)
        self.btn_neg_x.setGeometry(QtCore.QRect(0, 370, 30, 20))
        # self.btn_neg_x.setStyleSheet('color:#FFFFFF')
        self.btn_neg_x.setObjectName('btn_neg_x')
        self.label_status_z_num = QtWidgets.QLabel(self.printer_tab)
        self.label_status_z_num.setGeometry(QtCore.QRect(240, 600, 60, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_status_z_num.setFont(font)
#         self.label_status_z_num.setStyleSheet('color:#FFFFFF\n'
# '')
        self.label_status_z_num.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_status_z_num.setObjectName('label_status_z_num')
        self.label_status_x = QtWidgets.QLabel(self.printer_tab)
        self.label_status_x.setGeometry(QtCore.QRect(10, 600, 20, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_status_x.setFont(font)
        # self.label_status_x.setStyleSheet('color:#FFFFFF')
        self.label_status_x.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_status_x.setObjectName('label_status_x')
        self.label_status_y = QtWidgets.QLabel(self.printer_tab)
        self.label_status_y.setGeometry(QtCore.QRect(110, 600, 20, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_status_y.setFont(font)
        # self.label_status_y.setStyleSheet('color:#FFFFFF')
        self.label_status_y.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_status_y.setObjectName('label_status_y')
        self.label_status_z = QtWidgets.QLabel(self.printer_tab)
        self.label_status_z.setGeometry(QtCore.QRect(220, 600, 20, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_status_z.setFont(font)
        # self.label_status_z.setStyleSheet('color:#FFFFFF')
        self.label_status_z.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_status_z.setObjectName('label_status_z')
        self.lineedit_xincrement = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_xincrement.setGeometry(QtCore.QRect(30, 200, 31, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_xincrement.sizePolicy().hasHeightForWidth())
        self.lineedit_xincrement.setSizePolicy(sizePolicy)
        # self.lineedit_xincrement.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_xincrement.setObjectName('lineedit_xincrement')
        self.lineedit_yincrement = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_yincrement.setGeometry(QtCore.QRect(130, 200, 31, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_yincrement.sizePolicy().hasHeightForWidth())
        self.lineedit_yincrement.setSizePolicy(sizePolicy)
        # self.lineedit_yincrement.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_yincrement.setObjectName('lineedit_yincrement')
        self.lineedit_zincrement = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_zincrement.setGeometry(QtCore.QRect(230, 200, 31, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_zincrement.sizePolicy().hasHeightForWidth())
        self.lineedit_zincrement.setSizePolicy(sizePolicy)
        # self.lineedit_zincrement.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_zincrement.setObjectName('lineedit_zincrement')
        self.label_xincrement = QtWidgets.QLabel(self.printer_tab)
        self.label_xincrement.setGeometry(QtCore.QRect(10, 200, 21, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_xincrement.setFont(font)
        # self.label_xincrement.setStyleSheet('color:#FFFFFF')
        self.label_xincrement.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_xincrement.setObjectName('label_xincrement')
        self.label_yincrement = QtWidgets.QLabel(self.printer_tab)
        self.label_yincrement.setGeometry(QtCore.QRect(110, 200, 16, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_yincrement.setFont(font)
        # self.label_yincrement.setStyleSheet('color:#FFFFFF')
        self.label_yincrement.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_yincrement.setObjectName('label_yincrement')
        self.label_zincrement = QtWidgets.QLabel(self.printer_tab)
        self.label_zincrement.setGeometry(QtCore.QRect(210, 200, 16, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_zincrement.setFont(font)
        # self.label_zincrement.setStyleSheet('color:#FFFFFF')
        self.label_zincrement.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_zincrement.setObjectName('label_zincrement')
        self.btn_pause_print = QtWidgets.QPushButton(self.printer_tab)
        self.btn_pause_print.setGeometry(QtCore.QRect(110, 40, 91, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_pause_print.setFont(font)
#         self.btn_pause_print.setStyleSheet('color: rgb(255, 255, 255);\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(150, 0, 0);\n'
# 'border-left-color: rgb(150, 0, 0);\n'
# 'background-color: rgb(140, 100, 100);')
        self.btn_pause_print.setObjectName('btn_pause_print')
        self.btn_load_gcode = QtWidgets.QPushButton(self.printer_tab)
        self.btn_load_gcode.setGeometry(QtCore.QRect(10, 40, 91, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_load_gcode.setFont(font)
#         self.btn_load_gcode.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_load_gcode.setObjectName('btn_load_gcode')
        self.btn_laser_on = QtWidgets.QPushButton(self.printer_tab)
        self.btn_laser_on.setGeometry(QtCore.QRect(240, 40, 61, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_laser_on.setFont(font)
#         self.btn_laser_on.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_laser_on.setObjectName('btn_laser_on')
        self.btn_laser_off = QtWidgets.QPushButton(self.printer_tab)
        self.btn_laser_off.setGeometry(QtCore.QRect(240, 70, 61, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_laser_off.setFont(font)
#         self.btn_laser_off.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_laser_off.setObjectName('btn_laser_off')
        self.btn_set_laser_current = QtWidgets.QPushButton(self.printer_tab)
        self.btn_set_laser_current.setGeometry(QtCore.QRect(240, 120, 61, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_set_laser_current.setFont(font)
#         self.btn_set_laser_current.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_set_laser_current.setObjectName('btn_set_laser_current')
        self.lineedit_set_laser_current = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_set_laser_current.setGeometry(QtCore.QRect(240, 150, 61, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_set_laser_current.sizePolicy().hasHeightForWidth())
        self.lineedit_set_laser_current.setSizePolicy(sizePolicy)
        self.lineedit_set_laser_current.setStyleSheet('font: 8px')
#         self.lineedit_set_laser_current.setStyleSheet('background-color: rgb(128, 128, 128);\n'
#                                                       'font: 8px'
# '')
        self.lineedit_set_laser_current.setObjectName('lineedit_set_laser_current')
        self.line_3 = QtWidgets.QFrame(self.printer_tab)
        self.line_3.setGeometry(QtCore.QRect(10, 180, 281, 16))
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName('line_3')
        self.lineedit_set_zcent = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_set_zcent.setGeometry(QtCore.QRect(90, 70, 51, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_set_zcent.sizePolicy().hasHeightForWidth())
        self.lineedit_set_zcent.setSizePolicy(sizePolicy)
#         self.lineedit_set_zcent.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_set_zcent.setObjectName('lineedit_set_zcent')
        self.label_zcent_text = QtWidgets.QLabel(self.printer_tab)
        self.label_zcent_text.setGeometry(QtCore.QRect(20, 70, 60, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_zcent_text.setFont(font)
        # self.label_zcent_text.setStyleSheet('color:#FFFFFF')
        self.label_zcent_text.setAlignment(QtCore.Qt.AlignCenter)
        self.label_zcent_text.setObjectName('label_zcent_text')
        self.btn_set_zcent = QtWidgets.QPushButton(self.printer_tab)
        self.btn_set_zcent.setGeometry(QtCore.QRect(160, 70, 41, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_set_zcent.setFont(font)
#         self.btn_set_zcent.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_set_zcent.setObjectName('btn_set_zcent')
        self.line = QtWidgets.QFrame(self.printer_tab)
        self.line.setGeometry(QtCore.QRect(210, 10, 20, 171))
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName('line')
        self.label_printer_section_text = QtWidgets.QLabel(self.printer_tab)
        self.label_printer_section_text.setGeometry(QtCore.QRect(10, 10, 81, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(True)
        font.setWeight(50)
        self.label_printer_section_text.setFont(font)
        self.label_printer_section_text.setLayoutDirection(QtCore.Qt.LeftToRight)
#         self.label_printer_section_text.setStyleSheet('color:rgb(180, 180, 180);\n'
# '')
        self.label_printer_section_text.setAlignment(QtCore.Qt.AlignCenter)
        self.label_printer_section_text.setObjectName('label_printer_section_text')
        self.label_laser_section_text = QtWidgets.QLabel(self.printer_tab)
        self.label_laser_section_text.setGeometry(QtCore.QRect(240, 10, 61, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(True)
        font.setWeight(50)
        self.label_laser_section_text.setFont(font)
        self.label_laser_section_text.setLayoutDirection(QtCore.Qt.LeftToRight)
#         self.label_laser_section_text.setStyleSheet('color:rgb(180, 180, 180);\n'
# '')
        self.label_laser_section_text.setAlignment(QtCore.Qt.AlignCenter)
        self.label_laser_section_text.setObjectName('label_laser_section_text')
        self.lineedit_xvelocity = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_xvelocity.setGeometry(QtCore.QRect(70, 200, 31, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_xvelocity.sizePolicy().hasHeightForWidth())
        self.lineedit_xvelocity.setSizePolicy(sizePolicy)
#         self.lineedit_xvelocity.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_xvelocity.setObjectName('lineedit_xvelocity')
        self.lineedit_yvelocity = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_yvelocity.setGeometry(QtCore.QRect(170, 200, 31, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_yvelocity.sizePolicy().hasHeightForWidth())
        self.lineedit_yvelocity.setSizePolicy(sizePolicy)
#         self.lineedit_yvelocity.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_yvelocity.setObjectName('lineedit_yvelocity')
        self.lineedit_zvelocity = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_zvelocity.setGeometry(QtCore.QRect(270, 200, 31, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_zvelocity.sizePolicy().hasHeightForWidth())
        self.lineedit_zvelocity.setSizePolicy(sizePolicy)
#         self.lineedit_zvelocity.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_zvelocity.setObjectName('lineedit_zvelocity')
        self.label_incr_1 = QtWidgets.QLabel(self.printer_tab)
        self.label_incr_1.setGeometry(QtCore.QRect(30, 220, 31, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_incr_1.setFont(font)
        # self.label_incr_1.setStyleSheet('color:#FFFFFF')
        self.label_incr_1.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_incr_1.setObjectName('label_incr_1')
        self.label_vel_1 = QtWidgets.QLabel(self.printer_tab)
        self.label_vel_1.setGeometry(QtCore.QRect(70, 220, 31, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_vel_1.setFont(font)
        # self.label_vel_1.setStyleSheet('color:#FFFFFF')
        self.label_vel_1.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_vel_1.setObjectName('label_vel_1')
        self.label_incr_2 = QtWidgets.QLabel(self.printer_tab)
        self.label_incr_2.setGeometry(QtCore.QRect(130, 220, 31, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_incr_2.setFont(font)
        # self.label_incr_2.setStyleSheet('color:#FFFFFF')
        self.label_incr_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_incr_2.setObjectName('label_incr_2')
        self.label_vel_2 = QtWidgets.QLabel(self.printer_tab)
        self.label_vel_2.setGeometry(QtCore.QRect(170, 220, 31, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_vel_2.setFont(font)
        # self.label_vel_2.setStyleSheet('color:#FFFFFF')
        self.label_vel_2.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_vel_2.setObjectName('label_vel_2')
        self.label_incr_3 = QtWidgets.QLabel(self.printer_tab)
        self.label_incr_3.setGeometry(QtCore.QRect(230, 220, 31, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_incr_3.setFont(font)
        # self.label_incr_3.setStyleSheet('color:#FFFFFF')
        self.label_incr_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_incr_3.setObjectName('label_incr_3')
        self.label_vel_3 = QtWidgets.QLabel(self.printer_tab)
        self.label_vel_3.setGeometry(QtCore.QRect(270, 220, 31, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_vel_3.setFont(font)
        # self.label_vel_3.setStyleSheet('color:#FFFFFF')
        self.label_vel_3.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_vel_3.setObjectName('label_vel_3')
        self.lineedit_custom_serial_send = QtWidgets.QLineEdit(self.printer_tab)
        self.lineedit_custom_serial_send.setGeometry(QtCore.QRect(20, 120, 121, 25))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lineedit_custom_serial_send.sizePolicy().hasHeightForWidth())
        self.lineedit_custom_serial_send.setSizePolicy(sizePolicy)
#         self.lineedit_custom_serial_send.setStyleSheet('background-color: rgb(128, 128, 128);\n'
# '')
        self.lineedit_custom_serial_send.setObjectName('lineedit_custom_serial_send')
        self.btn_custom_serial_send = QtWidgets.QPushButton(self.printer_tab)
        self.btn_custom_serial_send.setGeometry(QtCore.QRect(160, 120, 41, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_custom_serial_send.setFont(font)
#         self.btn_custom_serial_send.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_custom_serial_send.setObjectName('btn_custom_serial_send')
        self.label_custom_serial_send = QtWidgets.QLabel(self.printer_tab)
        self.label_custom_serial_send.setGeometry(QtCore.QRect(20, 95, 121, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.label_custom_serial_send.setFont(font)
        # self.label_custom_serial_send.setStyleSheet('color:#FFFFFF')
        self.label_custom_serial_send.setAlignment(QtCore.Qt.AlignCenter)
        self.label_custom_serial_send.setObjectName('label_custom_serial_send')
        self.tabs.addTab(self.printer_tab, '')
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName('tab')
        self.btn_connect_all = QtWidgets.QPushButton(self.tab)
        self.btn_connect_all.setGeometry(QtCore.QRect(20, 10, 131, 101))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_connect_all.setFont(font)
#         self.btn_connect_all.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_connect_all.setObjectName('btn_connect_all')
        self.btn_connect_x = QtWidgets.QPushButton(self.tab)
        self.btn_connect_x.setGeometry(QtCore.QRect(160, 10, 121, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_connect_x.setFont(font)
#         self.btn_connect_x.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_connect_x.setObjectName('btn_connect_x')
        self.btn_connect_y = QtWidgets.QPushButton(self.tab)
        self.btn_connect_y.setGeometry(QtCore.QRect(160, 30, 121, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_connect_y.setFont(font)
#         self.btn_connect_y.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_connect_y.setObjectName('btn_connect_y')
        self.btn_connect_z = QtWidgets.QPushButton(self.tab)
        self.btn_connect_z.setGeometry(QtCore.QRect(160, 50, 121, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_connect_z.setFont(font)
#         self.btn_connect_z.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_connect_z.setObjectName('btn_connect_z')
        self.btn_connect_laser = QtWidgets.QPushButton(self.tab)
        self.btn_connect_laser.setGeometry(QtCore.QRect(160, 70, 121, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_connect_laser.setFont(font)
#         self.btn_connect_laser.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_connect_laser.setObjectName('btn_connect_laser')
        self.btn_connect_camera = QtWidgets.QPushButton(self.tab)
        self.btn_connect_camera.setGeometry(QtCore.QRect(160, 90, 121, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_connect_camera.setFont(font)
#         self.btn_connect_camera.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_connect_camera.setObjectName('btn_connect_camera')
        self.status_controller = QtWidgets.QLabel(self.tab)
        self.status_controller.setGeometry(QtCore.QRect(20, 120, 261, 20))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(True)
        font.setWeight(50)
        self.status_controller.setFont(font)
        self.status_controller.setLayoutDirection(QtCore.Qt.LeftToRight)
#         self.status_controller.setStyleSheet('color:rgb(180, 180, 180);\n'
# '')
        self.status_controller.setAlignment(QtCore.Qt.AlignCenter)
        self.status_controller.setObjectName('status_controller')
        self.btn_disconnect_all = QtWidgets.QPushButton(self.tab)
        self.btn_disconnect_all.setGeometry(QtCore.QRect(20, 150, 261, 21))
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        self.btn_disconnect_all.setFont(font)
#         self.btn_disconnect_all.setStyleSheet('color: #FFFFFF;\n'
# 'border-bottom-color: rgb(111, 0, 0);\n'
# 'border-right-color: rgb(111, 0, 0);\n'
# 'border-top-color: rgb(50,50,50);\n'
# 'border-left-color: rgb(50,50,50);\n'
# '')
        self.btn_disconnect_all.setObjectName('btn_disconnect_all')
        self.tabs.addTab(self.tab, '')
        self.status_printer = QtWidgets.QLabel(self.centralwidget)
        self.status_printer.setGeometry(QtCore.QRect(20, 870, 681, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.status_printer.setFont(font)
        self.status_printer.setObjectName('status_printer')
        self.status_fps_text = QtWidgets.QLabel(self.centralwidget)
        self.status_fps_text.setGeometry(QtCore.QRect(320, 5, 31, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.status_fps_text.setFont(font)
        # self.status_fps_text.setStyleSheet('color:#FFFFFF;')
        self.status_fps_text.setObjectName('status_fps_text')
        self.status_fps_number = QtWidgets.QLabel(self.centralwidget)
        self.status_fps_number.setGeometry(QtCore.QRect(360, 5, 60, 20))
        font = QtGui.QFont()
        font.setItalic(True)
        self.status_fps_number.setFont(font)
        # self.status_fps_number.setStyleSheet('color:#FFFFFF;')
        self.status_fps_number.setObjectName('status_fps_number')
        self.setCentralWidget(self.centralwidget)
        self.statusBar = QtWidgets.QStatusBar(self)
        self.statusBar.setObjectName('statusBar')
        self.setStatusBar(self.statusBar)

        self.tabs.setCurrentIndex(0)
        self.combobox_objective.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(self)

    def setup_ui_text(self):
        _translate = QtCore.QCoreApplication.translate
        self.status_image.setText(_translate('main_window', '... image status ...'))
        self.status_current_directory.setText(_translate('main_window', '... current directory ...'))
        self.btn_change_directory.setText(_translate('main_window', 'change dir'))
        self.btn_print.setText(_translate('main_window', 'print'))
        self.btn_ROI_in.setText(_translate('main_window', 'zoom in'))
        self.btn_ROI_out.setText(_translate('main_window', 'zoom out'))
        self.btn_ROI_home.setText(_translate('main_window', 'zoom home'))
        self.status_capture.setText(_translate('main_window', '...camera status...'))
        self.label_target_FPS.setText(_translate('main_window', 'target FPS'))
        self.combobox_binning.setItemText(0, _translate('main_window', '4x4'))
        self.combobox_binning.setItemText(1, _translate('main_window', '2x2'))
        self.combobox_binning.setItemText(2, _translate('main_window', '1x1'))
        self.btn_snap.setText(_translate('main_window', 'snap'))
        self.cbox_exposure.setText(_translate('main_window', 'auto'))
        self.cbox_analog_gain.setText(_translate('main_window', 'auto'))
        self.btn_save.setText(_translate('main_window', 'save'))
        self.label_camera_binning.setText(_translate('main_window', 'binning'))
        self.btn_video.setText(_translate('main_window', 'video'))
        self.cbox_live.setText(_translate('main_window', ' live'))
        self.label_analog_gain.setText(_translate('main_window', 'analog gain'))
        self.label_exposure.setText(_translate('main_window', 'exposure'))
        self.cbox_normalise.setText(_translate('main_window', ' digital norm.'))
        self.cbox_show_scalebar.setText(_translate('main_window', ' show scalebar'))
        self.combobox_objective.setCurrentText(_translate('main_window', 'x40'))
        self.combobox_objective.setItemText(0, _translate('main_window', 'x40'))
        self.combobox_objective.setItemText(1, _translate('main_window', 'x20'))
        self.combobox_objective.setItemText(2, _translate('main_window', 'x10'))
        self.combobox_objective.setItemText(3, _translate('main_window', 'x5'))
        self.combobox_objective.setItemText(4, _translate('main_window', 'x4'))
        self.combobox_colourmap.setItemText(0, _translate('main_window', 'magma'))
        self.combobox_colourmap.setItemText(1, _translate('main_window', 'green'))
        self.combobox_colourmap.setItemText(2, _translate('main_window', 'viridis'))
        self.combobox_colourmap.setItemText(3, _translate('main_window', 'jet'))
        self.combobox_colourmap.setItemText(4, _translate('main_window', 'raw'))
        self.cbox_saturated.setText(_translate('main_window', ' saturated pixels'))
        self.label_gamma.setText(_translate('main_window', 'gamma'))
        self.label_objective.setText(_translate('main_window', 'objective'))
        self.label_colourmap.setText(_translate('main_window', 'colormap'))
        self.tabs.setTabText(self.tabs.indexOf(self.camera_tab), _translate('main_window', 'camera'))
        self.btn_stop_print.setText(_translate('main_window', 'stop all'))
        self.label_status_x_num.setText(_translate('main_window', '... x pos ...'))
        self.label_status_y_num.setText(_translate('main_window', '... y pos ...'))
        self.label_status_z_num.setText(_translate('main_window', '... z pos ...'))
        self.btn_pos_y.setText(_translate('main_window', '+y'))
        self.btn_neg_y.setText(_translate('main_window', '-y'))
        self.btn_pos_z.setText(_translate('main_window', '+z'))
        self.btn_neg_z.setText(_translate('main_window', '-z'))
        self.btn_pos_x.setText(_translate('main_window', '+x'))
        self.btn_neg_x.setText(_translate('main_window', '-x'))
        self.label_status_x.setText(_translate('main_window', 'x:'))
        self.label_status_y.setText(_translate('main_window', 'y:'))
        self.label_status_z.setText(_translate('main_window', 'z:'))
        self.label_xincrement.setText(_translate('main_window', 'x:'))
        self.label_yincrement.setText(_translate('main_window', 'y:'))
        self.label_zincrement.setText(_translate('main_window', 'z:'))
        self.btn_pause_print.setText(_translate('main_window', 'pause'))
        self.btn_load_gcode.setText(_translate('main_window', 'load g.code'))
        self.btn_laser_on.setText(_translate('main_window', 'laser on'))
        self.btn_laser_off.setText(_translate('main_window', 'laser off'))
        self.btn_set_laser_current.setText(_translate('main_window', 'current'))
        self.label_zcent_text.setText(_translate('main_window', 'z-cent'))
        self.btn_set_zcent.setText(_translate('main_window', 'set'))
        self.label_printer_section_text.setText(_translate('main_window', 'printer'))
        self.label_laser_section_text.setText(_translate('main_window', 'laser'))
        self.label_incr_1.setText(_translate('main_window', 'incr'))
        self.label_vel_1.setText(_translate('main_window', 'vel'))
        self.label_incr_2.setText(_translate('main_window', 'incr'))
        self.label_vel_2.setText(_translate('main_window', 'vel'))
        self.label_incr_3.setText(_translate('main_window', 'incr'))
        self.label_vel_3.setText(_translate('main_window', 'vel'))
        self.btn_custom_serial_send.setText(_translate('main_window', 'send'))
        self.label_custom_serial_send.setText(_translate('main_window', 'custom serial send'))
        self.tabs.setTabText(self.tabs.indexOf(self.printer_tab), _translate('main_window', 'printer'))
        self.btn_connect_all.setText(_translate('main_window', 'connect ALL'))
        self.btn_connect_x.setText(_translate('main_window', 'connect x'))
        self.btn_connect_y.setText(_translate('main_window', 'connect y'))
        self.btn_connect_z.setText(_translate('main_window', 'connect z'))
        self.btn_connect_laser.setText(_translate('main_window', 'connect laser'))
        self.btn_connect_camera.setText(_translate('main_window', 'connect camera'))
        self.status_controller.setText(_translate('main_window', '... status ...'))
        self.btn_disconnect_all.setText(_translate('main_window', 'disconnect all'))
        self.tabs.setTabText(self.tabs.indexOf(self.tab), _translate('main_window', 'controllers'))
        self.status_printer.setText(_translate('main_window', '... printer status ...'))
        self.status_fps_text.setText(_translate('main_window', 'FPS:'))
        self.status_fps_number.setText(_translate('main_window', '#####'))
        ############################
        self.lineedit_gamma.setText(str(self.gamma))
        self.lineedit_xincrement.setText(str(c.p_xincrement))
        self.lineedit_yincrement.setText(str(c.p_yincrement))
        self.lineedit_zincrement.setText(str(c.p_zincrement))
        self.lineedit_xvelocity.setText(str(c.p_vel_global))
        self.lineedit_yvelocity.setText(str(c.p_vel_global))
        self.lineedit_zvelocity.setText(str(c.p_zvel_global))
        self.lineedit_set_laser_current.setText('---')
        self.lineedit_custom_serial_send.setText('---')
        self.lineedit_set_zcent.setText(str(c.p_z_cent))
        self.lineedit_target_FPS.setText('1.0')

        return

    def actions(self):
        self.btn_change_directory.clicked.connect(self.change_directory)
        self.btn_snap.clicked.connect(c_camera.take_image)
        self.combobox_colourmap.currentIndexChanged.connect(c_graphic_display.update_image)
        self.cbox_normalise.stateChanged.connect(c_graphic_display.update_image)
        self.cbox_live.stateChanged.connect(c_camera.camera_live)
        self.lineedit_target_FPS.returnPressed.connect(c_camera.camera_live)
        self.lineedit_exposure.returnPressed.connect(c_camera.update_exposure_time)
        self.lineedit_analog_gain.returnPressed.connect(c_camera.update_gain)
        self.cbox_show_scalebar.stateChanged.connect(c_graphic_display.update_image)
        self.cbox_saturated.stateChanged.connect(c_graphic_display.update_image)
        self.slider_gamma.valueChanged.connect(lambda: self.update_gamma(1))
        self.lineedit_gamma.returnPressed.connect(lambda: self.update_gamma(0))
        self.btn_pos_x.clicked.connect(partial(c.uimove, float(1), float(0), float(0)))
        self.btn_pos_y.clicked.connect(partial(c.uimove, float(0), float(1), float(0)))
        self.btn_pos_z.clicked.connect(partial(c.uimove, float(0), float(0), float(-1)))
        self.btn_neg_x.clicked.connect(partial(c.uimove, float(-1), float(0), float(0)))
        self.btn_neg_y.clicked.connect(partial(c.uimove, float(0), float(-1), float(0)))
        self.btn_neg_z.clicked.connect(partial(c.uimove, float(0), float(0), float(1)))
        self.btn_load_gcode.clicked.connect(c.read_gcode)
        self.btn_set_zcent.clicked.connect(self.update_zcent)
        self.lineedit_set_zcent.returnPressed.connect(self.update_zcent)
        self.combobox_binning.currentIndexChanged.connect(c_camera.update_binning)
        self.btn_connect_laser.clicked.connect(c.connect_laser)
        self.btn_laser_on.clicked.connect(partial(c.laser_on, 100))
        self.btn_laser_off.clicked.connect(partial(c.laser_on, 0))
        self.lineedit_set_laser_current.returnPressed.connect(c.laser_set)
        self.btn_set_laser_current.clicked.connect(c.laser_set)
        self.btn_save.clicked.connect(self.save_image)
        self.cbox_exposure.stateChanged.connect(c_camera.toggle_auto_exposure)
        self.cbox_analog_gain.stateChanged.connect(c_camera.toggle_auto_gain)
        self.btn_connect_camera.clicked.connect(c_camera.connect_camera)
        self.btn_disconnect_all.clicked.connect(self.disconnect_all)
        self.btn_connect_all.clicked.connect(self.connect_all)
        self.btn_connect_x.clicked.connect(c.connect_xy)
        self.btn_connect_y.clicked.connect(c.connect_xy)
        self.btn_connect_z.clicked.connect(c.connect_z)
        self.lineedit_xincrement.returnPressed.connect(c.position_velocity_toggled)
        self.lineedit_yincrement.returnPressed.connect(c.position_velocity_toggled)
        self.lineedit_zincrement.returnPressed.connect(c.position_velocity_toggled)
        self.lineedit_xvelocity.returnPressed.connect(c.position_velocity_toggled)
        self.lineedit_yvelocity.returnPressed.connect(c.position_velocity_toggled)
        self.lineedit_zvelocity.returnPressed.connect(c.position_velocity_toggled)
        self.btn_print.clicked.connect(self.start_printing)
        self.lineedit_custom_serial_send.returnPressed.connect(c.custom_serial_send)
        self.btn_custom_serial_send.clicked.connect(c.custom_serial_send)
        self.btn_ROI_in.clicked.connect(partial(self.zoom, 1))
        self.btn_ROI_out.clicked.connect(partial(self.zoom, 0))
        self.btn_ROI_home.clicked.connect(partial(self.zoom, 2))
        return

    def connect_all(self):
        print('connecting all')
        try:
            if c_main_window.btn_connect_z.text() == 'connect z':
                c.connect_z()
        except:
            print('no z stage connection')
        try:
            if c_main_window.btn_connect_x.text() == 'connect x':
                c.connect_xy()
        except:
            print('no xy stage connection')
        try:
            if c_main_window.btn_connect_laser.text() == 'connect laser':
                c.connect_laser()
        except:
            print('no laser connection')
        try:
            if c_main_window.btn_connect_camera.text() == 'connect camera':
                c_camera.connect_camera()
        except:
            print('no camera connection')

        return

    def disconnect_all(self):
        print('disconnecting all')
        if c_main_window.btn_connect_z.text() == 'disconnect z':
            c.connect_z()
        if c_main_window.btn_connect_x.text() == 'disconnect x':
            c.connect_xy()
        if c_main_window.btn_connect_laser.text() == 'disconnect laser':
            c.connect_laser()
        if c_main_window.btn_connect_camera.text() == 'disconnect camera':
            c_camera.connect_camera()
        return

    def update_zcent(self):
        print('zcent changed function')
        c.p_z_cent = np.array(self.lineedit_set_zcent.text(),dtype='float64')
        if c_main_window.btn_load_gcode.text() == 'unload g.code':
            c.read_gcode()
        self.lineedit_set_zcent.setText(str(c.p_z_cent))
        self.status_printer.setText('z-cent updated')
        return

    def change_directory(self):
        print('change directory function')
        if c_main_window.btn_load_gcode.text() == 'unload g.code':
            c.read_gcode()

        _filenames = []
        self.pathname = str(QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory'))
        print(self.pathname)
        try:
            c_main_window.list_current_directory.clear()
            self.filenames = os.listdir(self.pathname)
            contains_gcode = 0
            for i in range(len(self.filenames)):
                item = self.filenames[i]
                if '.gcode' in item:
                    self.list_current_directory.addItem(item)
                    contains_gcode = 1
                    _filenames.append(item)

            if contains_gcode:
                self.status_current_directory.setText(self.pathname)
            else:
                self.status_current_directory.setText('no *.gcode files here!')
                now = datetime.datetime.now().time()
                if np.mod(now.second,2) == 0:
                    self.status_current_directory.setStyleSheet('color:#FF0000;')
                else:
                    self.status_current_directory.setStyleSheet('color:#FFFF00;')

            c_main_window.list_current_directory.setCurrentRow(0)
            os.chdir(self.pathname)
            self.status_printer.setText('directory changed')
        except:
            c_main_window.list_current_directory.clear()
            self.status_current_directory.setText('no directory selected!')
            now = datetime.datetime.now().time()
            if np.mod(now.second,2) == 0:
                self.status_current_directory.setStyleSheet('color:#FF0000;')
            else:
                self.status_current_directory.setStyleSheet('color:#FFFF00;')
            self.status_printer.setText('directory not changed')

        self.filenames = _filenames
        return

    def status_text_update_image(self):
        print('update image text status')

        image_status_text = ''.join([
            'image size: ',str(c_camera.img_raw.shape),
            ', colourmap: ',self.combobox_colourmap.currentText()
            ])
        self.status_image.setText(image_status_text)
        app.processEvents()
        return

    def update_gamma(self,_input):
        print('update gamma func')
        if _input:
            self.gamma = c_main_window.slider_gamma.value()/100 # read from the slider
            c_main_window.lineedit_gamma.setText(str(self.gamma)) # update text
            c_graphic_display.update_image()

        if not _input:
            self.gamma = float(c_main_window.lineedit_gamma.text()) # read from the text input
            c_main_window.slider_gamma.setSliderPosition(self.gamma*100) # update slider
            c_graphic_display.update_image()
        return

    def repaint_image(self):
        print('repainting image function')

        # if c_main_window.combobox_colourmap.currentIndex() == 4: ## raw image
        #     if self.zoom_factor > 1:
        #         print(self.zoom_factor)
        #         r1 = c_camera.img_raw.shape[0]
        #         c1 = c_camera.img_raw.shape[1]
        #         r2 = int(np.round(r1/self.zoom_factor))
        #         c2 = int(np.round(c1/self.zoom_factor))
        #         # c_camera.img_raw = c_camera.img_raw[int((r1-r2)/2):int((r1-r2)/2)+r2, int((c1-c2)/2):int((c1-c2)/2)+c2]
        #         c_graphic_display.img = c_camera.img_raw[int((r1-r2)/2):int((r1-r2)/2)+r2, int((c1-c2)/2):int((c1-c2)/2)+c2]
        #     else:
        #         c_graphic_display.img = c_camera.img_raw
        #     print(c_graphic_display.img.shape[1], c_graphic_display.img.shape[0])
        #     qimage = QtGui.QImage(c_graphic_display.img.tobytes(), c_graphic_display.img.shape[1], c_graphic_display.img.shape[0], QtGui.QImage.Format_Indexed8)
        #     print(qimage.size())
        # else:
        c_graphic_display.img = c_graphic_display.img_fin
        qimage = QtGui.QImage(c_graphic_display.img.tobytes(), c_graphic_display.img.shape[1], c_graphic_display.img.shape[0], QtGui.QImage.Format_RGBA8888)

        pixmap_image = QtGui.QPixmap(qimage)
        c_main_window.image_camera.setPixmap(pixmap_image)
        print("repainting with maximum %d threads" % self.threadpool.maxThreadCount())
        return

    def save_image(self):
        print('saving image function')
        path = (QFileDialog.getSaveFileName(self, 'Save file', '', 'PNG (*.png))|*.png'))
        if path:
            mpl.image.imsave(path[0], c_graphic_display.img)
            c_main_window.status_printer.setText('Saved to: '+path[0])
        return

    def zoom(self,zin):
        if zin == 1: # zoom in
            self.zoom_factor = self.zoom_factor*1.2
        elif zin == 0: # zoom out
            self.zoom_factor = self.zoom_factor/1.2
        elif zin == 2: # zoom home
            self.zoom_factor = 1
        if self.zoom_factor < 1:
            self.zoom_factor = 1
            self.status_printer.setText('can''t zoom < x1!')
        if self.zoom_factor > 10:
            self.zoom_factor = 10
            self.status_printer.setText('can''t zoom > x10!')
        c_graphic_display.update_image()
        return

    def update_hist(self):
        print('update histogram function')
        # t = time.time()
        h1 = (c_camera.img_raw.flatten()*(80/256))
        h1 = np.unique(h1.astype(np.uint8), return_counts=True)
        x1 = np.arange(80)
        y1 = np.zeros(80)
        for i in np.unique(h1[0]):
            y1[i] = h1[1][np.where(h1[0] == i)]

        if self.hist_flag1 == None or self.hist_flag2 == None:
            self.hist_flag1 = 1
            self.hist_flag2 = 1
            y2 = np.zeros(80)
        else:
            if self.cbox_normalise.isChecked() or self.gamma != 1:
                h2 = (c_graphic_display.img_norm.flatten()*(80/256))
                h2 = np.unique(np.asarray(h2, dtype=np.uint8), return_counts=True)
                y2 = np.zeros(80)
                for i in np.unique(h2[0]):
                    y2[i] = h2[1][np.where(h2[0] == i)]
            else:
                y2 = np.zeros(80)

        x11 = x1[y1 != 0]
        y1  = y1[y1 != 0]
        x12 = x1[y2 != 0]
        y2  = y2[y2 != 0]
        self.hist.plot(x11*(256/80),y1, pen = ('b'), linewidth=2, alpha=0.5, clear = True)
        # self.histogram.setData(x1*(256/80),y1, pen = ('k'), linewidth=2)
        self.hist.plot(x12*(256/80),y2, pen = ('r'), linewidth=2, alpha=0.5)
        # self.histogram.setData(x1*(256/80),y2)
        # self.axes.axis(ymin=1,ymax=2.5*np.amax(np.hstack([y1,y2]),0))

    def print_output(self, s):
        print(s)

    def print_complete(self):
        print("Printing Complete")

    def progress_fn(self, n):
        print("%d%% done" % n)

    def start_printing(self):
        QtGui.QApplication.processEvents()
        # Pass the function to execute
        worker = pt.Worker(self.printing) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.print_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)
        print("Active thread count: " + str(self.threadpool.activeThreadCount()))

    def printing(self, progress_callback):
        #progress
        for n in range (0, 5):
            # time.sleep(1)
            progress_callback.emit(int(n * 100 / 4))

        if c_main_window.btn_load_gcode.text() == 'unload g.code':
            if self.btn_connect_z.text() == 'disconnect z' and self.btn_connect_x.text() == 'disconnect x' and self.btn_connect_laser.text() == 'disconnect laser':

                c.xy.sendPN('MOV 1 0 2 0')
                laser_off_str = 'slc 0' + chr(13)
                laser_off_str = str.encode(laser_off_str)
                laser_off_str = bytes(laser_off_str)
                c.l.writePN(laser_off_str)

                # add dialog here are you ready to print?!

                linear_tolerance = 0.05 # 50 um (in mm),
                # ~ for 1.67 mm/sec total velocity          * 0.03,
                # (float(xvel)**2+float(yvel))**2)**0.5)    * 0.03
                laser_current_old = np.array(0,dtype='float64')
                xpos_old = 0
                ypos_old = 0
                zpos_old = 0
                xvel_old = 0
                yvel_old = 0
                zvel_old = 0

                c.time_laser = []
                c.time_xymov = []
                c.time_xyisready = []
                c.time_xyismoving = []
                c.time_line = []
                c.time_vector = []
                c.c_xpos_vector = []
                c.c_ypos_vector = []

                # printing from gcode starts here
                c.print_start_time = time.time()
                while len(c.g) > 0:
                    current_line = c.g.loc[0] ## get the first row
                    self.list_current_directory.takeItem(0) # remove and get the first row
                    c.g = c.g[1:] ## update the dataframe
                    c.g = c.g.reset_index(drop=True)
                # for i in range(len(c.g)):
                #
                #     # time_line_start = time.time()
                #     current_line = c.g.loc[i]
                    print('DB@ '+ str(current_line['gcode']))
                    print(current_line)
                    wait_time = current_line['wait']
                    laser_current = current_line['laser']

                    if wait_time != 0: # if its not a wait time
                        time.sleep(wait_time)
                    elif laser_current != laser_current_old:  # and its not a laser power change
                        # s = time.time()
                        laser = 'slc ' + str(laser_current) + chr(13)
                        laser = str.encode(laser)
                        laser = bytes(laser)
                        c.l.writePN(laser)
                        # c.time_laser.append(time.time()-s)
                        laser_current_old = laser_current
                    else: # its a velocity or position change
                        xpos = current_line['xpos']
                        ypos = current_line['ypos']
                        zpos = current_line['zpos']
                        xvel = current_line['xvel']
                        yvel = current_line['yvel']
                        zvel = current_line['zvel']

                        if zvel_old != zvel:
                            # gcs.send(c.z,'VEL 1 ' + zvel)
                            c.z.sendPN('VEL 1 ' + zvel)
                            ready = False
                            while ready != True:
                                # ready = gcs.read(c.z, chr(7))
                                ready = c.z.readPN(chr(7))
                                if 177 == ord(ready.strip()):
                                    ready = True
                                elif 176 == ord(ready.strip()):
                                    ready = False
                            zvel_old = zvel

                        if zpos_old != zpos:
                            # gcs.send(c.z, 'MOV 1 ' + zpos)
                            c.z.sendPN('MOV 1 ' + zpos)
                            moving = 1
                            while moving > 0:
                                # moving = int(gcs.read(c.z, chr(5)))
                                moving = int(c.z.readPN(chr(5)))
                                self.update_position_graph()
                            zpos_old = zpos

                        if xvel_old != xvel or yvel_old != yvel:
                            # gcs.send(c.xy, 'VEL 1 ' + xvel + ' 2 ' + yvel)
                            c.xy.sendPN('VEL 1 ' + xvel + ' 2 ' + yvel)
                            ready = False
                            while ready != True:
                                # ready = gcs.read(c.xy, chr(7))
                                ready = c.xy.readPN(chr(7))
                                if 177 == ord(ready.strip()):
                                    ready = True
                                elif 176 == ord(ready.strip()):
                                    ready = False
                            xvel_old = xvel
                            yvel_old = yvel
                            if (((float(xvel)**2+float(yvel))**2)**0.5) >= c.p_max_vel_global:
                                if float(xvel) == c.p_max_vel_global:
                                    linear_tolerance = float(yvel)*0.03
                                elif float(yvel) == c.p_max_vel_global:
                                    linear_tolerance = float(xvel)*0.03
                            else:
                                linear_tolerance = (((float(xvel)**2+float(yvel))**2)**0.5)*0.025

                        if xpos_old != xpos or ypos_old != ypos:
                            # s = time.time()
                            # gcs.send(c.xy, 'MOV 1 ' + xpos + ' 2 ' + ypos)
                            c.xy.sendPN('MOV 1 ' + xpos + ' 2 ' + ypos)
                            # c.time_xymov.append(time.time()-s)
                            ready = False
                            while ready != True:
                                # s = time.time()
                                # ready = gcs.read(c.xy, chr(7))
                                ready = c.xy.readPN(chr(7))
                                if 177 == ord(ready.strip()):
                                    ready = True
                                elif 176 == ord(ready.strip()):
                                    ready = False
                                else:
                                    print('probably an error has occured')
                                # c.time_xyisready.append(time.time()-s)
                            moving = 1
                            xpos = np.array(xpos,dtype='float64')
                            ypos = np.array(ypos,dtype='float64')
                            while moving > 0:
                                # s = time.time()
                                # pos = gcs.read(c.xy,'POS? 1 2')
                                pos = c.xy.readPN('POS? 1 2')
                                pos = pos.split('\n')
                                pos0 = pos[0]
                                pos0 = np.array(pos0[2:],dtype='float64')
                                pos1 = pos[1]
                                pos1 = np.array(pos1[2:],dtype='float64')

                                c.time_vector.append(time.time())
                                c.c_xpos_vector.append(pos0)
                                c.c_ypos_vector.append(pos1)

                                pos_diff = np.abs(xpos-pos0) + np.abs(ypos-pos1)
                                if pos_diff < linear_tolerance:
                                    moving = 0

                                self.update_position_graph()
                                # c.time_xyismoving.append(time.time()-s)

                            xpos_old = str(xpos)
                            ypos_old = str(ypos)

                    # c.time_line.append(time.time()-time_line_start)

                c.print_end_time = time.time()
                print('printing took: ' + str(np.round((c.print_end_time-c.print_start_time)/60,8)) + ' mins')
                c.flush_laser
                c.l.write(laser_off_str)
                c.xy.sendPN('MOV 1 0 2 0') # move to center
                # dialog print finished

            else:
                c_main_window.status_printer.setText('connect to the stages and laser')
        else:
            c_main_window.status_printer.setText('load in a *.gcode file!')

        # np.savetxt("c.time_laser.csv", c.time_laser, delimiter=",")
        # np.savetxt("c.time_xymov.csv", c.time_xymov, delimiter=",")
        # np.savetxt("c.time_xyisready.csv", c.time_xyisready, delimiter=",")
        # np.savetxt("c.time_xyismoving.csv", c.time_xyismoving, delimiter=",")
        # np.savetxt("c.time_line.csv", c.time_line, delimiter=",")

        # plt.hist(c.time_xyismoving)

        # plt.figure(0)
        # plt.plot(c.time_vector, np.array(c.c_xpos_vector)-np.array(c.c_ypos_vector))
        # plt.plot(c.time_vector, np.array(c.c_xpos_vector))
        # plt.plot(c.time_vector, np.array(c.c_ypos_vector))
        # plt.show()

        # plt.figure(0)
        # sp1 = plt.subplot(221)
        # plt.hist(c.time_laser)
        # sp1.set_ylabel('laser')

        # sp2 = plt.subplot(222)
        # plt.hist(c.time_xymov)
        # sp2.set_ylabel('move')

        # sp3 = plt.subplot(223)
        # plt.hist(c.time_xyisready)
        # sp3.set_ylabel('isready')

        # sp4 = plt.subplot(224)
        # plt.hist(c.time_xyismoving)
        # sp4.set_ylabel('ismoving')

        # something to update the GUI pos display here
        playsound('C:/Users/sunyi/Desktop/app/flow_printer_app/water-droplet-2.mp3')
        return "Done"

    def update_position_graph(self):
        ## update position pyqtgraphs
        c.p_zpos_current = c.z.qPOS(1)
        c.p_zpos_current = c.p_zpos_current[1]
        pos = c.xy.qPOS([1,2])
        c.p_xpos_current = pos[1]
        c.p_ypos_current = pos[2]
        self.label_status_x_num.setText(str(np.round(c.p_xpos_current,6)))
        self.label_status_y_num.setText(str(np.round(c.p_ypos_current,6)))
        self.label_status_z_num.setText(str(np.round(c.p_zpos_current,6)))

        # c_main_window.image_printer_position_xy.update_plot()
        self.xy_graph_plot.setData([c.p_xpos_current], [c.p_ypos_current])
        self.xz_graph_plot.setData([c.p_xpos_current], [c.p_z_cent-c.p_zpos_current])
        print("x = " + str(c.p_xpos_current))
        print("y = " + str(c.p_ypos_current))
        print("z = " + str(c.p_z_cent-c.p_zpos_current))


class camera():
    def __init__(self):
        self.fps = 1
        self.timer_value = 1
        try:
            # initialize settings
            self.cam = Camera() # Acquire Camera
            self.cam.init() # Initialize camera
            self.cam.PixelFormat = 'Mono8'
            self.cam.GammaEnable = False
            self.cam.GainAuto = 'Off'
            self.cam.AcquisitionMode = 'SingleFrame'
            self.cam.AcquisitionFrameRateEnable = False
            self.cam.AcquisitionFrameCount = 2
            self.cam.BinningHorizontal = 4
            self.cam.BinningVertical = 4
            self.cam.ExposureAuto = 'Off'
            self.max_gain = self.cam.get_info('Gain')['max']
            self.min_gain = self.cam.get_info('Gain')['min']
            self.max_exposure = self.cam.get_info('ExposureTime')['max']
            self.min_exposure = self.cam.get_info('ExposureTime')['min']
            self.cam.Gain = max(min(10, self.max_gain), self.min_gain)
            self.cam.ExposureTime = max(min(100, self.max_exposure), self.min_exposure) # microseconds
            self.cam.start() # Start recording
            self.img_raw = self.cam.get_array() # Get frames
            self.cam.stop() # Stop recording
        except:
            if not hasattr(self, 'img_raw'):
                print('camera init failed...')
                self.img_raw = np.random.rand(100,100)*255
                self.img_raw = self.img_raw.astype(np.uint8)
                self.cam = []
        self.live_timer = QTimer()
        self.live_timer.timeout.connect(self.take_image)
        return

    def connect_camera(self):
        print('connect camera toggled')
        if c_main_window.btn_connect_camera.text() == 'disconnect camera':
            print('disconnecting camera')
            try:
                c_camera.cam.stop() # Stop recording if camera caught on
            except:
                0

            if c_main_window.cbox_live.isChecked():
                c_camera.live_timer.stop()
            try:
                c_camera.cam.close()
                time.sleep(0.2)
            except:
                print('couldn''t close/clean up camera')
            c_camera.cam = 0
            c_main_window.btn_connect_camera.setText('connect camera')
        else:
            print('connecting camera')
            self.cam = Camera() # Acquire Camera
            self.cam.init() # Initialize camera
            self.cam.PixelFormat = 'Mono8'
            self.cam.GammaEnable = False
            self.cam.GainAuto = 'Off'
            self.cam.AcquisitionMode = 'SingleFrame'
            self.cam.AcquisitionFrameRateEnable = False
            self.cam.AcquisitionFrameCount = 2
            self.cam.BinningHorizontal = 4
            self.cam.BinningVertical = 4
            self.cam.ExposureAuto = 'Off'
            self.max_gain = self.cam.get_info('Gain')['max']
            self.min_gain = self.cam.get_info('Gain')['min']
            self.max_exposure = self.cam.get_info('ExposureTime')['max']
            self.min_exposure = self.cam.get_info('ExposureTime')['min']
            self.cam.Gain = max(min(2, self.max_gain), self.min_gain)
            self.cam.ExposureTime = max(min(50, self.max_exposure), self.min_exposure) # microseconds
            self.cam.start() # Start recording
            self.img_raw = self.cam.get_array() # Get frames
            self.cam.stop() # Stop recording
            self.update_binning()
            self.update_exposure_time()
            self.update_gain()
            c_main_window.btn_connect_camera.setText('disconnect camera')
        return

    def toggle_auto_exposure(self):
        if c_main_window.cbox_exposure.isChecked():
            self.cam.ExposureAuto = 'Continuous'
            c_main_window.lineedit_exposure.setText('--')
        else:
            self.cam.ExposureAuto = 'Off'
            c_main_window.lineedit_exposure.setText(str(np.round(self.cam.get_info('ExposureTime')['value'],2))+' ms')
            self.update_exposure_time()
        c_main_window.status_printer.setText('exposure time toggled')
        return

    def toggle_auto_gain(self):
        if c_main_window.cbox_analog_gain.isChecked():
            self.cam.GainAuto = 'Continuous'
            c_main_window.lineedit_analog_gain.setText('--')
        else:
            c_camera.cam.GainAuto = 'Off'
            c_main_window.lineedit_analog_gain.setText(str(np.round(self.cam.get_info('Gain')['value'],2))+' dB')
            self.update_gain()
        c_main_window.status_printer.setText('auto gain toggled')
        return

    def update_binning(self):
        print('update camera binning function')
        try:
            if c_main_window.combobox_binning.currentIndex() == 0:
                self.cam.BinningHorizontal = 4
                self.cam.BinningVertical = 4
            if c_main_window.combobox_binning.currentIndex() == 1:
                self.cam.BinningHorizontal = 2
                self.cam.BinningVertical = 2
            if c_main_window.combobox_binning.currentIndex() == 2:
                self.cam.BinningHorizontal = 1
                self.cam.BinningVertical = 1
            c_main_window.status_printer.setText('binning updated')
        except:
            print('binning not set....')
        return

    def update_exposure_time(self):
        print('updating exposure time')
        try:
            user_exp = np.round(np.array(re.sub('[^\d\.]', '', c_main_window.lineedit_exposure.text()),dtype='float64'),0)
            self.cam.ExposureTime = max(min(user_exp, self.max_exposure), self.min_exposure)
            c_main_window.lineedit_exposure.setText(str(np.round(c_camera.cam.get_info('ExposureTime')['value'],2))+' ms')
            c_main_window.status_printer.setText('exposure time updated')
        except:
            print('exposure time not set....')
        return

    def update_gain(self):
        print('updating gain')
        try:
            user_gain = np.round(np.array(re.sub('[^\d\.]', '', c_main_window.lineedit_analog_gain.text()),dtype='float64'),1)
            self.cam.Gain = max(min(user_gain, self.max_gain), self.min_gain)
            c_main_window.lineedit_analog_gain.setText(str(np.round(self.cam.get_info('Gain')['value'],2))+' dB')
            c_main_window.status_printer.setText('gain updated')
        except:
            print('gain not set....')
        return

    def camera_live(self):
        print('camera live toggled')
        self.fps = np.array(re.sub('[^\d\.]', '', c_main_window.lineedit_target_FPS.text()),dtype='float64')
        c_main_window.lineedit_target_FPS.setText(str(self.fps)+' Hz')
        if c_main_window.cbox_live.isChecked():
            self.live_timer.stop()
            self.timer_value = (1/self.fps)*1000
            self.live_timer.start(self.timer_value)
            c_main_window.status_printer.setText('camera live')
        else:
            self.live_timer.stop()
            c_main_window.status_printer.setText('camera stopped')
        return

    def take_image(self):
        print('take image function')
        c_main_window.take_image_start_time = time.time()
        c_main_window.status_capture.setText('capturing image...')

        try:
            print('taking image')
            c_camera.cam.start() # Start recording
            c_camera.img_raw = c_camera.cam.get_array() # Get frames
            c_camera.cam.stop() # Stop recording
        except:
            print('generate random noise')
            self.img_raw = np.random.rand(100,100)*255
            self.img_raw = self.img_raw.astype(np.uint8)

        print('img time taken: '+str(time.time()-c_main_window.take_image_start_time))
        c_main_window.status_capture.setText('displaying image...')


        c_graphic_display.update_image()
        #c_graphic_display.fps_counter = np.append(c_graphic_display.fps_counter,time.time())
        #c_graphic_display.fps_counter = np.delete(c_graphic_display.fps_counter, 0)
        #c_main_window.status_fps_number.setText(str(np.round(1/np.mean(np.diff(c_graphic_display.fps_counter)),3)))
        print('current saved value for fps is: ' + str(self.fps) + ' current timer value is: ' + str(self.timer_value))


class printer():

    def __init__(self):
        # controller variables
        self.xy = 0
        self.z = 0
        self.l = 0
        # printer velocity variables
        self.p_vel_global = (10)      # maybe change after extensive PID calibrations
        self.p_zvel_global = float(1)
        self.p_max_vel_global = float(10)
        self.p_max_zvel_global = float(1)
        # printer position variables
        self.p_xpos_current = float(0)
        self.p_ypos_current = float(0)
        self.p_zpos_current = np.array(25, dtype ='float64')
        self.p_xpos_target = self.p_xpos_current
        self.p_ypos_target = self.p_ypos_current
        self.p_zpos_target = self.p_zpos_current
        # printer velocity variables
        self.p_xvel_current = self.p_vel_global
        self.p_yvel_current = self.p_vel_global
        self.p_zvel_current =self.p_zvel_global
        self.p_xvel_target = self.p_xvel_current
        self.p_yvel_target = self.p_yvel_current
        self.p_zvel_target = self.p_zvel_current

        # DB PN - 20201112
        self.laser_current_max_power = 137.8

        # printer increment vars
        self.p_xincrement = float(1)
        self.p_yincrement = float(1)
        self.p_zincrement = float(0.25)
        # printer other variables
        self.p_z_cent = float(25)
        # gcode variables
        self.G = 0
        self.g = 0
        return

    def read_gcode(self):
        print('reading gcode')
        self.g = [0]
        self.g_size = [0]
        if c_main_window.btn_load_gcode.text() == 'unload g.code': # toggle gcode obs and directory
            print('unload gcode')
            c_main_window.list_current_directory.clear()
            _filenames = []
            for i in range(len(c_main_window.filenames)):
                item = c_main_window.filenames[i]
                if '.gcode' in item:
                    c_main_window.list_current_directory.addItem(item)
                    print('item' + item)
                    _filenames.append(item)
            c_main_window.list_current_directory.setCurrentRow(0)
            os.chdir(c_main_window.pathname)
            c_main_window.filenames = _filenames
            c_main_window.btn_load_gcode.setText('load g.code')
            c_main_window.btn_load_gcode.setStyleSheet('color:#000000;')
            c_main_window.btn_print.setStyleSheet('color:#808080')
        else:
            print('loading gcode') # toggle gcode obs and directory
            if c_main_window.list_current_directory.currentRow() == -1:
                c_main_window.btn_print.setStyleSheet('color:#808080')
                c_main_window.status_current_directory.setText('select *.gcode file!')
                now = datetime.datetime.now().time()
                if np.mod(now.second,2) == 0:
                    c_main_window.status_current_directory.setStyleSheet('color:#FF0000;')
                else:
                    c_main_window.status_current_directory.setStyleSheet('color:#FFFF00;')
            else:
                # read in the gcode file
                filename = c_main_window.filenames[c_main_window.list_current_directory.currentRow()]
                gcode = open(filename, 'r')
                gcode = gcode.read()
                gcode = gcode.split('\n')
                gcode = [i.strip(' ') for i in gcode]
                c_main_window.list_current_directory.clear()
                for i in range(len(gcode)):
                    item = gcode[i]
                    print(type(item))
                    if len(item) > 0:
                        c_main_window.list_current_directory.addItem(item)
                    # c_main_window.list_current_directory.addItem(item)
                gcode = DataFrame(gcode, columns=['gcode'])
                gcode = gcode.replace('', np.nan)
                # gcode_blank_line_ind = np.where(pd.isnull(gcode))
                gcode_line_ind = np.where(pd.notnull(gcode))

                # initialize variables for controller quick access
                laser_state = np.array(0)
                xvel = np.array(0)
                yvel = np.array(0)
                zvel = np.array(0)
                xpos = np.array(0)
                ypos = np.array(0)
                zpos = np.array(0)
                xpos_old = np.array(0)
                ypos_old = np.array(0)
                zpos_old = np.array(0)

                Gcode = []
                Laser_state = []
                Xpos = []
                Ypos = []
                Zpos = []
                Xvel = []
                Yvel = []
                Zvel = []
                Gcode_estimated_time_to_completion = []
                Wait_time = []

                for gcode_line in gcode_line_ind[0]:
                    g_line = gcode.loc[gcode_line,'gcode']
                    try: # remove comments in the gcode
                        semicolon_ind = g_line.index(';')
                    except:
                        semicolon_ind = len(g_line)

                    g_line = g_line[0:semicolon_ind]
                    g_cell = g_line.split(' ')
                    gm_ind = [i for i, s in enumerate(g_cell) if 'G' in s]
                    if not gm_ind:
                        gm_ind = [i for i, s in enumerate(g_cell) if 'M' in s]
                    x_ind = [i for i, s in enumerate(g_cell) if 'X' in s]
                    y_ind = [i for i, s in enumerate(g_cell) if 'Y' in s]
                    z_ind = [i for i, s in enumerate(g_cell) if 'Z' in s]
                    f_ind = [i for i, s in enumerate(g_cell) if 'F' in s]
                    s_ind = [i for i, s in enumerate(g_cell) if 'S' in s]

                    if gm_ind:
                        gm_ind = int(re.sub('[^\d\.]', '', g_cell[gm_ind[0]]))
                    if x_ind:
                        xpos = np.array(re.sub('[^\d\.]', '', g_cell[x_ind[0]]), dtype='float64')
                    else:
                        xpos = xpos_old
                    if y_ind:
                        ypos = np.array(re.sub('[^\d\.]', '', g_cell[y_ind[0]]), dtype='float64')
                    else:
                        ypos = ypos_old
                    if z_ind:
                        zpos = np.array(re.sub('[^\d\.\-]', '', g_cell[z_ind[0]]), dtype='float64')
                    else:
                        zpos = zpos_old
                    if f_ind:
                        f_ind = np.array(re.sub('[^\d\.]', '', g_cell[f_ind[0]]), dtype='float64')
                    else:
                        f_ind = np.array(0,dtype='float64')
                    if s_ind:
                        s_ind = np.array(re.sub('[^\d\.]', '', g_cell[s_ind[0]]), dtype='float64')
                    else:
                        s_ind = np.array(0,dtype='float64')

                    gcode_estimated_time_to_completion = 0.001;

                    if gm_ind == 1 or gm_ind == 0:
                        distance = np.absolute([xpos-xpos_old, ypos-ypos_old])
                        total_distance = ((np.nansum(distance**2))**0.5)
                        if total_distance > 0:
                            if gm_ind == 0:
                                total_velocity = self.p_max_vel_global
                            else:
                                total_velocity = f_ind/60 # from mm/min -> in mm/sec
                            velocity = total_velocity*(distance/total_distance)
                            xvel = np.round(np.nanmin([velocity[0], self.p_max_vel_global]),4)
                            yvel = np.round(np.nanmin([velocity[1], self.p_max_vel_global]),4)
                            zvel = np.round(np.nanmin([f_ind/60, self.p_max_zvel_global]),4)

                            gcode_estimated_time_to_completion = total_distance/total_velocity

                        if not np.isnan(xpos):
                            xpos_old = xpos
                        if not np.isnan(ypos):
                            ypos_old = ypos
                        if not np.isnan(zpos):
                            zpos_old = zpos
                    if gm_ind == 4:
                        wait_time = s_ind/1000 # since in msec for gcode
                        gcode_estimated_time_to_completion = wait_time
                    else:
                        wait_time = 0
                    if gm_ind == 20:
                        raise Exception('gcode is in inches, please convert to mm')
                    if gm_ind == 21:
                        print('gcode is in mm')
                    if gm_ind == 90:
                        print('XYZ absolute')
                    if gm_ind == 91:
                        raise Exception('coordinate system should be absolute, & control @PI_')
                    if gm_ind == 106:
                        laser_state = np.array(c.laser_current_max_power, dtype='float64')*(np.array(s_ind, dtype='float64')/np.array(100, dtype='float64'))
                    if gm_ind == 203:
                        raise Exception('M203 codes have not been implemented')
                    if xvel == 0:
                        xvel = self.p_max_vel_global
                    if yvel == 0:
                        yvel = self.p_max_vel_global
                    if zvel == 0:
                        zvel = self.p_max_zvel_global

                    # the calculus to with on the PI stages
                    xpos = xpos - 10
                    ypos = ypos - 10
                    zpos = self.p_z_cent + zpos

                    Gcode.append(g_line)
                    Laser_state.append(laser_state)
                    Xpos.append(xpos)
                    Ypos.append(ypos)
                    Zpos.append(zpos)
                    print(zpos)
                    Xvel.append(xvel)
                    Yvel.append(yvel)
                    Zvel.append(zvel)
                    Gcode_estimated_time_to_completion.append(gcode_estimated_time_to_completion)
                    Wait_time.append(wait_time)

                # load into dataframe ready for interpretation
                gcode = DataFrame(Gcode, columns=['gcode'])
                gcode['laser'] = Laser_state
                gcode['xpos'] = Xpos
                gcode['ypos'] = Ypos
                gcode['zpos'] = Zpos
                gcode['xvel'] = Xvel
                gcode['yvel'] = Yvel
                gcode['zvel'] = Zvel
                gcode['time'] = Gcode_estimated_time_to_completion
                gcode['wait'] = Wait_time
                c_main_window.btn_load_gcode.setText('unload g.code')
                c_main_window.btn_load_gcode.setStyleSheet('color:#C0C0C0;')
                c_main_window.status_current_directory.setText('gcode loaded')

                if abs(gcode['xpos'].max()) > 10 or abs(gcode['ypos'].max()) > 10 or gcode['zpos'].max() > 29 or gcode['zpos'].min() < 21:
                    warnings.warn('you got some whack x, y or z values; unloading gcode')
                    gcode = [0]
                    c.read_gcode() # to unload

                # display code
                self.g_size = len(gcode)
                self.g = gcode
                pd.options.display.width = 0
                pd.set_option('display.max_rows',len(self.g))
                pd.set_option('display.max_columns',9)
                pd.set_option('max_colwidth',8)
                print(self.g)# pandas dataframe
                c_main_window.btn_print.setStyleSheet('color:#FF0000')

                gcode['xpos'] = gcode['xpos'].apply(str)
                gcode['ypos'] = gcode['ypos'].apply(str)
                gcode['zpos'] = gcode['zpos'].apply(str)
                gcode['xvel'] = gcode['xvel'].apply(str)
                gcode['yvel'] = gcode['yvel'].apply(str)
                gcode['zvel'] = gcode['zvel'].apply(str)

        return

    def position_velocity_toggled(self):

        c.p_xvel_target = np.min([self.p_vel_global,float(re.sub('[^\d\.]', '', c_main_window.lineedit_xvelocity.text()))])
        c.p_yvel_target = np.min([self.p_vel_global,float(re.sub('[^\d\.]', '', c_main_window.lineedit_yvelocity.text()))])
        c.p_zvel_target = np.min([self.p_zvel_global,float(re.sub('[^\d\.]', '', c_main_window.lineedit_zvelocity.text()))])
        c_main_window.lineedit_xvelocity.setText(str(c.p_xvel_target))
        c_main_window.lineedit_yvelocity.setText(str(c.p_yvel_target))
        c_main_window.lineedit_zvelocity.setText(str(c.p_zvel_target))

        c.p_xincrement = float(re.sub('[^\d\.]', '', c_main_window.lineedit_xincrement.text()))
        c.p_yincrement = float(re.sub('[^\d\.]', '', c_main_window.lineedit_yincrement.text()))
        c.p_zincrement = float(re.sub('[^\d\.]', '', c_main_window.lineedit_zincrement.text()))
        c_main_window.lineedit_xincrement.setText(str(c.p_xincrement))
        c_main_window.lineedit_yincrement.setText(str(c.p_yincrement))
        c_main_window.lineedit_zincrement.setText(str(c.p_zincrement))

        return

    def connect_laser(self):
        c_main_window.status_printer.setText('laser connect pressed...')
        if c_main_window.btn_connect_laser.text() == 'connect laser':
            c_main_window.status_printer.setText('...connecting to laser...')
            if not c.l:
                try:
                    try:
                        c.l = serial.Serial('COM3', 115200, timeout=0.1)
                    except:
                        c.l = serial.Serial('COM7', 115200, timeout=0.1)

                    c.laser_com('@cobas 0')
                    c.laser_com('@cob1')
                    c.laser_com('l1')
                    # c.laser_com('cp')
                    # c.laser_com('p 0.080') # turn on at 80 mW
                    # time.sleep(1) # wait for current to stabilize
                    c.laser_current_max_power = str(137.8) #c.laser_com('i?')
                    print('current at laser max power is: '+c.laser_current_max_power)
                    c.laser_com('ci')
                    laser_on_current = '0'
                    c.laser_com('slc '+ laser_on_current)
                    c_main_window.status_printer.setText('laser connected')
                    c_main_window.btn_connect_laser.setText('disconnect laser')
                    c_main_window.lineedit_set_laser_current.setText(laser_on_current+' ('+c.laser_current_max_power+')')
                except:
                    c_main_window.status_printer.setText('couldn''t connect to laser!...')
                    c.l = 0
            else:
                c_main_window.status_printer.setText('you might already be connected to the laser!...')
        else:
            try:
                try:
                    try:
                        laser_on_current = '0'
                        c.laser_com('slc ' + laser_on_current)
                        c_main_window.status_printer.setText('laser off')
                        c_main_window.lineedit_set_laser_current.setText(laser_on_current+' ('+c.laser_current_max_power+')')
                    except:
                        0
                    c.l.close()
                    c.l.__del__()
                    c.l = 0
                    c_main_window.status_printer.setText('laser disconnected')
                    c_main_window.btn_connect_laser.setText('connect laser')
                except:
                    print('couldnt disconnect dont know why')
            except:
                c_main_window.btn_connect_laser.setText('connect laser')
        return

    def laser_com(self,input_str):
        c.l.write(str.encode(input_str+chr(13)))
        answer = c.l.read_until(chr(13))
        answer = answer.decode('utf-8')
        answer = answer.rstrip()
        return answer

    def laser_on(self,pwr):
        if not c.l:
            c.connect_laser()
        else:
            laser_on_current = str(np.array(c.laser_current_max_power,dtype='float64')*((pwr)/100))
            c.laser_com('slc ' + laser_on_current)
            c_main_window.status_printer.setText('go laser go!')
            c_main_window.lineedit_set_laser_current.setText(laser_on_current +' (' + c.laser_current_max_power + ')')
        return

    def laser_set(self):
        c.connect_laser
        laser_on_current = c_main_window.lineedit_set_laser_current.text()
        laser_on_current = np.min([float(laser_on_current),float(c.laser_current_max_power)])
        laser_on_current = np.max([laser_on_current,0])
        laser_on_current = str(laser_on_current)
        c.laser_com('slc ' + laser_on_current)
        c_main_window.status_printer.setText('go laser go!')
        c_main_window.lineedit_set_laser_current.setText(laser_on_current+' ('+c.laser_current_max_power+')')
        return

    def laser_off(self):
        c.laser_com('slc 0')
        c_main_window.status_printer.setText('laser off')
        c_main_window.lineedit_set_laser_current.setText('0 ('+str(c.laser_current_max_power)+')')
        return

    def connect_xy(self):
        if c_main_window.btn_connect_x.text() == 'connect x':
            c.xy = GCSDevice('C-413')
            c.xy_serialnum = '0120007086'
            # pidevice.ConnectUSB(serialnum='0020550003')
            c.xy.ConnectUSB(serialnum=c.xy_serialnum)
            print('initialize connected stages...')
            c.xy.SVO(1,True)
            c.xy.SVO(2,True)
            print('referncing xy stage...')
            c.xy.FRF(1)
            c.xy.FRF(2)
            ready = 0
            while not ready:
                ready = c.xy.IsControllerReady()

            c_main_window.btn_connect_x.setText('disconnect x')
            c_main_window.btn_connect_y.setText('disconnect y')
            print('xy referenced...')

            gcs.send(c.xy, 'CCL 1 advanced')
            gcs.send(c.xy, 'SPA 1 0x06010400 '+str(self.p_vel_global)) # Profile Generator Maximum Velocity
            # gcs.read(c.xy, 'SPA? 1 0x06010400')
            gcs.send(c.xy, 'SPA 2 0x06010400 '+str(self.p_vel_global)) # Profile Generator Maximum Velocity
            # gcs.read(c.xy, 'SPA? 2 0x06010400')
            gcs.send(c.xy, 'SPA 1 0x06010000 2000') # startup default is set at 50 - Profile Generator Maximum Acceleration
            # gcs.read(c.xy, 'SPA? 1 0x06010000')
            gcs.send(c.xy, 'SPA 2 0x06010000 2000') # startup default is set at 50 - Profile Generator Maximum Acceleration
            # gcs.read(c.xy, 'SPA? 2 0x06010000')

            # acceleration	mean no zero line time	total time
            # 5	0.6241187	0.92
            # 10	0.48642	0.71
            # 20	0.4023073	0.59
            # 50	0.33021193	0.48
            # 100	0.30719449	0.45
            # 200	0.2920371	0.43
            # 500	0.28619	0.42
            # 1000	0.285229	0.42
            # 2000	0.28271	0.41
            # 5000	0.28632	0.42

        else:
            print('disconnecting z stage...')
            c.xy.SVO(1, False)
            c.xy.SVO(2, False)
            c.xy.CloseConnection()
            c.xy = 0
            c_main_window.btn_connect_x.setText('connect x')
            c_main_window.btn_connect_y.setText('connect y')

        return

    def connect_z(self):
        if c_main_window.btn_connect_z.text() == 'connect z':
            c.z = GCSDevice('C-863.11')
            # c.z.InterfaceSetupDlg(key='sample')
            c.z.ConnectUSB('0020550003')
            print('initialize connected stages...')
            c.z.SVO(1,True)
            c.z.VEL(1,1)
            print('referncing z stage...')
            c.z.FRF(1)
            ready = 0
            while not ready:
                ready = c.z.IsControllerReady()
            c_main_window.btn_connect_z.setText('disconnect z')
        else:
            print('disconnecting z stage...')
            c.z.SVO(1,False)
            c.z.CloseConnection()
            c.z = 0
            c_main_window.btn_connect_z.setText('connect z')
        return

    def uimove(self,xdel,ydel,zdel):

        xdel = xdel*c.p_xincrement
        ydel = ydel*c.p_yincrement
        zdel = -1*zdel*c.p_zincrement # -1 because the stage moves down (-ve), but the stage is upside down
        self.p_xpos_target = np.round(self.p_xpos_current,2) + xdel # rounded to the neartes 10 um
        self.p_ypos_target = np.round(self.p_ypos_current,2) + ydel
        self.p_zpos_target = np.round(self.p_zpos_current,2) + zdel

        if self.p_xpos_target > 10:
            self.p_xpos_target = 10
        if self.p_xpos_target < -10:
            self.p_xpos_target = -10
        if self.p_ypos_target > 10:
            self.p_ypos_target = 10
        if self.p_ypos_target < -10:
            self.p_ypos_target = -10

        self.move()

        c.p_zpos_current = c.z.qPOS(1)
        c.p_zpos_current = c.p_zpos_current[1]
        pos = c.xy.qPOS([1,2])
        c.p_xpos_current = pos[1]
        c.p_ypos_current = pos[2]
        c_main_window.label_status_x_num.setText(str(np.round(c.p_xpos_current,6)))
        c_main_window.label_status_y_num.setText(str(np.round(c.p_ypos_current,6)))
        c_main_window.label_status_z_num.setText(str(np.round(c.p_zpos_current,6)))

        # c_main_window.image_printer_position_xy.update_plot()
        c_main_window.xy_graph_plot.setData([c.p_xpos_current], [c.p_ypos_current])
        c_main_window.xz_graph_plot.setData([c.p_xpos_current], [c.p_z_cent-c.p_zpos_current])
        print("x = " + str(c.p_xpos_current))
        print("y = " + str(c.p_ypos_current))
        print("z = " + str(c.p_z_cent-c.p_zpos_current))
        # c_main_window.image_printer_position_xz.update_plot()
        return

    def move(self):

        if not c.z == 0:
            try:
                c.p_zpos_current = c.z.qPOS(1)
                c.p_zpos_current = c.p_zpos_current[1]
                if not c.p_zvel_current == c.p_zvel_target:
                    c.z.VEL(1, c.p_zvel_target)
                    c.p_zvel_current = c.p_zvel_target
                    ready = 0
                    while not ready:
                        ready = c.z.IsControllerReady()
                if not c.p_zpos_current == c.p_zpos_target:
                    c.z.MOV(1,c.p_zpos_target)
                    pitools.waitontarget(c.z)
                    c.p_zpos_current = c.p_zpos_target
            except:
                print('z move failed')
        else:
            c.p_zpos_current = c.p_zpos_target

        if not c.xy == 0:
            try:
                pos = c.xy.qPOS([1,2])
                c.p_xpos_current = pos[1]
                c.p_ypos_current = pos[2]
                if not c.p_xvel_current == c.p_xvel_target or not c.p_yvel_current == c.p_yvel_target:
                    c.xy.VEL([1,2],[c.p_xvel_target,c.p_yvel_target])
                    c.p_xvel_current = c.p_xvel_target
                    c.p_yvel_current = c.p_yvel_target
                    ready = 0
                    while not ready:
                        ready = c.xy.IsControllerReady()
                if not c.p_xpos_current == c.p_xpos_target or not c.p_ypos_current == c.p_ypos_target:
                    c.xy.MOV([1,2],[c.p_xpos_target,c.p_ypos_target])
                    pitools.waitontarget(c.xy)
                    c.p_xpos_current = c.p_xpos_target
                    c.p_ypos_current = c.p_ypos_target
            except:
                print('xy move failed')
        else:
            c.p_xpos_current = c.p_xpos_target
            c.p_ypos_current = c.p_ypos_target

        if self.p_xpos_target == -10 and self.p_ypos_target == -10 and self.p_zpos_target == self.p_z_cent:
            print('Pete, put a laser calibration tag in here when the printer returns home, i.e. cross reference the power to the current')

        c_main_window.label_status_x_num.setText(str(np.round(c.p_xpos_current,6)))
        c_main_window.label_status_y_num.setText(str(np.round(c.p_ypos_current,6)))
        c_main_window.label_status_z_num.setText(str(np.round(c.p_zpos_current,6)))

        return

    # @profile
    # def printing(self, progress_callback):
    #     #progress
    #     for n in range (0, 5):
    #         # time.sleep(1)
    #         progress_callback.emit(int(n * 100 / 4))
    # 
    #     if c_main_window.btn_load_gcode.text() == 'unload g.code':
    #         if c_main_window.btn_connect_z.text() == 'disconnect z' and c_main_window.btn_connect_x.text() == 'disconnect x' and c_main_window.btn_connect_laser.text() == 'disconnect laser':
    # 
    #             c.xy.sendPN('MOV 1 0 2 0')
    #             laser_off_str = 'slc 0' + chr(13)
    #             laser_off_str = str.encode(laser_off_str)
    #             laser_off_str = bytes(laser_off_str)
    #             c.l.writePN(laser_off_str)
    # 
    #             # add dialog here are you ready to print?!
    # 
    #             linear_tolerance = 0.05 # 50 um (in mm),
    #             # ~ for 1.67 mm/sec total velocity          * 0.03,
    #             # (float(xvel)**2+float(yvel))**2)**0.5)    * 0.03
    #             laser_current_old = np.array(0,dtype='float64')
    #             xpos_old = 0
    #             ypos_old = 0
    #             zpos_old = 0
    #             xvel_old = 0
    #             yvel_old = 0
    #             zvel_old = 0
    # 
    #             c.time_laser = []
    #             c.time_xymov = []
    #             c.time_xyisready = []
    #             c.time_xyismoving = []
    #             c.time_line = []
    #             c.time_vector = []
    #             c.c_xpos_vector = []
    #             c.c_ypos_vector = []
    # 
    #             # printing from gcode starts here
    #             c.print_start_time = time.time()
    #             for i in range(len(c.g)):
    # 
    #                 # time_line_start = time.time()
    #                 current_line = c.g.loc[i]
    #                 print('DB@ '+ str(current_line['gcode']))
    #                 print(c.g.loc[i])
    #                 wait_time = current_line['wait']
    #                 laser_current = current_line['laser']
    # 
    #                 if wait_time != 0: # if its not a wait time
    #                     time.sleep(wait_time)
    #                 elif laser_current != laser_current_old:  # and its not a laser power change
    #                     # s = time.time()
    #                     laser = 'slc ' + str(laser_current) + chr(13)
    #                     laser = str.encode(laser)
    #                     laser = bytes(laser)
    #                     c.l.writePN(laser)
    #                     # c.time_laser.append(time.time()-s)
    #                     laser_current_old = laser_current
    #                 else: # its a velocity or position change
    #                     xpos = current_line['xpos']
    #                     ypos = current_line['ypos']
    #                     zpos = current_line['zpos']
    #                     xvel = current_line['xvel']
    #                     yvel = current_line['yvel']
    #                     zvel = current_line['zvel']
    # 
    #                     if zvel_old != zvel:
    #                         # gcs.send(c.z,'VEL 1 ' + zvel)
    #                         c.z.sendPN('VEL 1 ' + zvel)
    #                         ready = False
    #                         while ready != True:
    #                             # ready = gcs.read(c.z, chr(7))
    #                             ready = c.z.readPN(chr(7))
    #                             if 177 == ord(ready.strip()):
    #                                 ready = True
    #                             elif 176 == ord(ready.strip()):
    #                                 ready = False
    #                         zvel_old = zvel
    # 
    #                     if zpos_old != zpos:
    #                         # gcs.send(c.z, 'MOV 1 ' + zpos)
    #                         c.z.sendPN('MOV 1 ' + zpos)
    #                         moving = 1
    #                         while moving > 0:
    #                             # moving = int(gcs.read(c.z, chr(5)))
    #                             moving = int(c.z.readPN(chr(5)))
    #                         zpos_old = zpos
    # 
    #                     if xvel_old != xvel or yvel_old != yvel:
    #                         # gcs.send(c.xy, 'VEL 1 ' + xvel + ' 2 ' + yvel)
    #                         c.xy.sendPN('VEL 1 ' + xvel + ' 2 ' + yvel)
    #                         ready = False
    #                         while ready != True:
    #                             # ready = gcs.read(c.xy, chr(7))
    #                             ready = c.xy.readPN(chr(7))
    #                             if 177 == ord(ready.strip()):
    #                                 ready = True
    #                             elif 176 == ord(ready.strip()):
    #                                 ready = False
    #                         xvel_old = xvel
    #                         yvel_old = yvel
    #                         if (((float(xvel)**2+float(yvel))**2)**0.5) >= self.p_max_vel_global:
    #                             if float(xvel) == self.p_max_vel_global:
    #                                 linear_tolerance = float(yvel)*0.03
    #                             elif float(yvel) == self.p_max_vel_global:
    #                                 linear_tolerance = float(xvel)*0.03
    #                         else:
    #                             linear_tolerance = (((float(xvel)**2+float(yvel))**2)**0.5)*0.025
    # 
    #                     if xpos_old != xpos or ypos_old != ypos:
    #                         # s = time.time()
    #                         # gcs.send(c.xy, 'MOV 1 ' + xpos + ' 2 ' + ypos)
    #                         c.xy.sendPN('MOV 1 ' + xpos + ' 2 ' + ypos)
    #                         # c.time_xymov.append(time.time()-s)
    #                         ready = False
    #                         while ready != True:
    #                             # s = time.time()
    #                             # ready = gcs.read(c.xy, chr(7))
    #                             ready = c.xy.readPN(chr(7))
    #                             if 177 == ord(ready.strip()):
    #                                 ready = True
    #                             elif 176 == ord(ready.strip()):
    #                                 ready = False
    #                             else:
    #                                 print('probably an error has occured')
    #                             # c.time_xyisready.append(time.time()-s)
    #                         moving = 1
    #                         xpos = np.array(xpos,dtype='float64')
    #                         ypos = np.array(ypos,dtype='float64')
    #                         while moving > 0:
    #                             # s = time.time()
    #                             # pos = gcs.read(c.xy,'POS? 1 2')
    #                             pos = c.xy.readPN('POS? 1 2')
    #                             pos = pos.split('\n')
    #                             pos0 = pos[0]
    #                             pos0 = np.array(pos0[2:],dtype='float64')
    #                             pos1 = pos[1]
    #                             pos1 = np.array(pos1[2:],dtype='float64')
    # 
    #                             c.time_vector.append(time.time())
    #                             c.c_xpos_vector.append(pos0)
    #                             c.c_ypos_vector.append(pos1)
    # 
    #                             pos_diff = np.abs(xpos-pos0) + np.abs(ypos-pos1)
    #                             if pos_diff < linear_tolerance:
    #                                 moving = 0
    #                             # c.time_xyismoving.append(time.time()-s)
    # 
    #                         xpos_old = str(xpos)
    #                         ypos_old = str(ypos)
    # 
    #                 # c.time_line.append(time.time()-time_line_start)
    # 
    #             c.print_end_time = time.time()
    #             print('printing took: ' + str(np.round((c.print_end_time-c.print_start_time)/60,8)) + ' mins')
    #             c.flush_laser
    #             c.l.write(laser_off_str)
    #             c.xy.sendPN('MOV 1 0 2 0') # move to center
    #             # dialog print finished
    # 
    #         else:
    #             c_main_window.status_printer.setText('connect to the stages and laser')
    #     else:
    #         c_main_window.status_printer.setText('load in a *.gcode file!')
    # 
    #     # np.savetxt("c.time_laser.csv", c.time_laser, delimiter=",")
    #     # np.savetxt("c.time_xymov.csv", c.time_xymov, delimiter=",")
    #     # np.savetxt("c.time_xyisready.csv", c.time_xyisready, delimiter=",")
    #     # np.savetxt("c.time_xyismoving.csv", c.time_xyismoving, delimiter=",")
    #     # np.savetxt("c.time_line.csv", c.time_line, delimiter=",")
    # 
    #     # plt.hist(c.time_xyismoving)
    # 
    #     # plt.figure(0)
    #     # plt.plot(c.time_vector, np.array(c.c_xpos_vector)-np.array(c.c_ypos_vector))
    #     # plt.plot(c.time_vector, np.array(c.c_xpos_vector))
    #     # plt.plot(c.time_vector, np.array(c.c_ypos_vector))
    #     # plt.show()
    # 
    #     # plt.figure(0)
    #     # sp1 = plt.subplot(221)
    #     # plt.hist(c.time_laser)
    #     # sp1.set_ylabel('laser')
    # 
    #     # sp2 = plt.subplot(222)
    #     # plt.hist(c.time_xymov)
    #     # sp2.set_ylabel('move')
    # 
    #     # sp3 = plt.subplot(223)
    #     # plt.hist(c.time_xyisready)
    #     # sp3.set_ylabel('isready')
    # 
    #     # sp4 = plt.subplot(224)
    #     # plt.hist(c.time_xyismoving)
    #     # sp4.set_ylabel('ismoving')
    # 
    #     # something to update the GUI pos display here
    #     playsound('C:/Users/sunyi/Desktop/app/flow_printer_app/water-droplet-2.mp3')
    #     return "Done"

    def flush_laser(self):
        ans = b'0' # flushing out the unread laser responses
        while ans != b'':
            ans = c.l.read()

    def custom_serial_send(self):

        action = c_main_window.lineedit_custom_serial_send.text()
        action = action.split(',')
        try:
            stage = action[0].replace(' ','')
            gcscom = action[1].strip()
            if '?' in gcscom:
                if 'xy' in stage:
                    ans = gcs.read(c.xy, gcscom)
                elif 'z' in stage:
                    ans = gcs.read(c.z, gcscom)
                else:
                    ans = 'should be in form "c.xy/z, GCSCOMMAND HERE" i.e. "c.xy, MOV 1 2 0 0"'
            else:
                if 'xy' in stage:
                    ans = gcs.send(c.xy, gcscom)
                elif 'z' in stage:
                    ans = gcs.send(c.z, gcscom)
                else:
                    ans = 'should be in form "c.xy/z, GCSCOMMAND HERE" i.e. "c.xy, MOV 1 2 0 0"'
        except:
            ans = 'should be in form "c.xy/z, GCSCOMMAND HERE" i.e. "c.xy, MOV 1 2 0 0"'
        if ans:
            c_main_window.status_printer.setText(ans)
        else:
            c_main_window.status_printer.setText('send to controler'+stage+', '+gcscom)
        return

# initi Qt
app = QtWidgets.QApplication(sys.argv)
# threadpool = QThreadPool()

# startup window
c_startup = su.startup_window()
c_startup.show()
app.processEvents()

# establish classes
c = printer()
c_graphic_display = gd.graphic_display()
c_camera = camera()
c_main_window = main_window()
c_main_window.connect_all()
c_main_window.setWindowTitle('flow printer software')
c_main_window.image_histogram.update_win(c_main_window)
c_main_window.image_histogram.update_cam(c_camera)
c_main_window.image_histogram.update_graph(c_graphic_display)
# c_main_window.image_printer_position_xy.update_win(c_main_window)
# c_main_window.image_printer_position_xz.update_win(c_main_window)
# c_main_window.image_printer_position_xy.update_printer(c)
# c_main_window.image_printer_position_xz.update_printer(c)
# c_main_window.image_printer_position_xy.update_plot()
# c_main_window.image_printer_position_xz.update_plot()
c_graphic_display.update_win(c_main_window)
c_graphic_display.update_cam(c_camera)
c_graphic_display.update_image()




print('up and running yah')
c_startup.close()

# show app
app.setWindowIcon(QtGui.QIcon('cells.png'))
c_main_window.show()
playsound('C:/Users/sunyi/Desktop/app/flow_printer_app/water-droplet-2.mp3')

# close events
sys.exit(app.exec_())
