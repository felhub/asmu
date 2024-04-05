"""Play an audio file using a limited amount of memory."""
import time
from asmu import Setup, Recording, Input, Output, Interface

setup = Setup("./setups/FF_UC.asm_setup")
interface = Interface(setup.interface)
outputs = []
for out_setup in setup.outputs:
    if out_setup["name"].startswith("spk"):
        outputs.append(Output(out_setup))


with Recording("./recordings/rec_unlimited.in.asm_recording", "r", setup.name, 1, interface.rate, interface.chunk) as inRecording:
    def callback(indata, outdata, frames, time):
        # route recording to all outputs, manage overflow and close_stream when done
        rec_data = inRecording.get_queue()
        if rec_data is None:
            interface.stop_stream()
        else:
            for idx in range(len(outputs)):
                outdata[:, idx] = rec_data[:, 0]
    interface.callback = callback

    with interface.start_stream(([], outputs)) as stream:
        inRecording.start_refill_thread(stream)
        while stream.active:
            time.sleep(0.1)

