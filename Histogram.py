import numpy as np
from matplotlib.figure import Figure
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class histogram_canvas(FigureCanvas):

    def __init__(self, parent=None):
        histo_fig = Figure(dpi=100, constrained_layout=True)
        histo_fig.set_facecolor((240/255, 240/255, 240/255))
        self.axes = histo_fig.add_subplot(111)
        self.axes.set_facecolor((180/255, 180/255, 180/255))
        super(histogram_canvas, self).__init__(histo_fig)
        # define properties for the image histogram
        self.number_of_bins = 80
        self.bin_range = int(255/80)
        self.x1 = range(0,255,self.bin_range)
        self.xtickedges = np.arange(0, 257, 257/self.number_of_bins).tolist()
        self.axes.set_xlabel('bit depth')
        self.axes.set_ylabel('histo count (log)')
        self.xtickbins = np.arange(0, 257, 256/10).tolist()
        self.axes.get_xaxis().set_ticks(self.xtickbins)
        self.axes.get_xaxis().set_ticklabels(np.hstack([1,['']*(len(self.xtickbins)-2),255]))
        self.axes.set(xlim=(-1, 257))
        self.axes.set_yscale('log')
        self.axes.get_yaxis().set_ticklabels([])
        self.axes.grid(which='major', color='black', linestyle='-', linewidth=0.1, alpha=0.5)
        self.axes.grid(which='minor', color='black', linestyle='-', linewidth=0.05, alpha=0.25)
        self.axes.xaxis.labelpad = -10
        self.axes.yaxis.labelpad = -3
        self._plot_ref1 = None
        self._plot_ref2 = None
        self.win = None
        self.graphic_display = None
        self.cam = None
        return

    def update_win(self, win):
        self.win = win

    def update_graph(self, gra):
        self.graphic_display = gra

    def update_cam(self, cam):
        self.cam = cam

    def update_histogram(self):
        print('update histogram function')
        # t = time.time()
        if self._plot_ref1 is None:
            h1 = (self.cam.img_raw.flatten()*(self.number_of_bins/256))
            h1 = np.unique(h1.astype(np.uint8), return_counts=True)
            x1 = np.arange(self.number_of_bins)
            y1 = np.zeros(self.number_of_bins)
            for i in np.unique(h1[0]):
                y1[i] = h1[1][np.where(h1[0] == i)]
            y2 = np.zeros(self.number_of_bins)
            plot_refs1 = self.axes.plot(x1*(256/self.number_of_bins),y1, 'white', linewidth=2, alpha=0.5)
            plot_refs2 = self.axes.plot(x1*(256/self.number_of_bins),y2, 'red', linewidth=2, alpha=0.5)
            self._plot_ref1 = plot_refs1[0]
            self._plot_ref2 = plot_refs2[0]
        else:
            h1 = (self.cam.img_raw.flatten()*(self.number_of_bins/256))
            h1 = np.unique(h1.astype(np.uint8), return_counts=True)
            x1 = np.arange(self.number_of_bins)
            y1 = np.zeros(self.number_of_bins)
            for i in np.unique(h1[0]):
                y1[i] = h1[1][np.where(h1[0] == i)]
            self._plot_ref1.set_ydata(y1)

            if self.win.cbox_normalise.isChecked() or self.win.gamma != 1:
                h2 = (self.graphic_display.img_norm.flatten()*(self.number_of_bins/256))
                h2 = np.unique(np.asarray(h2, dtype=np.uint8), return_counts=True)
                y2 = np.zeros(self.number_of_bins)
                for i in np.unique(h2[0]):
                    y2[i] = h2[1][np.where(h2[0] == i)]
                self._plot_ref2.set_ydata(y2)
            else:
                self._plot_ref2.set_ydata(np.zeros(self.number_of_bins))
                y2 = y1
            self.axes.axis(ymin=1,ymax=2.5*np.amax(np.hstack([y1,y2]),0))
        self.win.image_histogram.draw()
        return
