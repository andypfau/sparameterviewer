from .si import SiValue

import numpy as np
import math, skrf
from abc import ABC, abstractmethod



class SParameterCircle(ABC):

    @abstractmethod
    def _get_center_and_radius(self) -> tuple[complex,float]:
        pass


    def get_plot_data(self, n_points: int = 101) -> "np.ndarray":
        c, r = self._get_center_and_radius()
        
        result = []
        def add(angle):
            re = c.real + r*math.cos(angle)
            im = c.imag + r*math.sin(angle)
            result.append(re + 1j*im)
        
        for i in range(n_points-1):
            add(math.tau*i/(n_points-1))
        add(0) # close the circle

        return np.array(result)
    


class StabilityCircle(SParameterCircle):

    def __init__(self, network: "skrf.Network", frequency_hz: float, port: int = 2):

        n_ports = network.number_of_ports
        if n_ports != 2:
            raise ValueError(f'Stability circles are only defined for 2-port network, but the given network has {n_ports} port(s)')
        
        f_min, f_max = min(network.f), max(network.f)
        if (frequency_hz < f_min) or (frequency_hz > f_max):
            raise ValueError(f'The requested frequency is outside of the frequency range of the network ({SiValue(f_min,"Hz")} to {SiValue(f_max,"Hz")})')
        
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
        denom = abs(s22)**2 - abs(delta)**2
        self.center = (s22 - s11.conjugate()*delta).conjugate() / denom
        self.radius = abs((s12*s21) / denom)
        
        # determine if stable inside or outside
        # see <https://www.analog.com/en/resources/technical-articles/lownoise-amplifier-stability-concept-to-practical-considerations-part-2.html>
        # TODO: there are other definitions, which one is right? See Pozar, 11.2, Stability, and <https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_V%3A_Amplifiers_and_Oscillators_(Steer)/02%3A_Linear_Amplifiers/2.06%3A_Amplifier_Stability>
        surrounds_origin = abs(self.center) <= self.radius
        if surrounds_origin:
            self.stable_inside = bool(abs(s11)<1 and abs(delta)>abs(s22))
        else:
            self.stable_inside = bool(abs(s11)>1 and abs(delta)>abs(s22))
        
    
    def _get_center_and_radius(self) -> tuple[complex,float]:
        return self.center, self.radius


class NoiseCircle(SParameterCircle):

    def __init__(self, network: "skrf.Network", frequency_hz: float, nf_db: float):

        n_ports = network.number_of_ports
        if n_ports != 2:
            raise ValueError(f'Noise circles are only defined for 2-port network, but the network {network.name} has {n_ports} port(s)')

        f_min, f_max = min(network.f), max(network.f)
        if (frequency_hz < f_min) or (frequency_hz > f_max):
            raise ValueError(f'The requested frequency is outside of the frequency range of the network ({SiValue(f_min,"Hz")} to {SiValue(f_max,"Hz")})')
        
        nw = network.interpolate(skrf.Frequency(frequency_hz,frequency_hz,1,unit='hz'))

        z0, z_opt, f_min, rn = nw.z0[0,0], nw.z_opt[0], nw.nfmin[0], nw.rn[0]
        if z_opt is None or f_min is None or rn is None:
            raise ValueError(f'Network {network.name} does not include noise data, cannot calculate noise circles')
        
        Γ_opt = (z_opt - z0) / (z_opt + z0)
        
        # calculate noise circle; see Pozar, 12.3, Low-Noise Amplifier Design
        n = (10**(nf_db/10) - f_min) / (4 * rn / z0) * abs(1+Γ_opt)**2
        self.center = Γ_opt / (n + 1)
        self.radius = math.sqrt(n * (n + 1 - abs(Γ_opt)**2)) / (n + 1)
        
    
    def _get_center_and_radius(self) -> tuple[complex,float]:
        return self.center, self.radius
