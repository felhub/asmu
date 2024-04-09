import soundfile
import tempfile
import shutil
import os
import json
from datetime import datetime


class AFile(soundfile.SoundFile):
    def __init__(self, signal_path, mode="r", samplerate=None, channels=None):
        self._signal_path = signal_path
        if mode == "r":
            super().__init__(signal_path)
        else:
            _name = os.path.split(signal_path)[1].replace(".wav", "")
            self._tmp = tempfile.NamedTemporaryFile(prefix=_name, suffix='.wav', dir="", delete=True)
            super().__init__(self._tmp, mode=mode, samplerate=samplerate, channels=channels, subtype="PCM_24", format="WAV")
            now = datetime.now()
            # set wav metadata
            self.title = _name
            self.date = now.strftime("%d/%m/%Y %H:%M:%S")
    
    # store settings as json string in metadata "comment"
    @property
    def settings(self):
        if not self.comment:
            return {}
        else:
            return json.loads(self.comment)
    @settings.setter
    def settings(self, value):
        self.comment = json.dumps(value)

    @property
    def latency(self):
        try:
            return int(self.settings["latency"])
        except KeyError:
            return None
    @latency.setter
    def latency(self, value):
        self.settings = {"latency": int(value)}

    @property
    def data(self):
        self.flush()
        self.seek(0)
        return self.read(dtype="float32", always_2d=True)
    
    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return object.__getattribute__(self, name)

    def cal_latency(self, time):
       self.latency = round((time.outputBufferDacTime-time.inputBufferAdcTime)*self.samplerate + 1) # the +1 was measured experimentally (could be the cable?)

    def save_file(self):
        # persist temporary file in specified recording location
        self.flush()
        self._tmp.seek(0)
        with open(self._signal_path, 'wb') as file:
            shutil.copyfileobj(self._tmp, file)


