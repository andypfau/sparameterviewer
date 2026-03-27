import math
import numpy as np
import scipy
import logging
from .utils import window_has_argument
from .sparam_helpers import check_freqs_dc_and_equidist, get_missing_freq_dc_and_equidist, extrapolate_to_dc, interpolate_freq, interpolate_equidistant_freq, irndft



class TDR:


    def __init__(self):
        self.dc_extrapolation: str|None = 'IEEE370'  # 'IEEE370', 'polar', None
        self.dc_mag_assumption: str|None = 'auto'  # 'zero', 'unity', 'auto', None; only used for polar method
        self.interpolation: bool = True
        self.window: str = 'boxcar'
        self.window_args: tuple[float] = tuple()
        self.padded_length: int = 0
        self.shift_s: float = 0.0
        self.step_response: bool = False
        self.convert_to_impedance: bool = False
    

    def get(self, f: np.ndarray, s: np.ndarray, z0: float = 50) -> tuple[np.ndarray,np.ndarray]:

        # TODO: check quality metrics? See e.g. Shlepnev, How to Avoid Butchering S-parameters

        if len(f) < 2 or len(f) != len(s):
            raise ValueError('For TDR, at least 2 frequency points are needed')
        f, s, equidistant_from_dc = self._interpolate_extrapolate(f, s)
        s = self._apply_window(s)
        f, s, padding_factor = self._add_padding(f, s, need_power_of_2=equidistant_from_dc)
        t, w = self._get_impulse_response(f, s, equidistant_from_dc)
        t, w = self._shift(t, w)
        t, w = self._process_step_response(t, w, z0, padding_factor)
        return t, w


    def _interpolate_extrapolate(self, f: np.ndarray, s: np.ndarray) -> tuple[np.ndarray,np.ndarray,bool]:

        starts_at_dc, is_equidistant = check_freqs_dc_and_equidist(f)
        if starts_at_dc and is_equidistant:
            # already DC and equidistant
            return f, s, True
        
        if starts_at_dc:
            if self.interpolation:
                # DC OK, interpolating
                f, s = interpolate_equidistant_freq(f, s)
                return f, s, True
            # DC OK, but skipping because interpolation is disabled
            return f, s, False
        
        if self.dc_extrapolation is None:
            if self.interpolation:
                # DC missing, only interpolating
                f, s = interpolate_equidistant_freq(f, s)
                return f, s, False
            else:
                # DC missing, but interpolation is disabled
                return f, s, False
        
        assert self.dc_extrapolation is not None  # was checked above

        can_fix, f_missing = get_missing_freq_dc_and_equidist(f)
        if can_fix:
            # extrapolationg, while interpolation is not needed
            f, s = extrapolate_to_dc(f, s, f_missing, method=self.dc_extrapolation, dc_mag_assumption=self.dc_mag_assumption)
            assert check_freqs_dc_and_equidist(f) == (True,True)  # sanity check
            return f, s, True
        
        if not self.interpolation:
            # interpolation disabled, just adding some points towards DC

            f_first, f_step = f[0], f[1] - f[0]
            n_steps = round(f_first / f_step)
            f_missing = np.linspace(0, f_first-f_step, n_steps, dtype=f.dtype)
            
            f, s = extrapolate_to_dc(f, s, f_missing, method=self.dc_extrapolation, dc_mag_assumption=self.dc_mag_assumption)

            return f,s, False

        # find a frequency grid, such that it can be extrapolated to DC in an equidistant way
        df_mean = (f[-1] - f[0]) / len(f)
        n_steps = round((f[-1] - 0) / df_mean)
        f_new = np.linspace(0, f[-1], n_steps)
        f_extrap = f_new[f_new < f[0]]

        f, s = extrapolate_to_dc(f, s, f_extrapolate=f_extrap, method=self.dc_extrapolation, dc_mag_assumption=self.dc_mag_assumption)
        f, s = interpolate_freq(f, s, f_new)
        assert check_freqs_dc_and_equidist(f) == (True,True)  # sanity check
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
            # no padding needed
            return f, s, 1.0
        
        padding_factor = n_target / len(s)  # padding increases the highest spectrum frequency!
        
        # padding with zeros
        f_end, f_step = f[-1], f[-1] - f[-2]
        f = np.concatenate([f, np.linspace(f_end+f_step, f_end+f_step*n_missing, n_missing)])
        s = np.concatenate([s, np.zeros([n_missing], dtype=s.dtype)])
        return f, s, padding_factor


    def _apply_window(self, s: np.ndarray) -> np.ndarray:
        
        if window_has_argument(self.window):
            window_arg = (self.window, *self.window_args)
        else:
            window_arg = (self.window,)
        
        win_2sided = scipy.signal.get_window(window_arg, 2*len(s))
        win = win_2sided[len(s):]
        sp_windowed = s * win
        return sp_windowed


    def _get_impulse_response(self, f: np.ndarray, s: np.ndarray, use_fft: bool) -> tuple[np.ndarray,np.ndarray]:

        def can_use_fft(f: np.ndarray, s: np.ndarray) -> tuple[bool,np.ndarray,np.ndarray]:
            
            starts_at_dc, is_equidistant = check_freqs_dc_and_equidist(f)
            
            if not is_equidistant:
                # not equidistant, cannot use FFT
                return False, f, s
            
            if not starts_at_dc:
                can_fix, f_missing = get_missing_freq_dc_and_equidist(f)
                if not can_fix:
                    # equidistant, but doesn't start at DC, cannot use FFT
                    return False, f, s
                
                # just add zeros, then we are reasonably close to DC and equidistant
                f = np.concatenate([f_missing, f])
                s = np.concatenate([np.zeros([len(f_missing)], dtype=s.dtype), s])
                return True, f, s
            
            # data starts at DC and is equidistant, can use FFT
            return True, f, s

        if not use_fft:
            use_fft, f, s = can_use_fft(f, s)
        
        if use_fft:

            assert check_freqs_dc_and_equidist(f) == (True,True), 'Sanity check failed, expected frequencies to be equidistant from zero'

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

            # S-parameter to impedance
            w[w==1] = math.nextafter(1, -math.inf)  # avoid division by zero
            w = z0 * (1+w) / (1-w)
            
            # ensure the resulting trace is real-valued
            if z0.imag != 0:
                logging.warning(f'TDR: Converting to impedance with complex-valued characteristic impedance ({z0:.3g} Ω), dropping imaginary part of result')
            w = np.astype(np.real(w), float)
        
        return t, w
