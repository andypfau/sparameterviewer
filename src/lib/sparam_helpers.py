import numpy as np
import math
import scipy.interpolate
from typing import Callable
from .network_ext import NetworkExt
from .utils import window_has_argument
from .settings import Settings


def _get_mixed_port_names(nw: NetworkExt) -> list[tuple[str,int]]:
    result = []
    port_numbers = dict()
    for i in range(nw.number_of_ports):
        current_mode = nw.port_modes[i]
        current_number = port_numbers.setdefault(current_mode, 0) + 1
        port_numbers[current_mode] = current_number

        result.append((current_mode,current_number))

    return result


def get_sparam_name(nw: NetworkExt, egress: int, ingress: int, prefix: str = 'S') -> str:

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


def get_port_index(nw: NetworkExt, mode: str, number: int) -> int:
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


def check_freqs_dc_and_equidist(f: np.ndarray) -> tuple[bool,bool]:
    """ Checks if the given frequencies start at DC, and are equidistant """
    assert len(f) >= 2
    f_steps = np.diff(f)
    starts_at_dc = bool(f[0] == 0)
    is_equidistant = np.allclose(f_steps, f_steps[0])
    return starts_at_dc, is_equidistant


def get_missing_freq_dc_and_equidist(f: np.ndarray, max_rel_error: float = 1e-6) -> tuple[bool,np.ndarray]:
    """ Returns (True,ndarray) if the returned array can be appended at the beginning of the frequencies to make them
    equidistant, and start at DC; otherwise, returns (False,empty_ndarray) """
    starts_at_dc, is_equidistant = check_freqs_dc_and_equidist(f)
    
    if starts_at_dc and is_equidistant:
        return True, np.array([])  # no missing frequencies
    if starts_at_dc or not is_equidistant:
        return False, np.array([])  # cannot be fixed by just adding frequencies from DC
    
    f_first, f_step = f[0], f[1] - f[0]
    n_steps = round(f_first / f_step)
    f_first_stepped = n_steps * f_step
    f_error = abs(f_first - f_first_stepped)
    if f_error > f_step * max_rel_error:
        return False, np.array([])  # cannot be fixed by just adding frequencies from DC
    
    return True, np.linspace(0, f_first-f_step, n_steps, dtype=f.dtype)


def interpolate_freq(f: np.ndarray, s: np.ndarray, f_new: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    mag, pha = np.abs(s), np.unwrap(np.angle(s))

    pha_fn = scipy.interpolate.make_interp_spline(f, pha, k=3)
    mag_fn = scipy.interpolate.make_interp_spline(f, mag, k=3)
    
    s_new = mag_fn(f_new) * np.exp(1j * (pha_fn(f_new)))
    return f_new, s_new


def interpolate_equidistant_freq(f: np.ndarray, s: np.ndarray, max_rel_error: float = 1e-6, max_abs_error = 1e-3) -> tuple[np.ndarray,np.ndarray]:

    f_min, f_max, f_step = f[0], f[-1], f[1]-f[0]
    f_equidistant = np.linspace(f_min, f_max, len(f))

    error = f - f_equidistant
    max_error = max(np.abs(error))
    if max_error <= f_step*max_rel_error and max_error <= max_abs_error:
        return f, s # already good enough

    if len(f) < 2:
        raise RuntimeError('Cannot interpolate S-parameters: at least two frequency samples are required')
    
    f_equidistant, s_equidistant = interpolate_freq(f, s, f_equidistant)
    return f_equidistant, s_equidistant


def extrapolate_to_dc_ieee370(f: np.ndarray, s: np.ndarray, f_extrapolate: np.ndarray = None) -> tuple[np.ndarray,np.ndarray]:
    """ Extrapolation accoridng to IEEE370, Annex T """
    if f_extrapolate is None:
        f_extrapolate = np.array([0])
    assert f[0] > 0 and len(f) >= 2

    f1, f2 = f[0], f[1]
    s1, s2 = s[0], s[1]

    # real part: assume mirrored mirrorring Y-axis, use 2nd degree polynomial for interpolation
    f_re, s_re = [-f2, -f1, +f1, +f2], [s2.real, s1.real, s1.real, s2.real]
    int_re = scipy.interpolate.make_interp_spline(f_re, s_re, k=2)

    # real part: assume negative mirrorring across Y-axis (complex conjugate), use 3rd degree polynomial for interpolation
    f_im, p_im = [-f2, -f1, 0, +f1, +f2], [-s2.imag, -s1.imag, 0, s1.imag, s2.imag]
    int_im = scipy.interpolate.make_interp_spline(f_im, p_im, k=3)

    s_int = int_re(f_extrapolate) + 1j*int_im(f_extrapolate)

    f_complete, s_complete = np.concatenate([f_extrapolate, f]), np.concatenate([s_int, s])
    return f_complete, s_complete


def extrapolate_to_dc_polar(f: np.ndarray, s: np.ndarray, f_extrapolate: np.ndarray = None, dc_mag_assumption: str|None = None) -> tuple[np.ndarray,np.ndarray]:
    """ Extrapolation in polar coordinates """
    if f_extrapolate is None:
        f_extrapolate = np.array([0])
    assert f[0] > 0 and len(f) >= 2

    mag, pha = np.abs(s), np.unwrap(np.angle(s))

    def extrapolate_with_phase_assumption(dc_phase_assumption: float) -> tuple[Callable[tuple[np.ndarray],np.ndarray],Callable[tuple[np.ndarray],np.ndarray]]:
        f_pha, s_pha = np.concatenate([[0], f]), np.concatenate([[dc_phase_assumption], pha])
        interp_pha = scipy.interpolate.make_interp_spline(f_pha, s_pha, k=3)
        interp_mag = scipy.interpolate.make_interp_spline(f, mag, k=3)
        return interp_mag, interp_pha

    def extrapolate_with_magnitude_assumption(dc_mag_assumption: float) -> tuple[Callable[tuple[np.ndarray],np.ndarray],Callable[tuple[np.ndarray],np.ndarray]]:
        f_mag, s_mag = np.concatenate([[0], f]), np.concatenate([[dc_mag_assumption], mag])
        interp_pha = scipy.interpolate.make_interp_spline(f, pha, k=3)
        interp_mag = scipy.interpolate.make_interp_spline(f_mag, s_mag, k=3)
        return interp_mag, interp_pha
    
    def extrapolate_mag() -> tuple[float,float,float]:
        interp_mag = scipy.interpolate.make_interp_spline(f, mag, k=3)
        dc_mag_extrap = interp_mag(0)

        # this algorithm can only estimate if the extrapolated magnitude is zero or not
        dc_mag_guessed = 0
        
        # does the magnitude extrapolate towards zero, or away from it?
        if (dc_mag_extrap < 0) != abs(mag[0] < 0):
            dc_mag_error = 0  # extrapolation crosses zero -> assume it converges to zero at DC
        elif abs(dc_mag_extrap) < abs(mag[0]):
            # converges towards zero, estimate error
            if mag[0] == 0:
                dc_mag_error = abs(dc_mag_extrap)  # I have no better idea here...
            else:
                dc_mag_error = abs(dc_mag_extrap) / abs(mag[0])
        else:
            dc_mag_error = 1e99  # diverges away from zero -> large penalty
        
        return dc_mag_extrap, dc_mag_guessed, dc_mag_error

    def extrapolate_phase() -> tuple[float,float,float]:
        interp_pha = scipy.interpolate.make_interp_spline(f, pha, k=3)
        dc_phase_extrap = math.degrees(interp_pha(0))

        # the actual value can only be 0° or 180°
        dc_phase_real_guess = round(dc_phase_extrap / 180) * 180

        # how much is the extrapolated phase away from 0° or 180°?
        dc_phase_extrap_clamped = dc_phase_extrap
        while dc_phase_extrap_clamped > 90:
            dc_phase_extrap_clamped -= 180
        while dc_phase_extrap_clamped < -90:
            dc_phase_extrap_clamped += 180
        dc_phase_error = abs(dc_phase_extrap_clamped) / 90  # calculate error vs. real-valued DC phase (0° or 180°)

        return dc_phase_extrap, dc_phase_real_guess, dc_phase_error

    match dc_mag_assumption:
        case None:
            # make no assumption about magnitude, just extrapolate phase
            _, dc_phase_real_guess, _ = extrapolate_phase()
            interp_mag, interp_pha = extrapolate_with_phase_assumption(math.radians(dc_phase_real_guess))
            print(f'~~ DC extrapolation: assuming DC phase of {dc_phase_real_guess}° ({dc_mag_assumption=})')
        case 'auto':
            # check which method has the smaller error
            _, dc_phase_real_guess, dc_phase_error = extrapolate_phase()
            _, dc_mag_guessed, dc_mag_error = extrapolate_mag()
            if dc_mag_error < dc_phase_error:
                print(f'~~ DC extrapolation: assuming DC magnitude of {dc_mag_guessed} ({dc_mag_assumption=})')
                interp_mag, interp_pha = extrapolate_with_magnitude_assumption(dc_mag_guessed)
            else:
                print(f'~~ DC extrapolation: assuming DC phase of {dc_phase_real_guess}° ({dc_mag_assumption=})')
                interp_mag, interp_pha = extrapolate_with_phase_assumption(math.radians(dc_phase_real_guess))
        case 'zero':
            interp_mag, interp_pha = extrapolate_with_magnitude_assumption(0)
            print(f'~~ DC extrapolation: assuming DC magnitude of zero ({dc_mag_assumption=})')
        case 'unity':
            interp_mag, interp_pha = extrapolate_with_magnitude_assumption(1)
            print(f'~~ DC extrapolation: assuming DC magnitude of unity ({dc_mag_assumption=})')
        case _:
            raise ValueError(f'Invalid argument for dc_mag_assumption: expected one of None, "auto", "zero", "unity"; got "{dc_mag_assumption}"')

    s_extrap = interp_mag(f_extrapolate) * np.exp(1j * (interp_pha(f_extrapolate)))  # don't forget to add the DC phase again (we subtracted it above!)
    f_complete, s_complete = np.concatenate([f_extrapolate, f]), np.concatenate([s_extrap, s])
    return f_complete, s_complete


def extrapolate_to_dc(f: np.ndarray, s: np.ndarray, f_extrapolate: np.ndarray = None, method: str = 'IEEE370', dc_mag_assumption: str|None = None) -> tuple[np.ndarray,np.ndarray]:

    if f[0] < 0:
        raise RuntimeError('Cannot handle S-parameters with negative frequencies')
    if len(f) < 2:
        raise RuntimeError('Cannot extrapolate S-parameters to DC: at least two frequency samples are required')
    
    if method=='IEEE370':
        f, s = extrapolate_to_dc_ieee370(f, s, f_extrapolate)
    elif method=='polar':
        f, s = extrapolate_to_dc_polar(f, s, f_extrapolate, dc_mag_assumption)
    return f, s


def ensure_equidistant_to_dc(f: np.ndarray, s: np.ndarray, method: str = 'IEEE370') -> tuple[np.ndarray,np.ndarray]:

    starts_at_dc, is_equidistant = check_freqs_dc_and_equidist(f)
    if starts_at_dc and is_equidistant:
        return f, s
    
    if starts_at_dc:
        return interpolate_equidistant_freq(f, s)
    
    can_fix, f_missing = get_missing_freq_dc_and_equidist(f)
    if can_fix:
        f, s = extrapolate_to_dc(f, s, f_missing, method=method)
        assert check_freqs_dc_and_equidist(f) == (True,True)
        return f, s
    
    # find a frequency grid, such that it can be extrapolated to DC in an equidistant way
    df_mean = (f[-1] - f[0]) / len(f)
    n_steps = round((f[-1] - 0) / df_mean)
    f_new = np.linspace(0, f[-1], n_steps)
    f_extrap = f_new[f_new < f[0]]
    f_interp = f_new[f_new >= f[0]]

    f, s = interpolate_freq(f, s, f_interp)
    f, s = extrapolate_to_dc(f, s, f_extrapolate=f_extrap, method=method)
    assert check_freqs_dc_and_equidist(f) == (True,True)
    return f, s


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
