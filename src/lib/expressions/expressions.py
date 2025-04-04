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

    touched_files: list[SParamFile] = []

    @staticmethod
    def eval(code: str, \
        available_networks: "list[SParamFile]", \
        selected_networks: "list[SParamFile]", \
        plot_fn: "callable[np.ndarray,np.ndarray,complex,str,str]") -> "list[SParamFile]":
        
        SParam.plot_fn = plot_fn

        def select_networks(network_list: "list[SParamFile]", pattern: str, single: bool):
            nws = []
            if pattern is None and not single:
                nws = [nw for nw in network_list]
            else:
                for nw in network_list:
                    if pattern is None or fnmatch.fnmatch(nw.filename, pattern):
                        nws.append(nw)
            if single:
                if len(nws) != 1:
                    #raise RuntimeError(f'The pattern "{pattern}" matched {len(nws)} networks, but need exactly one')
                    logging.warning(f'The pattern "{pattern}" matched {len(nws)} networks, but need exactly one')
                    nws = []
            for nw in nws:
                if nws not in ExpressionParser.touched_files:
                    ExpressionParser.touched_files.append(nw)
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
