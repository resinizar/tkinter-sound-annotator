##################################################################################
#    Gabriel Cano                                                                #
##################################################################################
#                                                                                #
#                                                                                #
#                                                                                #
##################################################################################

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import csv
import sys
from playsound import playsound
from det_tools import *
import shutil



class SoundDetector:
    def __init__(self, root, audio_clip_folder, prev_f_ind=-1, prev_d_ind=0, prev_folder='', prev_csv='', prev_labels=[]):
        self.root = root
        self.data_folder = audio_clip_folder

        # get all wav files contained in given directory or subdirectories
        self.wav_files = []
        for rootdir, dirs, filenames in os.walk(self.data_folder):
            for filename in filenames:
                if 'wav' in filename or 'WAV' in filename:
                    self.wav_files.append(filename)
            break  # activate this line if only top level of directory wanted

        # saving folders
        self.folder = prev_folder
        self.csv = prev_csv

        # entry label variable
        self.label = tk.StringVar()
        
        # variables set elsewhere that last the program lifetime
        self.canvas = None # updated in create_ui
        self.spec_h = 0

        # variables set elsewhere that change with each new clip
        self.f_ind = prev_f_ind  # start index at 0 (incremented in next_ method)
        self.curr_clip = AudioClip(os.path.join(self.data_folder, self.wav_files[self.f_ind]))
        self.canvas_img1 = None  # I have no idea why I need two, it works
        self.canvas_img2 = None
        self.temp = None  # used so tkinter doesn't delete the images for the spectrogram

        # variables set elsewhere that change while working on one clip
        self.prev_d_ind = 0  # start at 0 for each audio clip (incrememnted in save, reset in next_)
        self.clip_start = 0  # updated on click in mouse_down
        self.curr_rect_id = None
        
        self.create_ui()
        self.next_()  # load everything you need to for each clip

    def curr_filename(self):
        return self.wav_files[self.f_ind]

 # ---------------------------------------------------------------------------

    def save(self):
        savepath = os.path.join(self.folder, 'd{}-{}.wav'.format(self.curr_filename().split('.')[0], self.d_ind))
        shutil.copy('./temp.wav', savepath)

        with open(self.csv, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([savepath, self.label.get()])

        self.d_ind += 1

    def next_(self):
        self.f_ind += 1
        self.d_ind = 0  # reset to 0 for next file
        self.curr_clip = AudioClip(os.path.join(self.data_folder, self.curr_filename()))  # get audioclip

        viewable_pil = Image.fromarray((self.curr_clip.spec * 255).astype('uint8'))
        self.temp = img =  ImageTk.PhotoImage(image=viewable_pil)
        self.canvas_img2 = self.canvas.itemconfig(self.canvas_img1, image=img)

        if self.curr_rect_id:
            self.canvas.delete(self.curr_rect_id)

    def play(self):
        playsound('temp.wav')  # TODO: do on a diff thread

    def exit(self):
        with open('bookmark.txt', 'w') as f:
            values = ','.join([str(self.f_ind), str(self.d_ind), self.folder, self.filename, self.csv.get()])
            print(values, file=f)
        self.root.destroy()

    # ---------------------------------------------------------------------------

    def mouse_down(self, event):
        self.clip_start = int(self.canvas.canvasx(event.x))

    def mouse_drag(self, event):
        if self.curr_rect_id:
            self.canvas.delete(self.curr_rect_id)

        self.curr_rect_id = self.canvas.create_rectangle(
            self.clip_start, 0, self.canvas.canvasx(event.x), self.spec_h,
            fill='', outline='yellow')

    def mouse_up(self, event):
        clip_end = int(self.canvas.canvasx(event.x))
        if clip_end < self.clip_start:
            self.curr_clip.write_mini_clip('./temp.wav', clip_end, self.clip_start)
        else:
            self.curr_clip.write_mini_clip('./temp.wav', self.clip_start, clip_end)

    def create_ui(self):
        viewable_pil = Image.fromarray((self.curr_clip.spec * 255).astype('uint8'))
        self.temp = img =  ImageTk.PhotoImage(image=viewable_pil)
        self.spec_h = img.height()

        frame = ttk.Frame(self.root)
        self.canvas = tk.Canvas(frame, width=1250, height=img.height(), bg='white')
        scrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.config(xscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.canvas.config(scrollregion=(0, 0, img.width(), img.height()))
        self.canvas.bind("<Button-1>", self.mouse_down)
        self.canvas.bind("<B1-Motion>", self.mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)
        self.canvas_img1 = self.canvas.create_image(0, 0, image=img, anchor='nw')

        frame.pack(side=tk.TOP)

        frame = ttk.Frame(self.root)

        # create & place entry label
        ttk.Label(frame, text='label').grid(row=1, column=0, sticky='e')

        # place blank entry
        ttk.Entry(frame, textvariable=self.label, width=20).grid(row=1, column=1, sticky='w')

        # create & place play button
        pil_img = resize_pil(Image.open('play_icon.png'), 20)
        self.icon = icon = ImageTk.PhotoImage(image=pil_img)
        ttk.Button(frame, image=icon, command=self.play).grid(row=1, column=2)      

        # create & place far right side buttons
        ttk.Button(frame, text='save', command=self.save).grid(row=1, column=3)
        ttk.Button(frame, text='next', command=self.next_).grid(row=1, column=4)
        ttk.Button(frame, text='exit', command=self.exit).grid(row=1, column=5)

        frame.pack(side=tk.BOTTOM, fill=tk.BOTH)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_folder', type=str, 
        help='The folder that has the audio clips.')
    parser.add_argument('--out', dest='out_folder', type=str,
        help='The folder where the labeled clips will be saved.')
    parser.add_argument('--csvfile', dest='csvfile', type=str,
        help='The full path and filename of the csvfile where data will be saved.')

    args = parser.parse_args()

    root = tk.Tk()

    try:
        with open('bookmark.txt', 'r') as f:
            f_ind, d_ind, save_folder, filename, csv = f.readline().strip().split(',')
            dtor = SoundDetector(root, args.in_folder, int(f_ind), int(d_ind), save_folder, filename, csv)
    except FileNotFoundError: 
        dtor = SoundDetector(root, datafolder)
    
    root.mainloop()
