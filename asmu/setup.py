import json
import numpy as np
import os

class Setup():
    def __init__(self, setupPath: str) -> None:
        """Class to handle setups.

        Args:
            setupPath (str): Path to .asm_setup file
        """
        self._path, file = os.path.split(setupPath)
        self._name = file.replace(".asm_setup", "") # extract name without file ending
        self.load_file(setupPath)

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def inputs(self):
        try:
            value = self._setup["inputs"]
            return value
        except KeyError:
            return []

    @property
    def outputs(self):
        try:
            value = self._setup["outputs"]
            return value
        except KeyError:
            return []

    @property
    def interface(self):
        return self._setup["interface"]

    def load_file(self, setupPath):
        with open(setupPath, "r") as file:
            self._setup = json.load(file)
        
        # load numpy arrays from external files
        for io in self.inputs+self.outputs:
            try:
                path = f"{self.path}/{self.name}/cFR_{io["name"]}.npy"
                io["cFR"] = np.load(path)
            except FileNotFoundError:
                pass

    def save_file(self, setupPath=None):
        if setupPath is not None:
            self.__init__(setupPath)
        setupPath = f"{self.path}/{self.name}.asm_setup"

        # save numpy arrays to external files
        for io in self.inputs+self.outputs:
            try:
                if isinstance(io["cFR"], np.ndarray):
                    path = f"{self.path}/{self.name}/cFR_{io["name"]}.npy"
                    np.save(path, io["cFR"])
                    io.pop("cFR")
            except KeyError:
                pass

        # save .asm_setup file
        with open(setupPath, 'w') as file:
            file.write(json.dumps(self._setup, sort_keys=True, indent=4, separators=(',', ': ')))

        

    

    