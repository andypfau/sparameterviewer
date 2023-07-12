from ..structs import SParamFile
from ..bodefano import BodeFano
from ..stabcircle import StabilityCircle
from ..sparam_helpers import get_quick_params
from .networks import Networks
from .sparams import SParam, SParams

import math
import numpy as np
import fnmatch
import logging


class ExpressionParser:

    @staticmethod
    def eval(code: str, \
        available_networks: "list[SParamFile]", \
        selected_networks: "list[SParamFile]", \
        plot_fn: "callable[np.ndarray,np.ndarray,str,str]") -> "list[SParamFile]":

        touched_files = []
        
        SParam.plot_fn = plot_fn

        def select_networks(network_list: "list[SParamFile]", pattern: str, single: bool) -> Networks:
            nws = []
            if pattern is None and not single:
                nws = [nw for nw in network_list]
            else:
                for nw in network_list:
                    if pattern is None or fnmatch.fnmatch(nw.filename, pattern):
                        nws.append(nw)
            logging.debug(f'Expression pattern "{pattern}" matched "' + '", "'.join([n.name for n in nws]) + '"')
            if single:
                if len(nws) != 1:
                    raise RuntimeError(f'The pattern "{pattern}" matched {len(nws)} networks, but need exactly one')
            nonlocal touched_files
            for nw in nws:
                if nws not in touched_files:
                    touched_files.append(nw)
            return Networks(nws)
        
        def sel_nws(pattern: str = None) -> Networks:
            return select_networks(selected_networks, pattern, single=False)
        
        def nws(pattern: str = None) -> Networks:
            return select_networks(available_networks, pattern, single=False)
        
        def nw(pattern: str) -> Networks:
            return select_networks(available_networks, pattern, single=True)

        def quick(*items):
            for (e,i) in get_quick_params(*items):
                try:
                    sel_nws().s(e,i).plot()
                except Exception as ex:
                    logging.error(f'Unable to plot "S{e},{i}" ({ex})')

        vars_global = {}
        vars_local = {
            'Networks': Networks,
            'SParams': SParams,
            'nw': nw,
            'nws': nws,
            'sel_nws': sel_nws,
            'quick': quick,
            'math': math,
            'np': np,
        }
        
        exec(code, vars_global, vars_local)

        return touched_files


    @staticmethod
    def help() -> str:
            return '''Basics
======

The basic concept is to load one or multiple networks, get a specific S-parameter (s), and plot it (plot):

    nws("*amp.s2p").s(2,1).plot("IL")

Which could be re-written as:
    
    n = nws("*amp.s2p") # type: Networks
    s = n.s(2,1) # type: SParams
    s.plot("IL")

However, there is also a quicker way if you don't need full control:

    quick(21)

The expressions use Python syntax. You also have access to `math` and `np` (numpy).


Objects
=======

Networks
--------

    A container for one or more S-parameter networks.

    Note that any operation on the object may, by design, fail silently. For example, if an object contains
    a 1-port and a 2-port, and you attempt to invert the object (an operation that only works on 2-ports),
    the 1-port will silently be dropped. This is to avoid excessive errors when applying general expressions
    on a large set of networks.

    Methods

        s(<egress_port=None>,<ingress_port=None>,<rl_only=False>,<il_only=False>,<fwd_il_only=False>,<rev_il_only=False>) -> SParams
            Returns S-parameters of a network.
            <egress_port> and <ingress_port> can be set to a number, or kept at None (wildcard). Further filtering can be applied with
            <rl_only>, <il_only>, <fwd_il_only>, <rev_il_only>.

        invert() -> Networks
            Inverts the ports (e.g. for de-embedding).

        flip() -> Networks
            Flips the ports (e.g. to use it in reverse direction).

        half([<method='IEEE370NZC'>][, <side=1>]) -> Networks
            Chops the network in half (e.g. for 2xTHRU de-embedding).
            Allowed methods are 'IEEE370NZC' (IEEE-370, no Z-compensation), or 'ChopInHalf'. For IEEE-370,
            an additional argument <side> can be provided, to return the left side (1) or the right side (2).

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
        
        s2m([inp=<ports>][, outp=<ports>]):
            Single-ended to mixed-mode conversion.
            The expected port order for the single-ended network is port1p, port1n, port2p, port2n, ....
            You may define your own mapping with inp; e.g. if your data is <port1p, port2p, port1n, port2n>, you
            can provide <inp=[1,3,2,4]>.
            The generated mixed-mode network has port order diff1, comm1, diff2, comm_2, ...
            You may define your own mapping with outp; e.g. if you want <diff1, diff2, comm1, comm2>, you
            can provide <outp=[1,3,2,4]>.
        
        m2s([inp=<ports>][, outp=<ports>]):
            Mixed-mode to single-ended conversion.
            The expected port order for the single-ended network is diff1, comm1, diff2, comm_2, ...
            You may define your own mapping with inp; e.g. if your data is <diff1, diff2, comm1, comm2>, you
            can provide <inp=[1,3,2,4]>.
            The generated mixed-mode network has port order port1p, port1n, port2p, port2n, ....
            You may define your own mapping with outp; e.g. if you want <port1p, port2p, port1n, port2n>, you
            can provide <outp=[1,3,2,4]>.

        quick(quick(parameter[, parameter...]))
            Does the same as the <quick()> function, see below.

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
            Plots the data. <label> is any string. "%n" is replaced with the name of the parameter.
            <style> is a matplotlib-compatible format (e.g. "-", ":", "--", "o-").

        db() -> Network
            Converts all values to dB.

        abs() -> SParam
            Takes abs() of each value.

        phase([processing=None]) -> SParam
            Takes the phase of each value.
            <processing> can be None, 'unwrap' (unwrap phase), or 'remove_linear' (unwrap, then
            remove linear phase).

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


quick(parameter[, parameter...])
--------------------------------

Quick plotting of some parameters, indicated either as an integer (e.g. 21 to plot S21), or by
a tuple (e.g. (2,1) to plot S21.). For example, to plot S21 and S22, call <quick(21, 22)>.


nws(pattern)
------------

Returns a Networks object that contains all networks that match the given pattern, e.g. '*.s2p'. Note that
this returns an empty Networks object if the pattern does not match anything.


sel_nws(pattern)
----------------

same as nws(), except that it only matches networks that are currently selected.


nw(pattern)
-----------

same as nws(), except that it raises an error if not exactly one network is matched.


Examples
========

Basic
-----

    nws().s(1,1).plot("RL")
    sel_nws().s(1,2).plot("Reverse IL")
    nws("amp.s2p").s(2,1).plot("IL")
    nw("amp.s2p").s(1,1).plot("RL",":")

Advanced
--------

    # calculate directivity (S42/S32) of a directional coupler
    # note that this example requires plotting in linear units, as the values are already converted to dB
    (nw("coupler_4port.s4p").s(4,2).db() - nw("coupler_4port.s4p").s(3,2).db()).plot("Directivity")

    # de-embed a 2xTHRU
    (nw("thru.s2p").half(side=1).invert() ** nw("atty_10db.s2p") ** nw("thru.s2p").half(side=2).flip()).s(2,1).plot("De-embedded")

    # crop frequency range; this can be handy e.g. if you want to see the Smith-chart only for a specific frequency range
    nws("amp.s2p").crop_f(10e9,11e9).s(1,1).plot("RL",":")

    # calculate stability factor
    nws("amp.s2p").mu().plot("µ Stability Factor",":")

    # add elements to a network (in this case, a parallel cap, followed by a short transmission line)
    nws("amp.s2p").s(1,1).plot("Baseline",":")
    nws("amp.s2p").add_pc(400e-15).add_tl(7,2e9,25).s(1,1).plot("Optimized","-")

    # Compare S21 of all available networks to the currently selected one
    (nws().s(2,1) / sel_nws().s(2,1)).plot()
'''
