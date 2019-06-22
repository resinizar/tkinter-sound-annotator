##################################################################################
#    Gabriel Cano                                                                #
##################################################################################
#                                                                                #
#                                                                                #
#                                                                                #
##################################################################################

import os
import numpy as np      
from copy import deepcopy as cpy
from scipy.io import wavfile
from scipy.ndimage import gaussian_filter
import itertools, operator
from scipy.signal import spectrogram
import librosa
from PIL import Image

class Detector:

    def __init__(self, filename, ident=1, frame_len=1024):
        self.clip, self.sr = librosa.load(filename)
        self.spec = self.norm(self.get_spec(frame_len))
        self.dets = None  # detections, set in create_segmentations
        self.id = ident  # so files have non overlapping detection names

    @staticmethod
    def norm(spec):
        """
        spec - 2d numpy array - representation of clip in frequency domain
        return - 2d numpy array - same shape, normalized between 1 and 0
        """
        return (spec - spec.min(0)) / spec.ptp(0)

    def get_spec(self, frame_len):
        stft_clip = librosa.stft(
            self.clip, n_fft=frame_len, hop_length=frame_len//2+1)
        stft_mag, stft_ph = librosa.magphase(stft_clip)
        stft_mag_db = librosa.amplitude_to_db(stft_mag)
        return stft_mag_db

    def detect_events(self, blur, pickup):
        """
        Lift sound events from background noise.
        spectrogram - 2d numpy array
        blur - int - the window size of the gaussian blur (bigger number = more blur)
        pickup - float [0,1] - the number above which things will be detected
        return - 2d numpy array - a spectrogram of the same shape
        """
        self.spec = gaussian_filter(self.spec, blur)
        self.spec = np.where(self.spec >= pickup, 1, 0)
        return self.spec

    def clean_low_noise(self, threshold_row):
        """
        Removes all detection areas contigous to the border.
        spectrogram - 2d numpy array
        threshold_row - int - detections in rows below threshold row will be ignored
        return - 2d numpy array - a spec of the same shape
        """
        self.spec = cpy(self.spec)
        self.spec[:threshold_row] = 1  # create artificial detections, will be set back to 0

        fill_in_inds = (self.spec==0).argmax(axis=0)  # find first nondetection in every col

        for c, ind in enumerate(fill_in_inds):
            self.spec[:ind, c] = 0  # set all detections (1) previous to nondetections (0)
        
        return self.spec

    def create_segmentations(self, blur, pickup):
        """
        This will split the spec up into parts.
        spec - 2d numpy array
        blur - int - the window for the gaussian blur (higher = less clips)
        pickup - int - if detection strength lower will not be considered
        return - list of 2-tuples - represents start, end of each clip
        """
        det_strength = np.sum(self.spec, axis=0)
        det_strength = gaussian_filter(det_strength, blur)
        det_strength = np.where(det_strength >= pickup, 1, 0)

        # find contigous 1s (detections)
        self.dets = [[i for i, value in it] for key, it in itertools.groupby(
            enumerate(det_strength), key=operator.itemgetter(1)) if key != 0]

        _, w = self.spec.shape
        for i in range(len(self.dets)):
            start, end = (int(self.dets[i][0]*len(self.clip)/w), 
                          int(self.dets[i][-1]*len(self.clip)/w))
            self.dets[i] = (start, end)

        return self.dets

    def write_detection_clips(self, vocs):
        """
        Write detected clips to wav files.
        clip - 1d numpy array - the original clip file
        spec - 2d numpy array - needed to translate vocs to original clip
        vocs - list of 2-tuples - represents start, end indices of clips in spectrogram
        return - None
        """
        for i, (start, end) in enumerate(vocs):
            new_clip = self.clip[start:end]
            wavfile.write('./dets/clip{}_d{}.wav'.format(self.id, i), self.sr, new_clip)


def main():
    filename = '/Users/appa/birds/d_parker/5CAA70D6.WAV'
    detector = Detector(filename)
    detector.detect_events(blur=3, pickup=.65)
    detector.clean_low_noise(threshold_row=55)
    vocs = detector.create_segmentations(blur=19, pickup=1)
    detector.write_detection_clips(vocs)


if __name__ == "__main__":
    main()
