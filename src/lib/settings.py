from .appsettings import AppSettings
import logging
import enum



class PlotType(enum.StrEnum):
    Cartesian = 'cartesian'
    TimeDomain = 'timedomain'
    Smith = 'smith'
    Polar = 'polar'

class SmithNorm(enum.StrEnum):
    Impedance = 'impedance'
    Admittance = 'admittance'

class TdResponse(enum.StrEnum):
    ImpulseResponse = 'impulse'
    StepResponse = 'step'

class YQuantity(enum.StrEnum):
    Off = 'none'
    Decibels = 'db'
    Magnitude = ''
    Real = 'real'
    Imag = 'imag'
    RealImag = 'real+imag'
    Phase = 'phase'
    GroupDelay = 'groupdelay'

class PhaseProcessing(enum.StrEnum):
    Off = 'none'
    Unwrap = 'unwrap'
    UnwrapDetrend = 'unwrap+detrend'
    
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
    Monochrome = 'monochrome'

class Parameters(enum.IntFlag):
    Off = 0
    S11 = 1
    S22 = 2
    Sii = 4  # this is NOT a combination of S11 and S22, because then e.g. S33, S44 would be ignored!
    S21 = 8  # all Sij with i>j
    S12 = 16  # all Sij with i<j
    ComboSij = 8+16
    ComboSii21 = 4+8
    ComboAll = 4+8+16
    Custom = 32

class LogNegativeHandling(enum.StrEnum):
    Abs = 'abs'
    Ignore = 'ignore'
    Fail = 'fail'

class MainWindowLayout(enum.StrEnum):
    Vertical = 'vertical'
    Wide = 'wide'
    Ultrawide = 'ultrawide'

class LargeMatrixBehavior(enum.StrEnum):
    Clickable = 'clickable'
    Scrollable = 'scrollable'

class GuiColorScheme(enum.StrEnum):
    Default = 'default'
    Light = 'light'
    Dark = 'dark'

class LegendPos(enum.StrEnum):
    Auto = 'auto'
    TopLeft = 'topleft'
    Top = 'top'
    TopRight = 'topright'
    Left = 'left'
    Center = 'center'
    Right = 'right'
    BottomLeft = 'bottomleft'
    Bottom = 'bottom'
    BottomRight = 'bottomright'



class SParamViewerAppSettings(AppSettings):
    plotted_params: Parameters = Parameters.ComboAll
    plot_type: PlotType = PlotType.Cartesian
    plot_y_quantitiy: YQuantity = YQuantity.Decibels
    plot_y2_quantitiy: YQuantity = YQuantity.Off
    td_response = TdResponse = TdResponse.StepResponse
    smith_norm: SmithNorm = SmithNorm.Impedance
    phase_processing: PhaseProcessing = PhaseProcessing.Off
    show_legend: bool = True
    hide_single_item_legend: bool = True
    show_grid: bool = True
    shorten_legend_items: bool = True
    smart_db_scaling: bool = True
    log_x: bool = False
    log_y: bool = False
    plot_semitransparent: bool = False
    plot_semitransparent_opacity: float = 0.15
    max_legend_items: int = 25
    use_expressions: bool = False
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
    export_phase_unit: PhaseUnit = PhaseUnit.Degrees
    extract_zip: bool = True
    plot_mark_points: bool = False
    path_history: list[str] = []
    path_history_maxsize: int = 10
    exprfile_history: list[str] = []
    expression_scratchpad: str = ''
    last_paths: list[str] = []
    comment_existing_expr: bool = True
    editor_font: str = ''
    csv_separator: CsvSeparator = CsvSeparator.Semicolon
    search_regex: bool = False
    last_filter_dialog_str: str = ''
    last_select_dialog_str: str = ''
    last_dir_filedialog: str = ''
    last_dir_dirdialog: str = ''
    cursor_snap: CursorSnap = CursorSnap.Point
    warn_timeout_s: int = 10
    color_assignment: ColorAssignment = ColorAssignment.ByFile
    singlefile_individualcolor: bool = False
    mainwindow_layout: MainWindowLayout = MainWindowLayout.Wide
    treat_all_as_complex: bool = False
    verbose: bool = False
    logx_negative_handling: LogNegativeHandling = LogNegativeHandling.Ignore
    logy_negative_handling: LogNegativeHandling = LogNegativeHandling.Abs
    simplified_param_sel: bool = False
    simplified_plot_sel: bool = False
    simplified_browser: bool = False
    simplified_no_expressions: bool = False
    dynamic_template_references: bool = False
    large_matrix_behavior: LargeMatrixBehavior = LargeMatrixBehavior.Clickable
    select_file_to_check: bool = True
    gui_color_scheme: GuiColorScheme = GuiColorScheme.Default
    legend_position: LegendPos = LegendPos.Auto
    restore_window_geometry: bool = True
    last_screen_width: int = -1
    last_screen_height: int = -1
    main_win_width: int = -1
    main_win_height: int = -1
    main_win_splitter_pos: int = -1
    plot_cursor_readouts: bool = True
    log_to_file: bool = True



Settings = SParamViewerAppSettings(format_version_str='0.15')
