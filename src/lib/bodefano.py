import numpy as np
import math
import skrf
import scipy.integrate


class BodeFano:


    def __init__(self, freuqencies_hz: "np.ndarray", sparam_sii_term: "np.ndarray",
            f_integration_start_hz: float, f_integration_stop_hz: float,
            f_target_start_hz: float, f_target_stop_hz: float):
        
        def crop_freq_range(freqs, sparam, f_min=-1e99, f_max=+1e99):
            cropped = [(f,s) for f,s in zip(freqs,sparam) if f_min<=f<=f_max]
            freqs_cropped = [f for (f,_) in cropped]
            sparam_cropped = [s for (_,s) in cropped]
            return np.array(freqs_cropped), np.array(sparam_cropped)

        def bode_fano_integral(freqs, sparam):
            return scipy.integrate.trapezoid(np.log(1/np.abs(sparam)), freqs*math.tau)

        def calc_avg_rl(integral_value, f_min, f_max):
            gamma = 1 / math.exp(integral_value / ((f_max-f_min)*math.tau))
            db = 20*math.log10(gamma)
            return db

        self.nw_f_intrange, self.nw_s_intrange = crop_freq_range(freuqencies_hz, sparam_sii_term, f_integration_start_hz, f_integration_stop_hz)
        self.nw_f_calcrange, self.nw_s_calcrange = crop_freq_range(freuqencies_hz, sparam_sii_term, f_target_start_hz, f_target_stop_hz)
        
        self.f_integration_actual_start_hz = min(self.nw_f_intrange)
        self.f_integration_actual_stop_hz = max(self.nw_f_intrange)
        
        integral_intrange = bode_fano_integral(self.nw_f_intrange, self.nw_s_intrange)
        integral_calcrange = bode_fano_integral(self.nw_f_calcrange, self.nw_s_calcrange)
        
        self.db_available = calc_avg_rl(integral_intrange, self.f_integration_actual_start_hz, self.f_integration_actual_stop_hz)
        self.db_current = calc_avg_rl(integral_calcrange, f_target_start_hz, f_target_stop_hz)
        self.db_achievable = calc_avg_rl(integral_intrange, f_target_start_hz, f_target_stop_hz)


    @staticmethod
    def from_network(network: skrf.Network, port: int,
            f_integration_start_hz: float, f_integration_stop_hz: float,
            f_target_start_hz: float, f_target_stop_hz: float):
        f = network.f
        s = network.s[:,port-1,port-1]
        return BodeFano(f, s, f_integration_start_hz, f_integration_stop_hz, f_target_start_hz, f_target_stop_hz)
