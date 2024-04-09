import numpy as np
import scipy as sp
import queue
import threading

class Analyzer():
    def __init__(self, queuesize):
        self._q = queue.Queue(queuesize)

    def reset(self):
        # process full queue
        while not self._q.empty():
            self._process_queue()

    def put_queue(self, data):
        self._q.put(data.copy())

    def _process_queue(self):
        raise NotImplementedError("Subclass has to define a process_queue function!")

    def start_process_thread(self, stream):
        def runner(self, stream):
            while stream.active:
                try:
                    self._process_queue()
                except queue.Empty:
                    pass
        threading.Thread(target=runner, args=(self, stream, )).start()


    def _get_fft(self) -> np.ndarray:
        raise NotImplementedError() # TODO: Move this to helper function
        return np.fft.rfft(self._q.get()*self._w, axis=0, norm="forward")*2/np.mean(self._w)
    
class Recorder(Analyzer):
    def __init__(self, signal, queuesize=10):
        self._signal = signal
        super().__init__(queuesize)
        
    def _process_queue(self):
        self._signal.write(self._q.get(timeout=0.2))

class calSPL(Analyzer):
    def __init__(self, chunk, queuesize: int=10):
        self._uks = []
        self._ks = []
        super().__init__(queuesize)

    def _process_queue(self):
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


            
        