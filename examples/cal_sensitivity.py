raise NotImplementedError
"""Live calibrate cSPL for each michrophone and SPL-Calibrator."""
import time
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

from asmu import Setup, Interface, Recording, Input, calSPL

SETUP = "./setups/cal_cSPL.asm_setup"
SPL = 114
INPUT = "diy_mm"
DURATION = 2 # s

setup = Setup(SETUP)
interface = Interface(setup.interface)
inpu = Input(setup.inputs[setup.inputNames.index(INPUT)])

with Recording("./recordings/cal_cSPL.asm_rec", "w", setup.name, 1, interface.rate, interface.chunk) as inRecording:
    def callback(indata, outdata, frames, time):
        # record input
        inRecording.put_queue(indata)
    interface.callback = callback

    with interface.start_stream((setup.inputChannels, 0)) as stream:
        start = time.time()
        while stream.active:
            inRecording.process_queue()
            if time.time()-start >= DURATION: stream.stop()

    fig, axs = plt.subplots(3, figsize=(10,9))
    fig.suptitle(f"find transients", fontsize=16)
    indata = inRecording.data[:, 0]

    # fft
    _w = np.hanning(indata.size)
    _w /= np.mean(_w)
    fft_indata = 2*np.fft.rfft(indata*_w, axis=0, norm="forward")
    freqs = np.fft.rfftfreq(indata.size)*interface.rate

    # comute sensitivity
    UFL = np.max(np.abs(fft_indata))
    #UFL = (np.max(indata)- np.min(indata))/2
    UFL_dB = 20*np.log10(UFL)
    dBu = UFL_dB + 13 # according to RME Fireface UFX datasheet
    Urms = 0.7746 * 10**(dBu/20)

    Parms = 20e-6*10**(SPL/20)

    S = Urms/Parms

    print(f"Sensitivity S (V_rms/Pa_rms) = {S}, {20*np.log10(S)}")
    print(f"\tUFL = {UFL}, UFL = {UFL_dB:.2f}dB")
    print(f"\tUrms = {Urms}Vrms")

    # PLOT
    axs[0].plot(indata[4*interface.chunk:5*interface.chunk], label=inpu.name)

    minffti = 1950
    maxffti = 2050

    axs[1].plot(freqs[minffti:maxffti], np.abs(fft_indata[minffti:maxffti]))
    axs[2].plot(freqs[minffti:maxffti], np.unwrap(np.angle(fft_indata[minffti:maxffti])))

    for ax in axs:
        ax.grid()

    plt.show()

    
    #print(f"\tMeasuring {inpu.name}, found cSPL = {cSPL:.4f}Pa/Unit @ kSPL = {kSPL}")
    #inpu.cSPL = cSPL
    #inpu.kSPL = kSPL


