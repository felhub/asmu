"""This script is used to analyze frequency response, noise and THD of an amplifier circuit."""
import time
import numpy as np
from asmu import ASetup, AFile, Recorder, Sine, Chirp


mode="r"
MEASURE = True; mode = "w+"
DURATION = 10

setup = ASetup("./setups/FF_UC.asm_setup")
interface = setup.interface
iref = setup.inputs[0]
icirc = setup.inputs[1]
oref = setup.outputs[0]

# frequency response
with AFile("./recordings/circuit_eval_fr.wav", mode, samplerate=interface.rate, channels=2) as afile:
    if MEASURE:
        gen = Chirp(interface.rate, interface.chunk, 8, 50000, DURATION, queuesize=100)
        alz = Recorder(afile)

        def callback(indata, outdata, frames, time):
            if afile.latency is None:
                afile.cal_latency(time)
            outdata[:, 0] = gen.get_queue()
            alz.put_queue(indata)
        interface.callback = callback

        with interface.start_stream(([iref, icirc], [oref])) as stream:
            gen.start_refill_thread(stream)
            alz.start_process_thread(stream)
            time.sleep(DURATION)
            stream.stop()

        afile.save_file()

    indata = afile.data[afile.latency:, :]
    f = np.fft.rfftfreq(np.ma.size(indata, axis=0))*interface.rate
    ifu = np.argmin(np.abs(f-40000))
    ifl = np.argmin(np.abs(f-10))
    f_fr = f[ifl:ifu]
    uk_in = (np.fft.rfft(indata, axis=0, norm="forward")*2)[ifl:ifu, :]
    fr = uk_in[:, 1]/uk_in[:, 0]

# noise 
with AFile("./recordings/circuit_eval_noise.wav", mode, samplerate=interface.rate, channels=1) as afile:
    if MEASURE:
        alz = Recorder(afile)

        def callback(indata, outdata, frames, time):
            alz.put_queue(indata)
        interface.callback = callback

        with interface.start_stream(([icirc], [])) as stream:
            alz.start_process_thread(stream)
            time.sleep(DURATION)
            stream.stop()

        afile.save_file()

    indata = afile.data
    f = np.fft.rfftfreq(np.ma.size(indata, axis=0))*interface.rate
    ifu = np.argmin(np.abs(f-40000))
    ifl = np.argmin(np.abs(f-10))
    f_noise = f[ifl:ifu]
    uk_in = (np.fft.rfft(indata, axis=0, norm="forward")*2)[ifl:ifu, :]
    noise = np.abs(uk_in[:, 0])*icirc.cV*1e6/np.sqrt(2) # noise in mV(RMS)

# THD
with AFile("./recordings/circuit_eval_thd.wav", mode, samplerate=interface.rate, channels=2) as afile:
    if MEASURE:
        gen = Sine(interface.rate, interface.chunk, 1000, queuesize=100)
        alz = Recorder(afile)

        def callback(indata, outdata, frames, time):
            if afile.latency is None:
                afile.cal_latency(time)
            outdata[:, 0] = gen.get_queue()
            alz.put_queue(indata)
        interface.callback = callback

        with interface.start_stream(([iref, icirc], [oref])) as stream:
            gen.start_refill_thread(stream)
            alz.start_process_thread(stream)
            time.sleep(DURATION)
            stream.stop()
    
        afile.save_file()

    indata = afile.data[afile.latency:, :]
    f = np.fft.rfftfreq(np.ma.size(indata, axis=0))*interface.rate
    ifu = np.argmin(np.abs(f-40000))
    ifl = np.argmin(np.abs(f-10))
    f_THD = f[ifl:ifu]
    uk_in = (np.fft.rfft(indata, axis=0, norm="forward")*2)[ifl:ifu, :]
    THD = np.abs(uk_in[:, 1])


# EVALUATION AND PLOTTING
import matplotlib.pyplot as plt
fig, axs = plt.subplots(4, figsize=(12,8))

# fr eval
axs[0].loglog(f_fr, np.abs(fr), color=icirc.color, label=icirc.name)
axs[1].semilogx(f_fr, np.rad2deg(np.angle(fr)), color=icirc.color, label=icirc.name)
print("FR")
if1k = np.argmin(np.abs(f_fr-1000))
20*np.log10(np.min(np.abs(fr)/np.abs(fr[if1k])))
dev = fr/fr[if1k]
print(f"\t10Hz to 40kHz, {20*np.log10(np.min(np.abs(dev))):.2f}dB, +{20*np.log10(np.max(np.abs(dev))):.2f}dB (re. 1kHz)")
print(f"\t10Hz to 40kHz, {np.min(np.rad2deg(np.angle(dev))):.1f}°, {np.max(np.rad2deg(np.angle(dev))):.1f}° (re. 1kHz)")
print(f"\tAttenuation: {20*np.log10(np.min(np.abs(fr))):.2f}dB (max.)")


# noise eval
axs[2].loglog(f_noise, noise, color=icirc.color, label=icirc.name)
print("NOISE")
print(f"\t{np.mean(noise):.4f}uV(RMS) Lin. (20Hz - 40kHz)")
print(f"\t{np.max(noise):.4f}uV(RMS) Lin. (20Hz - 40kHz) (max.)")

# THD eval
axs[3].loglog(f_THD, THD, color=icirc.color, label=icirc.name)
print("THD")
harmonics = [2, 3, 4, 5, 6]
base_idx = np.argmin(np.abs(f_THD-1000))
v_base = THD[base_idx]
v_n = []
for n in harmonics:
    n_idx = np.argmin(np.abs(f_THD-1000*n))
    v_n.append(THD[n_idx])
THDn6 = np.sqrt(np.sum([v**2 for v in v_n]))/v_base
print(f"\t{20*np.log10(THDn6):.0f}dB at 1V(RMS), 1kHz")

# general plot settings
axs[0].set(xlabel="Frequency (Hz)", ylabel="Absolute response")
axs[1].set(xlabel="Frequency (Hz)", ylabel="Phase response (deg)")
axs[2].set(xlabel="Frequency (Hz)", ylabel="Noise (uV(RMS))")
axs[3].set(xlabel="Frequency (Hz)", ylabel="Absolute response")
terzbands = [10, 12.5, 16, 20, 25, 31.5, 40, 50, 63, 80,
             100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
             1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000,
             10000, 12500, 16000, 20000, 25000, 31500, 40000]
for ax in axs:
    ax.set_xlim(terzbands[0], terzbands[-1])
    ax.set_xticks(terzbands)
    ax.set_xticklabels([f"{tb:.0f}" for tb in terzbands], rotation=45)
    ax.legend()
    ax.grid()
    ax.minorticks_off()

dBs = [10**(dB/20) for dB in [-3, -1, -0.5, 0, 0.5, 1, 3]]
axs[0].set_ylim(dBs[0], dBs[-1])
axs[0].set_yticks(dBs)
axs[0].yaxis.set_major_formatter(lambda x, pos: f"{20*np.log10(x):.1f}dB")

degs = [-20, -10, 0, 10, 20]
axs[1].set_ylim(degs[0], degs[-1])
axs[1].set_yticks(degs)
axs[1].set_yticklabels([f"{deg:.0f}°" for deg in degs])

fig.tight_layout()
plt.show()
