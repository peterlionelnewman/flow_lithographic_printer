import numpy as np
from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class printer_canvas(FigureCanvas):
    def __init__(self, key):
        self.id = key
        self.c = None
        self.win = None

        if self.id == "xy":
            self.xy_fig = (Figure(constrained_layout=True))
            self.axes = self.xy_fig.add_subplot(111)
            super(printer_canvas, self).__init__(self.xy_fig)
            self.axes.set_ylabel('y pos (mm)', fontsize=6)
            self.axes.set(xlim=(-10, 11))
            self.yticks = np.arange(-10, 10, 2).tolist()
            self.axes.get_yaxis().set_ticks(self.yticks)
            self.axes.set(ylim=(-10, 11))
            self.gcode_loaded = 0

        elif self.id == "xz":
            self.xz_fig = (Figure(constrained_layout=True))
            self.axes = self.xz_fig.add_subplot(111)
            super(printer_canvas, self).__init__(self.xz_fig)
            self.axes.set_ylabel('z pos (mm)', fontsize=6)
            self.axes.set(xlim=(-10, 10))
            self.zticks = np.arange(-3, 3, 3).tolist()
            self.axes.get_yaxis().set_ticks(self.zticks)
            self.axes.set(ylim=(-3, 3))

        self.axes.set_facecolor((180/255, 180/255, 180/255))
        self.axes.set_xlabel('x pos (mm)', fontsize=6)
        self.xticks = np.arange(-10, 10, 2).tolist()
        self.axes.get_xaxis().set_ticks(self.xticks)
        self.axes.tick_params(axis='both', which='major', labelsize=6)
        self.axes.tick_params(axis='both', which='minor', labelsize=6)
        self.axes.grid(which='major', color='black', linestyle='-', linewidth=0.1, alpha=0.5)
        self.axes.grid(which='minor', color='black', linestyle='-', linewidth=0.05, alpha=0.25)
        self.axes.xaxis.labelpad = -2
        self.axes.yaxis.labelpad = -5
        self._plot_ref1 = None

    def update_win(self, win):
        self.win = win

    def update_printer(self, c):
        self.c = c

    def update_plot(self):
        if self.id == "xy":
            print('update plot xy function')
            if self._plot_ref1 is None:
                plot_refs1 = self.axes.scatter(self.c.p_xpos_current,self.c.p_ypos_current,color='red',label='label',marker='o',s=15)
                self._plot_ref1 = plot_refs1
            else:
                self._plot_ref1.set_offsets([self.c.p_xpos_current,self.c.p_ypos_current])
            self.win.image_printer_position_xy.draw()
        elif self.id == "xz":
            print('update plot xz function')
            if self._plot_ref1 is None:
                plot_refs1 = self.axes.scatter(self.c.p_xpos_current,self.c.p_z_cent-self.c.p_zpos_current,color='red',label='label',marker='o',s=15)
                self._plot_ref1 = plot_refs1
            else:
                self._plot_ref1.set_offsets([self.c.p_xpos_current,self.c.p_z_cent+self.c.p_zpos_current])
            self.win.image_printer_position_xz.draw()

# class printer_xy_canvas(FigureCanvas):
#
#     def __init__(self):
#         self.xy_fig = (Figure(constrained_layout=True))
#         # self.xy_fig.set_facecolor((80/255, 80/255, 80/255))
#         self.axes = self.xy_fig.add_subplot(111)
#         self.axes.set_facecolor((180/255, 180/255, 180/255))
#         super(printer_xy_canvas, self).__init__(self.xy_fig)
#         self.axes.set_xlabel('x pos (mm)', fontsize=6)
#         self.axes.set_ylabel('y pos (mm)', fontsize=6)
#         self.axes.tick_params(axis='both', which='major', labelsize=6)
#         self.axes.tick_params(axis='both', which='minor', labelsize=6)
#         self.xticks = np.arange(-10, 10, 2).tolist()
#         self.axes.get_xaxis().set_ticks(self.xticks)
#         self.axes.set(xlim=(-10, 11))
#         self.yticks = np.arange(-10, 10, 2).tolist()
#         self.axes.get_yaxis().set_ticks(self.yticks)
#         self.axes.set(ylim=(-10, 11))
#         self.axes.grid(which='major', color='black', linestyle='-', linewidth=0.1, alpha=0.5)
#         self.axes.grid(which='minor', color='black', linestyle='-', linewidth=0.05, alpha=0.25)
#         self.axes.xaxis.labelpad = -2
#         self.axes.yaxis.labelpad = -5
#         self._plot_ref1 = None
#         self.gcode_loaded = 0
#         self.win = None
#         self.c = None
#         return
#
#     def update_win(self, win):
#         self.win = win
#
#     def update_printer(self, c):
#         self.c = c
#
#     def update_plot(self):
#         print('update plot xy function')
#         if self._plot_ref1 is None:
#             plot_refs1 = self.axes.scatter(self.c.p_xpos_current,self.c.p_ypos_current,color='red',label='label',marker='o',s=15)
#             self._plot_ref1 = plot_refs1
#         else:
#             self._plot_ref1.set_offsets([self.c.p_xpos_current,self.c.p_ypos_current])
#         self.win.image_printer_position_xy.draw()
#         return
#
# class printer_xz_canvas(FigureCanvas):
#
#     def __init__(self):
#         self.xz_fig = (Figure(constrained_layout=True))
#         # self.xz_fig.set_facecolor((80/255, 80/255, 80/255))
#         self.axes = self.xz_fig.add_subplot(111)
#         self.axes.set_facecolor((180/255, 180/255, 180/255))
#         super(printer_xz_canvas, self).__init__(self.xz_fig)
#         self.axes.set_xlabel('x pos (mm)', fontsize=6)
#         self.axes.set_ylabel('z pos (mm)', fontsize=6)
#         self.axes.tick_params(axis='both', which='major', labelsize=6)
#         self.axes.tick_params(axis='both', which='minor', labelsize=6)
#         self.xticks = np.arange(-10, 10, 2).tolist()
#         self.axes.get_xaxis().set_ticks(self.xticks)
#         self.axes.set(xlim=(-10, 10))
#         self.zticks = np.arange(-3, 3, 3).tolist()
#         self.axes.get_yaxis().set_ticks(self.zticks)
#         self.axes.set(ylim=(-3, 3))
#         self.axes.grid(which='major', color='black', linestyle='-', linewidth=0.1, alpha=0.5)
#         self.axes.grid(which='minor', color='black', linestyle='-', linewidth=0.05, alpha=0.25)
#         self.axes.xaxis.labelpad = -2
#         self.axes.yaxis.labelpad = -5
#         self._plot_ref1 = None
#         self.c = None
#         return
#
#     def update_win(self, win):
#         self.win = win
#
#     def update_printer(self, c):
#         self.c = c
#
#     def update_plot(self):
#         print('update plot xz function')
#         if self._plot_ref1 is None:
#             plot_refs1 = self.axes.scatter(self.c.p_xpos_current,self.c.p_z_cent-self.c.p_zpos_current,color='red',label='label',marker='o',s=15)
#             self._plot_ref1 = plot_refs1
#         else:
#             self._plot_ref1.set_offsets([self.c.p_xpos_current,self.c.p_z_cent+self.c.p_zpos_current])
#         self.win.image_printer_position_xz.draw()
#         return
