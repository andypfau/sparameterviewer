import skrf
import numpy as np
from scipy.interpolate import interp1d
import math, cmath, copy


def get_sparam_name(egress: int, ingress: int) -> str:
    if egress<10 and ingress<10:
        return f'S{egress}{ingress}'
    else:
        return f'S{egress},{ingress}'


def ensure_equidistant_freq(f: np.ndarray, sp: np.ndarray, max_rel_error: float = 1e-3, max_abs_error = 1.0) -> "tuple(np.ndarray,np.ndarray)":

    f_min, f_max = f[0], f[-1]
    f_equidistant = np.linspace(f_min, f_max, len(f))

    error = f - f_equidistant
    max_error = max(np.abs(error))
    if max_error < f_max*max_rel_error and max_abs_error:
        return f, sp # already good enough

    if len(f) < 2:
        raise RuntimeError('Cannot interpolate S-parameters: at least two frequency samples are required')
    
    get_interpolator = lambda f,x: interp1d(f, x, kind='cubic', bounds_error=False, fill_value='extrapolate')
    
    pha, mag = np.unwrap(np.angle(sp)), np.abs(sp)
    pha_fn, mag_fn = get_interpolator(f, pha), get_interpolator(f, mag)
    
    pha_int = [pha_fn(f) for f in f_equidistant]
    mag_int = [mag_fn(f) for f in f_equidistant]
    sp_complete = np.array([cmath.rect(m,p) for m,p in zip(mag_int,pha_int)])
    
    return f_equidistant, sp_complete


def ensure_equidistant_freq_from_dc(f: np.ndarray, sp: np.ndarray) -> "tuple(np.ndarray,np.ndarray)":

    if f[0] == 0:
        return ensure_equidistant_freq(f, sp) # DC is already included
    if f[0] < 0:
        raise RuntimeError('Cannot handle S-parameters with negative frequencies')
    if len(f) < 2:
        raise RuntimeError('Cannot extrapolate S-parameters to DC: at least two frequency samples are required')
    
    # Extrapolation method: see IEEE370, Annex T

    f1, f2 = f[0], f[1]
    h1, h2 = sp[0], sp[1]

    # real part: assume mirrored mirrorring Y-axis, use 2nd degree polynomial for interpolation
    f_re, sp_re = [-f2, -f1, +f1, +f2], [h2.real, h1.real, h1.real, h2.real]
    int_re = interp1d(f_re, sp_re, kind='quadratic', bounds_error=False, fill_value='extrapolate')

    # real part: assume negative mirrorring across Y-axis (complex conjugate), use 3rd degree polynomial for interpolation
    f_im, sp_im = [-f2, -f1, 0, +f1, +f2], [-h2.imag, -h1.imag, 0, h1.imag, h2.imag]
    int_im = interp1d(f_im, sp_im, kind='cubic', bounds_error=False, fill_value='extrapolate')

    extend = f[0] / f[-1]
    n = max(10, int(math.ceil(len(f)*extend)))
    f_int = np.linspace(0, f[0]*(n-1)/n, n)

    sp_re_int = [int_re(f) for f in f_int]
    sp_im_int = [int_im(f) for f in f_int]
    sp_int = np.array([r+1j*i for r,i in zip(sp_re_int,sp_im_int)])

    f_complete, sp_complete = np.concatenate([f_int, f]), np.concatenate([sp_int, sp])
    return ensure_equidistant_freq(f_complete, sp_complete)


def sparam_to_timedomain(f: np.ndarray, spar: np.ndarray, step_response: bool = False, kaiser: float = 35.0) -> "tuple(np.ndarray,np.ndarray)":
    
    f_dc,sp_dc = ensure_equidistant_freq_from_dc(f, spar)
    
    if kaiser > 0:
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
