#!/usr/bin/env python3
"""Record latency and compute from recording for comparison."""
import time

from asmu import Setup, Recording, Input, Output, Interface, SineBurst, get_corrs_sampleshifts

DURATION = 2 # s
RECORD = True # create a fresh recording

setup = Setup("./setups/latency_from_rec.asm_setup")
interface = Interface(setup.interface)
inputs = []
for inputSetup in setup.inputs:
    inputs.append(Input(inputSetup))
outputs = []
for outputSetup in setup.outputs:
    outputs.append(Output(outputSetup))

sineburst = SineBurst(interface.rate, interface.chunk, f=12000, n=9)

if RECORD:
    with Recording("./recordings/latency_from_rec.in.asm_recording", "w", setup.name, len(inputs), interface.rate, interface.chunk) as inRecording,\
        Recording("./recordings/latency_from_rec.out.asm_recording", "w", setup.name, len(outputs), interface.rate, interface.chunk) as outRecording:
        def callback(indata, outdata, frames, time):
            # calculate interface latency on inRecording
            if inRecording.latency is None:
                inRecording.set_latency(time)

            # route gen to output
            gen_data = sineburst.get_queue()
            if gen_data is not None:
                outdata[:, 0] = gen_data

            # record input and output
            inRecording.put_queue(indata)
            outRecording.put_queue(outdata)
        interface.callback = callback

        with interface.start_stream((setup.inputChannels, setup.outputChannels)) as stream:
            start = time.time()
            while stream.active:
                sineburst.refill_queue()
                inRecording.process_queue()
                outRecording.process_queue()
                if time.time()-start >= DURATION: stream.stop()

        inRecording.save_file()
        outRecording.save_file()
    print(f"Recorded latency is {inRecording.latency} samples")

with Recording("./recordings/latency_from_rec.in.asm_recording", "r", setup.name, len(inputs), interface.rate, interface.chunk) as inRecording,\
    Recording("./recordings/latency_from_rec.out.asm_recording", "r", setup.name, len(outputs), interface.rate, interface.chunk) as outRecording:
    corrs, sampleshifts = get_corrs_sampleshifts(inRecording.data, outRecording.data[:, 0], sineburst.burstlen)
    latency = sampleshifts[0]
    print(f"Calculated latency is {latency} samples")




