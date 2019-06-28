import tkinter as tk
from PIL import Image, ImageTk
import os
import csv
import sys
import det_tools



class SoundDetector:
    def __init__(self, root, audio_clip_folder):
        self.root = root
        self.data_folder = audio_clip_folder

        # get all wav files contained in given directory or subdirectories
        self.wav_files = []
        for rootdir, dirs, filenames in os.walk(self.data_folder):
            for filename in filenames:
                if 'wav' in filename or 'WAV' in filename:
                    self.wav_files.append(filename)
            # break  # activate this line if only top level of directory wanted
        self.file_ind = 0  # start index at 0 (incremented in next_ method)
        self.d_ind = 0  # start at 0 for each audio clip (incrememnted in save, reset in next_)

        # variables for entry labels created in create_ui
        self.folder = tk.StringVar()
        self.filename = tk.StringVar()
        self.label = tk.StringVar()
        self.csv = tk.StringVar()
        
        self.create_ui()
        self.set_defaults()

    def curr_filename(self):
        return self.wav_files[self.file_ind]

    def save(self):
        savepath = os.path.join(self.folder.get(), self.filename.get())
        # TODO: create .WAV clip
        # TODO: save .WAV clip to savepath

        # save entry to csv file 
        with open(self.csv, 'a') as csvfile:
            writer = csv.writer(csvfile.get())
            writer.writerow([savepath, self.label.get()])

        self.d_ind += 1
        self.set_defaults()

    def next_(self):
        # maybe reset some things?
        self.file_ind += 1
        self.d_ind = 0  # reset to 0 for next file
        self.set_defaults()

    def exit(self):
        # save bookmark things? or ask if that is wanted?
        pass

    def display_spec(self):
        full_filepath = os.path.join(self.data_folder, self.curr_filename())
        spec, sr = det_tools.get_spec(full_filepath, frame_len=1024)
        spec = (det_tools.norm(spec) * 255).astype('uint8')
        self.img = img =  ImageTk.PhotoImage(image=Image.fromarray(spec))

        frame = tk.Frame(self.root)
        canvas = tk.Canvas(frame, width=1100, height=img.height(), bg='green')
        scrollbar = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.config(xscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        canvas.config(scrollregion=(0, 0, img.width(), img.height()))
        canvas.create_image(0, 0, image=img, anchor='nw')

        frame.grid(row=0, columnspan=16)

    def create_ui(self):
        self.display_spec()

        # create & place entry labels
        tk.Label(self.root, text='folder').grid(row=1, column=0, sticky='e')
        tk.Label(self.root, text='filename').grid(row=2, column=0, sticky='e')
        tk.Label(self.root, text='label').grid(row=3, column=0, sticky='e')
        tk.Label(self.root, text='csv file').grid(row=4, column=0, sticky='e')

        # place blank entries
        tk.Entry(self.root, textvariable=self.folder).grid(row=1, column=1, sticky='w')
        tk.Entry(self.root, textvariable=self.filename).grid(row=2, column=1, sticky='w')
        tk.Entry(self.root, textvariable=self.label).grid(row=3, column=1, sticky='w')
        tk.Entry(self.root, textvariable=self.csv).grid(row=4, column=1, sticky='w')        

        # create & place far right side buttons
        tk.Button(self.root, text='save', command=self.save).grid(row=1, column=15)
        tk.Button(self.root, text='next', command=self.next_).grid(row=2, column=15)
        tk.Button(self.root, text='exit', command=self.exit).grid(row=3, column=15)

    def set_defaults(self):
        self.filename.set('d{}-{}.WAV'.format(self.curr_filename().split('.')[0], self.d_ind))
        self.csv.set('data.csv')


def main(folder):
    root = tk.Tk()
    dtor = SoundDetector(root, folder)
    root.mainloop()


if __name__ == '__main__':
    # search for bookmark text file
    # get appropriate vars and pass in
    folder = sys.argv[1]
    main(folder)
