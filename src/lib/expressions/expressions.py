from ..sparam_file import SParamFile, PathExt
from ..bodefano import BodeFano
from ..stabcircle import StabilityCircle
from ..sparam_helpers import parse_quick_param
from .networks import Networks
from .sparams import SParam, SParams
from .helpers import DefaultAction

import math
import numpy as np
import fnmatch
import logging
import dataclasses


class ExpressionParser:

    
    @dataclasses.dataclass
    class Result:
        default_actions_used: bool


    @staticmethod
    def eval(code: str,
        available_networks: "list[SParamFile]",
        selected_networks: "list[SParamFile]",
        default_actions: "list[DefaultAction]",
        ref_nw_name: "str|None",
        plot_fn: "callable[np.ndarray,np.ndarray,complex,str,str,str,float,float,PathExt,str]"):

        SParam._plot_fn = plot_fn
        Networks.default_actions = default_actions

        def select_networks(network_list: "list[SParamFile]", pattern: str, single: bool):
            nws = []
            if pattern is None and not single:
                nws = [nw for nw in network_list]
            else:
                for nw in network_list:
                    if pattern is None or fnmatch.fnmatch(nw.path.final_name, pattern):
                        nws.append(nw)
            if single:
                if len(nws) != 1:
                    logging.warning(f'The pattern "{pattern}" matched {len(nws)} networks, but need exactly one')
                    nws = []
            else:
                if pattern is not None:
                    if len(nws) == 0:
                        logging.info(f'The pattern "{pattern}" didn\'t match any networks; returning empty Networks object)')
            return Networks(nws)
        
        def sel_nws(pattern: str = None) -> Networks:
            return select_networks(selected_networks, pattern, single=False)
        
        def nws(pattern: str = None) -> Networks:
            return select_networks(available_networks, pattern, single=False)
        
        def nw(pattern: str) -> Networks:
            return select_networks(available_networks, pattern, single=True)

        def saved_nw() -> Networks:
            if ref_nw_name is None:
                logging.warning(f'saved_nw(): no network was saved for this purpose; returning empty object')
                return Networks([]) 
            return select_networks(available_networks, ref_nw_name, single=True)

        def quick(*items):
            for (e,i) in [parse_quick_param(item) for item in items]:
                try:
                    sel_nws().s(e,i).plot()
                except Exception as ex:
                    logging.error(f'Unable to plot "S{e},{i}" ({ex})')

        vars_global = {}
        vars_local = {
            'Networks': Networks,
            'SParams': SParams,
            'nw': nw,
            'saved_nw': saved_nw,
            'nws': nws,
            'sel_nws': sel_nws,
            'quick': quick,
            'math': math,
            'np': np,
        }
        
        Networks.default_actions_used = False
        exec(code, vars_global, vars_local)

        return ExpressionParser.Result(Networks.default_actions_used)
