import json
import numpy as np
import os
from asmu import Input, Output, Interface

class ASetup():
    def __init__(self, setupPath: str) -> None:
        """Class to handle setups.

        Args:
            setupPath (str): Path to .asm_setup file
        """
        self._path, file = os.path.split(setupPath)
        self._name = file.replace(".asm_setup", "") # extract name without file ending
        self.load_file(setupPath)

        # create asmu objects
        self._interface = Interface(self._setup["interface"])

        self._inputs = []
        for in_setup in self._setup["inputs"]:
            self._inputs.append(Input(in_setup))

        self._outputs = []
        for out_setup in self._setup["outputs"]:
            self._outputs.append(Output(out_setup))

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def interface(self):
        return self._interface

    def load_file(self, setupPath):
        with open(setupPath, "r") as file:
            self._setup = json.load(file)
        
        # load numpy arrays from external files
        for io in self._setup["inputs"]+self._setup["outputs"]:
            for k in io.keys():
                try:
                    path = f"{self.path}/{self.name}/{k}_{io["name"]}.npy"
                    io[k] = np.load(path)
                except FileNotFoundError:
                    pass

    def save_file(self, setupPath=None):
        # update path
        if setupPath is not None:
            self.__init__(setupPath)
        setupPath = f"{self.path}/{self.name}.asm_setup"

        # save numpy arrays to external files
        for io in self._setup["inputs"]+self._setup["outputs"]:
            for (k, v) in io.items():
                try:
                    if isinstance(v, np.ndarray):
                        path = f"{self.path}/{self.name}/{k}_{io["name"]}.npy"
                        np.save(path, v)
                        io.pop(k)
                except KeyError:
                    pass

        # save .asm_setup file
        with open(setupPath, 'w') as file:
            file.write(json.dumps(self._setup, sort_keys=True, indent=4, separators=(',', ': ')))

        

    

    