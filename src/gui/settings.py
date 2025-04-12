from lib import AppSettings
import logging
import enum



class ParamMode(enum.IntEnum):
    All = 0
    AllFwd = 1
    IL = 2
    IlFwd = 3
    S21 = 4
    RL = 5
    S11 = 6
    S22 = 7
    S33 = 8
    S44 = 9
    Expr = 10

class PlotUnit(enum.IntEnum):
    Off = 0
    dB = 1
    LogMag = 2
    LinMag = 3
    ReIm = 4
    Real = 5
    Imag = 6
    ReImPolar = 7
    SmithY = 8
    SmithZ = 9
    Impulse = 10
    Step = 11

class PlotUnit2(enum.IntEnum):
    Off = 0
    Phase = 1
    Unwrap = 2
    LinRem = 3
    GDelay = 4



class SParamViewerAppSettings(AppSettings):
    plot_mode: ParamMode = ParamMode.All
    plot_unit: PlotUnit = PlotUnit.dB
    plot_unit2: PlotUnit2 = PlotUnit2.Off
    show_legend: bool = True
    hide_single_item_legend: bool = True
    shorten_legend_items: bool = True
    log_freq: bool = False
    expression: str = ''
    window_type: str = 'kaiser'
    window_arg: float = 35.0
    tdr_shift: float = 100e-12
    tdr_impedance: bool = False
    tdr_minsize: int = 1024*8
    log_level: int = logging.WARNING
    ext_editor_cmd: str = ''
    plot_style: str = 'bmh'
    phase_unit: str = 'deg'
    extract_zip: bool = False
    plot_mark_points: bool = False
    last_directories: list[str] = []
    comment_existing_expr: bool = True
    editor_font: str = ''
    csv_separator: str = ';'
    search_regex: bool = False


Settings = SParamViewerAppSettings(format_version_str='0.15')
