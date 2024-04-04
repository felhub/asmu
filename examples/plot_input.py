#!/usr/bin/env python3
"""Plot the live microphone signal(s) with PySide."""
import keyboard
import matplotlib.pyplot as plt

from asmu import Setup, Input, Output, Interface, Sine, Timeview

setup = Setup("./setups/rec_unlimited.asm_setup")
interface = Interface(setup.interface)
inputs = []
for inputSetup in setup.inputs:
    inputs.append(Input(inputSetup))
outputs = []
for outputSetup in setup.outputs:
    outputs.append(Output(outputSetup))

gen = Sine(interface.rate, interface.chunk, f=50, queuesize=100)

fig = plt.figure()
#timeview = Timeview()
timeview = fig.add_axes(axes_class=Timeview())
fig.show()

def callback(indata, outdata, frames, time):
    # route gen to all outputs
    gen_data = gen.get_queue()
    if gen_data is not None:
        for idx in range(len(outputs)):
            outdata[:, idx] = gen_data

    # route data to timeview
    timeview.put_queue(indata, outdata)
interface.callback = callback


with interface.start_stream((setup.inputChannels, setup.outputChannels)) as stream:
    print("Press q to stop recording!")
    while stream.active:
        gen.refill_queue()
        if keyboard.is_pressed('q'): stream.stop()



