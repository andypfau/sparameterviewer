from .touchstone import Touchstone

import numpy as np
import math
from scipy.integrate import trapz



def crop_xrange(x, y, xmin=-1e99, xmax=+1e99):
    cropped = [(xx,yy) for xx,yy in zip(x,y) if xmin<=xx<=xmax]
    x_cropped = [xx for (xx,_) in cropped]
    y_cropped = [yy for (_,yy) in cropped]
    return np.array(x_cropped), np.array(y_cropped)


def integrate(f, s):
    integral = trapz(np.log(1/np.abs(s)), f*math.tau)
    return integral


def get_optimum_rl(integral, f0, f1):
    omega0, omega1 = math.tau*f0, math.tau*f1
    gamma = 1 / math.exp(integral / (omega1-omega0))
    db = 20*math.log10(gamma)
    return db


class BodeFano:

    def __init__(self, freuqencies_hz: "np.ndarray", sparam_rl: "np.ndarray",
            f_integration_start_hz: float, f_integration_stop_hz: float,
            f_target_start_hz: float, f_target_stop_hz: float):

        self.nw_f_intrange, self.nw_s_intrange = crop_xrange(freuqencies_hz, sparam_rl, f_integration_start_hz, f_integration_stop_hz)
        self.nw_f_calcrange, self.nw_s_calcrange = crop_xrange(freuqencies_hz, sparam_rl, f_target_start_hz, f_target_stop_hz)
        
        self.f_integration_actual_start_hz = min(self.nw_f_intrange)
        self.f_integration_actual_stop_hz = max(self.nw_f_intrange)
        
        integral_intrange = integrate(self.nw_f_intrange, self.nw_s_intrange)
        integral_calcrange = integrate(self.nw_f_calcrange, self.nw_s_calcrange)
        
        self.db_total = get_optimum_rl(integral_intrange, self.f_integration_actual_start_hz, self.f_integration_actual_stop_hz)
        self.db_current = get_optimum_rl(integral_calcrange, f_target_start_hz, f_target_stop_hz)
        self.db_optimized = get_optimum_rl(integral_intrange, f_target_start_hz, f_target_stop_hz)

    @staticmethod
    def from_touchstone(touchstone: Touchstone, port: int,
            f_integration_start_hz: float, f_integration_stop_hz: float,
            f_target_start_hz: float, f_target_stop_hz: float):
        f = touchstone.frequencies
        s = touchstone.get_sparam(port, port)
        return BodeFano(f, s, f_integration_start_hz, f_integration_stop_hz, f_target_start_hz, f_target_stop_hz)
