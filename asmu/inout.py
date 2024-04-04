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

class Input(IO):
    def __init__(self, inputSetup: dict) -> None: 
        super().__init__(inputSetup)
        self._inputSetup = inputSetup

    @property
    def cSPL(self):
        return float(self._inputSetup["cSPL"])
    @cSPL.setter
    def cSPL(self, value:float):
        self._inputSetup["cSPL"] = value

    @property
    def kSPL(self):
        return int(self._inputSetup["kSPL"])
    @kSPL.setter
    def kSPL(self, value:int):
        self._inputSetup["kSPL"] = value 

    @property
    def cFR(self):
        return self._inputSetup["cFR"]
    @cFR.setter
    def cFR(self, value):
        self._inputSetup["cFR"] = np.array(value)


class Output(IO):
    def __init__(self, outputSetup: dict) -> None: 
        super().__init__(outputSetup)

        