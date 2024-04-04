#!/usr/bin/env python3
"""Play an audio file using a limited amount of memory."""
from asmu import Setup, Recording, Input, Output, Interface

setup = Setup("./setups/rec_unlimited.asm_setup")
interface = Interface(setup.interface)
inputs = []
for inputSetup in setup.inputs:
    inputs.append(Input(inputSetup))
outputs = []
for outputSetup in setup.outputs:
    outputs.append(Output(outputSetup))

with Recording("./recordings/rec_unlimited.in.asm_recording", "r", setup.name, len(inputs), interface.rate, interface.chunk) as inRecording:
    def callback(indata, outdata, frames, time):
        # route recording to all outputs, manage overflow and close_stream when done
        rec_data = inRecording.get_queue()
        if rec_data is None:
            interface.stop_stream()
        else:
            for idx in range(len(outputs)):
                outdata[:, idx] = rec_data
    interface.callback = callback

    with interface.start_stream(([input.channel for input in inputs], [output.channel for output in outputs])) as stream:
        while stream.active:
            inRecording.refill_queue()

