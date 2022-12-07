from time import sleep
from typing import Dict

import numpy as np
from epics import PV
from lcls_tools.superconducting.scLinac import (Cavity, CryoDict, Cryomodule, Piezo, SSA, StepperTuner)
from scipy import stats

MAX_STEP = 5
MULT = -51.0471


class SELCavity(Cavity):
    def __init__(self, cavityNum, rackObject, ssaClass=SSA,
                 stepperClass=StepperTuner, piezoClass=Piezo):
        super().__init__(cavityNum, rackObject, ssaClass,
                         stepperClass, piezoClass)
        self._q_waveform_pv: PV = None
        self._i_waveform_pv: PV = None
        self._sel_poff_pv: PV = None
    
    @property
    def sel_poff_pv(self) -> PV:
        if not self._sel_poff_pv:
            self._sel_poff_pv = PV(self.pvPrefix + "SEL_POFF")
        return self._sel_poff_pv
    
    @property
    def sel_phase_offset(self):
        while not self.sel_poff_pv.connect():
            print(f"waiting for {self._sel_poff_pv.pvname} to connect")
            sleep(1)
        return self._sel_poff_pv.get()
    
    @property
    def i_waveform(self):
        if not self._i_waveform_pv:
            self._i_waveform_pv = PV(self.pvPrefix + "CTRL:IWF")
        while not self._i_waveform_pv.connect():
            print(f"waiting for {self._i_waveform_pv.pvname} to connect")
            sleep(1)
        return self._i_waveform_pv.get()
    
    @property
    def q_waveform(self):
        if not self._q_waveform_pv:
            self._q_waveform_pv = PV(self.pvPrefix + "CTRL:QWF")
        while not self._q_waveform_pv.connect():
            print(f"waiting for {self._q_waveform_pv.pvname} to connect")
            sleep(1)
        return self._q_waveform_pv.get()
    
    @property
    def aact(self) -> float:
        while not self.selAmplitudeActPV.connect():
            print(f"Waiting for {self.selAmplitudeActPV.pvname} to connect")
            sleep(1)
        return self.selAmplitudeActPV.get()
    
    def straighten_cheeto(self):
        if self.aact <= 1:
            return
        
        chisum = 0
        startVal = self.sel_phase_offset
        iwf = self.i_waveform
        qwf = self.q_waveform
        large_step = False
        
        [slop, inter] = stats.siegelslopes(iwf, qwf)
        for nn, yy in enumerate(iwf):
            chisum += (yy - (slop * iwf[nn] + inter)) ** 2 / (slop * iwf[nn] + inter)
        
        if not np.isnan(slop):
            step = slop * MULT
            if abs(step) > MAX_STEP:
                step = MAX_STEP * np.sign(step)
                prefix = '\033[91m'
                suffix = '\033[0m'
                large_step = True
            else:
                prefix = ''
                suffix = ''
            if startVal + step < -180:
                step = step + 360
            elif startVal + step > 180:
                step = step - 360
            
            print(f"{prefix}{self}{suffix}")
            print("\t", "old:", f"{startVal:7.2f}")
            print("\t", "new:", f"{startVal + step:7.2f}")
            print("\t", "step:", f"{step:5.2f}")
            print("\t", "chi^2", f"{chisum:.2g}")
            
            self.sel_poff_pv.put(startVal + step)
            return large_step


SEL_CRYOMODULES: Dict[str, Cryomodule] = CryoDict(cavityClass=SELCavity)
