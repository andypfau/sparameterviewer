from lib import AppSettings

import logging


class SParamViewerAppSettings(AppSettings):
    plot_mode: int = 0
    plot_unit: int = 0
    show_legend: bool = True
    hide_single_item_legend: bool = True
    shorten_legend_items: bool = True
    log_freq: bool = False
    expression: str = ''
    window_type: str = 'kaiser'
    window_arg: float = 35.0
    tdr_shift: float = 100e-12
    log_level: int = logging.WARNING
    mainwin_geom: str = None


Settings = SParamViewerAppSettings(
    appname='apfau.de S-Parameter Viewer',
    author='apfau.de',
    version='0.13'
)
