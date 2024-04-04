#!/usr/bin/env python3
"""Records all inputs for given duration and saves amm.recording-file for later computations."""
import time
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

from asmu import Setup, Interface, Input, Output, Recording, SincBurst

def measure_record(setupPath, duration, loop):
    setup = Setup(setupPath)
    interface = Interface(setup.interface)
    inputs = []
    for inputSetup in setup.inputs:
        inputs.append(Input(inputSetup))
    output = Output(setup.outputs[0])

    sinc = SincBurst(interface.rate, interface.chunk, 8000, 3, loop=loop)
    print(sinc.burstlen)

    with Recording("./test_transient.asm_rec", "w", setup.name, len(inputs), interface.rate, interface.chunk) as inRecording:
        # Record WhiteNoise response for all inputs
        def callback(indata, outdata, frames, time):
            # route gen to all outputs
            gen_data = sinc.get_queue()
            if gen_data is not None:
                outdata[:, 0] = gen_data

            # record input
            inRecording.put_queue(indata)
        interface.callback = callback

        with interface.start_stream((setup.inputChannels, setup.outputChannels)) as stream:
            start = time.time()
            while stream.active:
                sinc.refill_queue()
                inRecording.process_queue()
                if time.time()-start >= duration: stream.stop()

        fig, axs = plt.subplots(3, figsize=(10,9))
        fig.suptitle(f"find transients", fontsize=16)
        indata = inRecording.data
        # find first incident transient
        peaks, _ = sp.signal.find_peaks(indata[:, 2]/np.max(indata[:, 2]), prominence=0.8, distance=sinc.burstlen, height=0.5)
        # plot full recording with marked peaks
        axs[0].plot(indata[:, 2])
        axs[0].plot(peaks, indata[peaks, 2], "x")
        for peak in peaks:
            axs[1].plot(indata[peak-200:peak+500, 2], label=f"{inputs[2].name}@{peak}")

        for im, inpu in enumerate(inputs):
            ir = []
            for peak in peaks:
                ir.append(indata[peak-200:peak+500, im])
            avg = np.mean(ir, axis=0)
            axs[2].plot(avg/np.max(avg), label=inpu.name)
        for ax in axs:
            ax.grid()
            ax.legend()
        plt.show()

if __name__ == "__main__":
    DURATION = 10 # s
    LOOP = 1 # s
    SETUP = "./setups/test_transient.asm_setup"

    measure_record(SETUP, DURATION, LOOP)