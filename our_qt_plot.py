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
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
from matplotlib.backends.backend_qt5agg import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure

from PyQt5.QtWidgets import (QDockWidget, QGroupBox, QPushButton, QVBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt
import yaml
import argparse


def add_subplot2fig(fig):
    '''
    Modifies existing figure by adding a subplot at top and moving all the existing plots down.
    All the plots share the same x axis and the one in the bottom shows the ticklabels
    Returns the new axis that is created
    '''
    n = len(fig.axes)
    for i in range(n):
        fig.axes[i].change_geometry(n+1, 1, n+1-i)
    
    ax_new = fig.add_subplot(n+1, 1, 1, sharex=fig.axes[0])
    plt.setp(ax_new.get_xticklabels(), visible=False)
    return ax_new


        
def plot_by_string(axes, full_data_dict, namespace, topic, fields):
    '''
    Plot 
    '''
    full_dict[namespace][topic].plot(ax=axes,y=fields,grid=True,style='.',ms=3,
              label=[f +'_'+namespace for f in fields])
    axes.set_ylabel(topic)
    

# Start with one
#fig, ax = plt.subplots(1, 1, sharex = True)
#ax.plot([1,2,3])
#ax.grid()

#axn = add_subplot2fig(fig)
#axn.plot([4, 5, 6, 7, 8, 8, 8, 9],label="One")
#axn.plot([2,3,4,2,4],label="Two")
#axn.grid()
#axn.legend()
#axn = add_subplot2fig(fig)
#axn.plot([8, 8, 8, 9])
#axn.grid()
#axn = add_subplot2fig(fig)
#axn.plot([3, 4, 2, 5, 3, 4])
#axn.grid()


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, args):
        super(ApplicationWindow,self).__init__()
        self.args = args
        self._read_config()
        self._create_window()

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
        self.selectPlotGroup.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        selectPlotGroupLayout = QVBoxLayout()
        
        plotButtonList = [QPushButton(x) for x in self.button_dict.keys()]
        
        [selectPlotGroupLayout.addWidget(b) for b in plotButtonList]

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
        self.main_figure.delaxes(self.main_figure.axes[-1])
        n = len(self.main_figure.axes)
        for i in range(n):
            self.main_figure.axes[i].change_geometry(n, 1, n-i)
        self.main_figure.canvas.draw()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
            description='Plot ROSBAG data converted into pandas dataframes.\n\n')
    parser.add_argument('-c','--config_file', help='Yaml file which specifies topic names to convert',
                    default = 'config/oqtplot_config_uas.yaml')

    args = parser.parse_args()

    qapp = QtWidgets.QApplication(sys.argv)
    app = ApplicationWindow(args)
    
    
    app.show()
    
    full_dict = pd.read_pickle('/home/vik748/apps/bag2mat_ws/sample_data/uas2_2019-05-01-14-32-51.pkl')

    fig = app.main_figure
    fig.clf()
    ax = fig.subplots(1, 1, sharex = True)
    full_dict['uas2']['velocity'].plot(ax=ax,grid=True,style='.',ms=3)
    
    axn = add_subplot2fig(fig)
    full_dict['uas2']['cmd_vel'].plot(ax=axn,y=['velocity_x','velocity_y','velocity_z'],grid=True,style='.',ms=3)
    axn.set_ylabel("cmd_vel")
    
    axn = add_subplot2fig(fig)
    plot_by_string(axn, full_dict, 'uas2', 'uas_odom', ['position_x','position_y','position_z'])
    
    qapp.exec_()