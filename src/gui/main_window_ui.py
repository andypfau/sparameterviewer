from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import pathlib
import enum
import logging
import os



class MyNavigationToolbar(NavigationToolbar2QT):
    toolitems = [toolitem for toolitem in NavigationToolbar2QT.toolitems if toolitem[0] in ('Home', 'Pan', 'Zoom')]


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class Mode(enum.IntEnum):
    All = 0
    AllFwd = 1
    IL = 2
    IlFwd = 3
    S21 = 4
    S12 = 5
    RL = 6
    S11 = 7
    S22 = 8
    S33 = 9
    S44 = 10

MODE_NAMES = {
    Mode.All: 'All S-Parameters',
    Mode.AllFwd: 'All S-Parameters (reciprocal)',
    Mode.IL: 'Insertion Loss',
    Mode.IlFwd: 'Insertion Loss (reciprocal)',
    Mode.S21: 'S21',
    Mode.S12: 'S12',
    Mode.RL: 'Return Loss',
    Mode.S11: 'S11',
    Mode.S22: 'S22',
    Mode.S33: 'S33',
    Mode.S44: 'S44',
}


class Unit(enum.IntEnum):
    Off = 0
    dB = 1
    LinMag = 2
    LogMag = 3

UNIT_NAMES = {
    Unit.Off: ' ',
    Unit.dB: 'dB',
    Unit.LinMag: 'Lin Mag',
    Unit.LogMag: 'Log Mag',
}


class Unit2(enum.IntEnum):
    Off = 0
    Phase = 1

UNIT2_NAMES = {
    Unit2.Off: ' ',
    Unit2.Phase: 'Phase',
}


class MainWindowUi(QMainWindow):

    def __init__(self):
        super().__init__()

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
            self.mode_combo.addItem(MODE_NAMES[mode.value])
        self.mode_combo.currentIndexChanged.connect(self.on_select_mode)
        for unit in Unit:
            self.unit_combo.addItem(UNIT_NAMES[unit.value])
        self.unit_combo.currentIndexChanged.connect(self.on_select_unit)
        for unit2 in Unit2:
            self.unit2_combo.addItem(UNIT2_NAMES[unit2.value])
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

        def add_submenu(menu, text):
            submenu = QMenu(text, self)
            menu.addMenu(submenu)
            return submenu

        def add_item(menu, text, action):
            item = QAction(text)
            item.triggered.connect(action)
            menu.addAction(item)
            return item
        
        self.mainmenu_file = add_submenu(self.menu_bar, '&File')
        self.menuitem_open_dir = add_item(self.mainmenu_file, 'Open Directory...', self.on_open_directory)
        self.menuitem_append_dir = add_item(self.mainmenu_file, 'Append Directory...', self.on_append_directory)
        self.menuitem_reload_all_files = add_item(self.mainmenu_file, 'Reload All Files', self.on_reload_all_files)
        self.mainmenu_file.addSeparator()
        self.menuitem_exit = add_item(self.mainmenu_file, 'Exit', self.close)
    

    def _build_template_menu(self):
        self.template_menu = QMenu()
        self.template1 = self.template_menu.addAction('Example 1')
        self.template_submenu1 = QMenu('More Examples')
        self.template_menu.addMenu(self.template_submenu1)
        self.template2 = self.template_submenu1.addAction('Example 2')


    def update_window_title(self, title: str):
        self.setWindowTitle(title)


    def add_fileview_item(self, path, contents=''):
        self.fileview_root.appendRow([QtGui.QStandardItem(pathlib.Path(path).name), QtGui.QStandardItem(contents)])


    def get_selected_file_indices(self) -> list[int]:
        sel = self.fileview.selectionModel().selectedIndexes()
        if not sel:
            return []
        return list(set([item.row() for item in sel]))


    def update_files_history(self, paths: list[str]):

        def make_loader_closure(dir):
            def load():
                if not os.path.exists(dir):
                    logging.error(f'Cannot load recent directory <{dir}> (does not exist any more)')
                    return
                absdir = os.path.abspath(dir)
                self.directories = [absdir]
                self.clear_loaded_files()
                self.load_files_in_directory(absdir)
                self.update_file_list(only_select_first=True)
                self.add_to_most_recent_directories(dir)
            return load

        logging.error('update_files_history not implemented')



    def on_select_mode(self):
        raise NotImplementedError()

    def on_select_unit(self):
        raise NotImplementedError()
    
    def on_select_unit2(self):
        raise NotImplementedError()
    
    def on_select_file(self):
        raise NotImplementedError()
    
    def on_open_directory(self):
        raise NotImplementedError()
    
    def on_append_directory(self):
        raise NotImplementedError()
    
    def on_reload_all_files(self):
        raise NotImplementedError()
    
    def on_load_history_item(self, path: str):
        raise NotImplementedError()
