"""Record latency and compute from recording for comparison."""
import time
from asmu import ASetup, AFile, SineBurst, Recorder, get_corrs_sampleshifts


DURATION = 2 # s
RECORD = True # create a fresh recording

setup = ASetup("./setups/FF_UC.asm_setup")
interface = setup.interface
in_loop = [inpu for inpu in setup.inputs if inpu.name == "loop"][0]
out_loop = [outpu for outpu in setup.outputs if outpu.name == "loop"][0]

if RECORD:
    with AFile("./recordings/latency_from_rec.in.wav", mode="w", samplerate=interface.rate, channels=1) as in_afile,\
        AFile("./recordings/latency_from_rec.out.wav", mode="w", samplerate=interface.rate, channels=1) as out_afile:
        gen = SineBurst(interface.rate, interface.chunk, f=12000, n=9)
        in_alz = Recorder(in_afile)
        out_alz = Recorder(out_afile)

        def callback(indata, outdata, frames, time):
            # calculate interface latency on inRecording
            if in_afile.latency is None:
                in_afile.cal_latency(time)
            # route gen to output
            data = gen.get_queue()
            if data is not None:
                outdata[:, 0] = data
            # record input and output
            in_alz.put_queue(indata)
            out_alz.put_queue(outdata)
        interface.callback = callback

        with interface.start_stream(([in_loop], [out_loop])) as stream:
            gen.start_refill_thread(stream)
            in_alz.start_process_thread(stream)
            out_alz.start_process_thread(stream)
            time.sleep(DURATION)
            stream.stop()

        print(f"Recorded latency is {in_afile.latency} samples")
        in_afile.save_file()
        out_afile.save_file()

with AFile("./recordings/latency_from_rec.in.wav") as in_afile,\
    AFile("./recordings/latency_from_rec.out.wav") as out_afile:
    corrs, sampleshifts = get_corrs_sampleshifts(in_afile.data, out_afile.data[:, 0], gen.burstlen)
    latency = sampleshifts[0]
    print(f"Calculated latency is {latency} samples")
