from .touchstone import Touchstone
from .si import Si

import numpy as np
import math, cmath


class StabilityCircle:

    def __init__(self, touchstone: Touchstone, frequency_hz: float, at_output: bool = False):

        n_ports = touchstone.n_ports
        if n_ports != 2:
            raise ValueError(f'Stability circles are only defined for 2-port network, but the given network has {n_ports} port(s)')
        
        f_min, f_max = min(touchstone.network.f), max(touchstone.network.f)
        if (frequency_hz < f_min) or (frequency_hz > f_max):
            raise ValueError(f'The requested frequency is outside of the frequency range of the network ({Si(f_min,"Hz")} to {Si(f_max,"Hz")})')
        
        nw = touchstone.network.interpolate([frequency_hz])
        s11 = nw.s[0,0,0]
        s21 = nw.s[0,1,0]
        s22 = nw.s[0,1,1]
        s12 = nw.s[0,0,1]
        
        if at_output:
            s11,s22 = s22,s11 # the calculation at the output is the same, but with the RL terms switched...

        # see <https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability>
        delta = s11*s22 - s12*s21
        denom = pow(abs(s22),2) - pow(abs(delta),2)
        self.center = ((s22 - delta*s11.conjugate()).conjugate()) / denom
        self.radius = abs((s12*s21) / denom)
