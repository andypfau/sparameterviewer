from multiprocessing.sharedctypes import Value
from .si import Si

import numpy as np
import math, cmath, skrf


class StabilityCircle:

    def __init__(self, network: "skrf.Network", frequency_hz: float, port: int = 2):

        n_ports = network.number_of_ports
        if n_ports != 2:
            raise ValueError(f'Stability circles are only defined for 2-port network, but the given network has {n_ports} port(s)')
        
        f_min, f_max = min(network.f), max(network.f)
        if (frequency_hz < f_min) or (frequency_hz > f_max):
            raise ValueError(f'The requested frequency is outside of the frequency range of the network ({Si(f_min,"Hz")} to {Si(f_max,"Hz")})')
        
        nw = network.interpolate(skrf.Frequency(frequency_hz,frequency_hz,1,unit='hz'))
        s11 = nw.s[0,0,0]
        s21 = nw.s[0,1,0]
        s12 = nw.s[0,0,1]
        s22 = nw.s[0,1,1]

        if port==1:
            s11, s21, s12, s22 = s22, s12, s21, s11 # just flip the network, then do the same calculation
        elif port!=2:
            raise ValueError('Stability circle argument <port> must be 1 or 2')
        
        # calculate stability circle for output
        # see <https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability>
        delta = s11*s22 - s12*s21
        denom = pow(abs(s22),2) - pow(abs(delta),2)
        self.center = (s22 - s11.conjugate()*delta).conjugate() / denom
        self.radius = abs((s12*s21) / denom)
        self.stable_inside = True if abs(s22)>1 else False
    

    def get_plot_data(self, n_points: int = 101) -> "np.ndarray":
        result = []
        def add(angle):
            re = self.center.real + self.radius*math.cos(angle)
            im = self.center.imag + self.radius*math.sin(angle)
            result.append(re + 1j*im)
        for i in range(n_points-1):
            add(math.tau*i/(n_points-1))
        add(0) # close the circle
        return np.array(result)
