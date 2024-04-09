"""Create a recording with arbitrary duration."""
from asmu import ASetup, AFile, Sine, WhiteNoise, SineBurst, Recorder


setup = ASetup("./setups/FF_UC.asm_setup")
interface = setup.interface
inputs = [inpu for inpu in setup.inputs if inpu.name == "mic"]
outputs = [outpu for outpu in setup.outputs if outpu.name.startswith("spk")]

with AFile("./recordings/rec_unlimited.wav", mode="w", samplerate=interface.rate, channels=1) as afile:
    gen = Sine(interface.rate, interface.chunk, f=50)
    #gen = WhiteNoise(interface.chunk)
    #gen = SineBurst(interface.rate, interface.chunk, f=50, n=20)
    alz = Recorder(afile)

    def callback(indata, outdata, frames, time):
        # calculate interface latency on inRecording
        if afile.latency is None:
            afile.cal_latency(time)
        # route gen to all outputs
        data = gen.get_queue()
        if data is not None:
            for idx in range(len(outputs)):
                outdata[:, idx] = data
        # record input and output
        alz.put_queue(indata)
        # layer input over all outputs for direct listening feedback
        for idx in range(len(outputs)):
            outdata[:, idx] += indata[:, 0]
        outdata /= 2
    interface.callback = callback

    with interface.start_stream((inputs, outputs)) as stream:
        gen.start_refill_thread(stream)
        alz.start_process_thread(stream)
        input("Press ENTER to stop recording!")
        stream.stop()
        
    afile.save_file()
    print(f"Recording {afile.title} started at {afile.date} finished!")
