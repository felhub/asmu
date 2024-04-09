import numpy as np
import scipy as sp
import threading
import queue

class Generator():
    def __init__(self, queuesize) -> None:
        self._q = queue.Queue(queuesize)
        self._prefill_queue()

    def get_queue(self) -> queue.Queue:
        return self._q.get_nowait()

    def _prefill_queue(self) -> None:
        while self._q.full() is False:
           self.refill_queue(block=False)

    def refill_queue(self, block=True) -> None:
        #if self._q.full() is False:
        data = self._gen()
        self._q.put(data, block=block, timeout=0.2)

    def start_refill_thread(self, stream):
        def runner(self, stream):
            while stream.active:
                try:
                    self.refill_queue()
                except queue.Full:
                    pass
        threading.Thread(target=runner, args=(self, stream, )).start()
    
    def _gen(self):
        raise NotImplementedError("Subclass has to define a _gen function!")

class Player(Generator):
    def __init__(self, asfile, chunk, queuesize=10):
        self._asfile = asfile
        self._chunk = chunk
        super().__init__(queuesize)

    def _gen(self):
        data = self._asfile.read(self._chunk, dtype="float32", always_2d=True)
        length = np.ma.size(data, axis=0)
        if data.size == 0:
            return None
        elif length < self._chunk:
            pad = np.zeros((self._chunk, self._asfile.channels))
            pad[:length, :] = data
            return pad
        else:
            return data

class Chirp(Generator):
    def __init__(self, rate: int, chunk: int, f0: float, f1: float, duration: int, queuesize: int=10) -> None:
        self._rate = rate
        self._chunk = chunk
        
        t = np.arange(0, int(duration*rate)) / rate
        self._chirp = sp.signal.chirp(t, f0=f0, t1=duration, f1=f1, method="logarithmic")
        self._idx = 0
        super().__init__(queuesize)
    
    def _gen(self) -> np.ndarray:
        data = self._chirp[self._idx:self._idx+self._chunk]
        self._idx += self._chunk

        length = np.ma.size(data, axis=0)
        if data.size == 0:
            return None
        elif length < self._chunk:
            pad = np.zeros(self._chunk)
            pad[:length] = data
            return pad
        else:
            return data


class SineBurst(Generator):
    def __init__(self, rate: int, chunk: int, f: float, n: int, loop: float=-1, queuesize: int=10) -> None:
        self._rate = rate
        self._chunk = chunk
        self._freq = f

        # generate wave parameters
        self._omegas = np.linspace(0, 2*np.pi*f*chunk/rate, chunk, endpoint=False, dtype=np.float32)
        self._phi = 0
        self._maxang = 2*np.pi*n
        self._loopang = 2*np.pi*loop*f

        super().__init__(queuesize)

    @property
    def burstlen(self):
        return self._rate/(2*np.pi*self._freq)*self._maxang

    def _gen(self) -> np.ndarray:
        ang = self._omegas + self._phi
        if self._loopang > 0: ang = np.mod(ang, self._loopang)
        sineburst = np.sin(ang)
        sineburst[ang > self._maxang] = 0
        self._phi += 2*np.pi*self._freq*self._chunk/self._rate
        return sineburst
    
class SincBurst(Generator):
    def __init__(self, rate: int, chunk: int, f: float, n: int, loop: float=-1, queuesize: int=10) -> None:
        self._rate = rate
        self._chunk = chunk
        self._freq = f

        # generate wave parameters
        self._omegas = np.linspace(0, 2*np.pi*f*chunk/rate, chunk, endpoint=False, dtype=np.float32)
        self._phi = 0
        self._maxang = 2*np.pi*n
        self._loopang = 2*np.pi*loop*f

        super().__init__(queuesize)

    @property
    def burstlen(self):
        return self._rate/(2*np.pi*self._freq)*self._maxang

    def _gen(self) -> np.ndarray:
        ang = self._omegas + self._phi
        if self._loopang > 0: ang = np.mod(ang, self._loopang)
        sincburst = np.sinc((ang-self._maxang/2)/np.pi)
        sincburst[ang > self._maxang] = 0
        self._phi += 2*np.pi*self._freq*self._chunk/self._rate
        return sincburst
        
class WhiteNoise(Generator):
    def __init__(self, chunk: int, queuesize: int=10) -> None:
        self._chunk = chunk

        super().__init__(queuesize)

    def _gen(self) -> np.ndarray:
        fwhite = np.fft.rfft(np.random.randn(self._chunk))
        return np.clip(np.fft.irfft(fwhite)/4, -1, 1)
    
class PinkNoise(Generator):
    def __init__(self, chunk: int, queuesize: int=10) -> None:
        self._chunk = chunk

        super().__init__(queuesize)

    def _gen(self) -> np.ndarray:
        fwhite = np.fft.rfft(np.random.randn(self._chunk))

        # apply noise color and normalize for power
        f = np.fft.rfftfreq(self._chunk)
        S = 1/np.where(f == 0, float('inf'), np.sqrt(f))
        S = S / np.sqrt(np.mean(S**2))
        fpink = fwhite * S

        return np.clip(np.fft.irfft(fpink)/4, -1, 1)

class Sine(Generator):
    def __init__(self, rate: int, chunk: int, f: float, queuesize: int=10) -> None:
        self._rate = rate
        self._chunk = chunk
        self._freq = f

        # generate wave parameters
        self._omegas = np.linspace(0, 2*np.pi*f*chunk/rate, chunk, endpoint=False, dtype=np.float32)
        self._phi = 0

        super().__init__(queuesize)

    def _gen(self) -> np.ndarray:
        ang = self._omegas + self._phi
        self._phi += 2*np.pi*self._freq*self._chunk/self._rate
        self._phi %= 2*np.pi
        return np.sin(ang)

                    
        