"""Record latency and compute from recording for comparison."""
import time
from asmu import Setup, Recording, Input, Output, Interface, SineBurst, get_corrs_sampleshifts


DURATION = 2 # s
RECORD = True # create a fresh recording

setup = Setup("./setups/FF_UC.asm_setup")
interface = Interface(setup.interface)
loop_in = Input(*[in_setup for in_setup in setup.inputs if in_setup["name"] == "loop_in"])
loop_out = Output(*[out_setup for out_setup in setup.outputs if out_setup["name"] == "loop_out"])

gen = SineBurst(interface.rate, interface.chunk, f=12000, n=9)
if RECORD:
    with Recording("./recordings/latency_from_rec.in.asm_recording", "w", setup.name, 1, interface.rate, interface.chunk) as inRecording,\
        Recording("./recordings/latency_from_rec.out.asm_recording", "w", setup.name, 1, interface.rate, interface.chunk) as outRecording:
        def callback(indata, outdata, frames, time):
            # calculate interface latency on inRecording
            if inRecording.latency is None:
                inRecording.set_latency(time)
            # route gen to output
            gen_data = gen.get_queue()
            if gen_data is not None:
                outdata[:, 0] = gen_data
            # record input and output
            inRecording.put_queue(indata)
            outRecording.put_queue(outdata)
        interface.callback = callback

        with interface.start_stream(([loop_in], [loop_out])) as stream:
            gen.start_refill_thread(stream)
            inRecording.start_process_thread(stream)
            outRecording.start_process_thread(stream)
            time.sleep(DURATION)
            stream.stop()

        inRecording.save_file()
        outRecording.save_file()
    print(f"Recorded latency is {inRecording.latency} samples")

with Recording("./recordings/latency_from_rec.in.asm_recording", "r", setup.name, 1, interface.rate, interface.chunk) as inRecording,\
    Recording("./recordings/latency_from_rec.out.asm_recording", "r", setup.name, 1, interface.rate, interface.chunk) as outRecording:
    corrs, sampleshifts = get_corrs_sampleshifts(inRecording.data, outRecording.data[:, 0], gen.burstlen)
    latency = sampleshifts[0]
    print(f"Calculated latency is {latency} samples")




