from lib import AppSettings
import logging
import enum



class ParamMode(enum.StrEnum):
    All = 'all'
    AllFwd = 'all_fwd'
    IL = 'il'
    IlFwd = 'il_fwd'
    S21 = 's21'
    RL = 'rl'
    S11 = 's11'
    S22 = 's22'
    S33 = 's33'
    S44 = 's44'
    Expr = 'expr'

class PlotUnit(enum.StrEnum):
    Off = 'off'
    dB = 'db'
    LogMag = 'lin_mag'
    LinMag = 'log_mag'
    ReIm = 're_im'
    Real = 're'
    Imag = 'im'
    ReImPolar = 'polar'
    SmithY = 'smith_z'
    SmithZ = 'smith_y'
    Impulse = 'impulse'
    Step = 'step'

class PlotUnit2(enum.StrEnum):
    Off = 'off'
    Phase = 'phase'
    Unwrap = 'unwrap'
    LinRem = 'remove_linear'
    GDelay = 'groupdelay'

class PhaseUnit(enum.StrEnum):
    Degrees = 'deg'
    Radians = 'rad'

class CsvSeparator(enum.StrEnum):
    Tab = 'tab'
    Comma = 'comma'
    Semicolon = 'semicolon'

class CursorSnap(enum.StrEnum):
    X = 'x'
    Point = 'point'



class SParamViewerAppSettings(AppSettings):
    plot_mode: ParamMode = ParamMode.All
    plot_unit: PlotUnit = PlotUnit.dB
    plot_unit2: PlotUnit2 = PlotUnit2.Off
    show_legend: bool = True
    hide_single_item_legend: bool = True
    shorten_legend_items: bool = True
    log_freq: bool = False
    expression: str = '# click "Template" or "Help" to learn more about expressions...\nsel_nws().s().plot()'
    window_type: str = 'kaiser'
    window_arg: float = 35.0
    tdr_shift: float = 100e-12
    tdr_impedance: bool = False
    tdr_minsize: int = 1024*8
    log_level: int = logging.WARNING
    ext_editor_cmd: str = ''
    plot_style: str = 'bmh'
    phase_unit: PhaseUnit = PhaseUnit.Degrees
    extract_zip: bool = True
    plot_mark_points: bool = False
    last_directories: list[str] = []
    history_appends: bool = False
    comment_existing_expr: bool = True
    editor_font: str = ''
    csv_separator: CsvSeparator = CsvSeparator.Semicolon
    search_regex: bool = False
    last_dir_filedialog: str = ''
    last_dir_dirdialog: str = ''
    cursor_snap: CursorSnap = CursorSnap.Point
    show_filesys: bool = True
    filesys_doubleclick_appends: bool = False
    filesys_showfiles: bool = False
    search_count_first_warning: int = 1_000
    load_count_first_warning: int = 30


Settings = SParamViewerAppSettings(format_version_str='0.15')
