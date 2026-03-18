import skrf
import numpy as np
import math
import cmath
import scipy
import re
from .utils import window_has_argument
from .sparam_helpers import ensure_equidistant_freq_from_dc, irndft



class TDR:


    def __init__(self):
        self.dc_extrapolation: str|None = 'IEEE370'
        self.window: str = 'boxcar'
        self.window_args: tuple[float] = tuple()
        self.padded_length: int = 0
        self.shift_s: float = 0.0
        self.step_response: bool = False
        self.convert_to_impedance: bool = False
    

    def get(self, f: np.ndarray, s: np.ndarray, z0: float = 50) -> tuple[np.ndarray,np.ndarray]:
        if len(f) < 2 or len(f) != len(s):
            raise ValueError('For TDR, at least 2 frequency points are needed')
        f, s, equidist_from_dc = self._extrapolate_to_dc(f, s)
        s = self._apply_window(s)
        f, s, padding_factor = self._add_padding(f, s, need_power_of_2=equidist_from_dc)
        t, w = self._get_impulse_response(f, s, equidist_from_dc)
        t, w = self._shift(t, w)
        t, w = self._process_step_response(t, w, z0, padding_factor)
        return t, w


    def _extrapolate_to_dc(self, f: np.ndarray, s: np.ndarray) -> tuple[np.ndarray,np.ndarray,bool]:
        
        if self.dc_extrapolation is None:
            assert len(f) >= 2
            f_dc, f_step1 = f[0], f[1] - f[0]
            f_steps = np.diff(f)
            equidist_from_dc = (f_dc == 0) and (np.allclose(f_step1, f_steps))
            return f, s, equidist_from_dc
        
        f, s = ensure_equidistant_freq_from_dc(f, s, method=self.dc_extrapolation)
        return f, s, True


    def _add_padding(self, f: np.ndarray, s: np.ndarray, need_power_of_2: bool) -> tuple[np.ndarray,np.ndarray,float]:
        
        def get_next_power_of_2(x: int) -> int:
            next_pow_of_2 = 1
            while next_pow_of_2 < x:
                next_pow_of_2 *= 2
            return next_pow_of_2
        
        n_target = max(len(s), self.padded_length)
        if need_power_of_2:
            n_target = get_next_power_of_2(n_target)
        
        n_missing = n_target - len(s)
        if n_missing < 1:
            return f, s, 1.0
        
        padding_factor = n_target / len(s)  # padding increases the highest spectrum frequency!
        
        f_end, f_step = f[-1], f[-1] - f[-2]
        f_extended = np.concatenate([f, np.linspace(f_end+f_step, f_end+f_step*(1+n_missing), n_missing)])
        s_padded = np.concatenate([s, np.zeros([n_missing], dtype=s.dtype)])
        return f_extended, s_padded, padding_factor


    def _apply_window(self, s: np.ndarray) -> np.ndarray:
        
        if window_has_argument(self.window):
            window_arg = (self.window, *self.window_args)
        else:
            window_arg = (self.window,)
        
        win_2sided = scipy.signal.get_window(window_arg, 2*len(s))
        win = win_2sided[len(s):]
        sp_windowed = s * win
        return sp_windowed


    def _get_impulse_response(self, f: np.ndarray, s: np.ndarray, equidist_from_dc: bool) -> tuple[np.ndarray,np.ndarray]:
        
        if equidist_from_dc:
            use_fft = True
        else:
            f_steps = np.diff(f)
            starts_at_dc = f[0] == 0
            is_equidistant = np.allclose(f_steps, f_steps[0])
            if is_equidistant:
                if starts_at_dc:
                    use_fft = True  # data already starts at DC and is equidistant
                else:
                    f_first, f_step = f[0], f[1] - f[0]
                    n_steps = round(f_first / f_step)
                    f_first_stepped = n_steps * f_step
                    f_error = abs(f_first - f_first_stepped)
                    if f_error < f_step / 1e6:
                        # just add zeros, then we are reasonably close to DC and equidistant
                        f = np.concatenate([np.linspace(0, f_first-f_step, n_steps, dtype=f.dtype), f])
                        s = np.concatenate([np.zeros([n_steps], dtype=s.dtype), s])
                        use_fft = True
                    else:
                        use_fft = False  # cannot use FFT
            else:
                use_fft = False  # cannot use FFT
        
        if use_fft:

            w = np.fft.irfft(s)
            
            f_nyq = max(f)
            f_sa = 2.0 * f_nyq
            sa_period = 1.0 / f_sa
            t_tot = (len(w)-1) * sa_period
            t = np.linspace(0, t_tot, len(w))
            
            return t, w
        
        else:
            
            # must use DFT
            t, w = irndft(f, s)
        
        return t, w


    def _shift(self, t: np.ndarray, w: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
        if self.shift_s == 0:
            return t, w
        
        assert len(t) >= 2
        sa_period = t[1] - t[0]
        n_shift = round(self.shift_s / sa_period)
        w = np.roll(w, n_shift)
        return t, w


    def _process_step_response(self, t: np.ndarray, w: np.ndarray, z0: float, padding_factor: float) -> tuple[np.ndarray,np.ndarray]:
        
        if self.step_response:
            w = np.cumsum(w)
        
        if self.convert_to_impedance:

            def get_one_plus_epsilon():
                epsilon = 1
                while True:
                    if 1 + (epsilon / 2) == 1:
                        break
                    epsilon /= 2
                greater_than_one = 1 + epsilon
                assert greater_than_one > 1
                return greater_than_one

            # S-parameter to impedance
            w[w==1] = get_one_plus_epsilon()  # avoid division by zero
            w = z0 * (1+w) / (1-w)
        
        return t, w
