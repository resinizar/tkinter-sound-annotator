##################################################################################
#    Gabriel Cano                                                                #
##################################################################################
#                                                                                #
#                                                                                #
#                                                                                #
##################################################################################

import numpy as np
import librosa  # TODO: try removing librosa and using something else, too many dependencies



class AudioClip:
    def __init__(self, filename, frame_len=1024):
        self.clip, self.sr = librosa.load(filename)
        stft_clip = librosa.stft(self.clip, n_fft=frame_len, hop_length=frame_len//2+1)
        stft_mag, stft_ph = librosa.magphase(stft_clip)
        stft_mag_db = librosa.amplitude_to_db(stft_mag)
        self.spec = self.norm(stft_mag_db)

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
