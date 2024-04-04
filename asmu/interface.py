import numpy as np
import sounddevice as sd

DEBUG = True

class Interface():
    def __init__(self, interfaceSetup: dict) -> None:
        """Class for Audiointerface communication and settings.

        Args:
            interfaceSetup (dict): Interface setup.
        """
        self._interfaceSetup = interfaceSetup
        self.callback = None

    @property
    def name(self):
        return self._interfaceSetup["name"]

    @property
    def device(self):
        return self._interfaceSetup["device"]
    @device.setter
    def device(self, value):
        self._interfaceSetup["device"] = value

    @property
    def rate(self):
        return int(self._interfaceSetup["rate"])

    @property
    def chunk(self):
        return int(self._interfaceSetup['chunk'])
    
    # SOUNDDEVICE
    def initSounddevice(self, channels: tuple[int, int]) -> None:
        sd.default.samplerate = self.rate
        sd.default.dtype = np.float32
        sd.default.blocksize = self.chunk
        try:
            sd.default.device = self.device # TODO - different input and output device
        except KeyError:
            print("interface - no device specified, using default")
            return

        if "ASIO" in self.device:
            if channels[0]:
                inChannels = [c - 1 for c in channels[0]] # convert to channel names starting with 0
                asio_in = sd.AsioSettings(channel_selectors=inChannels)

                if not channels[1]:
                    sd.default.extra_settings = asio_in
                    sd.default.channels = len(inChannels)
                    return

            if channels[1]:
                outChannels = [c - 1 for c in channels[1]]
                asio_out = sd.AsioSettings(channel_selectors=outChannels)

                if not channels[0]:
                    sd.default.extra_settings = asio_out
                    sd.default.channels = len(outChannels)
                    return
            
            if channels[0] and channels[1]:
                sd.default.extra_settings = (asio_in, asio_out)
                sd.default.channels = (len(inChannels), len(outChannels))
                return
            
        elif "CoreAudio" in self.device: # TODO - update this
            inChannels = [c - 1 for c in channels[0]] # convert to channel names starting with 0
            ca_in = sd.CoreAudioSettings(channel_map=inChannels)

            if channels[1]:
                outChannels = [-1]*sd.query_devices(device=self.device, kind="output")["max_output_channels"]
                for idx, c in enumerate(channels[1]):
                    outChannels[c-1] = idx
                ca_out = sd.CoreAudioSettings(channel_map=outChannels)

                sd.default.extra_settings = (ca_in, ca_out)
                sd.default.channels = (len(inChannels), len(outChannels))
            else:
                sd.default.extra_settings = ca_in
                sd.default.channels = len(inChannels)
        else:
            raise NotImplementedError
                
    def _callback(self, indata: np.ndarray, outdata: np.ndarray, frames: int, time, status) -> None:
        if status:
            print(status, flush=True)

        outdata.fill(0)
        self.callback(indata, outdata, frames, time)

    def start_stream(self, channels:tuple, finished_callback=None) -> None:  
        self.initSounddevice(channels)   
        return sd.Stream(callback=self._callback, finished_callback=finished_callback)
    
    def stop_stream(self) -> None:
        raise sd.CallbackStop

    


    

       