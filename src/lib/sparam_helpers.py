import skrf
import numpy as np
from scipy.interpolate import interp1d
import math, cmath, copy


def get_sparam_name(egress: int, ingress: int) -> str:
    if egress<10 and ingress<10:
        return f'S{egress}{ingress}'
    else:
        return f'S{egress},{ingress}'


def extrapolate_sparams_to_dc(f: np.ndarray, sp: np.ndarray) -> "tuple(np.ndarray,np.ndarray)":
    
    if len(f)<2 or f[0]==0:
        sp_realdc = copy.copy(sp)
        sp_realdc[0] = np.real(sp)[0]
        return f, sp_realdc
    
    f0 = f[0]
    fmax = f[-1]
    df = f[1] - f[0]
    n_points_missing = int(round(f0 / df))
    n_final = len(f) + n_points_missing
    
    f_ext = copy.copy(f)
    sp_ext = copy.copy(sp)
    
    f_ext = np.insert(f_ext, 0, 0)
    sp_ext = np.insert(sp_ext, 0, np.real(sp)[0])
    
    get_interpolator = lambda f,pha: interp1d(f, pha, kind='cubic', bounds_error=False, fill_value='extrapolate')
    
    pha, mag = np.unwrap(np.angle(sp_ext)), np.abs(sp_ext)
    pha_fn, mag_fn= get_interpolator(f_ext, pha), get_interpolator(f_ext, mag)
    
    f_complete = np.linspace(0, fmax, n_final)
    pha_int = [pha_fn(f) for f in f_complete]
    mag_int = [mag_fn(f) for f in f_complete]
    sp_complete = np.array([cmath.rect(m,p) for m,p in zip(mag_int,pha_int)])
    
    return f_complete, sp_complete  


def sparam_to_timedomain(f: np.ndarray, spar: np.ndarray, step_response: bool = False, kaiser: float = 35.0) -> "tuple(np.ndarray,np.ndarray)":
    
    f_dc,sp_dc = extrapolate_sparams_to_dc(f, spar)
    
    if kaiser>0:
        win = np.kaiser(2*len(sp_dc), kaiser)[len(sp_dc):]
    else:
        win = np.ones([len(sp_dc)])

    ir = np.fft.irfft(sp_dc * win)
    ir = np.fft.fftshift(ir)
    
    f_nyq = max(f)
    f_sa = 2.0 * f_nyq
    t_spc = 1.0 / f_sa
    t_tot = (len(ir)-1)*t_spc
    t = np.linspace(0, t_tot, len(ir))
    t -= t_tot/2 # compensate for the FFT-shift

    if step_response:
        sr = np.cumsum(ir)
        return t, sr
    else:
        return t, ir
