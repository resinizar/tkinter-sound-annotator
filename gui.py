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
from math import ceil



class AudioAnnotator:
    def __init__(self, data_folder, save_folder, csv_filename, ss_fp, min_dur, f_ind=0, d_ind=0):
        self.root = tk.Tk()
        self.root.title('sound annotator')
        self.data_folder = data_folder
        self.ss_fp = ss_fp
        self.min_dur = min_dur

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
        self.tag = tk.StringVar()
        self.show_filename = tk.StringVar()
        self.show_mini = tk.StringVar()
        self.show_saved = tk.StringVar()
        
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
        self.clip_end = 0  # updated in mouse_up
        self.curr_rect_id = None
        
        self.create_ui()

        self.show_filename.set('displaying file #{} ({})'.format(self.f_ind, self.curr_filename()))
        self.show_mini.set('working on mini clip #{}'.format(self.d_ind))

        self.root.mainloop()

    def curr_filename(self):
        return self.wav_files[self.f_ind]

    def curr_save_filename(self):
        return 'v{}-{}.wav'.format(self.curr_filename().split('.')[0], self.d_ind)

 # ---------------------------------------------------------------------------

    def save(self):
        savepath = os.path.join(self.save_folder, self.curr_save_filename())

        shutil.copy('./support/temp.wav', savepath)

        with open(os.path.join(self.save_folder, self.csv_filename), 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([savepath, self.tag.get()])

        self.show_saved.set('Saved last file as {} to {}'.format(self.tag.get(), savepath))

        self.d_ind += 1  
        self.show_mini.set('working on mini clip #{}'.format(self.d_ind))

    # def undo(self):
    #     curr_filename = self.curr_save_filename()
    #     prev_file_ind = str(int(curr_filename.split('.')[0].split('-')[-1]) - 1)
    #     prev_file = self.curr_save_filename().split('-')[0] + '-' + prev_file_ind + '.wav'
    #     os.remove(os.path.join(self.save_folder, prev_file))

    #     with open(os.path.join(self.save_folder, self.csv_filename), 'r') as csvfile:
    #         r = csv.reader(csvfile)
    #         rows = []
    #         for row in r:
    #             rows.append(row)

    #     with open(os.path.join(self.save_folder, self.csv_filename), 'w') as csvfile:
    #         writer = csv.writer(csvfile)
    #         writer.writerows(rows[:-1])

    #     self.show_saved.set('Erased {}'.format(os.path.join(self.save_folder, prev_file)))

    #     self.d_ind -= 1  
    #     self.show_mini.set('working on mini clip #{}'.format(self.d_ind))

    def prev(self):
        self.f_ind -= 1
        self.show_filename.set('displaying file #{} ({})'.format(self.f_ind, self.curr_filename()))

        # figure out what next d_ind should be
        highest = -1
        for filename in os.listdir(self.save_folder):
            if self.curr_filename().split('.')[0] in filename:  # if voc pertains to current file
                ind = int(filename.split('-')[-1].split('.')[0])
                if ind > highest:
                    highest = cpy(ind)

        self.d_ind = highest + 1
        self.show_mini.set('working on mini clip #{}'.format(self.d_ind))

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
        if self.f_ind >= len(self.wav_files):
            self.show_saved.set('No more wav files. You are done!')
            self.f_ind -= 1

        self.show_filename.set('displaying file #{} ({})'.format(self.f_ind, self.curr_filename()))

        # figure out what next d_ind should be
        highest = -1
        for filename in os.listdir(self.save_folder):
            if self.curr_filename().split('.')[0] in filename:  # if voc pertains to current file
                ind = int(filename.split('-')[-1].split('.')[0])
                if ind > highest:
                    highest = cpy(ind)

        self.d_ind = highest + 1
        self.show_mini.set('working on mini clip #{}'.format(self.d_ind))

        self.curr_clip = AudioClip(os.path.join(self.data_folder, self.curr_filename()))  # get audioclip

        viewable_pil = Image.fromarray((self.curr_clip.spec * 255).astype('uint8'))
        self.temp = img =  ImageTk.PhotoImage(image=viewable_pil)
        self.canvas_img2 = self.canvas.itemconfig(self.canvas_img1, image=img)

        if self.curr_rect_id:
            self.canvas.delete(self.curr_rect_id)

    def play(self):
        playsound('./support/temp.wav')  # TODO: do on a diff thread

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
        self.clip_end = int(self.canvas.canvasx(event.x))
        if self.clip_end < self.clip_start:
            self.curr_clip.write_mini_clip('./support/temp.wav', self.clip_end, self.clip_start, self.min_dur)
        else:
            self.curr_clip.write_mini_clip('./support/temp.wav', self.clip_start, self.clip_end, self.min_dur)

    # ---------------------------------------------------------------------------

    def create_ui(self):
        viewable_pil = Image.fromarray((self.curr_clip.spec * 255).astype('uint8'))
        self.temp = img =  ImageTk.PhotoImage(image=viewable_pil)
        self.spec_h = img.height()

        frame = ttk.Frame(self.root)
        self.canvas = tk.Canvas(frame, width=800, height=img.height(), bg='white')
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

        frame.pack(side=tk.TOP, fill=tk.BOTH)

        frame = ttk.Frame(self.root)

        # create & place entry for tag
        ttk.Label(frame, text='tag').pack(side=tk.LEFT)

        # place blank entry & label saying which mini clip
        ttk.Entry(frame, textvariable=self.tag, width=20).pack(side=tk.LEFT)
        ttk.Label(frame, textvariable=self.show_mini).pack(side=tk.LEFT)

        # create & place far right side buttons
        ttk.Button(frame, text='exit', command=self.exit).pack(side=tk.RIGHT)
        ttk.Button(frame, text='next', command=self.next_).pack(side=tk.RIGHT)
        ttk.Button(frame, text='back', command=self.prev).pack(side=tk.RIGHT)
        ttk.Button(frame, text='save', command=self.save).pack(side=tk.RIGHT)

        # create & place play button
        pil_img = resize_pil(Image.open('./support/play_icon.png'), 20)
        self.icon = icon = ImageTk.PhotoImage(image=pil_img)
        ttk.Button(frame, image=icon, command=self.play).pack(side=tk.RIGHT)

        frame.pack(fill=tk.BOTH)

        frame = ttk.Frame(self.root)

        # informational labels
        ttk.Label(frame, textvariable=self.show_filename).pack(side=tk.LEFT, anchor='se')
        ttk.Label(frame, textvariable=self.show_saved).pack(side=tk.RIGHT, anchor='sw')

        # create key bindings for play, save, next, & exit
        self.root.bind_all('<Command-KeyPress-p>', lambda _: self.play())
        self.root.bind_all('<Command-KeyPress-u>', lambda _: self.undo())
        self.root.bind_all('<Command-KeyPress-s>', lambda _: self.save())
        self.root.bind_all('<Command-KeyPress-n>', lambda _: self.next_())
        self.root.bind_all('<Command-KeyPress-b>', lambda _: self.prev())
        self.root.bind_all('<Escape>', lambda _: self.exit())
        
        frame.pack(fill=tk.BOTH)


class SaveSessionPopup():
    def __init__(self, annotator):
        self.annotator = annotator
        self.root = tk.Tk()
        self.root.title('sound annotator')
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
        with open(self.annotator.ss_fp, 'w') as f:
            values = ','.join([self.annotator.data_folder, 
                                self.annotator.save_folder, 
                                self.annotator.csv_filename, 
                                str(self.annotator.min_dur),
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

    def write_mini_clip(self, filename, start_spec, end_spec, min_dur=None):
        """
        filename - string - the full filepath to save the clip
        start_ind - int - the desired starting place in spec
        end_ind - int - the desired stopping place in spec
        return - None
        """
        _, spec_w = self.spec.shape
        start = int(start_spec * len(self.clip) / spec_w)
        end   = int(end_spec   * len(self.clip) / spec_w)

        dur = (end - start) / self.sr
        if min_dur and dur < min_dur:
            pad_len = ceil((min_dur - dur) / 2 * self.sr)
            mini = self.clip[start - pad_len:end + pad_len]
        else:
            mini = self.clip[start:end]
        librosa.output.write_wav(filename, mini, self.sr)


def resize_pil(img, max_w):
    h, w = img.size
    new_h = int(h * max_w / w)
    return img.resize((new_h, max_w))


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('You must supply either a saved session textfile or the datapath, savepath, and csvfilename. See python gui.py -h for more info.')
    else:
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('-d', dest='datapath', type=str, 
            help='Full path to folder with audio clips.')
        parser.add_argument('-s', dest='savepath', type=str,
            help='Full path to existing folder where new clips will be saved.')
        parser.add_argument('-f', dest='csvfile', type=str,
            help='The full path and filename of the csvfile where data tags will be saved.')
        parser.add_argument('-t', dest='savesession', default='./support/ss.txt', type=str,
            help='The filepath of the saved session you want to save.')
        parser.add_argument('-l', dest='loadsession', type=str,
            help='The filepath of the saved session you want to load. This will be overwritten in next save.')
        parser.add_argument('-m', dest='min_dur', default=1.0, type=float,
            help='The minimum duration in seconds of a miniclip.')
        args = parser.parse_args()

        if args.loadsession is not None:  # if provided with a session to load
            with open(args.loadsession, 'r') as f:
                data_folder, save_folder, csv_filename, min_dur, f_ind, d_ind = f.readline().strip().split(',')
                AudioAnnotator(data_folder, save_folder, csv_filename, args.loadsession, float(min_dur), int(f_ind), int(d_ind))
        else:
            if '.csv' not in args.csvfile:
                raise Exception('must be a csvfile (got {})'.format(args.csvfile))
            AudioAnnotator(args.datapath, args.savepath, args.csvfile, args.savesession, args.min_dur)
