from typing import Dict, Optional

import numpy as np
from lcls_tools.common.controls.pyepics.utils import PV
from lcls_tools.superconducting.scLinac import (
    Cavity,
    CryoDict,
    Cryomodule,
    Piezo,
    SSA,
    StepperTuner,
)
from scipy import stats

MAX_STEP = 5
MULT = -51.0471


class SELCavity(Cavity):
    def __init__(
        self,
        cavityNum,
        rackObject,
        ssaClass=SSA,
        stepperClass=StepperTuner,
        piezoClass=Piezo,
    ):
        super().__init__(cavityNum, rackObject, ssaClass, stepperClass, piezoClass)
        self._q_waveform_pv: Optional[PV] = None
        self._i_waveform_pv: Optional[PV] = None
        self._sel_poff_pv: Optional[PV] = None

    @property
    def sel_poff_pv(self) -> PV:
        if not self._sel_poff_pv:
            self._sel_poff_pv = PV(self.pv_addr("SEL_POFF"))
        return self._sel_poff_pv

    @property
    def sel_phase_offset(self):
        return self.sel_poff_pv.get()

    @property
    def i_waveform(self):
        if not self._i_waveform_pv:
            self._i_waveform_pv = PV(self.pv_addr("CTRL:IWF"))
        return self._i_waveform_pv.get()

    @property
    def q_waveform(self):
        if not self._q_waveform_pv:
            self._q_waveform_pv = PV(self.pv_addr("CTRL:QWF"))
        return self._q_waveform_pv.get()

    def straighten_cheeto(self) -> bool:
        """
        :return: True if wanted to take a step larger than MAX_STEP
        """

        if not self.is_online or self.aact <= 1:
            return False

        startVal = self.sel_phase_offset
        iwf = self.i_waveform
        qwf = self.q_waveform
        large_step = False

        [slop, inter] = stats.siegelslopes(iwf, qwf)

        if not np.isnan(slop):
            chisum = 0
            for nn, yy in enumerate(iwf):
                chisum += (yy - (slop * iwf[nn] + inter)) ** 2 / (
                    slop * iwf[nn] + inter
                )

            step = slop * MULT
            if abs(step) > MAX_STEP:
                step = MAX_STEP * np.sign(step)
                prefix = "\033[91m"
                suffix = "\033[0m"
                large_step = True
                print(f"{prefix}Large step taken{suffix}")
            else:
                prefix = ""
                suffix = ""
            if startVal + step < -180:
                step = step + 360
            elif startVal + step > 180:
                step = step - 360

            print(f"{prefix}{self}{suffix}  step: {step:5.2f} chi^2: {chisum:.2g}")

            self.sel_poff_pv.put(startVal + step)
            return large_step

        else:
            print(f"{self} slope is NaN, skipping")


SEL_CRYOMODULES: Dict[str, Cryomodule] = CryoDict(cavityClass=SELCavity)
