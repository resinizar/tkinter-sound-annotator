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


def saveim(im, filename, size=(10, 4)):
    pil_img = Image.fromarray((im*255).astype('uint8')).convert('RGB')
    pil_img.save(filename)


def load_clip(filepath):
    """
    filepath - string - full filepath to desired clip
    return - int, 2d numpy array - sampling rate and data for the clip
    """
    clip, sr = librosa.load(filepath)
    return sr, clip


def get_spec(clip, frame_len):
    stft_clip = librosa.stft(clip, n_fft=frame_len, hop_length=frame_len//2+1)
    stft_mag, stft_ph = librosa.magphase(stft_clip)
    stft_mag_db = librosa.amplitude_to_db(stft_mag)
    return stft_mag_db


def norm(spec):
    """
    spec - 2d numpy array - representation of clip in frequency domain
    return - 2d numpy array - same shape, normalized between 1 and 0
    """
    return (spec - spec.min(0)) / spec.ptp(0)


def detect_events(spec, blur, pickup):
    """
    Lift sound events from background noise.
    spectrogram - 2d numpy array
    blur - int - the window size of the gaussian blur (bigger number = more blur)
    pickup - float [0,1] - the number above which things will be detected
    return - 2d numpy array - a spectrogram of the same shape
    """
    s = cpy(spec)
    s = gaussian_filter(s, blur)
    s = np.where(s >= pickup, 1, 0)
    return s


def clean_low_noise(spec, threshold_row):
    """
    Removes all detection areas contigous to the border.
    spectrogram - 2d numpy array
    threshold_row - int - detections in rows below threshold row will be ignored
    return - 2d numpy array - a spec of the same shape
    """
    s = cpy(spec)
    s[:threshold_row] = 1  # create artificial detections, will be set back to 0

    fill_in_inds = (s==0).argmax(axis=0)  # find first nondetection in every col

    for c, ind in enumerate(fill_in_inds):
        s[:ind, c] = 0  # set all detections (1) previous to nondetections (0)
    
    return s


def create_segmentations(spec, blur, pickup):
    """
    This will split the spec up into parts.
    spec - 2d numpy array
    blur - int - the window for the gaussian blur (higher = less clips)
    pickup - int - if detection strength lower will not be considered
    return - list of 2-tuples - represents start, end of each clip
    """
    detection_strength = np.sum(spec, axis=0)
    detection_strength = gaussian_filter(detection_strength, blur)
    detection_strength = np.where(detection_strength >= pickup, 1, 0)

    # find contigous 1s (detections)
    vocs = [[i for i, value in it] for key, it in itertools.groupby(
        enumerate(detection_strength), key=operator.itemgetter(1)) if key != 0]

    for i in range(len(vocs)):
        start, end = vocs[i][0], vocs[i][-1]
        vocs[i] = (start, end)

    return vocs


def write_detection_clips(clip, spec, sr, vocs):
    """
    Write detected clips to wav files.
    clip - 1d numpy array - the original clip file
    spec - 2d numpy array - needed to translate vocs to original clip
    vocs - list of 2-tuples - represents start, end indices of clips in spectrogram
    return - None
    """
    _, w = spec.shape

    for i, (start, end) in enumerate(vocs):
        new_clip = clip[int(start*len(clip)/w) : int(end*len(clip)/w)]
        wavfile.write('./d{}.wav'.format(i), sr, new_clip)  # TODO: change so no ov


def main():
    filename = '/Users/appa/birds/d_parker/5CAA70D6.WAV'
    sr, clip = load_clip(filename)
    s = get_spec(clip, frame_len=1024)
    s = norm(s)
    saveim(s, './normed.jpeg')
    s = detect_events(s, blur=3, pickup=.65)
    saveim(s, './detections.png')
    s = clean_low_noise(s, threshold_row=55)
    saveim(s, './cleaned.png')
    vocs = create_segmentations(s, blur=19, pickup=1)
    write_detection_clips(clip, s, sr, vocs)


if __name__ == "__main__":
    main()
