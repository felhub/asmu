import serial
import numpy as np

# type "mode" in shell to find port and baudrate

class SparkCalibrator():
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud

    def fire(self):
        try: 
            with serial.Serial(self.port, self.baud, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=1) as s:
                s.flush()
                s.write("F\r".encode())
        except serial.SerialException:
            Exception(f"SparkCalibrator - could not open port {self.port}")


class BME280():
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud

    def read(self):
        try:
            # open serial port
            with serial.Serial(self.port, self.baud, timeout=1) as s:
                # clear buffer
                s.reset_input_buffer()

                # block until read one line
                line = False
                while not line:
                    line = s.readline()

                # parse recieved line
                str_line = line.decode().rstrip()
                t, h, p = tuple(float(s) for s in str_line.strip("()").split(","))

                return (t, h/100, p)

        except serial.SerialException:
            print(f"BME280 - could not open port {self.port}")


def get_c0_cramer(t, h, p=98700):
    """Owen Cramer. “The variation of the specific heat ratio and the speed of sound in air with
    temperature, pressure, humidity, and CO2 concentration.” In: The Journal of the Acoustical
    Society of America 93.5 (1993), pp. 2510–2516. doi: 10 . 1121 / 1 . 405827. url: https :
    //doi.org/10.1121/1.405827."""

    a = [331.5024, 0.603055, -0.000528, 51.471935, 0.1495874,
        -0.000782, -1.82e-7, 3.73e-8, -2.93e-10, -85.20931,
        -0.228525, 5.91e-5, -2.835149, -2.15e-13, 29.179762, 0.000486]

    # thermodynamic temperature 
    T = t + 273.15 
    # enhancement  factor  for  moist  air 
    f = 1.0062 + 3.14e-8 * p + 5.6e-7 * t**2
    # saturation vapor pressure of water vapor in air
    psv = np.exp(1.2811805e-5 * T**2 - 1.9509874e-2 * T + 34.04926034 - 6.3536311e3 / T)

    xw = h*f*psv/p
    xc = 0.0004147

    return a[0] + a[1]*t + a[2]*t**2 + (a[3] + a[4]*t + a[5]*t**2)*xw \
        + (a[6] + a[7]*t + a[8]*t**2)*p + (a[9] + a[10]*t + a[11]*t**2)*xc \
        + a[12]*xw**2 + a[13]*p**2 + a[14]*xc**2 + a[15]*xw*p*xc


def get_c0_wong(t, h, p=None):
    """George S. K. Wong. “Characteristic impedance of humid air”. In: The Journal of the Acoustical
    Society of America 80.4 (Oct. 1, 1986), pp. 1203–1204. issn: 0001-4966, 1520-8524. doi: 10.1121/
    1.394468. url: https://pubs.aip.org/jasa/article/80/4/1203/770989/Characteristic-
    impedance-of-humid (visited on 10/03/2023)."""
    T0 = 273.15
    ch_cref = 1 + h*(9.66e-4 + 7.22e-5*t + 1.8e-6*t**2 + 7.2e-8*t**3 + 6.5e-11*t**4)
    return 331.29*ch_cref*((T0+t)/T0)**0.5

def get_Z0_wong(t, h, p):
    """George S. K. Wong. “Characteristic impedance of humid air”. en. In: The Journal of the Acoustical
    Society of America 80.4 (Oct. 1986), pp. 1203–1204. issn: 0001-4966, 1520-8524. doi: 10.1121/
    1.394468. url: https://pubs.aip.org/jasa/article/80/4/1203/770989/Characteristic-
    impedance-of-humid."""
    Zh_Zref = 1 - h*(1.3238e-3 + 1.02404e-4*t + 2.0624e-6*t**2 + 1.11e-7*t**3)
    return 428.11*(p)/101325*Zh_Zref*np.sqrt((273.15)/(273.15+t))