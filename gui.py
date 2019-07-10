##################################################################################
#    Gabriel Cano                                                                #
##################################################################################
#    A gui made for labeling sound events in a spectrogram manually.             #
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
import shutil
from copy import deepcopy as cpy
import librosa
import numpy as np



class AudioAnnotator:
    def __init__(self, data_folder, save_folder, csv_filename, f_ind=0, d_ind=0):
        self.root = root = tk.Tk()
        self.data_folder = data_folder

        # get all wav files contained in given directory or subdirectories
        self.wav_files = []
        for rootdir, dirs, filenames in os.walk(self.data_folder):
            for filename in filenames:
                if 'wav' in filename or 'WAV' in filename:
                    self.wav_files.append(filename)
            break  # activate this line if only top level of directory wanted

        # saving folders
        self.save_folder = save_folder
        self.csv_filename = csv_filename

        # entry label variable
        self.label = tk.StringVar()
        self.info1 = tk.StringVar()
        self.info2 = tk.StringVar()
        self.info3 = tk.StringVar()
        
        # variables set elsewhere that last the program lifetime
        self.canvas = None # updated in create_ui
        self.spec_h = 0

        # variables set elsewhere that change with each new clip
        self.f_ind = f_ind
        self.curr_clip = AudioClip(os.path.join(self.data_folder, self.wav_files[self.f_ind]))
        self.canvas_img1 = None  # I have no idea why I need two, it works
        self.canvas_img2 = None
        self.temp = None  # used so tkinter doesn't delete the images for the spectrogram

        # variables set elsewhere that change while working on one clip
        self.d_ind = d_ind
        self.clip_start = 0  # updated on click in mouse_down
        self.curr_rect_id = None
        
        self.create_ui()

        self.info1.set('displaying file #{} ({})'.format(self.f_ind, self.curr_filename()))
        self.info2.set('working on mini clip #{}'.format(self.d_ind))

        self.root.mainloop()

    def curr_filename(self):
        return self.wav_files[self.f_ind]

    def curr_save_filename(self):
        return 'd{}-{}.wav'.format(self.curr_filename().split('.')[0], self.d_ind)

 # ---------------------------------------------------------------------------

    def save(self):
        savepath = os.path.join(self.save_folder, self.curr_save_filename())
        shutil.copy('./temp.wav', savepath)

        with open(os.path.join(self.save_folder, self.csv_filename), 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([savepath, self.label.get()])

        self.info3.set('Saved last file as {} to {}'.format(self.label.get(), savepath))

        self.d_ind += 1  
        self.info2.set('working on mini clip #{}'.format(self.d_ind))

    def undo(self):
        curr_filename = self.curr_save_filename()
        prev_file_ind = str(int(curr_filename.split('.')[0].split('-')[-1]) - 1)
        prev_file = self.curr_save_filename().split('-')[0] + '-' + prev_file_ind + '.wav'
        os.remove(os.path.join(self.save_folder, prev_file))

        with open(os.path.join(self.save_folder, self.csv_filename), 'r') as csvfile:
            r = csv.reader(csvfile)
            rows = []
            for row in r:
                rows.append(row)

        with open(os.path.join(self.save_folder, self.csv_filename), 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows[:-1])

        self.info3.set('Erased {}'.format(os.path.join(self.save_folder, prev_file)))

        self.d_ind -= 1  
        self.info2.set('working on mini clip #{}'.format(self.d_ind))

    def prev(self):
        self.f_ind -= 1
        self.info1.set('displaying file #{} ({})'.format(self.f_ind, self.curr_filename()))

        # figure out what next d_ind should be
        highest = -1
        for filename in os.listdir(self.save_folder):
            if self.curr_filename().split('.')[0] in filename:  # if detection pertains to current file
                ind = int(filename.split('-')[-1].split('.')[0])
                if ind > highest:
                    highest = cpy(ind)

        self.d_ind = highest + 1
        self.info2.set('working on mini clip #{}'.format(self.d_ind))

        self.curr_clip = AudioClip(os.path.join(self.data_folder, self.curr_filename()))  # get audioclip

        # display audioclip
        viewable_pil = Image.fromarray((self.curr_clip.spec * 255).astype('uint8'))
        self.temp = img =  ImageTk.PhotoImage(image=viewable_pil)
        self.canvas_img2 = self.canvas.itemconfig(self.canvas_img1, image=img)

        # delete any yellow rects
        if self.curr_rect_id:
            self.canvas.delete(self.curr_rect_id)

    def next_(self):
        self.f_ind += 1
        self.info1.set('displaying file #{} ({})'.format(self.f_ind, self.curr_filename()))

        # figure out what next d_ind should be
        highest = -1
        for filename in os.listdir(self.save_folder):
            if self.curr_filename().split('.')[0] in filename:  # if detection pertains to current file
                ind = int(filename.split('-')[-1].split('.')[0])
                if ind > highest:
                    highest = cpy(ind)

        self.d_ind = highest + 1
        self.info2.set('working on mini clip #{}'.format(self.d_ind))

        self.curr_clip = AudioClip(os.path.join(self.data_folder, self.curr_filename()))  # get audioclip

        viewable_pil = Image.fromarray((self.curr_clip.spec * 255).astype('uint8'))
        self.temp = img =  ImageTk.PhotoImage(image=viewable_pil)
        self.canvas_img2 = self.canvas.itemconfig(self.canvas_img1, image=img)

        if self.curr_rect_id:
            self.canvas.delete(self.curr_rect_id)

    def play(self):
        playsound('temp.wav')  # TODO: do on a diff thread

    def exit(self):
        SaveSessionPopup(self)
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

    # ---------------------------------------------------------------------------

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

        # self.canvas.bind_all('<MouseWheel>', lambda e: self.canvas.xview_scroll(-1 * e.delta, 'units'))

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
        ttk.Button(frame, text='back', command=self.prev).grid(row=1, column=4)
        ttk.Button(frame, text='next', command=self.next_).grid(row=1, column=5)
        ttk.Button(frame, text='exit', command=self.exit).grid(row=1, column=6)

        # informational labels
        ttk.Label(frame, textvariable=self.info1).grid(row=1, column=7)
        ttk.Label(frame, textvariable=self.info2).grid(row=1, column=8)
        ttk.Label(frame, textvariable=self.info3).grid(row=2, column=0, columnspan=8, sticky='w')

        # create key bindings for play, save, next, & exit
        self.root.bind_all('<Command-KeyPress-p>', lambda _: self.play())
        self.root.bind_all('<Command-KeyPress-u>', lambda _: self.undo())
        self.root.bind_all('<Command-KeyPress-s>', lambda _: self.save())
        self.root.bind_all('<Command-KeyPress-n>', lambda _: self.next_())
        self.root.bind_all('<Command-KeyPress-b>', lambda _: self.prev())
        self.root.bind_all('<Escape>', lambda _: self.exit())
        
        frame.pack(side=tk.BOTTOM, fill=tk.BOTH)


class SaveSessionPopup():
    def __init__(self, annotator):
        self.annotator = annotator
        self.root = tk.Tk()
        frame = ttk.Frame(self.root)
        ttk.Label(frame, text='save session?').grid(row=0, column=0, columnspan=2, sticky='w')
        ttk.Button(frame, text='yes', command=self.save).grid(row=1, column=1)
        ttk.Button(frame, text='no', command=self.exit).grid(row=1, column=2)
        frame.pack()

        frame.bind('<Command-KeyPress-s>', lambda _: self.save())
        frame.bind('<Escape>', lambda _: self.exit())
        self.root.mainloop()
        self.root.destroy()

    def save(self):
        with open('savedsession.txt', 'w') as f:
            values = ','.join([self.annotator.data_folder, 
                                self.annotator.save_folder, 
                                self.annotator.csv_filename, 
                                str(self.annotator.f_ind), 
                                str(self.annotator.d_ind)])
            print(values, file=f)
        self.root.quit()

    def exit(self):
        self.root.quit()


class AudioClip:
    def __init__(self, filename, frame_len=1024):
        self.clip, self.sr = librosa.load(filename)

        # creates spectrogram
        stft_clip = librosa.stft(self.clip, n_fft=frame_len, hop_length=frame_len//2+1)
        stft_mag, stft_ph = librosa.magphase(stft_clip)
        self.spec = librosa.amplitude_to_db(stft_mag)
        self.spec = self.norm(self.spec)  # norm between 0 and 1
        self.spec = self.spec[np.where(np.sum(self.spec, axis=1) > 1)]
        self.spec = np.flipud(self.spec)  # flip so low sounds are on bottom

    @staticmethod
    def norm(spec):
        """
        spec - 2d numpy array - representation of clip in frequency domain
        return - 2d numpy array - same shape, normalized between 0 and 1
        """
        min_num = np.amin(spec)
        max_num = np.amax(spec)
        return np.divide(np.add(spec, -min_num), max_num-min_num)

    def write_mini_clip(self, filename, start_spec, end_spec):
        """
        filename - string - the full filepath to save the clip
        start_ind - int - the desired starting place in spec
        end_ind - int - the desired stopping place in spec
        return - None
        """
        _, spec_w = self.spec.shape
        start = int(start_spec * len(self.clip) / spec_w)
        end   = int(end_spec   * len(self.clip) / spec_w)

        mini = self.clip[start:end]
        librosa.output.write_wav(filename, mini, self.sr)


if __name__ == '__main__':
    try:
        with open('savedsession.txt', 'r') as f:
            data_folder, save_folder, csv_filename, f_ind, d_ind = f.readline().strip().split(',')
            AudioAnnotator(data_folder, save_folder, csv_filename, int(f_ind), int(d_ind))
    except FileNotFoundError:

        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--in', dest='in_folder', type=str, 
            help='The folder that has the audio clips.')
        parser.add_argument('--out', dest='out_folder', type=str,
            help='The folder where the labeled clips will be saved.')
        parser.add_argument('--csvfile', dest='csvfile', type=str,
            help='The full path and filename of the csvfile where data will be saved.')
        args = parser.parse_args()

        AudioAnnotator(args.in_folder, args.out_folder, args.csvfile)
    
    