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
from scipy.signal import medfilt
import librosa
from PIL import Image


DET = 1
NO_DET = 0

def norm(spec):
    """
    spec - 2d numpy array - representation of clip in frequency domain
    return - 2d numpy array - same shape, normalized between 0 and 1
    """
    min_num = np.amin(spec)
    max_num = np.amax(spec)
    return np.divide(np.add(spec, -min_num), max_num-min_num)


def get_spec(filename, frame_len):
    clip, sr = librosa.load(filename)
    stft_clip = librosa.stft(clip, n_fft=frame_len, hop_length=frame_len//2+1)
    stft_mag, stft_ph = librosa.magphase(stft_clip)
    stft_mag_db = librosa.amplitude_to_db(stft_mag)
    return stft_mag_db, sr


def detect_events(spec, pickup):
    """
    Lift sound events from background noise.
    spectrogram - 2d numpy array
    pickup - float [0, 1] - the number above which things will be detected
    return - 2d numpy array - a spectrogram of the same shape
    """
    s = cpy(spec) 
    s = gaussian_filter(s, 1)
    s = np.where(s >= pickup, DET, NO_DET)
    s = medfilt(s, 5)
    return s


def remove_low_noise(spec, threshold_row):
    """
    Removes all detection areas contigous to the border.
    spectrogram - 2d numpy array
    threshold_row - int - detections in rows below threshold row will be ignored
    return - 2d numpy array - a spec of the same shape
    """
    s = cpy(spec) 
    s[:threshold_row] = DET  # create artificial detections, will be set back
    fill_in_inds = (s==NO_DET).argmax(axis=0)  # find first nondetection in every col

    for c, ind in enumerate(fill_in_inds):
        s[:ind, c] = NO_DET  
    
    return s


def create_segmentations(summed, blur, pickup):
    """
    This will split the spec up into parts.
    spec - 2d numpy array
    blur - int - the window for the gaussian blur (higher = less clips)
    pickup - int - if detection strength lower will not be considered
    return - 1d numpy array - contiguous 1s are detected clips
    """
    det_strength = gaussian_filter(summed, blur)
    return np.where(det_strength >= pickup, DET, NO_DET)


def write_detection_clips(dets):
    """
    Write detected clips to wav files.
    dets - 1d numpy array - contiguous 1s are detected clips
    return - None
    """
    # find contigous 1s (detections)
    clips = [[i for i, value in it] for key, it in itertools.groupby(
        enumerate(dets), key=operator.itemgetter(DET)) if key != NO_DET]

    _, w = self.spec.shape
    for i in range(len(clips)):
        start, end = (int(clips[i][0]*len(self.clip)/w), 
                      int(clips[i][-1]*len(self.clip)/w))
        clips[i] = (start, end)

    for i, (start, end) in enumerate(clips):
        new_clip = self.clip[start:end]
        wavfile.write('/Volumes/BIRDS/park/a_dets/d{}-{}.wav'.format(self.id, i), self.sr, new_clip)
