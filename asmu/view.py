raise NotImplementedError
from PySide6 import QtGui
import pyqtgraph as pg
import numpy as np
import queue
import threading

pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')

class TimeView(pg.PlotWidget):
    def __init__(self, ioNames, ioColors, rate, queuesize:int=10, parent=None):
        super(TimeView, self).__init__(parent)
        # TODO give list of input classes instead?
        self.ioNames = ioNames
        self.ioQColors = [QtGui.QColor(ioColor) for ioColor in ioColors]

        self._rate = rate
        self.initPlots()

        self._q = queue.Queue(queuesize)

    def put_queue(self, data):
        self._q.put(data.copy())
    
    def process_queue(self):
        data = self._q.get(block=True, timeout=0.2)

        # plot buffer
        for idx, plot in enumerate(self._plots):
            plot.setData(data[:,idx])

    def start_process_thread(self, stream):
        def runner(self, stream):
            while stream.active:
                try:
                    self.process_queue()
                except queue.Empty:
                    pass
        threading.Thread(target=runner, args=(self, stream, )).start()


    def _get_fft(self) -> np.ndarray:
        return np.fft.rfft(self._q.get()*self._w, axis=0, norm="forward")*2/np.mean(self._w)

    def initPlots(self):
        # disable user interaction
        #self.setMouseEnabled(x=False, y=True)
        self.hideButtons()
        self.setMenuEnabled(False)

        # enable downsampling
        self.setDownsampling(auto=True, mode="subsample")

        # set ranges
        #self.setRange(yRange = (-10*self.pressureGrid, 10*self.pressureGrid), xRange = (-10*self.timeGrid*self.interfaceRate, 0), disableAutoRange=True)

        # set xTicks (with zero on the right)
        xAxis = self.getAxis("bottom")
        #xTicks = range(-10, 1, 1)

        #xAxis.setTicks([[(v*self.timeGrid*self.interfaceRate, f"{v*self.timeGrid:.2f}") for v in xTicks]])

        # set yTicks (with zero in the center)
        yAxis = self.getAxis("left")
        #yTicks = range(-20, 21, 1)
        #yAxis.setTicks([[(v*self.pressureGrid, f"{v*self.pressureGrid:.2f}") for v in yTicks ]])

        # set lables
        xAxis.setLabel("samples")
        yAxis.setLabel("amplitude")

        # add grid
        self.showGrid(x=True, y=True, alpha=0.2)

        # add legend
        self.addLegend()
        
        # create plots
        self._plots = []
        for name, color in zip(self.ioNames, self.ioQColors):
            plot = self.plot(pen=color, name=name)
            self._plots.append(plot)

class Corrview(pg.PlotWidget):
    def __init__(self, corrviewSetup, inputNames, inputQColors, outputName, interfaceRate, parent=None):
        super(Corrview, self).__init__(parent)
        self.corrviewSetup = corrviewSetup

        self.inputNames = inputNames
        self.inputQColors = inputQColors

        self.outputName = outputName

        self.interfaceRate = interfaceRate

        self.microphonePlots = []
        self.speakerPlots = []
        self.initPlots()

    @property
    def timeGrid(self):
        return float(self.corrviewSetup["timeGrid"])
    
    def updateView(self, corrs):
        for idx, plot in enumerate(self.inputPlots):
            plot.setData(corrs[idx])

    def initPlots(self):
        # disable user interaction
        #self.setMouseEnabled(x=False, y=True)
        #self.hideButtons()
        #self.setMenuEnabled(False)

        # enable downsampling
        self.setDownsampling(auto=True, mode="peak")

        xAxis = self.getAxis("bottom")
        yAxis = self.getAxis("left")

        # set lables
        xAxis.setLabel("delaytime (s)")
        yAxis.setLabel("match (%)")

        # add grid
        self.showGrid(x=True, y=True, alpha=0.2)

        # add legend
        self.addLegend()
        
        # create plots
        self.inputPlots = []
        for name, color in zip(self.inputNames, self.inputQColors):
            plot = self.plot(pen=color, name=f"{self.outputName}*{name}")
            self.inputPlots.append(plot)
        

    