"""Create a recording with arbitrary duration."""
from asmu import Setup, Recording, Input, Output, Interface, Sine, WhiteNoise, SineBurst

setup = Setup("./setups/FF_UC.asm_setup")
interface = Interface(setup.interface)
inputs = []
for in_setup in setup.inputs:
    if in_setup["name"] == "mic":
        inputs.append(Input(in_setup))
outputs = []
for out_setup in setup.outputs:
    if out_setup["name"].startswith("spk"):
        outputs.append(Output(out_setup))

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


    with interface.start_stream((inputs, outputs)) as stream:
        gen.start_refill_thread(stream)
        inRecording.start_process_thread(stream)
        outRecording.start_process_thread(stream)
        input("Press ENTER to stop recording!")
        stream.stop()
        
    inRecording.save_file()
    outRecording.save_file()
print(f"Recording {inRecording.name} finished: {inRecording.path}")
print(f"Recording {outRecording.name} finished: {outRecording.path}")
