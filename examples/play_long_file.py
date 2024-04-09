"""Play an audio file."""
import time
from asmu import ASetup, AFile, Player


setup = ASetup("./setups/FF_UC.asm_setup")
interface = setup.interface
outputs = [outpu for outpu in setup.outputs if outpu.name.startswith("spk")]

with AFile("./recordings/rec_unlimited.wav") as afile:
    gen = Player(afile, interface.chunk)

    def callback(indata, outdata, frames, time):
        # route recording to all outputs, stop_stream when done
        data = gen.get_queue()
        if data is None:
            interface.stop_stream()
        else:
            for idx in range(len(outputs)):
                outdata[:, idx] = data[:, 0]
    interface.callback = callback

    with interface.start_stream(([], outputs)) as stream:
        gen.start_refill_thread(stream)
        while stream.active:
            time.sleep(0.1)
