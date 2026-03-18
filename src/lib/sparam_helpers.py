import skrf
import numpy as np
import math
import cmath
import scipy
import re
from .utils import window_has_argument


def _get_mixed_port_names(nw: skrf.Network) -> list[tuple[str,int]]:
    result = []
    port_numbers = dict()
    for i in range(nw.number_of_ports):
        current_mode = nw.port_modes[i]
        current_number = port_numbers.setdefault(current_mode, 0) + 1
        port_numbers[current_mode] = current_number

        result.append((current_mode,current_number))

    return result


def get_sparam_name(nw: skrf.Network, egress: int, ingress: int, prefix: str = 'S') -> str:

    is_mixed_mode = 'C' in nw.port_modes or 'D' in nw.port_modes

    if is_mixed_mode:
        names = _get_mixed_port_names(nw)
        assert egress<=len(names) and ingress<=len(names), f'Expected egress and ingress port to be within the range of names, got {egress}/{ingress} and names {names}'
        (egress_mode,egress_number) = names[egress-1]
        (ingress_mode,ingress_number) = names[ingress-1]
        if egress_number<10 and ingress_number<10:
            return f'{prefix}{egress_mode}{ingress_mode}{egress_number}{ingress_number}'
        else:
            return f'{prefix}{egress_mode}{ingress_mode}{egress_number},{ingress_number}'
    
    else:
        if egress<10 and ingress<10:
            return f'{prefix}{egress}{ingress}'
        else:
            return f'{prefix}{egress},{ingress}'


def get_port_index(nw: skrf.Network, mode: str, number: int) -> int:
    assert mode in ['S','D','C'], f'Expected mode to be one of "S", "D", "C", got "{mode}"'
    for i,(m,n) in enumerate(_get_mixed_port_names(nw)):
        if m==mode and n==number:
            return i
    raise RuntimeError(f'Cannot find port {mode}{number} in network {nw.name}')


def irndft(f: np.ndarray, s: np.ndarray, n_samples: int = None, t_total: float = None) -> tuple[np.ndarray,np.ndarray]:
    """ Inverse real-valued non-equidistant DFT """
    assert len(f) >= 2 and len(f) == len(s)
    
    if n_samples is None:
        f_max, f_span = f[-1], f[-1] - f[0]
        n_freqs_onesided = round(len(f) * f_max/f_span)
        n_samples = (n_freqs_onesided - 1) * 2
    
    if t_total is None:
        f_min, f_step_min = f[0], np.min(np.diff(f))
        assert f_step_min > 0
        if f_min > 0:
            t_total = max(1/f_min, 1/f_step_min)  
        else:
            t_total = 1/f_step_min
    
    t = np.linspace(0, t_total*(n_samples-1)/n_samples, n_samples)

    # wave[i] = Σ_j s[j] * e^(2jπ * t[i] * f[j])
    twopi_t_f = np.tensordot(1j * math.tau * t, f, axes=0)
    wave = np.sum(s * np.exp(twopi_t_f), axis=1)
    
    return t, np.real(wave) / len(wave) * 2


def ensure_equidistant_freq(f: np.ndarray, sp: np.ndarray, max_rel_error: float = 1e-3, max_abs_error = 1.0) -> "tuple(np.ndarray,np.ndarray)":

    f_min, f_max = f[0], f[-1]
    f_equidistant = np.linspace(f_min, f_max, len(f))

    error = f - f_equidistant
    max_error = max(np.abs(error))
    if max_error < f_max*max_rel_error and max_abs_error:
        return f, sp # already good enough

    if len(f) < 2:
        raise RuntimeError('Cannot interpolate S-parameters: at least two frequency samples are required')
    
    get_interpolator = lambda f,x: scipy.interpolate.interp1d(f, x, kind='cubic', bounds_error=False, fill_value='extrapolate')
    
    pha, mag = np.unwrap(np.angle(sp)), np.abs(sp)
    pha_fn, mag_fn = get_interpolator(f, pha), get_interpolator(f, mag)
    
    pha_int = [pha_fn(f) for f in f_equidistant]
    mag_int = [mag_fn(f) for f in f_equidistant]
    sp_complete = np.array([cmath.rect(m,p) for m,p in zip(mag_int,pha_int)])
    
    return f_equidistant, sp_complete


def extrapolate_to_dc_ieee370(f: np.ndarray, sp: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    """ Extrapolation accoridng to IEEE370, Annex T """
    assert f[0] > 0 and len(f) >= 2

    f1, f2 = f[0], f[1]
    sp1, sp2 = sp[0], sp[1]

    # real part: assume mirrored mirrorring Y-axis, use 2nd degree polynomial for interpolation
    f_re, sp_re = [-f2, -f1, +f1, +f2], [sp2.real, sp1.real, sp1.real, sp2.real]
    int_re = scipy.interpolate.interp1d(f_re, sp_re, kind='quadratic', bounds_error=False, fill_value='extrapolate')

    # real part: assume negative mirrorring across Y-axis (complex conjugate), use 3rd degree polynomial for interpolation
    f_im, sp_im = [-f2, -f1, 0, +f1, +f2], [-sp2.imag, -sp1.imag, 0, sp1.imag, sp2.imag]
    int_im = scipy.interpolate.interp1d(f_im, sp_im, kind='cubic', bounds_error=False, fill_value='extrapolate')

    df = f[0] / f[-1]
    n = max(10, int(math.ceil(len(f)*df)))
    f_int = np.linspace(0, f[0]*(n-1)/n, n)

    sp_int = int_re(f_int) + 1j*int_im(f_int)

    f_complete, sp_complete = np.concatenate([f_int, f]), np.concatenate([sp_int, sp])
    return f_complete, sp_complete


def extrapolate_to_dc_polar(f: np.ndarray, sp: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    """ Extrapolation in polar coordinates """
    assert f[0] > 0 and len(f) >= 2

    mag, pha = np.abs(sp), np.unwrap(np.angle(sp))
    
    # extrapolate phase to DC
    interp_pha = scipy.interpolate.interp1d(f, pha, kind='linear', bounds_error=False, fill_value='extrapolate')
    dc_phase_extrap = interp_pha(0)
    
    # subtract DC-phase, so that we can assume the overall phase crosses the point (0 Hz, 0°)
    pha -= dc_phase_extrap
    
    # magnitude: just use cubic interpolation/extrapolation, do not make any further assumptions
    interp_mag = scipy.interpolate.interp1d(f, mag, kind='cubic', bounds_error=False, fill_value='extrapolate')

    # phase: assume negative mirrorring across Y-axis (phase crosses zero), use 3rd degree polynomial for interpolation
    f_pha, sp_pha = [*(-np.flip(f)), 0, *f], [*(-np.flip(pha)), 0, *pha]
    interp_pha = scipy.interpolate.interp1d(f_pha, sp_pha, kind='cubic', bounds_error=False, fill_value='extrapolate')

    df = f[0] / f[-1]
    n = max(10, int(math.ceil(len(f)*df)))
    f_int = np.linspace(0, f[0]*(n-1)/n, n)

    sp_int = interp_mag(f_int) * np.exp(1j * (interp_pha(f_int) + dc_phase_extrap))  # don't forget to add the DC phase again (we subtracted it above!)

    f_complete, sp_complete = np.concatenate([f_int, f]), np.concatenate([sp_int, sp])
    return f_complete, sp_complete


def ensure_equidistant_freq_from_dc(f: np.ndarray, sp: np.ndarray, method: str = 'IEEE370') -> tuple[np.ndarray,np.ndarray]:

    if f[0] == 0:
        return ensure_equidistant_freq(f, sp) # DC is already included
    if f[0] < 0:
        raise RuntimeError('Cannot handle S-parameters with negative frequencies')
    if len(f) < 2:
        raise RuntimeError('Cannot extrapolate S-parameters to DC: at least two frequency samples are required')
    
    if method=='IEEE370':
        f, sp = extrapolate_to_dc_ieee370(f, sp)
    elif method=='polar':
        f, sp = extrapolate_to_dc_polar(f, sp)
    else:
        raise NotImplementedError()
    return ensure_equidistant_freq(f, sp)


def parse_quick_param(param: any) -> tuple[int,int]:
    match param:
        case int():
            if param<11 or param>99:
                raise ValueError(f'Integer argument must be in range 11...99 (e.g. `21` for S2,1); got `{param}`')
            return (param//10, param % 10)
        case str():
            if m := re.match(r'^([0-9][0-9]+)$', param):
                return parse_quick_param(int(m.group()))
            if m := re.match(r'^([0-9]+)[,;]([0-9]+)$', param):
                return ((int(m.group(1)),int(m.group(2))))
            raise ValueError(f'String argument must be one or two integers (e.g. `"21"` or `"2,1"` for S2,1); got `{param}`')
        case tuple() | list():
            if len(param) != 2:
                raise ValueError(f'Tuple or list argument must have two elements (e.g. `(2,1)` for S2,1); got `{param}`')
            return (param[0], param[1])
    raise ValueError(f'Expecting an integer (e.g. `21` for <S2,1>), a tuple or list (e.g. `(2,1)` for S2,1) or a string (e.g. `"21"` for S2,1); got `{param}`')
