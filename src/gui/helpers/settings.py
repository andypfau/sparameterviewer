from lib import AppSettings
import logging
import enum



class PlotType(enum.Enum):
    Cartesian = 0
    Smith = 1
    Polar = 2

class YQuantity(enum.Enum):
    Off = 0
    Decibels = 1
    Magnitude = 2
    Real = 3
    Imag = 4
    RealImag = 5
    Phase = 6
    GroupDelay = 7

class PhaseProcessing(enum.Enum):
    Off = 0
    Unwrap = 1
    UnwrapDetrend = 2
    
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

class ColorAssignment(enum.StrEnum):
    Default = 'default'
    ByParam = 'param'
    ByFile = 'file'
    ByFileLoc = 'file-container'


class Parameters(enum.IntFlag):
    Off = 0
    S11 = 1
    S22 = 2
    Sii = 4  # this is NOT a combination of S11 and S22, because then e.g. S33, S44 would be ignored!
    S21 = 8  # all Sij with i>j
    S12 = 16  # all Sij with i<j
    ComboSij = 8+16
    ComboAll = 4+8+16
    Custom = 32
    Expressions = 64



class SParamViewerAppSettings(AppSettings):
    plotted_params: Parameters = Parameters.ComboAll
    plot_type: PlotType = PlotType.Cartesian
    plot_y_quantitiy: YQuantity = YQuantity.Decibels
    plot_y2_quantitiy: YQuantity = YQuantity.Off
    plot_tdr: bool = False
    tdr_step_response: bool = False
    smith_y: bool = False
    phase_processing: PhaseProcessing = PhaseProcessing.Off
    show_legend: bool = True
    hide_single_item_legend: bool = True
    shorten_legend_items: bool = True
    log_x: bool = False
    log_y: bool = False
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
    path_history: list[str] = []
    comment_existing_expr: bool = True
    editor_font: str = ''
    csv_separator: CsvSeparator = CsvSeparator.Semicolon
    search_regex: bool = False
    last_search: str = ''
    last_dir_filedialog: str = ''
    last_dir_dirdialog: str = ''
    cursor_snap: CursorSnap = CursorSnap.Point
    warncount_file_list: int = 1_000
    warncount_file_load: int = 30
    color_assignment: ColorAssignment = ColorAssignment.ByFile
    wide_layout: bool = False
    paramgrid_min_size: int = 2
    paramgrid_max_size: int = 4


Settings = SParamViewerAppSettings(format_version_str='0.15')
