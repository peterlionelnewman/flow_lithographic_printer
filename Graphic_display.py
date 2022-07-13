import matplotlib.pyplot as plt
import time
import numpy as np
from PIL import Image

class graphic_display():
    def __init__(self):
        self.um_per_pixel = 0.5
        self.cm_hot       = plt.get_cmap('hot')
        self.cm_jet       = plt.get_cmap('jet')
        self.cm_vir       = plt.get_cmap('viridis')
        self.cm_mag       = plt.get_cmap('magma')
        # self.cm_grn       = plt.get_cmap('Greens')
        self.cm_raw       = plt.get_cmap('gray')
        self.fps_counter  = np.array([time.time(),time.time(),time.time()])
        self.img_rs       = None
        self.img_norm     = None
        self.img_gamma    = None
        self.img_p        = None
        self.img_cm       = None
        self.img_sb       = None
        self.img_fin      = None
        self.win          = None
        self.cam          = None
        return

    def update_win(self, win):
        self.win = win

    def update_cam(self, cam):
        self.cam = cam

    def update_image(self):
        print('update image function')
        self.img_rs = np.array(Image.fromarray(self.cam.img_raw).resize(size=(958, 638)),dtype = 'float64')/255
        if self.win.zoom_factor > 1:
            r1 = self.img_rs.shape[0]
            c1 = self.img_rs.shape[1]
            r2 = int(np.round(r1/self.win.zoom_factor))
            c2 = int(np.round(c1/self.win.zoom_factor))
            self.img_rs = self.img_rs[int((r1-r2)/2):int((r1-r2)/2)+r2, int((c1-c2)/2):int((c1-c2)/2)+c2]

        # update and process the image for display from the camera
        self.update_image_gamma()
        self.normalise_img()
        self.update_colormap()
        self.display_saturated_pixels_purple() ### error
        self.burn_scalebar_into_image()

        # gui functions
        self.win.repaint_image() ### may zoom in twice for raw image, need double check
        self.win.update_hist()
        # self.win.image_histogram.update_histogram() # method in histogram_canvas class
        self.win.status_text_update_image()

        # fps counter
        self.fps_counter = np.append(self.fps_counter,time.time())
        self.fps_counter = np.delete(self.fps_counter, 0)
        self.win.status_fps_number.setText(str(np.round(1/np.mean(np.diff(self.fps_counter)),5)))
        print('current saved value for fps is: ' + str(self.cam.fps) + ' current timer value is: ' + str(self.cam.timer_value))
        return

    def update_image_gamma(self):

        if self.win.gamma == 1:
            self.img_gamma = self.img_rs
        else:
            self.img_gamma = self.img_rs**self.win.gamma
        return

    def normalise_img(self):
        print('normalise function')
        if self.win.cbox_normalise.isChecked():
            imgnormmin = np.min(np.nonzero(self.img_gamma))
            imgnormmax = np.max(self.img_gamma)
            self.img_norm = (self.img_gamma-imgnormmin)/(imgnormmax--imgnormmin)
            self.img_norm = self.img_norm
        else:
            self.img_norm = self.img_gamma
        return

    def update_colormap(self):
        print('update colormap function')
        # convert from gray to colormap magma selection
        if self.win.combobox_colourmap.currentIndex() == 0:
            self.img_cm = self.cm_mag(self.img_norm)
        # convert from gray to colormap green selection
        elif self.win.combobox_colourmap.currentIndex() == 1:
            self.img_cm = np.zeros(np.hstack([np.shape(self.img_norm),4]))
            self.img_cm[:,:,1] = self.img_norm
            self.img_cm[:,:,3] = 255
            ## or use Greens colormap directly
            # self.img_cm = self.cm_grn(self.img_norm)
        # convert from gray to colormap viridis (3 channel) selection
        elif self.win.combobox_colourmap.currentIndex() == 2:
            self.img_cm = self.cm_vir(self.img_norm)
        # convert from gray to colormap jet selection
        elif self.win.combobox_colourmap.currentIndex() == 3:
            self.img_cm = self.cm_jet(self.img_norm)
        elif self.win.combobox_colourmap.currentIndex() == 4:
            # self.img_cm = np.zeros(np.hstack([np.shape(self.img_norm),4]))
            # self.img_cm[:,:,0] = self.img_norm
            # self.img_cm[:,:,1] = self.img_norm
            # self.img_cm[:,:,2] = self.img_norm
            # self.img_cm[:,:,3] = 1
            # print(self.img_cm)
            # print(self.cam.img_raw)
            ## or use gray colormap directly
            self.img_cm = self.cm_raw(self.img_norm)
        return

    def display_saturated_pixels_purple(self):
        print('saturated pxls purple function')
        # saturated pixels show up purple if check box is selected
        # if self.win.combobox_colourmap.currentIndex() != 4:
        self.img_p = self.img_cm
        if self.win.cbox_saturated.isChecked():
            ind = self.img_norm > 254
            self.img_p[ind,0] = 255
            self.img_p[ind,1] = 0
            self.img_p[ind,2] = 255
        return

    def burn_scalebar_into_image(self):
        print('burn scalebar function')
        self.img_sb = self.img_p
        if self.win.cbox_show_scalebar.isChecked():
            s = self.img_sb.shape
            if self.win.combobox_colourmap.currentIndex() == 1:
                self.img_sb[int(s[0]*0.95):int(s[0]*0.955), int(s[1]*0.05):int(s[1]*0.05+100/self.um_per_pixel), 0] = 255
                self.img_sb[int(s[0]*0.95):int(s[0]*0.955), int(s[1]*0.05):int(s[1]*0.05+100/self.um_per_pixel), 1] = 0
                self.img_sb[int(s[0]*0.95):int(s[0]*0.955), int(s[1]*0.05):int(s[1]*0.05+100/self.um_per_pixel), 2] = 255
            else:
                self.img_sb[int(s[0]*0.95):int(s[0]*0.955), int(s[1]*0.05):int(s[1]*0.05+100/self.um_per_pixel), 0] = 0
                self.img_sb[int(s[0]*0.95):int(s[0]*0.955), int(s[1]*0.05):int(s[1]*0.05+100/self.um_per_pixel), 1] = 255
                self.img_sb[int(s[0]*0.95):int(s[0]*0.955), int(s[1]*0.05):int(s[1]*0.05+100/self.um_per_pixel), 2] = 0
        self.img_fin = self.img_sb
        self.img_fin = np.array(self.img_fin*255,dtype='uint8')
        return
