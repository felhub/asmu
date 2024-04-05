import numpy as np


class IO():
    def __init__(self, IOsetup: dict) -> None:
        self._IOSetup = IOsetup

    def __repr__(self):
        return self.name

    @property
    def name(self):
        return self._IOSetup["name"]

    @property
    def channel(self):
        return int(self._IOSetup["channel"])

    @property
    def color(self):
        return self._IOSetup["color"]
    @color.setter
    def color(self, value):
        self._IOSetup["color"] = str(value)
    
    @property
    def pos(self):
        return np.array(self._IOSetup["pos"])
    @pos.setter
    def pos(self, value):
        self._IOSetup["pos"] = value

    @property
    def reference(self):
        try:
            return bool(self._IOSetup["reference"])
        except KeyError:
            return False
    @reference.setter
    def reference(self, value):
        if value:
            self._IOSetup["reference"] = True
        else:
            try:
                del self._IOSetup["reference"]
            except KeyError:
                pass
    
    # CALIBRATION FACTORS - defined by amplitude -> direct signal conversion!
    @property
    def cPa(self):
        return float(self._IOSetup["cPa"])
    @cPa.setter
    def cPa(self, value:float):
        self._IOSetup["cPa"] = value

    @property
    def kPa(self):
        return int(self._IOSetup["kPa"])
    @kPa.setter
    def kPa(self, value:int):
        self._IOSetup["kPa"] = value

    @property
    def cV(self):
        return float(self._IOSetup["cV"])
    @cV.setter
    def cV(self, value:float):
        self._IOSetup["cV"] = value

    @property
    def kV(self):
        return int(self._IOSetup["kV"])
    @kV.setter
    def kV(self, value:int):
        self._IOSetup["kV"] = value

    @property
    def cFR(self):
        return self._IOSetup["cFR"]
    @cFR.setter
    def cFR(self, value):
        self._IOSetup["cFR"] = np.array(value)


class Input(IO):
    def __init__(self, inputSetup: dict) -> None: 
        super().__init__(inputSetup)


class Output(IO):
    def __init__(self, outputSetup: dict) -> None: 
        super().__init__(outputSetup)