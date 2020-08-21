#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from __future__ import print_function

import matplotlib.pyplot as plt
import pickle
import sys
import pandas as pd
import numpy as np
import time
import random
import yaml
import argparse
from functools import partial
import psutil
import os
import time

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QMainWindow, QApplication, QStyle, QWidget, QDockWidget, QTabWidget, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QFileDialog, QLabel, QToolButton)
from PyQt5.QtCore import (Qt, QSettings, QTimer)
from PyQt5.QtGui import QIcon



def add_subplot2fig(fig):
    '''
    Modifies existing figure by adding a subplot at top and moving all the existing plots down.
    All the plots share the same x axis and the one in the bottom shows the ticklabels
    Returns the new axis that is created
    '''
    n = len(fig.axes)
    if n == 0:
        ax_new = fig.subplots(1, 1, sharex = True)
    else:
        for i in range(n):
            fig.axes[i].change_geometry(n+1, 1, n+1-i)
        
        ax_new = fig.add_subplot(n+1, 1, 1, sharex=fig.axes[0])
        plt.setp(ax_new.get_xticklabels(), visible=False)
        #fig.tight_layout() 
        #fig.subplots_adjust(hspace=0) # Makes vertical gap between plots 0 
    return ax_new

        
def plot_per_dict(axes, full_data_dict, namespace, plot_dict):
    '''
    Plot as specifed in the config file. This is where all the magic happens
    '''
    topic = plot_dict['topic']
    fields = plot_dict.get('fields')
    pd_eval_strings = plot_dict.get('pre_process_string')
    df = full_data_dict[namespace].get(topic)
    
    if df is not None:
        # Create or modify any column as specified in the pre-prepocessing string
        if pd_eval_strings:
            if np.isscalar(pd_eval_strings):
                pd_eval_strings = [pd_eval_strings]
            for exp in pd_eval_strings:
                df.eval(exp, inplace=True, global_dict={'pi':np.pi,
                                                        'wrapToPi':lambda a: (a + np.pi) % (2 * np.pi) - np.pi,
                                                        'wrapTo2Pi':lambda a: a % (2 * np.pi) })
        
        # If fields is not specified, plot all available fields    
        if fields is None:
            fields = sorted(list(df.columns))
        
        if type(fields) is not list:
            raise TypeError("For Topic: {}, supplied value of fields: '{}' is not of type list ".format(topic, fields))
            
        df.plot(ax=axes,y=fields,grid=True,style='.',ms=3,
                label=[f +'_'+namespace for f in fields])
        axes.set_ylabel(topic)
        return True
    
    else:
        return False        

def plot_xy_per_dict(axes, full_data_dict, namespace, plot_dict):
    '''
    Plot as specifed in the config file. This is where all the magic happens
    '''
    topic = plot_dict['topic']
    all_fields = plot_dict.get('fields')        
    pd_eval_strings = plot_dict.get('pre_process_string')
    df = full_data_dict[namespace].get(topic)
    
    if df is not None:
        # Create or modify any column as specified in the pre-prepocessing string
        if pd_eval_strings:
            if np.isscalar(pd_eval_strings):
                pd_eval_strings = [pd_eval_strings]
            for exp in pd_eval_strings:
                df.eval(exp, inplace=True, global_dict={'pi':np.pi,
                                                        'wrapToPi':lambda a: (a + np.pi) % (2 * np.pi) - np.pi,
                                                        'wrapTo2Pi':lambda a: a % (2 * np.pi) })
              
        for field_pair in all_fields:
            if type(field_pair) is not list:
                raise TypeError("For Topic: {}, supplied value of fields: '{}' is not of type list ".format(topic, fields))

            if len(field_pair) != 2:
                return False

            
            df.plot(ax=axes,x=field_pair[0], y=field_pair[1], grid=True,style='.',ms=3)
            axes.axis('equal')

        #axes.set_ylabel(topic)
        return True
    
    else:
        return False        
    

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, args):
        ''' 
        Class Constructor
        '''
        super(ApplicationWindow,self).__init__()
        self.args = args
        self.settings = QSettings("NEUFR", "our_qt_plot")
        self._read_config()
        self._create_window()
        self._create_memory_timer()
        self.full_dict = None
        self.data_file_loaded = False
        
            
    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        QMainWindow.closeEvent(self, event)

    def _create_window(self):
        '''
        Create the QT window and all widgets
        '''
        self.setWindowTitle("Our QT Plot")
        
        if self.settings.value("geometry") == None: # First launch on this computer
            self.left = 200
            self.top = 400
            self.width = 1240
            self.height = 960
            self.setGeometry(self.left, self.top, self.width, self.height)
        else:   # restored saved windows position
            self.restoreGeometry(self.settings.value("geometry"))
        
        nav_toolbar_home = NavigationToolbar.home
        
        def new_home(self, *args, **kwargs):
            print ('new home')
            nav_toolbar_home(self, *args, **kwargs)

        NavigationToolbar.home = new_home

        
        self.tab_widget = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        #self.tabs.resize(300,200)
        
        # Add tabs
        self.tab_widget.addTab(self.tab1,"Timeseries Plot")
        self.tab_widget.addTab(self.tab2,"XY Plot")
        
        # Create first timeseries tab
        self.tab1.layout = QHBoxLayout()
        timeseries_canvas = FigureCanvas(Figure())
        self.main_figure = timeseries_canvas.figure
        self.tab1.layout.addWidget(timeseries_canvas)
        timeseries_nav_tb = NavigationToolbar(timeseries_canvas, self)
        timeseries_nav_tb.setOrientation(Qt.Vertical)
        
        # Relove last plot button
        timeseries_removePlotButton = QToolButton()
        timeseries_removePlotButton.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogOkButton))
        timeseries_removePlotButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        timeseries_removePlotButton.setToolTip('Remove Last Plot')
        timeseries_nav_tb.addSeparator()
        timeseries_nav_tb.addWidget(timeseries_removePlotButton)
        timeseries_removePlotButton.clicked.connect(self._remove_last_subplot)
        
        # Clear plot button
        timeseries_clear_button = QToolButton()
        timeseries_clear_button.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserStop))
        timeseries_clear_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        timeseries_clear_button.setToolTip('Clear All Plots')
        timeseries_nav_tb.addWidget(timeseries_clear_button)
        timeseries_clear_button.clicked.connect(self._remove_all_timeseries_subplots)
        
        timeseries_nav_tb.setFixedWidth(36)
        self.tab1.layout.addWidget(timeseries_nav_tb)
        self.tab1.setLayout(self.tab1.layout)

        # Create XY figure tab
        self.tab2.layout = QHBoxLayout()
        xy_canvas = FigureCanvas(Figure())
        self.xy_figure = xy_canvas.figure
        self.xy_axes = self.xy_figure.subplots(1, 1)
        self.tab2.layout.addWidget(xy_canvas)
        
        xy_nav_tb = NavigationToolbar(xy_canvas, self)
        xy_nav_tb.setOrientation(Qt.Vertical)
        xy_clear_button = QToolButton()
        xy_clear_button.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserStop))
        xy_clear_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        xy_clear_button.setToolTip('Clear All Plots') 
        xy_nav_tb.addSeparator()
        xy_nav_tb.addWidget(xy_clear_button)
        xy_clear_button.clicked.connect(self._clear_xy_axes)
        xy_nav_tb.setFixedWidth(36)
        #xy_nav_tb.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.tab2.layout.addWidget(xy_nav_tb)
        self.tab2.setLayout(self.tab2.layout)
        
        self.setCentralWidget(self.tab_widget)
        
        #self.addToolBar(NavigationToolbar(timeseries_canvas, self))

        # Add time series plot buttons
        self.tsp_widget = QDockWidget("Select Timeseries Plot", self)
        self.tsp_button_Group = QGroupBox()
        self.tsp_button_Group.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        tsp_button_GroupLayout = QVBoxLayout()
        
        tsplotButtonList = []
        
        for time_series_buttons_dict_key, time_series_buttons_dict_value in self.time_series_buttons_dict.items():
            buttonwidget = QPushButton(time_series_buttons_dict_key)
            #buttonwidget.clicked.connect(lambda: self._add_new_plot(time_series_buttons_dict_value))
            buttonwidget.clicked.connect(partial(self._add_new_plot, time_series_buttons_dict_value))
            tsp_button_GroupLayout.addWidget(buttonwidget)
            tsplotButtonList.append(buttonwidget)
        

        tsp_button_GroupLayout.addStretch(1)
        self.tsp_button_Group.setLayout(tsp_button_GroupLayout)
        
        self.tsp_widget.setWidget(self.tsp_button_Group)
        self.tsp_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.tsp_widget.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tsp_widget)
        
        # Add xy plot buttons
        self.xyp_widget = QDockWidget("Select XY Plot", self)
        self.xyp_button_Group = QGroupBox()
        self.xyp_button_Group.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        xyp_button_GroupLayout = QVBoxLayout()
        
        xyplotButtonList = []
        
        for xy_buttons_dict_key, xy_buttons_dict_value in self.xy_buttons_dict.items():
            buttonwidget = QPushButton(xy_buttons_dict_key)
            #buttonwidget.clicked.connect(lambda: self._add_new_plot(xy_buttons_dict_value))
            buttonwidget.clicked.connect(partial(self._add_new_xy_plot, xy_buttons_dict_value))
            xyp_button_GroupLayout.addWidget(buttonwidget)
            xyplotButtonList.append(buttonwidget)
        
        #xyp_button_GroupLayout.addWidget(xy_clear_button)
        
        xyp_button_GroupLayout.addStretch(1)
        self.xyp_button_Group.setLayout(xyp_button_GroupLayout)
        
        self.xyp_widget.setWidget(self.xyp_button_Group)
        self.xyp_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.xyp_widget.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.xyp_widget)

        # Add load data button
        self.openDataWidget = QDockWidget("Open Data File", self)
        self.openDataGroup = QGroupBox()
        self.openDataGroup.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        openDataGroupLayout = QHBoxLayout()
        openDataButton = QPushButton("Load Datafile")
        openDataButton.setDefault(False)
        #openDataButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        openDataButton.clicked.connect(self._load_datafile)
        openDataGroupLayout.addWidget(openDataButton)
        self.openDataGroup.setLayout(openDataGroupLayout)
        self.openDataWidget.setWidget(self.openDataGroup)
        self.openDataWidget.setFloating(False)
        self.addDockWidget(Qt.TopDockWidgetArea, self.openDataWidget)
        
        self.memory_status_qlabel = QLabel("Memory: {:.1f}%".format(0))
        self.statusBar().addPermanentWidget(self.memory_status_qlabel)
        #self.memory_status_qlabel.setText("File Loaded")
        
        
    def _create_namespace_box(self):
        '''
        Add the namespace widget to the QT Application window based on the file loaded.        
        '''
        self.namespaceWidget = QDockWidget("Namespace Dock Widget", self)        
        self.namespaceGroup = QGroupBox("Select Namespaces")
        self.namespaceGroup.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        namespaceGroupLayout = QHBoxLayout()
        
        self.namespaceButtonList = []
        self.namespaceButtonChecked = []
        
        for buttonindex, namespace in enumerate(self.namespaceList):
            buttonwidget = QPushButton(namespace)
            buttonwidget.setCheckable(True)
            buttonwidget.clicked.connect(partial(self._handle_namespace_button, buttonindex))
            namespaceGroupLayout.addWidget(buttonwidget)
            self.namespaceButtonList.append(buttonwidget)
            self.namespaceButtonChecked.append(False)
        
        if len(self.namespaceList) > 1:
            self.checkAllbuttonwidget = QPushButton("All")
            self.checkAllbuttonwidget.setCheckable(True)
            self.checkAllbuttonwidget.clicked.connect(self._handle_all_namespace_button)
            namespaceGroupLayout.addWidget(self.checkAllbuttonwidget)
            #self.namespaceButtonList.append(checkAllbuttonwidget)
        else:
            self.namespaceButtonList[0].setChecked(True)
            self.namespaceButtonChecked[0] = True
            self.namespaceButtonList[0].setEnabled(False)
        

        #namespaceGroupLayout.addStretch(1)
        self.namespaceGroup.setLayout(namespaceGroupLayout)
        
        self.namespaceWidget.setWidget(self.namespaceGroup)
        self.namespaceWidget.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.namespaceWidget.setFloating(False)
        self.addDockWidget(Qt.TopDockWidgetArea, self.namespaceWidget)
    
    def _update_memory_box(self):
        self.memory_status_qlabel.setText("Memory: {:.1f}%".format(psutil.virtual_memory().percent))
        
    def _create_memory_timer(self):
        '''
        Create timer to update memory status box
        '''
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_memory_box)
        self.timer.start(5000)       
        
    def _read_config(self):
        '''
        Read the config file which specifies all the topic buttons as supplied by the cmd line argument
        '''
        with open(args.config_file, 'r') as f:
            self.button_dict = yaml.safe_load(f)
            self.time_series_buttons_dict = self.button_dict['time_series_buttons']
            self.xy_buttons_dict = self.button_dict['xy_plot_buttons']
            
    def _remove_last_subplot(self):
        '''
        Removes the last plot added to the figure (typically the top plot), removes 
        the axes from the figure and adjust the subplots
        '''   
        if len(self.main_figure.axes) > 0:
            self.main_figure.delaxes(self.main_figure.axes[-1])
            n = len(self.main_figure.axes)
            for i in range(n):
                self.main_figure.axes[i].change_geometry(n, 1, n-i)
            self.main_figure.canvas.draw()
            
    def _remove_all_timeseries_subplots(self):
        '''
        Removes the all timeseries subplots from figure
        '''   
        while len(self.main_figure.axes) > 0:
            self.main_figure.delaxes(self.main_figure.axes[-1])        
        self.main_figure.canvas.draw()

    def _clear_xy_axes(self):
        self.xy_axes.clear()
        self.xy_figure.canvas.draw()        
            
    def _add_new_xy_plot(self, plot_dict_list):
        '''
        When a plot button is pressed process the list of plot_dicts specified in the YAML config file and add 
        to a new subplot.
        '''
        if self.data_file_loaded:
            start_time = time.time()
            for buttonChecked, namespace in zip(self.namespaceButtonChecked, self.namespaceList):
                if buttonChecked:
                    for plot_dict in plot_dict_list:                    
                        success = plot_xy_per_dict(self.xy_axes, self.full_dict, namespace, plot_dict)
                        if not success:
                            self.statusBar().showMessage('Couldn\'t find topic {} in namespace {}'.format(plot_dict['topic'],namespace),3000)
            self.xy_figure.canvas.draw()
            #self.statusBar().showMessage('Plot loaded in {:.2f} seconds'.format(time.time()-start_time),500)            
        else:
            self.statusBar().showMessage('Come on dude you gotta load a datafile first !!!',3000)
        # Todo add a warning to status bar if one of the topics is not available on a particular namespace
               
    def _add_new_plot(self, plot_dict_list):
        '''
        When a plot button is pressed process the list of plot_dicts specified in the YAML config file and add 
        to a new subplot.
        '''
        if self.data_file_loaded:
            start_time = time.time()
            axn = add_subplot2fig(self.main_figure)
            for buttonChecked, namespace in zip(self.namespaceButtonChecked, self.namespaceList):
                if buttonChecked:
                    for plot_dict in plot_dict_list:                    
                        success = plot_per_dict(axn, self.full_dict, namespace, plot_dict)
                        if not success:
                            self.statusBar().showMessage('Couldn\'t find topic {} in namespace {}'.format(plot_dict['topic'],namespace),3000)
                            self._remove_last_subplot()
            self.main_figure.canvas.draw()
            #self.statusBar().showMessage('Plot loaded in {:.2f} seconds'.format(time.time()-start_time),500)            
        else:
            self.statusBar().showMessage('Come on dude you gotta load a datafile first !!!',3000)
        # Todo add a warning to status bar if one of the topics is not available on a particular namespace
               
    def _load_datafile(self): 
        '''
        Load dadtafile by selecting from file chooser
        '''
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 
                                               self.settings.value("data_file_location"),
                                               "Pickle files (*.pkl)")
        if fname:
            self.full_dict = pd.read_pickle(fname)
            self.namespace_list = self.full_dict.keys()
            self.setWindowTitle("Our QT Plot - " +fname ) 
            self.namespaceList = self.full_dict.keys()
            #self.namespaceList = ['uas1', 'uas2']
            if hasattr(self, 'namespaceWidget'):
                self.removeDockWidget(self.namespaceWidget)
            self._create_namespace_box()
            self.statusBar().showMessage('File {} loaded successfully'.format(fname))
            self.settings.setValue("data_file_location", os.path.dirname(fname))
            self.data_file_loaded = True
            #Todo remove all subplots when loading new file??? 
        
    def _handle_all_namespace_button(self):
        '''
        Handle the button toggle when the 'all' namespace button is pressed
        '''
        state = self.checkAllbuttonwidget.isChecked()
        for button_index, button in enumerate(self.namespaceButtonList):
            button.setChecked(state)
            self.namespaceButtonChecked[button_index] = state
            
    def _handle_namespace_button(self, button_index):
        '''
        Handle the selection of namespaces when button is pressed
        '''
        self.namespaceButtonChecked[button_index] = self.namespaceButtonList[button_index].isChecked()
        if hasattr(self, 'checkAllbuttonwidget'):
            if all(self.namespaceButtonChecked):
                self.checkAllbuttonwidget.setChecked(True)      
            else:
                self.checkAllbuttonwidget.setChecked(False)             

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
            description='Plot ROSBAG data converted into pandas dataframes.\n\n')
    parser.add_argument('-c','--config_file', help='Yaml file which specifies topic names to convert',
                    default = 'config/oqtplot_config_uas.yaml')

    args = parser.parse_args()

    qapp = QtWidgets.QApplication(sys.argv)
    app = ApplicationWindow(args)
    
    app.show()

    qapp.exec_()