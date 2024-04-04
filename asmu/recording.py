import json
import numpy as np
import queue
import soundfile as sf
import tempfile
import shutil
import os
import threading

from datetime import datetime

class Recording():
    def __init__(self, recordingPath: str, mode: str, setupName: str, channels: int, rate: int, chunk: int, queuesize=10) -> None:
        """Constructs all the necessary attributes for the Recording object.

        Args:
            recordingPath (str): Path to an .asm_rec file
            mode ("r", "w"): Set recording mode to read "r", or write "w"
            setupName (str): Name of the current setup for comparison with the recordings setupName
            channels (int): Channel count
            rate (int): Samplerate
            chunk (int): Chunksize
            queuesize (int, optional): The size of the internal queue. Defaults to 10.
        """
        # path and recording info
        self._path, file = os.path.split(recordingPath)
        self._name = file.replace(".asm_recording", "") # extract name without file ending
        now = datetime.now()
        self._recordingData = {
            "setupName" : setupName,
            "date" : now.strftime("%d/%m/%Y"),
            "time" : now.strftime("%H:%M:%S"),
        }

        # save parameters
        self._mode = mode
        self._rate = rate
        self._chunk = chunk
        self._channels = channels

        # create buffer queue for transfer between threads
        self._rq = queue.Queue(queuesize)
        self._pq = queue.Queue(queuesize)

    def __enter__(self):
        if self._mode=="r":
            self.load_file(self.setupName)
        elif self._mode=="w":
            self.create_file()
        else:
            raise Exception(f"Recording - invalid mode specified, use \"r\" or \"w\".")

        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._filesf.close()

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path
    
    @property 
    def setupName(self):
        return self._recordingData["setupName"]

    @property
    def date(self):
        return self._recordingData["date"]

    @property
    def time(self):
        return self._recordingData["time"]
    
    @property
    def extra_settings(self):
        """:obj:`dict` of :obj:`dict`: Store extra settings in .asm_rec file.

        Setting the dict overwrites existing extra_settings!
        """
        return self._recordingData["extra_settings"]
    @extra_settings.setter
    def extra_settings(self, value):
        self._recordingData["extra_settings"] = value
    
    @property
    def latency(self):
        try:
            return self._recordingData["latency"]
        except KeyError:
            return None
    @latency.setter
    def latency(self, value):
        self._recordingData["latency"] = int(value)
    
    @property
    def data(self):
        # process full queue
        while not self._rq.empty():
            self.process_queue()
            
        self._filesf.flush()
        self._filesf.seek(0)
        return self._filesf.read(dtype="float32", always_2d=True)

# LATENCY
    def set_latency(self, time):
        self.latency = round((time.outputBufferDacTime-time.inputBufferAdcTime)*self._rate + 1) # the +1 was measured experimentally (could be the cable?)

# PLAYBACK
    def get_queue(self):
        return self._pq.get_nowait()

    def prefill_queue(self):
        self.empty_queue()
        self._filesf.seek(0)
        while self._pq.full() is False:
           self.refill_queue(block=False)

    def refill_queue(self, block=True):
        if self._pq.full() is False:
            data = self._gen()
            self._pq.put(data, block=block)

    def empty_queue(self):
        while not self._pq.empty():
            self.get_queue()
        
    def _gen(self):
        data = self._filesf.read(self._chunk, dtype="float32", always_2d=True)
        length = np.ma.size(data, axis=0)
        if data.size == 0:
            return None
        elif length < self._chunk:
            pad = np.zeros((self._chunk, self._channels))
            pad[:length, :] = data
            return pad
        else:
            return data

# RECORDING
    def create_file(self, subtype="PCM_24"):
        self._file = tempfile.NamedTemporaryFile(prefix=f"{self.name}", suffix='.wav', dir="", delete=True)
        self._filesf = sf.SoundFile(self._file, mode='w+', samplerate=self._rate, channels=self._channels, subtype=subtype, format="WAV")
    
    def put_queue(self, data):
        self._rq.put(data.copy())

    def process_queue(self):
        self._filesf.write(self._rq.get(timeout=0.2))

    def start_process_thread(self, stream):
        def runner(self, stream):
            while stream.active:
                try:
                    self.process_queue()
                except queue.Empty:
                    pass
        threading.Thread(target=runner, args=(self, stream, )).start()

# SAVE/LOAD
    def save_file(self, extra_settings={}):
        # add new extra_settings
        if extra_settings:
            self.extra_settings = extra_settings
            
        # save .asm_rec file
        with open(f"{self.path}/{self.name}.asm_rec", 'w') as file:
            file.write(json.dumps(self._recordingData))

        # process full queue
        while not self._rq.empty():
            self.process_queue()

        # persist temporary files in specified recording location 
        self._file.flush()
        self._file.seek(0)
        with open(f"{self.path}/{self.name}.wav", 'wb') as file:
            shutil.copyfileobj(self._file, file)

    def load_file(self, currentSetupName):
        # open .asm_rec file
        with open(f"{self.path}/{self.name}.asm_rec", 'r') as file:
            self._recordingData = json.load(file)

        # check if setups are equal
        if self.setupName != currentSetupName:
            raise Exception(f"Recording - current setup does not match setup of {self.setupName}.asm_rec")

        # open .wav file
        self._filesf = sf.SoundFile(f"{self.path}/{self.name}.wav")
        self.prefill_queue()
