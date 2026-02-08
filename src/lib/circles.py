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
            s11, s21, s12, s22 = s22, s12, s21, s11 # just flip the network, then do the same calculation, to get an input circle
        elif port!=2:
            raise ValueError('Stability circle argument <port> must be 1 or 2')
        
        # calculate stability circle for output, see e.g. <Pozar, Microwave Engineering>, <Sorrentino Bianchi, Microwave and RF Engineering>, <https://www.analog.com/en/resources/technical-articles/lownoise-amplifier-stability-concept-to-practical-considerations-part-2.html>
        delta = s11*s22 - s12*s21
        denom = abs(s22)**2 - abs(delta)**2
        self.center = (s22 - s11.conjugate()*delta).conjugate() / denom
        self.radius = abs((s12*s21) / denom)
        
        # determine if stable inside or outside, see e.g. <Sorrentino Bianchi, Microwave and RF Engineering>, <https://www.analog.com/en/resources/technical-articles/lownoise-amplifier-stability-concept-to-practical-considerations-part-2.html>
        distance_to_origin = abs(self.center - 0)
        surrounds_origin = distance_to_origin <= self.radius
        self.stable_inside = (abs(s11) <= 1) == (surrounds_origin)
        
    
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
        sqrt_arg = n * (n + 1 - abs(Γ_opt)**2)
        if sqrt_arg < 0:
            raise ValueError(f'Cannot calculate noise circle for NF={nf_db} dB at f={SiValue(frequency_hz,"Hz")}: out of range')
        self.radius = math.sqrt(sqrt_arg) / (n + 1)
        
    
    def _get_center_and_radius(self) -> tuple[complex,float]:
        return self.center, self.radius



class BilateralPowerGainCircle(SParameterCircle):

    def __init__(self, network: "skrf.Network", frequency_hz: float, g_lin: float, typ: str):

        assert typ in ['GA', 'GP']
        
        n_ports = network.number_of_ports
        if n_ports != 2:
            raise ValueError(f'Gain circles are only defined for 2-port network, but the network {network.name} has {n_ports} port(s)')

        f_min, f_max = min(network.f), max(network.f)
        if (frequency_hz < f_min) or (frequency_hz > f_max):
            raise ValueError(f'The requested frequency is outside of the frequency range of the network ({SiValue(f_min,"Hz")} to {SiValue(f_max,"Hz")})')
        
        nw = network.interpolate(skrf.Frequency(frequency_hz,frequency_hz,1,unit='hz'))
        s11: complex = nw.s[0,0,0]
        s21: complex = nw.s[0,1,0]
        s12: complex = nw.s[0,0,1]
        s22: complex = nw.s[0,1,1]
        k: float = nw.stability[0]

        if typ == 'GP':
            # operating power gain is the same equation as available power gain, but with S11 and S22 swapped
            s11, s22 = s22, s11
        
        # see <https://cc.ee.ntu.edu.tw/~thc/course_meng/chap10.pdf>
        delta = s11*s22 - s12*s21
        self.center = (g_lin * (s11 - s22.conjugate()*delta).conjugate()) / (1 + g_lin * (abs(s11)**2 - abs(delta)**2))
        self.radius = math.sqrt(1 - 2 * k * abs(s12*s21) * g_lin + (abs(s12*s21)**2) * (g_lin**2)) / (1 + g_lin * (abs(s11)**2 - abs(delta)**2))
        
    
    def _get_center_and_radius(self) -> tuple[complex,float]:
        return self.center, self.radius
