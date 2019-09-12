# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

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
from PyQt5.QtWidgets import (QMainWindow, QDockWidget, QGroupBox, QPushButton, QHBoxLayout, QVBoxLayout, QSizePolicy, QFileDialog, QLabel)
from PyQt5.QtCore import (Qt, QSettings, QTimer)



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
        fig.tight_layout() 
        fig.subplots_adjust(hspace=0) # Makes vertical gap between plots 0 
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

        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QHBoxLayout(self._main)

        static_canvas = FigureCanvas(Figure())
        self.main_figure = static_canvas.figure
        layout.addWidget(static_canvas)
        self.addToolBar(NavigationToolbar(static_canvas, self))

        # Add plot buttons
        self.verticalWidget = QDockWidget("Select Plot", self)
        #self.verticalWidgetLayout = QVBoxLayout()
        
        self.selectPlotGroup = QGroupBox()
        self.selectPlotGroup.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        selectPlotGroupLayout = QVBoxLayout()
        
        plotButtonList = []
        
        for button_dict_key, button_dict_value in self.button_dict.items():
            buttonwidget = QPushButton(button_dict_key)
            #buttonwidget.clicked.connect(lambda: self._add_new_plot(button_dict_value))
            buttonwidget.clicked.connect(partial(self._add_new_plot, button_dict_value))
            selectPlotGroupLayout.addWidget(buttonwidget)
            plotButtonList.append(buttonwidget)
        

        selectPlotGroupLayout.addStretch(1)
        self.selectPlotGroup.setLayout(selectPlotGroupLayout)
        
        self.verticalWidget.setWidget(self.selectPlotGroup)
        self.verticalWidget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.verticalWidget.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.verticalWidget)
                
        # Add removePlot Button
        self.removePlotWidget = QDockWidget("Remove Plot", self)
        self.removePlotGroup = QGroupBox()
        self.removePlotGroup.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        removePlotLayout = QVBoxLayout()
        removePlotButton = QPushButton("Remove Last Plot")
        removePlotButton.setDefault(False)
        #removePlotButton.setStyleSheet("background-color: red")
        #removePlotButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        removePlotButton.clicked.connect(self._remove_last_subplot)
        removePlotLayout.addWidget(removePlotButton)
        self.removePlotGroup.setLayout(removePlotLayout)
        self.removePlotWidget.setWidget(self.removePlotGroup)
        self.removePlotWidget.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.removePlotWidget)
        
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
            self.statusBar().showMessage('Plot loaded in {:.2f} seconds'.format(time.time()-start_time),3000)            
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