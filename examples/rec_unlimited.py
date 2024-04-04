#!/usr/bin/env python3
"""Create a recording with arbitrary duration."""
import keyboard

from asmu import Setup, Recording, Input, Output, Interface, Sine, WhiteNoise, SineBurst

setup = Setup("./setups/rec_unlimited.asm_setup")
interface = Interface(setup.interface)
inputs = []
for inputSetup in setup.inputs:
    inputs.append(Input(inputSetup))
outputs = []
for outputSetup in setup.outputs:
    outputs.append(Output(outputSetup))

gen = Sine(interface.rate, interface.chunk, f=50)
#gen = WhiteNoise(interface.chunk)
#gen = SineBurst(interface.rate, interface.chunk, f=50, n=20)

with Recording("./recordings/rec_unlimited.in.asm_recording", "w", setup.name, len(inputs), interface.rate, interface.chunk) as inRecording, \
    Recording("./recordings/rec_unlimited.out.asm_recording", "w", setup.name, len(outputs), interface.rate, interface.chunk) as outRecording:

    def callback(indata, outdata, frames, time):
        # calculate interface latency on inRecording
        if inRecording.latency is None:
            inRecording.set_latency(time)

        # route gen to all outputs
        gen_data = gen.get_queue()
        if gen_data is not None:
            for idx in range(len(outputs)):
                outdata[:, idx] = gen_data

        # record input and output
        inRecording.put_queue(indata)
        outRecording.put_queue(outdata)

        # layer input over all outputs for direct listening feedback
        for idx in range(len(outputs)):
            outdata[:, idx] += indata[:, 0]
        outdata /= 2
    interface.callback = callback


    with interface.start_stream(([input.channel for input in inputs], [output.channel for output in outputs])) as stream:
        print("Press q to stop recording!")
        while stream.active:
            gen.refill_queue()
            inRecording.process_queue()
            outRecording.process_queue()
            if keyboard.is_pressed('q'):stream.stop()
        
    inRecording.save_file()
    outRecording.save_file()
print(f"\tRecording {inRecording.name} finished: {inRecording.path}")
print(f"\tRecording {outRecording.name} finished: {outRecording.path}")
