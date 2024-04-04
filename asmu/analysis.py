import numpy as np
import scipy as sp
import queue

class Analyzer():
    def __init__(self, chunk, queuesize):
        self._chunk = chunk

        self._w = np.hanning(chunk)
        self._q = queue.Queue(queuesize)

    def reset(self):
        # process full queue
        while not self._q.empty():
            self.process_queue()

    def put_queue(self, data):
        self._q.put(data.copy())

    def process_queue(self):
        pass

    def _get_fft(self) -> np.ndarray:
        return np.fft.rfft(self._q.get()*self._w, axis=0, norm="forward")*2/np.mean(self._w)

class calSPL(Analyzer):
    def __init__(self, chunk, queuesize: int=10):
        self._uks = []
        self._ks = []
        super().__init__(chunk, queuesize)

    def process_queue(self):
        ukm = self._get_fft()

        kmax = np.argmax(np.abs(ukm))
        self._uks.append(np.abs(ukm[kmax]))
        self._ks.append(kmax)

    def get_cSPL(self, spl):
        self.reset()

        p0 = 2e-5                           # [Pa]Rms
        p = p0 * 10 ** (spl / 20)           # [Pa]Rms
        pcal = p * np.sqrt(2)               # [Pa]

        return pcal/np.mean(self._uks[2:]) # dont use the first three measurements

    def get_kSPL(self):
        return round(np.mean(self._ks))
    
def get_corrs_sampleshifts(indata: np.ndarray, refdata: np.ndarray, burstLength: int) -> tuple[np.ndarray, np.ndarray]:
    corrs = []
    sampleshifts = []
    n = int(np.size(refdata))
    for cidx in range(np.ma.size(indata, axis=1)):
        v = indata[:, cidx]
        corr = sp.signal.correlate(v, refdata)
        corr /= np.max(corr)
        peaks, _ = sp.signal.find_peaks(corr, prominence=0.8, distance=burstLength, height=0.5)

        # shift correlation correctly
        corrs.append(corr[n-1:])
        sampleshifts.append(peaks[0]-(n-1))
    return np.array(corrs).T, np.array(sampleshifts)


            
        