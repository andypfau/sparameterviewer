from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import pathlib
import enum



class MyNavigationToolbar(NavigationToolbar2QT):
    toolitems = [toolitem for toolitem in NavigationToolbar2QT.toolitems if toolitem[0] in ('Home', 'Pan', 'Zoom')]


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class Mode(enum.StrEnum):
    All = 'All S-Parameters'
    AllFwd = 'All S-Parameters (reciprocal)'
    IlFwd = 'Insertion Loss (reciprocal)'
    S21 = 'S21'
    S12 = 'S12'
    RL = 'Return Loss'
    S11 = 'S11'
    S22 = 'S22'
    S33 = 'S33'
    S44 = 'S44'

class Unit(enum.StrEnum):
    Off = ' '
    dB = 'dB'
    LinMag = 'Lin Mag'
    LogMag = 'Log Mag'

class Unit2(enum.StrEnum):
    Off = ' '
    Phase = 'Phase'


class MainWindowUi(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('S-Parameter Viewer')

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(splitter)
        self._build_main_menu()

        plot_layout = QVBoxLayout()
        self.plot = MplCanvas(self, width=5, height=4, dpi=100)
        plot_layout.addWidget(self.plot)
        plot_toolbar = MyNavigationToolbar(self.plot, self)
        plot_layout.addWidget(plot_toolbar)
        plot_layout_widget = QWidget()
        plot_layout_widget.setLayout(plot_layout)
        plot_layout_widget.setMinimumSize(200, 150)
        splitter.addWidget(plot_layout_widget)
        
        bottom_widget = QWidget()
        bottom_widget_layout = QVBoxLayout()
        bottom_widget.setLayout(bottom_widget_layout)
        splitter.addWidget(bottom_widget)

        self.mode_combo = QComboBox()
        self.unit_combo = QComboBox()
        self.unit2_combo = QComboBox()
        combo_layout = QHBoxLayout()
        combo_layout_widget = QWidget()
        combo_layout_widget.setLayout(combo_layout)
        combo_layout.addWidget(self.mode_combo)
        combo_layout.addWidget(self.unit_combo)
        combo_layout.addWidget(self.unit2_combo)
        bottom_widget_layout.addWidget(combo_layout_widget)
        for mode in Mode:
            self.mode_combo.addItem(mode.value)
        self.mode_combo.currentIndexChanged.connect(self.on_select_mode)
        for unit in Unit:
            self.unit_combo.addItem(unit.value)
        self.unit_combo.currentIndexChanged.connect(self.on_select_unit)
        for unit2 in Unit2:
            self.unit2_combo.addItem(unit2.value)
        self.unit2_combo.currentIndexChanged.connect(self.on_select_unit2)
        
        tabs = QTabWidget()
        bottom_widget_layout.addWidget(tabs)
        
        files_tab = QWidget()
        tabs.addTab(files_tab, 'Files')
        expressions_tab = QWidget()
        tabs.addTab(expressions_tab, 'Expressions')

        self.fileview = QTreeView()
        filesview_layout = QVBoxLayout()
        filesview_layout.addWidget(self.fileview)
        files_tab.setLayout(filesview_layout)
        self.filemodel = QStandardItemModel()
        self.filemodel.setHorizontalHeaderLabels(['File', 'Properties'])
        self.fileview_root = self.filemodel.invisibleRootItem()
        self.fileview.setModel(self.filemodel)
        self.fileview.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.fileview.selectionModel().selectionChanged.connect(self.on_select_file)
        
        expressions_layout = QHBoxLayout()
        exprbuttons_layout = QVBoxLayout()
        expressions_layout.addLayout(exprbuttons_layout)
        self.editor = QPlainTextEdit()
        self.template_button = QPushButton('Template...')
        exprbuttons_layout.addWidget(self.template_button)
        exprbuttons_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        editor_font = QFont()
        editor_font.setFamilies(['Fira Code', 'Consolas', 'Courier New', 'monospace'])
        self.editor.setFont(editor_font)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.editor)
        expressions_layout.addLayout(editor_layout)
        expressions_tab.setLayout(expressions_layout)

        def on_template_button():
            button_pos = self.template_button.mapToGlobal(QPoint(0, self.template_button.height()))
            self.template_menu.popup(button_pos)
        self.template_button.clicked.connect(on_template_button)
        self._build_template_menu()

        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
    

    def _build_main_menu(self):
        self.menu_bar = self.menuBar()
        file_menu = QMenu("&File", self)
        self.menu_bar.addMenu(file_menu)
        self.menuaction_exit = QAction('Exit')
        self.menuaction_exit.triggered.connect(self.on_exit)
        file_menu.addAction(self.menuaction_exit)
    

    def _build_template_menu(self):
        self.template_menu = QMenu()
        self.template1 = self.template_menu.addAction('Example 1')
        self.template_submenu1 = QMenu('More Examples')
        self.template_menu.addMenu(self.template_submenu1)
        self.template2 = self.template_submenu1.addAction('Example 2')


    def add_fileview_item(self, path, contents=''):
        self.fileview_root.appendRow([QtGui.QStandardItem(pathlib.Path(path).name), QtGui.QStandardItem(contents)])

    def get_selected_file_indices(self) -> list[int]:
        sel = self.fileview.selectionModel().selectedIndexes()
        if not sel:
            return []
        return list(set([item.row() for item in sel]))
        

    def on_select_mode(self):
        raise NotImplementedError()

    def on_select_unit(self):
        raise NotImplementedError()
    
    def on_select_unit2(self):
        raise NotImplementedError()
    
    def on_select_file(self):
        raise NotImplementedError()
