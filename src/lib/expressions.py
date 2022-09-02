from .structs import LoadedSParamFile
from .bodefano import BodeFano
from .stabcircle import StabilityCircle
from .networks import Networks
from .sparams import SParam, SParams

import skrf, math, os
import numpy as np
import fnmatch


class ExpressionParser:

    @staticmethod
    def eval(code: str, \
        available_networks: "list[LoadedSParamFile]", \
        selected_networks: "list[LoadedSParamFile]", \
        plot_fn: "callable[np.ndarray,np.ndarray,str,str]"):

        available = [nw.sparam.network for nw in available_networks]
        selected = [nw.sparam.network for nw in selected_networks]
        
        SParam.plot_fn = plot_fn
        Networks.available_networks = available

        def all_nws() -> Networks:
            return Networks(None, nws=available)
        
        def sel_nws() -> Networks:
            return Networks(None, nws=selected)
        
        def nws(name: str) -> Networks:
            return Networks(name)
        
        def _get_nw(obj: "str|Networks") -> Networks:
            return obj if isinstance(obj, Networks) else Networks(obj)
        
        def s(network: "str|Networks", egress_port: int, ingress_port: int) -> SParams:
            return _get_nw(network).s(egress_port, ingress_port)
        
        def k(network: "str|Networks") -> SParams:
            return _get_nw(network).k()
        
        def mu(network: "str|Networks", mu: int = 1) -> SParams:
            return _get_nw(network).mu(mu)
        
        def cascade(*networks: "tuple[str|Networks, ...]") -> Networks:
            networks = [_get_nw(n) for n in networks]
            result = networks[0]
            for i in range(1,len(networks)):
                result = result ** networks[i-1]
            return result
        
        def half(network: "Networks") -> Networks:
            return _get_nw(network).half()
        
        def flip(network: "Networks") -> Networks:
            return _get_nw(network).flip()
        
        def invert(network: "Networks") -> Networks:
            return ~_get_nw(network)
        
        def abs(sparam: "SParams") -> SParams:
            return sparam.abs()
        
        def db(sparam: "SParams") -> SParams:
            return sparam.db()
        
        def plot(sparam: SParams, label: "str|None" = None, style: "str|None" = None):
            sparam.plot(label, style)

        def rl_avg(sparam: SParams, f_start: "float|None" = None, f_end: "float|None" = None) -> SParams:
            return sparam.rl_avg(f_start, f_end)

        def rl_opt(sparam: SParams, f_integrate_start: "float|None" = None, f_integrate_end: "float|None" = None, f_target_start: "float|None" = None, f_target_end: "float|None" = None) -> SParams:
            return sparam.rl_opt(f_integrate_start, f_integrate_end, f_target_start, f_target_end)
        
        def crop_f(obj: "Networks|SParams", f_start: "float|None" = None, f_end: "float|None" = None) -> "Networks|SParams":
            return obj.crop_f(f_start, f_end)
        
        def add_sr(network: "Networks", resistance: float, port: int = 1) -> "Networks":
            return _get_nw(network).add_sr(resistance, port)
        
        def add_sl(network: "Networks", resistance: float, port: int = 1) -> "Networks":
            return _get_nw(network).add_sl(resistance, port)
        
        def add_sc(network: "Networks", inductance: float, port: int = 1) -> "Networks":
            return _get_nw(network).add_sc(inductance, port)
        
        def add_pr(network: "Networks", resistance: float, port: int = 1) -> "Networks":
            return _get_nw(network).add_pr(resistance, port)
        
        def add_pl(network: "Networks", capacitance: float, port: int = 1) -> "Networks":
            return _get_nw(network).add_pl(capacitance, port)
        
        def add_pc(network: "Networks", inductance: float, port: int = 1) -> "Networks":
            return _get_nw(network).add_pc(inductance, port)
    
        def add_tl(network: "Networks", degrees: float, frequency_hz: float = 1e9, z0: float = None, loss: float = 0, port: int = 1) -> "Networks":
            return _get_nw(network).add_tl(degrees, frequency_hz, z0, loss, port)

        def plot_stab(network: "Networks", frequency_hz: float, port: int = 2, n_points=101, label: "str|None" = None, style: "str|None" = None):
            network.plot_stab(frequency_hz, port, n_points, label, style)

        vars_global = {}
        vars_local = {
            'Networks': Networks,
            'SParams': SParams,
            'all_nws': all_nws,
            'sel_nws': sel_nws,
            'nws': nws,
            's': s,
            'k': k,
            'mu': mu,
            'half': half,
            'flip': flip,
            'invert': invert,
            'cascade': cascade,
            'add_sr': add_sr,
            'add_sl': add_sl,
            'add_sc': add_sc,
            'add_pr': add_pr,
            'add_pl': add_pl,
            'add_pc': add_pc,
            'add_tl': add_tl,
            'plot': plot,
            'plot_stab': plot_stab,
            'crop_f': crop_f,
            'abs': abs,
            'db': db,
            'rl_avg': rl_avg,
            'rl_opt': rl_opt,
            'math': math,
            'np': np,
        }
        
        for code_line in code.split('\n'):
            code_linestripped = code_line.strip()
            if code_linestripped.startswith('#'):
                continue
            if len(code_linestripped) < 1:
                continue
            _ = eval(code_linestripped, vars_global, vars_local)


    @staticmethod
    def help() -> str:
            return '''Basics
======

The basic idea is to load a network (nw), get a specific S-parameter (s), and plot it (plot):

    nw("Amplifier.s2p").s(2,1).plot("IL")

The expression use Python syntax. Everything is object-oriented,
but there are function-wrappers for convenience.

You also have access to `math` and `np` (numpy).


Objects
=======

Networks
--------

    A container for one or more S-parameter networks.

    Note that any operation on the object might fail silently. For example, if an object contains a 1-port
    and a 2-port, and you attempt to invert the object (an operation that only works on 2-ports), the 1-port
    will silently be dropped.

    Constructor

        Network(<name_or_partial_name>)
            Returns the networks that match the provided name; e.g. Networks("Amplifier") would match
            a file named "Amplifier.s2p" or "MyAmplifier01.s2p".

    Methods

        s(<egress_port>,<ingress_port>) -> SParams
            Gets an S-parameters.

        invert() -> Networks
            Inverts the ports (e.g. for de-embedding).

        flip() -> Networks
            Flips the ports (e.g. to use it in reverse direction).

        half() -> Networks
            Chops the network in half (e.g. for 2xTHRU de-embedding).

        k() -> SParams
            Returns the K (Rollet) stability factor (should be >1, or >0 dB).

        mu(<mu=1>) -> SParams
            Returns the µ or µ' (Edwards-Sinsky) stability factor (should be >1, or >0 dB;
            mu must be 1 or 2, default is 1).

        crop_f([f_start], [f_end]) -> Networks
            Returns the same network, but with a reduced frequency range
        
        add_sr(resistance[, <port=1>]) -> Networks
            Returns a network with a series resistance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_sl(inductance[, <port=1>]) -> Networks
            Returns a network with a series inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_sc(capacitance[, <port=1>]) -> Networks
            Returns a network with a series inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pr(resistance[, <port=1>]) -> Networks
            Returns a network with a parallel resistance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pl(inductance[, <port=1>]) -> Networks
            Returns a network with a parallel inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_pc(capacitance[, <port=1>]) -> Networks
            Returns a network with a parallel inductance attached to the specified port.
            Works only for 1-ports and 2-ports.
        
        add_tl(degrees, frequency_hz=1e9[, <z0=default>][, <loss=0>][, <port=1>]) -> Networks
            Returns a network with a transmission line attached to the specified port.
            Works only for 1-ports and 2-ports. The length is specified in degrees at the given frequency.
            The loss is the real part of the propagation constant.
            If Z0 is not provided, the reference impedance of the corresponding port is used.
        
        rl_avg(f_start_hz=-inf, f_stop_hz=+inf) -> SParams
            Calculates the average return loss over the given frequency range.
        
        rl_opt(f_integrate_start_hz=-inf, f_integrate_stop_hz=+inf, f_target_start_hz=-inf, f_target_stop_hz=+inf) -> SParams
            Integrates the return loss over the given integration frequency range, then uses
            the Bode-Fano limit to calculate the maximum achievable return loss over the
            given target frequency range.
        
        plot_stab(frequency_hz, [<port=2>], [<n_points=101>], ([<label=None>],[<style="-">]):
            Plots the stability circle at the given frequency. Set port=1 if you want to calculate the stability at
            the input, otherwise the output is calculated. It adds "s.i." (stable inside circle) or "s.o." (stable outside
            of the circle) to the plot name.

    Unary Operators

        ~
            Same as invert().

    Binary Operators

        **
            Cascades two networks.

SParams
-------

    Methods

        plot([<label=None>],[<style="-">]) -> Network
            Plots the data. <label> is any string.
            <style> is a matplotlib-compatible format (e.g. "-", ":", "--", "o-").

        db() -> Network
            Converts all values to dB.

        abs() -> SParam
            Takes abs() of each value.

        crop_f([f_start=-inf], [f_end=+inf]) -> SParam.
            Returns the same S-Param, but with a reduced frequency range.

    Unary Operators

        ~
            Takes the inverse (i.e. 1/x) of each value.

    Binary Operators

        + - * /
            Applies the corresponding mathematical operator.
            Each operand can also be a numeric constant.


Functions
=========

Most available functions are just shortcuts to object methods; the arguments denoted by "..." are the same as for the object methods.

    Object Method                              | Corresponding Function
    -------------------------------------------+----------------------------
    all_nws()                                  | returns all available networks
    sel_nws()                                  | returns all selected networks
    nws(<name_or_partial_name>)                | Networks(...)
    s(<network>,<egress_port>,<ingress_port>)  | Networks.s(...)
    invert(<network>)                          | Networks.invert()
    flip(<network>)                            | Networks.flip()
    half(<network>)                            | Networks.half()
    k(<network>)                               | Networks.k()
    mu(<network>,...)                          | Networks.mu(...)
    add_sr(<network>,...)                      | Networks.add_sr(...))
    add_sl(<network>,...)                      | Networks.add_sr(...)]
    add_sc(<network>,...)                      | Networks.add_sr(...))
    add_pr(<network>,...)                      | Networks.add_pr(...))
    add_pl(<network>,...)                      | Networks.add_pl(...)]
    add_pc(<network>,...)                      | Networks.add_pc(...))
    add_tl(<network>,...)                      | Networks.add_tl(,...)
    plot_stab(<network>,...)                   | Networks.plot_stab(,...)
    cascade(<network>,<network>[,...])         | Networks**Networks...
    crop_f(<network|SParam>,...)               | Networks|SParam.crop_f(...)
    plot(<sparam>,...)                         | SParams.plot(...)
    db(<sparam>)                               | SParams.db()
    abs(<sparam>)                              | SParams.abs()
    rl_avg(<sparam>, ...)                      | SParams.rl_avg(...)
    rl_opt(<sparam>, ...)                      | SParams.rl_opt(...)


Examples
========

Basic
-----

    all_nws().s(1,1).plot("RL")
    sel_nws().s(1,2).plot("Reverse IL")
    nws("Amplifier.s2p").s(2,1).plot("IL")
    nws("Amplifier.s2p").s(1,1).plot("RL",":")

Objects vs. Functions
---------------------

The following examples are all identical:

    nws("Amplifier.s2p").s(1,1).plot("RL",":")
    Networks("Amplifier.s2p").s(1,1).plot("RL",":")
    plot(s(nws("Amplifier.s2p"),1,1),"RL",":")

Advanced
--------

    # calculate directivity (S42/S32) of a directional coupler
    # note that this example requires plotting in linear units, as the values are already converted to dB
    (nws("Coupler.s2p").s(4,2).db() / nw("Coupler.s2p").s(3,2).db()).plot("Directivity")

    # de-embed a 2xTHRU
    (nws("2xThru").half().invert() ** nw("DUT") ** nw("2xThru").half().invert().flip()).s(2,1).plot("De-embedded")

    # crop frequency range; this can be handy e.g. if you want to see the Smith-chart only for a specific frequency range
    nws("Amplifier.s2p").crop_f(1e9,10e9).s(1,1).plot("RL",":")

    # calculate stability factor
    nws("Amplifier").mu().plot("µ Stability Factor",":")

    # add elements to a network (in this case, a parallel cap, followed by a short transmission line)
    nws("Amplifier").s(1,1).plot("Baseline",":")
    nws("Amplifier").add_pc(400e-15).add_tl(7,2e9,25).s(1,1).plot("Optimized","-")
'''
