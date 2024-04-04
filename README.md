# Acoustic Signal Measurement Utilities

This package provides tools to conduct (acoustic) signal measurements utilizing a multichannel soundcard. One major advantage is the use of a .asm_setup file, to set the basic input and output parameters.

## Recording
The ASMU package comes with a Recording class, that can be used to record, store and play multichannel audio data.

## Signal generation
Derived from the Generator class, there are several classes available for real time signal generation used for various measurement applications.

## Signal analysis
For the time being signal analysis is done manually via Numpy arrays. For future versions there will be several analysis classes and functions available, automatically incorporation calibration data. 

## Real-time processing
The package structure allows all tools to operate in real time, making additional analysis possible.

## Viewing
Viewing is not fully implemented yet.
