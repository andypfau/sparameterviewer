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


def _ensure_equidistant_freq_from_dc_ieee370(f: np.ndarray, sp: np.ndarray) -> "tuple(np.ndarray,np.ndarray)":
    # Extrapolation method: see IEEE370, Annex T
    assert f[0] > 0 and len(f) >= 2

    f1, f2 = f[0], f[1]
    h1, h2 = sp[0], sp[1]

    # real part: assume mirrored mirrorring Y-axis, use 2nd degree polynomial for interpolation
    f_re, sp_re = [-f2, -f1, +f1, +f2], [h2.real, h1.real, h1.real, h2.real]
    int_re = scipy.interpolate.interp1d(f_re, sp_re, kind='quadratic', bounds_error=False, fill_value='extrapolate')

    # real part: assume negative mirrorring across Y-axis (complex conjugate), use 3rd degree polynomial for interpolation
    f_im, sp_im = [-f2, -f1, 0, +f1, +f2], [-h2.imag, -h1.imag, 0, h1.imag, h2.imag]
    int_im = scipy.interpolate.interp1d(f_im, sp_im, kind='cubic', bounds_error=False, fill_value='extrapolate')

    df = f[0] / f[-1]
    n = max(10, int(math.ceil(len(f)*df)))
    f_int = np.linspace(0, f[0]*(n-1)/n, n)

    sp_int = int_re(f_int) + 1j*int_im(f_int)

    f_complete, sp_complete = np.concatenate([f_int, f]), np.concatenate([sp_int, sp])
    return ensure_equidistant_freq(f_complete, sp_complete)


def _ensure_equidistant_freq_from_dc_phasesnap(f: np.ndarray, sp: np.ndarray) -> "tuple(np.ndarray,np.ndarray)":
    # Extrapolation method: extrapolate gain, extrapolate phase to 0 or 180°
    assert f[0] > 0 and len(f) >= 2

    int_mag = scipy.interpolate.interp1d(f, abs(sp), kind='cubic', bounds_error=False, fill_value='extrapolate')
    
    sp_pha = np.unwrap(np.angle(sp))
    int_pha = scipy.interpolate.interp1d(f, sp_pha, kind='cubic', bounds_error=False, fill_value='extrapolate')
    dc_pha_extrap = int_pha(0)
    dc_pha_guessed = round(dc_pha_extrap / math.pi) * math.pi  # must be 0 or 180° (no complex phase allowed)
    int_pha = scipy.interpolate.interp1d([0,*f], [dc_pha_guessed,*sp_pha], kind='cubic', bounds_error=False, fill_value='extrapolate')

    df = f[0] / f[-1]
    n = max(10, int(math.ceil(len(f)*df)))
    f_int = np.linspace(0, f[0]*(n-1)/n, n)

    sp_int = int_mag(f_int) * np.exp(1j * int_pha(f_int))

    f_complete, sp_complete = np.concatenate([f_int, f]), np.concatenate([sp_int, sp])
    return ensure_equidistant_freq(f_complete, sp_complete)


# TODO: make method selection a GUI option
def ensure_equidistant_freq_from_dc(f: np.ndarray, sp: np.ndarray, method: str = 'IEEE370') -> "tuple(np.ndarray,np.ndarray)":

    if f[0] == 0:
        return ensure_equidistant_freq(f, sp) # DC is already included
    if f[0] < 0:
        raise RuntimeError('Cannot handle S-parameters with negative frequencies')
    if len(f) < 2:
        raise RuntimeError('Cannot extrapolate S-parameters to DC: at least two frequency samples are required')
    
    if method=='IEEE370':
        return _ensure_equidistant_freq_from_dc_ieee370(f, sp)
    elif method=='PhaseSnap':
        return _ensure_equidistant_freq_from_dc_phasesnap(f, sp)
    else:
        raise NotImplementedError()


def sparam_to_timedomain(f: np.ndarray, spar: np.ndarray, *, shift: float = 0.0, step_response: bool = False, window_type: str = 'boxcar', window_arg: float = None, min_size: int = 0) -> "tuple(np.ndarray,np.ndarray)":
    
    f_dc,sp_dc = ensure_equidistant_freq_from_dc(f, spar)

    if window_has_argument(window_type):
        window_arg = (window_type, window_arg)
    else:
        window_arg = (window_type,)
    
    win_2sided = scipy.signal.get_window(window_arg, 2*len(sp_dc))
    win = win_2sided[len(sp_dc):]

    sp_windowed = sp_dc * win
    
    next_pow_of_2 = 1
    while next_pow_of_2 < max(len(sp_windowed), min_size):
        next_pow_of_2 *= 2
    n_missing = next_pow_of_2 - len(sp_windowed)
    correction_factor = next_pow_of_2 / len(sp_windowed)  # padding increases the highest frequency!
    sp_padded = np.concatenate([sp_windowed, np.zeros([n_missing], dtype=sp_windowed.dtype)])

    f_nyq = max(f) * correction_factor
    f_sa = 2.0 * f_nyq
    sa_period = 1.0 / f_sa

    ir_unshifted = np.fft.irfft(sp_padded)
    ir_unshifted_gaincorrected = ir_unshifted * correction_factor
    
    n_shift = round(shift / sa_period)
    ir = np.roll(ir_unshifted_gaincorrected, n_shift)
    
    t_tot = (len(ir)-1) * sa_period
    t = np.linspace(0, t_tot, len(ir))

    if step_response:
        sr = np.cumsum(ir) / correction_factor
        return t, sr
    else:
        return t, ir


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
