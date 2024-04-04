#!/usr/bin/env python3
"""Records all inputs for given duration and saves amm.recording-file for later computations."""
import time
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

from asmu import Setup, Interface, Input, Output, Recording, Sine

DURATION = 1 # s
SETUP = "./setups/test_transient.asm_setup"

setup = Setup(SETUP)
interface = Interface(setup.interface)
inputs = []
for inputSetup in setup.inputs:
    inputs.append(Input(inputSetup))
output = Output(setup.outputs[0])

sine = Sine(interface.rate, interface.chunk, 1000)

with Recording("./test_transient.asm_rec", "w", setup.name, len(inputs), interface.rate, interface.chunk) as inRecording:
    # Record WhiteNoise response for all inputs
    def callback(indata, outdata, frames, time):
        # route gen to all outputs
        gen_data = sine.get_queue()
        if gen_data is not None:
            outdata[:, 0] = gen_data

        # record input
        inRecording.put_queue(indata)
    interface.callback = callback

    with interface.start_stream((setup.inputChannels, setup.outputChannels)) as stream:
        start = time.time()
        while stream.active:
            sine.refill_queue()
            inRecording.process_queue()
            if time.time()-start >= DURATION: stream.stop()

    fig, ax = plt.subplots(1, figsize=(10,9))
    fig.suptitle(f"find transients", fontsize=16)
    indata = inRecording.data

    print(indata)
    cSPL = [200, 100, 502]
    for im, inpu in enumerate(inputs):
        ax.plot(indata[10000:11000, im]*cSPL[im], label=inpu.name)

    ax.grid()
    ax.legend()
    plt.show()