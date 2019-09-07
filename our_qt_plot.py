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

from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QDockWidget, QGroupBox, QPushButton, QVBoxLayout, QSizePolicy, QFileDialog)
from PyQt5.QtCore import Qt

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
    return ax_new

        
def plot_by_string(axes, full_data_dict, namespace, topic, fields):
    '''
    Plot 
    '''
    full_data_dict[namespace][topic].plot(ax=axes,y=fields,grid=True,style='.',ms=3,
              label=[f +'_'+namespace for f in fields])
    axes.set_ylabel(topic)
    

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, args):
        super(ApplicationWindow,self).__init__()
        self.args = args
        self._read_config()
        self._create_window()
        self.full_dict = None

    def _create_window(self):
        self.setWindowTitle("Our QT Plot")
        self.left = 200
        self.top = 400
        self.width = 1240
        self.height = 960
        self.setGeometry(self.left, self.top, self.width, self.height)

        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QHBoxLayout(self._main)

        static_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.main_figure = static_canvas.figure
        layout.addWidget(static_canvas)
        self.addToolBar(NavigationToolbar(static_canvas, self))

        self.verticalWidget = QDockWidget("Vertical Dock Widget", self)
        self.verticalWidgetLayout = QVBoxLayout()
        
        self.selectPlotGroup = QGroupBox("Select Plot")
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
                
        self.removePlotWidget = QDockWidget("Remove Plot Widget", self)
        removePlotButton = QPushButton("Remove Last Plot")
        removePlotButton.setDefault(False)
        removePlotButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        removePlotButton.clicked.connect(self._remove_last_subplot)
        self.removePlotWidget.setWidget(removePlotButton)
        self.removePlotWidget.setFloating(False)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.removePlotWidget)
        
        self.openDataWidget = QDockWidget("Open Data Widget", self)
        openDataButton = QPushButton("Load Datafile")
        openDataButton.setDefault(False)
        openDataButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

        openDataButton.clicked.connect(self._load_datafile)
        self.openDataWidget.setWidget(openDataButton)
        self.openDataWidget.setFloating(False)
        self.addDockWidget(Qt.TopDockWidgetArea, self.openDataWidget)
        
    def _read_config(self):
        with open(args.config_file, 'r') as f:
            self.button_dict = yaml.safe_load(f)
        
    def _update_canvas(self):
        self._dynamic_ax.clear()
        t = np.linspace(0, 10, 101)
        # Shift the sinusoid as a function of time.
        self._dynamic_ax.plot(t, np.sin(t + time.time()))
        self._dynamic_ax.figure.canvas.draw()
    
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
    
    def _add_new_plot(self, plot_dict):
        axn = add_subplot2fig(self.main_figure)
        plot_by_string(axn, self.full_dict, 'uas2', plot_dict['topic'], plot_dict['fields'])
        self.main_figure.canvas.draw()
        
    def _load_datafile(self):
        
        fname, _ = QFileDialog.getOpenFileName(self, 'Open file', 
                                            '~',"Pickle files (*.pkl)")
        print("Loading datafile - ", fname)
        self.full_dict = pd.read_pickle(fname)
        #Todo remove all subplots when loading new file??? 

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