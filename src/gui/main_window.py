#!/bin/python3

from tkinter import *
from tkinter import filedialog, messagebox, simpledialog, ttk

import os, glob, appdirs, math, copy, logging, traceback, datetime, io
import numpy as np
import re
import cmath
import zipfile

import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from lib.si import SiFmt
import scipy.signal

from .main_window_pygubuui import PygubuAppUI
from .info_dialog import SparamviewerInfoDialog
from .rl_dialog import SparamviewerReturnlossDialog
from .cursor_dialog import SparamviewerCursorDialog
from .log_dialog import SparamviewerLogDialog
from .log_handler import LogHandler
from .settings_dialog import SparamviewerSettingsDialog
from .axes_dialog import SparamviewerAxesDialog
from .settings import Settings
from .tabular_dialog import TabularDialog, TabularDataset, TabularDatasetSFile, TabularDatasetPlot
from info import Info

from lib import Clipboard
from lib import open_file_in_default_viewer
from lib import sparam_to_timedomain, get_sparam_name
from lib import Si
from lib import SParamFile, PlotHelper
from lib import ExpressionParser
from lib import TkText, TkCommon, AppGlobal



MAX_DIRECTORY_HISTORY_SIZE = 10



# extend auto-generated UI code
class SparamviewerMainDialog(PygubuAppUI):
    def __init__(self, filenames: "list[str]"):
        super().__init__()

        try:
            self.directories = [] # type: list[str]
            self.next_file_tag = 1
            self.files: list[SParamFile]
            self.files = []
            self.generated_expressions = ''
            self.plot_mouse_down = False
            self.cursor_dialog = None # type: SparamviewerCursorDialog
            self.plot_axes_are_valid = False
            self.lock_xaxis = False
            self.lock_yaxis = False

            # init UI
            AppGlobal.set_toplevel_icon(self.toplevel_main)
            TkCommon.default_keyhandler(self.toplevel_main, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(**kwargs))
            TkText.default_keyhandler(self.text_expr, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(**kwargs))
            self.show_legend.set('1' if Settings.show_legend else '0')
            self.hide_single_legend.set('1' if Settings.hide_single_item_legend else '0')
            self.short_legend.set('1' if Settings.shorten_legend_items else '0')
            self.logf.set('1' if Settings.log_freq else '0')
            self.lock_plot_xaxis.set('1' if self.lock_xaxis else '0')
            self.lock_plot_yaxis.set('1' if self.lock_yaxis else '0')
            self.plot_mark_points.set('1' if Settings.plot_mark_points else '0')
            self.combobox_mode['values']= (
                'All S-Params',
                'All S-Params (reciprocal/1st IL only)',
                'Insertion Loss',
                'Insertion Loss (reciprocal/1st only)',
                'Insertion Loss S21',
                'Return Loss / Impedance',
                'Return Loss S11',
                'Return Loss S22',
                'Return Loss S33',
                'Return Loss S44',
                'Expression-Based',
            )
            self.MODE_ALL = 0
            self.MODE_ALL_RECIPROCAL = 1
            self.MODE_IL_ALL = 2
            self.MODE_IL_RECIPROCAL = 3
            self.MODE_S21 = 4
            self.MODE_RL = 5
            self.MODE_S11 = 6
            self.MODE_S22 = 7
            self.MODE_S33 = 8
            self.MODE_S44 = 9
            self.MODE_EXPR = 10
            self.combobox_mode.current(Settings.plot_mode)
            self.combobox_unit['values']= (
                ' ',
                'dB',
                'Log. Magnitude',
                'Linear Magnitude',
                'Re/Im vs. Freq.',
                'Re vs. Freq.',
                'Im vs. Freq.',
                'Re/Im Polar',
                'Smith (Impedance)',
                'Smith (Admittance)',
                'Impulse Response',
                'Step Response',
            )
            self.UNIT_NONE = 0
            self.UNIT_DB = 1
            self.UNIT_LOG_MAG = 2
            self.UNIT_LIN_MAG = 3
            self.UNIT_RE_IM_VS_F = 4
            self.UNIT_RE_VS_F = 5
            self.UNIT_IM_VS_F = 6
            self.UNIT_RE_IM_POLAR = 7
            self.UNIT_SMITH_Z = 8
            self.UNIT_SMITH_Y = 9
            self.UNIT_IMPULSE = 10
            self.UNIT_STEP = 11
            self.combobox_unit.current(Settings.plot_unit)
            self.combobox_unit2['values']= (
                ' ',
                'Phase',
                'Unwrapped Phase',
                'Linear Phase Removed',
                'Group Delay',
            )
            self.UNIT2_NONE = 0
            self.UNIT2_PHASE = 1
            self.UNIT2_PHASE_UNWRAP = 2
            self.UNIT2_PHASE_REMLIN = 3
            self.UNIT2_GROUP_DELAY = 4
            self.combobox_unit2.current(Settings.plot_unit2)
            TkText.set_text(self.text_expr, Settings.expression.strip())
            def on_click_errors(event):
                self.open_error_dialog()
            self.entry_err.bind('<Button-1>', on_click_errors)
            self.update_most_recent_directories_menu()

            # load TTK theme
            try:
                style = ttk.Style(self.toplevel_main)
                style.theme_use(Settings.ttk_theme)
            except: pass

            # register event
            def on_generate_button_click(event):
                self.on_gen_expr(event)
            self.button_gen_expr.bind("<1>", on_generate_button_click)

            # remember window size
            if Settings.mainwin_geom is not None:
                try:
                    self.mainwindow.geometry(Settings.mainwin_geom)
                except:
                    Settings.mainwin_geom = None
            def save_window_size(event):
                Settings.mainwin_geom = self.mainwindow.geometry()
            self.mainwindow.bind("<Configure>", save_window_size)
            
            # fix treeview
            self.treeview_files['columns'] = ('filename', 'props')
            self.treeview_files.heading('filename', text='File')
            self.treeview_files.heading('props', text='Properties')
            self.treeview_files['show'] = 'headings'

            self.toplevel_main.title(Info.AppName)

            # create plot
            try:
                pyplot.style.use(Settings.plot_style if Settings.plot_style is not None else 'bmh')
                self.plot = None # type: PlotHelper
                self.fig = Figure()
                panel = self.frame_plot
                self.canvas = FigureCanvasTkAgg(self.fig, master=panel)  
                self.canvas.draw()
                toolbar = NavigationToolbar2Tk(self.canvas, panel)
                toolbar.update()
                self.canvas.get_tk_widget().pack(expand=True, fill='both')

                def callback_click(event):
                    if event.button and event.xdata and event.ydata:
                        self.on_plot_mouse_down(event.button, event.xdata, event.ydata)
                def callback_release(event):
                    if event.button:
                        self.on_plot_mouse_up(event.button)
                def callback_move(event):
                    if event.xdata and event.ydata:
                        self.on_plot_mouse_move(event.xdata, event.ydata)
                self.fig.canvas.callbacks.connect('button_press_event', callback_click)
                self.fig.canvas.callbacks.connect('button_release_event', callback_release)
                self.fig.canvas.callbacks.connect('motion_notify_event', callback_move)

            except Exception as ex:
                logging.exception(f'Unable to init plots: {ex}')

            self.initially_load_files_or_directory(filenames)
            self.update_plot()
        
        except Exception as ex:
            Settings.reset()
            logging.exception(f'Unable to init main dialog: {ex}')
            messagebox.showerror('Error', f'Error ({ex}); maybe corrupted config... reset, try again next time')
    

    def on_check_for_global_keystrokes(self, key, ctrl, alt, **kwargs):
        no_mod = not ctrl and not alt
        ctrl_only = ctrl and not alt
        if key=='F1' and no_mod:
            self.on_menu_help()
            return 'break'
        if key=='F3' and no_mod:
            self.on_cursor_cmd()
            return 'break'
        if key=='F5' and no_mod:
            self.on_use_expr()
            return 'break'
        if key=='F5' and ctrl_only:
            self.on_reload_all_files()
            return 'break'
        if key=='o' and ctrl_only:
            self.on_open_dir()
            return 'break'
        if key=='s' and ctrl_only:
            self.on_save_expr()
            return 'break'
        if key=='l' and ctrl_only:
            self.on_load_expr()
            return 'break'
        if key=='t' and ctrl_only:
            self.on_view_tabular()
            return 'break'
        if key=='e' and ctrl_only:
            self.on_click_open_externally()
            return 'break'
        if key=='i' and ctrl_only:
            self.on_click_info()
            return 'break'
        return


    def on_plot_mouse_down(self, button: int, x: float, y: float):
        if button == 1:
            self.plot_mouse_down = True
            self.update_cursors(left_btn_pressed=True, left_btn_event=True, x=x, y=y)
        
 
    def on_plot_mouse_up(self, button: int):
        if button == 1:
            self.plot_mouse_down = False
            self.update_cursors(left_btn_pressed = False, left_btn_event=True)
        
 
    def on_plot_mouse_move(self, x: float, y: float):
        if self.plot_mouse_down:
            self.update_cursors(left_btn_pressed=True, x=x, y=y)


    def update_cursors(self, left_btn_pressed: bool = False, left_btn_event: bool = False, x: "float|None" = None, y: "float|None" = None):

        if not self.cursor_dialog:
            self.plot.cursors[0].enable(False)
            self.plot.cursors[1].enable(False)
            self.canvas.draw()
            return

        self.plot.cursors[0].enable(self.cursor_dialog.enable_cursor_1)
        self.plot.cursors[1].enable(self.cursor_dialog.enable_cursor_2)
        
        if left_btn_pressed:

            # find out which cursor to move
            if self.cursor_dialog.auto_select_cursor and left_btn_event:
                target_cursor_index, _ = self.plot.get_closest_cursor(x, y)
                if target_cursor_index is not None:
                    self.cursor_dialog.set_cursor(target_cursor_index)
            else:
                target_cursor_index = self.cursor_dialog.selected_cursor_idx
            
            # move the cursor
            if target_cursor_index is not None:

                if self.cursor_dialog.auto_select_trace:
                    plot, x, y, z = self.plot.get_closest_plot_point(x, y)
                    if plot is not None:
                        self.cursor_dialog.set_trace(target_cursor_index, plot.name)
                else:
                    selected_trace_name = self.cursor_dialog.selected_trace_name_1 if target_cursor_index == 0 else self.cursor_dialog.selected_trace_name_2
                    if selected_trace_name is not None:
                        plot, x, y, z = self.plot.get_closest_plot_point(x, y, name=selected_trace_name)
                    else:
                        plot, x, y, z = None, None, None, None

                if plot is not None:
                    target_cursor = self.plot.cursors[target_cursor_index]
                    target_cursor.set(x, y, z, enable=True, color=plot.color)
                    
                sync_x = self.cursor_dialog.var_sync_x.get() == 'sync'
                if sync_x:
                    other_trace_name = self.cursor_dialog.selected_trace_name_2 if target_cursor_index == 0 else self.cursor_dialog.selected_trace_name_1
                    other_plot, x, y, z = self.plot.get_closest_plot_point(x, y, name=other_trace_name)
                    if other_plot is not None:
                        other_cursor_index = 1 - target_cursor_index
                        other_cursor = self.plot.cursors[other_cursor_index]
                        other_cursor.set(x, y, z, enable=True, color=other_plot.color)
        
        readout = ''
        xf = copy.copy(self.plot.x_fmt)
        yf = copy.copy(self.plot.y_fmt)
        zf = copy.copy(self.plot.z_fmt)
        xf.significant_digits += 3
        yf.significant_digits += 3
        if zf is not None:
            zf.significant_digits += 1
        if self.cursor_dialog.enable_cursor_1:
            x,y,z = self.plot.cursors[0].x, self.plot.cursors[0].y, self.plot.cursors[0].z
            readout += f'Cursor 1: '
            if z is not None:
                readout += f'{Si(z,si_fmt=zf)} | '
            readout += f'{Si(x,si_fmt=xf)} | {Si(y,si_fmt=yf)}\n'
        if self.cursor_dialog.enable_cursor_2:
            x,y,z = self.plot.cursors[1].x, self.plot.cursors[1].y, self.plot.cursors[1].z
            readout += f'Cursor 2: '
            if z is not None:
                readout += f'{Si(z,si_fmt=zf)} |'
            readout += f'{Si(x,si_fmt=xf)} | {Si(y,si_fmt=yf)}\n'
            if self.cursor_dialog.enable_cursor_1:
                dx = self.plot.cursors[1].x - self.plot.cursors[0].x
                dx_str = str(Si(dx,si_fmt=xf))
                if xf.unit=='s' and dx!=0:
                    dx_str += f' = {Si(1/dx,unit='Hz⁻¹')}'
                if yf.unit=='dB' or yf.unit=='°':
                    dy = self.plot.cursors[1].y - self.plot.cursors[0].y
                    readout += f'Delta X: {dx_str} | Delta Y:{Si(dy,si_fmt=yf)}\n'
                else:
                    dy = self.plot.cursors[1].y - self.plot.cursors[0].y
                    dys = Si.to_significant_digits(dy, 4)
                    if self.plot.cursors[0].y==0:
                        rys = 'N/A'
                    else:
                        ry = self.plot.cursors[1].y / self.plot.cursors[0].y
                        rys = Si.to_significant_digits(ry, 4)
                    readout += f'Delta X: {dx_str} | Delta Y: {dys}, Ratio Y: {rys}\n'
        self.cursor_dialog.update_readout(readout)
        
        self.canvas.draw()


    def on_cursor_cmd(self):

        if self.cursor_dialog:
            return # don't open a 2nd dialog
        
        def callback(dialog: SparamviewerCursorDialog) -> str:
            # note that we'll received a null argument when dialog is closed
            self.cursor_dialog = dialog
            self.update_cursors()
        
        SparamviewerCursorDialog(self.toplevel_main, self.plot.plots, callback)

    
    def on_select_file(self, event=None):
        self.update_plot()
    

    def on_select_plotmode(self, event=None):
        Settings.plot_mode = self.combobox_mode.current()
        self.update_plot()
    

    def on_select_plotunit(self, event=None):
        changed = Settings.plot_unit != self.combobox_unit.current()
        Settings.plot_unit = self.combobox_unit.current()
        if changed:
            Settings.save()

            # different kind of chart -> axes scale is probably no longer valid
            self.invalidate_axes_lock(update=False)

            # only allow phase in specific combinations
            if Settings.plot_unit not in [self.UNIT_NONE, self.UNIT_DB, self.UNIT_LIN_MAG, self.UNIT_LOG_MAG]:
                self.combobox_unit2.current(self.UNIT2_NONE)

        self.update_plot()
    

    def on_select_plotunit2(self, event=None):
        if Settings.plot_unit not in [self.UNIT_NONE, self.UNIT_DB, self.UNIT_LIN_MAG, self.UNIT_LOG_MAG]:
            self.combobox_unit2.current(self.UNIT2_NONE)
            return # no phase allowed

        changed = Settings.plot_unit2 != self.combobox_unit2.current()
        Settings.plot_unit2 = self.combobox_unit2.current()

        if changed:
            Settings.save()

            # different kind of chart -> axes scale is probably no longer valid
            self.invalidate_axes_lock(update=False)

        self.update_plot()
    

    def on_exit_cmd(self):
        self.toplevel_main.quit()

    
    def on_open_settings_click(self):
        def settings_callback():
            self.update_plot()
        SparamviewerSettingsDialog(self.toplevel_main, settings_callback)

    
    def on_use_expr(self):
        self.combobox_mode.current(self.MODE_EXPR)
        Settings.plot_mode = self.MODE_EXPR
        self.update_plot()


    def on_gen_expr(self, event):

        def selected_file_names():
            return [file.name for file in self.files if file.tag in self.treeview_files.selection()]

        def set_expression(*expressions):
            current = TkText.get_text(self.text_expr).strip()
            new = '\n'.join(expressions)
            for line in current.splitlines():
                if Settings.comment_existing_expr:
                    existing_line = '#' + line.strip() if not line.startswith('#') else line.strip()
                else:
                    existing_line = line
                if len(new)>0:
                    new += '\n'
                new += existing_line
            Settings.expression = new
            TkText.set_text(self.text_expr, new)
            self.on_use_expr()
        
        def switch_to_linear_scale():
            idx = self.combobox_unit['values'].index('Linear Magnitude')
            self.combobox_unit.current(idx)
            self.on_select_plotunit(None)
        
        def switch_to_logarithmic_scale():
            idx = self.combobox_unit['values'].index('dB')
            self.combobox_unit.current(idx)
            self.on_select_plotunit(None)
        
        def ensure_selected_file_count(op, n_required):
            n = len(selected_file_names())
            if op == '>=':
                if n < n_required:
                    messagebox.showinfo('Invalid operation', f'To use this template, select at least {n_required} file{"s" if n_required!=1 else ""}.')
                    return False
            elif op == '==':
                if n != n_required:
                    messagebox.showinfo('Invalid operation', f'To use this template, select exactly {n_required} file{"s" if n_required!=1 else ""}.')
                    return False
            else:
                raise ValueError()
            return True
        
        def as_currently_selected():
            if len(self.generated_expressions) < 1:
                messagebox.showinfo('Invalid operation', 'To use this template, select anything other than Expression-Based.')
                return
            set_expression(self.generated_expressions)
        
        def all_sparams():
            set_expression('sel_nws().s().plot()')
            switch_to_logarithmic_scale()
        
        def insertion_loss():
            set_expression('sel_nws().s(il_only=True).plot()')
            switch_to_logarithmic_scale()
        
        def insertion_loss_reciprocal():
            set_expression('sel_nws().s(fwd_il_only=True).plot()')
            switch_to_logarithmic_scale()
        
        def return_loss():
            set_expression('sel_nws().s(rl_only=True).plot()')
            switch_to_logarithmic_scale()
        
        def vswr():
            set_expression('sel_nws().s(rl_only=True).vswr().plot()')
            switch_to_linear_scale()
        
        def mismatch_loss():
            set_expression('sel_nws().s(rl_only=True).ml().plot()')
            switch_to_logarithmic_scale()

        def quick11():
            set_expression('quick(11)')
            switch_to_logarithmic_scale()
        
        def quick112122():
            set_expression('quick(11)', 'quick(21)', 'quick(22)')
            switch_to_logarithmic_scale()
        
        def quick11211222():
            set_expression('quick(11)', 'quick(21)', 'quick(12)', 'quick(22)')
            switch_to_logarithmic_scale()

        def quick112122313233():
            set_expression('quick(11)', 'quick(21)', 'quick(12)', 'quick(22)', 'quick(31)', 'quick(32)', 'quick(33)')
            switch_to_logarithmic_scale()
        
        def stability():
            set_expression('sel_nws().mu(1).plot() # should be > 1 for stable network',
                           'sel_nws().mu(2).plot() # should be > 1 for stable network')
            switch_to_linear_scale()
        
        def reciprocity():
            set_expression('sel_nws().reciprocity().plot() # should be 0 for reciprocal network')
            switch_to_linear_scale()
        
        def passivity():
            set_expression('sel_nws().passivity().plot() # should be <= 1 for passive network')
            switch_to_linear_scale()
        
        def losslessness():
            set_expression("sel_nws().losslessness('ii').plot() # should be 1 for lossless network",
                           "sel_nws().losslessness('ij').plot() # should be 0 for lossless network")
            switch_to_linear_scale()
        
        def cascade():
            if not ensure_selected_file_count('>=', 2):
                return
            nws = ' ** '.join([f'nw(\'{n}\')' for n in selected_file_names()])
            set_expression(f'({nws}).s(2,1).plot()')
        
        def deembed1from2():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"((nw('{n1}').invert()) ** nw('{n2}')).s(2,1).plot()")
        
        def deembed2from1():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"(nw('{n1}') ** (nw('{n2}').invert())).s(2,1).plot()")
        
        def deembed2from1flipped():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"(nw('{n1}') ** (nw('{n2}').flip().invert())).s(2,1).plot()")
        
        def deembed2xthru():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"((nw('{n1}').half(side=1)) ** nw('{n2}') **(nw('{n1}').half(side=2))).s(2,1).plot()")
        
        def ratio_of_two():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"(nw('{n1}').s(2,1)/nw('{n2}').s(2,1)).plot()")
        
        def mixed_mode():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').s2m(['p1','p2','n1','n2']).s('dd21').plot()" for n in selected_file_names()]
            set_expression(*expressions)

        def z_renorm():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').renorm([50,75]).s(2,1).plot()" for n in selected_file_names()]
            set_expression(*expressions)

        def add_tline():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').add_tl(degrees=360,frequency_hz=1e9,port=2).s(2,1).plot()" for n in selected_file_names()]
            set_expression(*expressions)
        
        def impedance():
            set_expression('sel_nws().s2z().s(rl_only=True).plot()')
            switch_to_linear_scale()
        
        def admittance():
            set_expression('sel_nws().s2y().s(rl_only=True).plot()')
            switch_to_linear_scale()

        def all_selected():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').s().plot()" for n in selected_file_names()]
            set_expression(*expressions)
        
        self.template_menu = Menu(self.toplevel_main, tearoff=False)
        self.template_menu.add_command(label='As Currently Selected', command=as_currently_selected)
        self.template_menu.add_separator()
        
        self.template_submenu_plotting = Menu(self.template_menu, tearoff=False)
        self.template_menu.add(CASCADE, menu=self.template_submenu_plotting, label='S-Parameters')
        self.template_submenu_plotting.add_command(label='All S-Parameters', command=all_sparams)
        self.template_submenu_plotting.add_command(label='Insertion Loss', command=insertion_loss)
        self.template_submenu_plotting.add_command(label='Insertion Loss (Reciprocal / 1st Only)', command=insertion_loss_reciprocal)
        self.template_submenu_plotting.add_command(label='Return Loss', command=return_loss)
        self.template_submenu_plotting.add_command(label='VSWR', command=vswr)
        self.template_submenu_plotting.add_command(label='Mismatch Loss', command=mismatch_loss)
        self.template_submenu_plotting.add_separator()
        self.template_submenu_plotting.add_command(label='S11', command=quick11)
        self.template_submenu_plotting.add_command(label='S11, S21, S22', command=quick112122)
        self.template_submenu_plotting.add_command(label='S11, S21, S12, S22', command=quick11211222)
        self.template_submenu_plotting.add_command(label='S11, S21, S22, S31, S32, S33', command=quick112122313233)
        self.template_submenu_plotting.add_separator()
        self.template_submenu_plotting.add_command(label='Impedance', command=impedance)
        self.template_submenu_plotting.add_command(label='Admittance', command=admittance)

        self.template_submenu_analysis = Menu(self.template_menu, tearoff=False)
        
        self.template_menu.add(CASCADE, menu=self.template_submenu_analysis, label='Network Analysis')
        self.template_submenu_analysis.add_command(label='Stability', command=stability)
        self.template_submenu_analysis.add_command(label='Reciprocity', command=reciprocity)
        self.template_submenu_analysis.add_command(label='Passivity', command=passivity)
        self.template_submenu_analysis.add_command(label='Losslessness', command=losslessness)

        self.template_submenu_templates = Menu(self.template_menu, tearoff=False)
        self.template_menu.add(CASCADE, menu=self.template_submenu_templates, label='Operations on Selected Networks')
        self.template_submenu_templates.add_command(label='Single-Ended to Mixed-Mode', command=mixed_mode)
        self.template_submenu_templates.add_command(label='Impedance Renormalization', command=z_renorm)
        self.template_submenu_templates.add_command(label='Add Line To Network', command=add_tline)
        self.template_submenu_templates.add_separator()
        self.template_submenu_templates.add_command(label='Just Plot All Selected Files', command=all_selected)
        
        self.template_submenu_2nw = Menu(self.template_menu, tearoff=False)
        self.template_menu.add(CASCADE, menu=self.template_submenu_2nw, label='Operations on Two Selected Networks')
        self.template_submenu_2nw.add_command(label='De-Embed First Network from Second', command=deembed1from2)
        self.template_submenu_2nw.add_command(label='De-Embed Second Network from First', command=deembed2from1)
        self.template_submenu_2nw.add_command(label='De-Embed Second (Flipped) Network from First', command=deembed2from1flipped)
        self.template_submenu_2nw.add_command(label='Treat First as 2xTHRU, De-Embed from Second', command=deembed2xthru)
        self.template_submenu_2nw.add_command(label='Ratio of Two Networks', command=ratio_of_two)
        
        self.template_submenu_nnw = Menu(self.template_menu, tearoff=False)
        self.template_menu.add(CASCADE, menu=self.template_submenu_nnw, label='Operations on Two or More Selected Networks')
        self.template_submenu_nnw.add_command(label='Cascade Selected Networks', command=cascade)
        
        # show poupu at cursor
        x, y = event.x_root, event.y_root
        self.template_menu.post(x, y)
    

    def on_menu_help(self):
        AppGlobal.show_help()


    def on_expr_help(self):
        AppGlobal.show_help('expressions.md')


    def on_load_expr(self):

        if len(TkText.get_text(self.text_expr).strip())>0:
            if not messagebox.askokcancel('Overwrite', 'Expressions are not empty and will be overwritten'):
                return

        try:
            fn = filedialog.askopenfilename(filetypes=(('Expressions','.py'),('Text','.txt'),('All Files','*')))
            if not fn:
                return
            with open(fn, 'r') as fp:
                py = fp.read()
            TkText.set_text(self.text_expr, py.strip())
        except Exception as ex:
            logging.exception(f'Loading expressions failed: {ex}')
            messagebox.showerror('Error', str(ex))


    def on_save_expr(self):
        try:
            py = TkText.get_text(self.text_expr)
            fn = filedialog.asksaveasfilename(confirmoverwrite=True, filetypes=[('Expressions','.py'),('Text','.txt'),('All Files','*')], defaultextension='.py')
            if not fn:
                return
            with open(fn, 'w') as fp:
                fp.write(py.strip())
        except Exception as ex:
            logging.exception(f'Saving expressions failed: {ex}')
            messagebox.showerror('Error', str(ex))


    def on_call_optrlcalc(self):

        selected_id = None
        if len(self.treeview_files.selection())>0:
            selected_id = self.treeview_files.selection()[0]

        SparamviewerReturnlossDialog(self.toplevel_main, self.files, selected_id)


    def get_info_str(self, sparam_file: SParamFile) -> str:
        
        f0, f1 = sparam_file.nw.f[0], sparam_file.nw.f[-1]
        n_pts = len(sparam_file.nw.f)
        _, fname = os.path.split(sparam_file.file_path)
        comm = '' if sparam_file.nw.comments is None else sparam_file.nw.comments
        n_ports = sparam_file.nw.s.shape[1]

        fileinfo = ''
        def fmt_tstamp(ts):
            return f'{datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M:%S}'
        if sparam_file.archive_path is not None:
            fileinfo += f'Archive path: {os.path.abspath(sparam_file.archive_path)}\n'
            try:
                created = fmt_tstamp(os.path.getctime(sparam_file.archive_path))
                fileinfo += f'Archive created: {created}, '
            except:
                fileinfo += f'Archive created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(sparam_file.archive_path))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(sparam_file.archive_path):,.0f} B'
                fileinfo += f'Archive size: {size}\n'
            except:
                fileinfo += f'Archive size: unknown\n'
            fileinfo += f'File path in archive: {sparam_file.file_path}\n'
        else:
            fileinfo += f'File path: {os.path.abspath(sparam_file.file_path)}\n'
            try:
                created = fmt_tstamp(os.path.getctime(sparam_file.file_path))
                fileinfo += f'File created: {created}, '
            except:
                fileinfo += f'File created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(sparam_file.file_path))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(sparam_file.file_path):,.0f} B'
                fileinfo += f'File size: {size}\n'
            except:
                fileinfo += f'File size: unknown\n'
        
        if (sparam_file.nw.z0 == sparam_file.nw.z0[0,0]).all():
            z0 = str(Si(sparam_file.nw.z0[0,0],'Ohm'))
        else:
            z0 = 'different for each port and/or frequency'
        
        info = f'{fname}\n'
        info += '-'*len(fname)+'\n\n'
        
        if len(comm)>0:
            for comm_line in comm.splitlines():
                info += comm_line.strip() + '\n'
            info += '\n'
        info += f'Ports: {n_ports}, reference impedance: {z0}\n'

        n_points_str = f'{n_pts:,.0f} point{"s" if n_pts!=0 else ""}'
        
        freq_steps = np.diff(sparam_file.nw.f)
        freq_equidistant = np.allclose(freq_steps,freq_steps[0])
        if freq_equidistant:
            freq_step = freq_steps[0]
            spacing_str =  f'{Si(freq_step,"Hz")} equidistant spacing'
        else:
            freq_arbitrary = True
            if np.all(sparam_file.nw.f != 0):
                freq_ratios = np.exp(np.diff(np.log(sparam_file.nw.f)))
                if np.allclose(freq_ratios,freq_ratios[0]):
                    freq_arbitrary = False
                    freq_step = np.mean(freq_steps)
                    freq_ratio = freq_ratios[0]
                    spacing_str = f'{freq_ratio:.4g}x logarithmic spacing, average spacing {Si(freq_step,"Hz")}'
            if freq_arbitrary:
                freq_step = np.mean(freq_steps)
                spacing_str =  f'non-equidistant spacing, average spacing {Si(freq_step,"Hz")}'
        
        info += f'Frequency range: {Si(f0,"Hz")} to {Si(f1,"Hz")}, {n_points_str}, {spacing_str}'
        info += '\n\n'

        info += fileinfo

        return info


    def on_click_info(self):
        info = ''
        for file in self.files:
            if file.tag in self.treeview_files.selection():
                if len(info)>0:
                    info+= '\n\n\n'
                info += self.get_info_str(file)
        
        if len(info)>0:
            dlg = SparamviewerInfoDialog(self.toplevel_main, title='File Info', text=info)
            dlg.run()
        else:
            messagebox.showerror(title='File Info', message='No file selected.')


    def on_click_open_externally(self):

        if not Settings.ext_editor_cmd:
            messagebox.showerror(title='Open File', message=f'No external editor specified. Please select one.')
            dialog_result = SparamviewerSettingsDialog.let_user_select_ext_editor()
            if not dialog_result:
                return

        files = []
        for file in self.files:
            if file.tag in self.treeview_files.selection():
                files.append(file.file_path)
        
        try:
            import subprocess
            subprocess.run([Settings.ext_editor_cmd, *files])
        except Exception as ex:
            messagebox.showerror(title='Open File', message=f'Unable to open file with external editor ({str(ex)}).')


    def on_show_legend(self):
        Settings.show_legend = (self.show_legend.get() == '1')
        self.update_plot()


    def on_change_logf(self):
        Settings.log_freq = (self.logf.get() == '1')
        self.update_plot()


    def on_hide_single_legend(self):
        Settings.hide_single_item_legend = (self.hide_single_legend.get() == '1')
        self.update_plot()


    def on_short_legend(self):
        Settings.shorten_legend_items = (self.short_legend.get() == '1')
        self.update_plot()


    def on_lock_xaxis(self):
        self.lock_xaxis = (self.lock_plot_xaxis.get() == '1')
        if not self.lock_xaxis:
            self.update_plot()


    def on_mark_points(self):
        Settings.plot_mark_points = (self.plot_mark_points.get() == '1')
        self.update_plot()


    def on_lock_yaxis(self):
        self.lock_yaxis = (self.lock_plot_yaxis.get() == '1')
        if not self.lock_yaxis:
            self.update_plot()
    

    def on_rescale_locked_axes(self):
        self.invalidate_axes_lock()


    def on_lock_axes(self):
        self.lock_plot_xaxis.set(True)
        self.lock_plot_yaxis.set(True)
        self.lock_xaxis = True
        self.lock_yaxis = True
        self.update_plot()


    def on_unlock_axes(self):
        self.lock_plot_xaxis.set(False)
        self.lock_plot_yaxis.set(False)
        self.lock_xaxis = False
        self.lock_yaxis = False
        self.update_plot()
    

    def on_manual_axes(self):
        def scaling_callback(x0, x1, xauto, y0, y1, yauto):
            try:
                self.lock_plot_xaxis.set(not xauto)
                self.lock_xaxis = not xauto
                if not xauto:
                    self.plot.plot.set_xlim((x0,x1))
                self.lock_plot_yaxis.set(not yauto)
                self.lock_yaxis = not yauto
                if not yauto:
                    self.plot.plot.set_ylim((y0,y1))
            except:
                pass
            self.update_plot()
        
        (x0,x1) = self.plot.plot.get_xlim()
        (y0,y1) = self.plot.plot.get_ylim()
        SparamviewerAxesDialog(self.toplevel_main, scaling_callback, x0, x1, not self.lock_xaxis, y0, y1, not self.lock_yaxis)

    
    def invalidate_axes_lock(self, update: bool = True):
        self.plot_axes_are_valid = False
        if update:
            self.update_plot()

    
    def on_view_tabular(self):
        
        selected_files = [file for file in self.files if file.tag in self.treeview_files.selection()]

        datasets = []
        selection = None
        for i,file in enumerate(self.files):
            if (selection is None) and (file.tag in self.treeview_files.selection()):
                selection = i
            datasets.append(TabularDatasetSFile(file))
        for plot in self.plot.plots:
            datasets.append(TabularDatasetPlot(plot))
        TabularDialog(datasets=datasets, initial_selection=selection, master=self.toplevel_main).run()


    def on_save_plot_graphic(self):

        if not self.plot.fig:
            return

        try:
            filename = filedialog.asksaveasfilename(
                title='Save Plot Graphic', confirmoverwrite=True, defaultextension='.png',
                filetypes=(
                    ('PNG','.png'),
                    ('All Files','*'),
                ))
            if not filename:
                return
            self.plot.fig.savefig(filename)
        except Exception as ex:
            logging.exception(f'Exporting failed: {ex}')
            messagebox.showerror('Error', str(ex))
    

    def on_copy_plot_image_to_clipboard(self):

        if not self.plot.fig:
            return

        try:
            Clipboard.copy_figure(self.plot.fig)
        except Exception as ex:
            logging.exception(f'Copying plot to clipboard failed: {ex}')
            messagebox.showerror('Error', str(ex))
    

    def on_menu_about(self):
        messagebox.showinfo('About', f'{Info.AppName}\n\nVersion: {Info.AppVersionStr}\nDate: {Info.AppDateStr}')


    def show_error(self, error: "str|None"):
        self.eval_err_msg.set('\u26A0 ' + error if error is not None else "No problems found")


    def open_error_dialog(self):
        SparamviewerLogDialog(self.toplevel_main).run()


    def on_show_error_log_click(self):
        self.open_error_dialog()
    

    def on_open_dir(self):
        initialdir = self.directories[0] if len(self.directories)>0 else appdirs.user_data_dir()
        dir = filedialog.askdirectory(initialdir=initialdir)
        if not dir:
            return
        absdir = os.path.abspath(dir)
        self.directories = [absdir]
        self.clear_loaded_files()
        self.load_files_in_directory(absdir)
        self.update_file_list(only_select_first=True)
    

    def on_append_dir(self):
        initialdir = self.directories[0] if len(self.directories)>0 else appdirs.user_data_dir()
        dir = filedialog.askdirectory(initialdir=initialdir)
        if not dir:
            return
        absdir = os.path.abspath(dir)
        if absdir not in self.directories:
            self.directories.append(absdir)
            self.load_files_in_directory(absdir)
        self.update_file_list()
    

    def on_reload_all_files(self):
        self.reload_all_files()


    def clear_loaded_files(self):
        self.files = []
        self.trace_data = []

    
    def initially_load_files_or_directory(self, filenames_or_directory: "list[str]"):
        if len(filenames_or_directory)<1:
            filenames_or_directory = [appdirs.user_data_dir()]

        is_dir = os.path.isdir(filenames_or_directory[0])
        if is_dir:
            directory = filenames_or_directory
            absdir = os.path.abspath(directory[0])
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(only_select_first=True)
        else:
            filenames = filenames_or_directory
            if not Settings.extract_zip:
                contains_archives = False
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.zip']:
                        contains_archives = True
                        break
                if contains_archives:
                    if messagebox.askyesno('Extract .zip Files', 'A .zip-file was selected, but the option to extract .zip-files is disabled. Do you want to enable it?'):
                        Settings.extract_zip = True
            absdir = os.path.split(filenames[0])[0]
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(selected_filenames=filenames)
    

    def update_most_recent_directories_menu(self):
        
        self.menuitem_recent.delete(0, 'end')
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
        for dir in Settings.last_directories:
           self.menuitem_recent.add_command(label=dir, command=make_loader_closure(dir))
        
    
    def add_to_most_recent_directories(self, dir: str):
        if dir in Settings.last_directories:
            idx = Settings.last_directories.index(dir)
            del Settings.last_directories[idx]
        
        Settings.last_directories.insert(0, dir)
        
        while len(Settings.last_directories) > MAX_DIRECTORY_HISTORY_SIZE:
            del Settings.last_directories[-1]
        
        Settings.save()

        self.update_most_recent_directories_menu()


    def load_files_in_directory(self, dir: str):

        self.add_to_most_recent_directories(dir)

        try:

            absdir = os.path.abspath(dir)
            
            def filetype_matches(path):
                ext = os.path.splitext(path)[1]
                return re.match(r'(\.ci?ti)|(\.s[0-9]+p)', ext, re.IGNORECASE)
        
            def load_file(filename, archive_path=None):
                try:
                    tag = f'file{self.next_file_tag}'
                    file = SParamFile(filename, tag=tag, archive_path=archive_path)
                    self.files.append(file)
                    self.next_file_tag += 1
                except Exception as ex:
                    logging.info(f'Ignoring file <{filename}>: {ex}')
            
            def find_all_files(path):
                all_items = [os.path.join(path,f) for f in os.listdir(path)]
                return sorted(list([f for f in all_items if os.path.isfile(f)]))

            all_files = find_all_files(absdir)

            for filename in all_files:
                if not filetype_matches(filename):
                    continue
                load_file(filename)

            if Settings.extract_zip:
                for zip_filename in all_files:
                    ext = os.path.splitext(zip_filename)[1].lower()
                    if ext != '.zip':
                        continue
                    try:
                        with zipfile.ZipFile(zip_filename, 'r') as zf:
                            for internal_name in zf.namelist():
                                if not filetype_matches(internal_name):
                                    continue
                                load_file(internal_name, archive_path=zip_filename)
                    except Exception as ex:
                        logging.warning(f'Unable to open zip file <{zip_filename}>: {ex}')
        
        except Exception as ex:
            logging.exception(f'Unable to load files: {ex}')
            raise ex


    def reload_all_files(self):
        self.clear_loaded_files()
        for dir in self.directories:
            self.load_files_in_directory(dir)
        self.update_file_list()
    

    def on_search_press_key(self, event=None):
        if event is not None:
            if event.keysym == 'Return':
                self.update_file_list()
    

    def update_file_in_list(self, file: "SParamFile"):
        
        tag = file.tag
        name_str = file.name
        prop_str = self.get_file_prop_str(file)
        
        self.treeview_files.item(tag, values=(name_str,prop_str))


    def get_file_prop_str(self, file: "SParamFile") -> str:
        if file.loaded():
            return f'{file.nw.number_of_ports}-port, {Si(min(file.nw.f),"Hz")} to {Si(max(file.nw.f),"Hz")}'
        elif file.error():
            return '[loading failed]'
        else:
            return '[not loaded]'
    

    def update_file_list(self, selected_filenames: "list[str]" = [], only_select_first: bool = False):
        
        if len(selected_filenames) == 0 and not only_select_first:
            search = self.search_str.get()
            if len(search) != 0:
                previously_selected_files = []
            else:
                previously_selected_files = self.get_selected_files()
                search = None
        else:
            previously_selected_files = []
            search = None
            self.search_str.set('')

        self.treeview_files.delete(*self.treeview_files.get_children())
        selected_archives = set()
        for i,file in enumerate(self.files):
            
            tag = file.tag
            name_str = file.name
            prop_str = self.get_file_prop_str(file)
            
            self.treeview_files.insert('', 'end', tag, values=(name_str,prop_str))
            
            do_select = False
            if only_select_first and i==0:
                do_select = True
            elif file.tag in [s.tag for s in previously_selected_files]:
                do_select = True
            elif os.path.abspath(file.file_path) in [os.path.abspath(f) for f in selected_filenames]:
                do_select = True
            elif (file.archive_path is not None) and (os.path.abspath(file.archive_path) in [os.path.abspath(f) for f in selected_filenames]):
                if file.archive_path not in selected_archives:
                    # only select the 1st file in any archive, to avoid excessive loading time
                    selected_archives.add(file.archive_path)
                    do_select = True
            elif search is not None:
                try:
                    if re.search(search, file.filename, re.IGNORECASE):
                        do_select = True
                except:
                    pass
            
            if do_select:
                self.treeview_files.selection_add(tag)


    def get_selected_files(self) -> "list[SParamFile]":
        selected_files = []
        for file in self.files:
            if file.tag in self.treeview_files.selection():
                selected_files.append(file)
        return selected_files


    def update_plot(self):

        try:

            
            prev_xlim, prev_ylim = None, None
            if self.plot is not None:
                if self.plot.plot is not None:
                    try:
                        prev_xlim = self.plot.plot.get_xlim()
                        prev_ylim = self.plot.plot.get_ylim()
                    except:
                        pass
            
            self.fig.clf()
            self.generated_expressions = ''
            self.plot = None

            def v2db(v):
                return 20*np.log10(np.maximum(1e-15, np.abs(v)))
            
            def group_delay(f,sp):
                gd = -np.diff(np.unwrap(np.angle(sp)))/np.diff(f)
                gd = np.insert(gd, 0, gd[0]) # repeat 1st value, so that the f-axis is correct
                return gd

            self.show_error(None)              
            n_log_entries_before = len(LogHandler.inst().get_messages(logging.WARNING))

            data_expr_based = Settings.plot_mode==self.MODE_EXPR

            enable_1st_y = (Settings.plot_unit != self.UNIT_NONE)
            enable_2nd_y = (Settings.plot_unit2 != self.UNIT2_NONE)
            if (Settings.plot_unit not in [self.UNIT_NONE, self.UNIT_DB, self.UNIT_LIN_MAG, self.UNIT_LOG_MAG]):
                enable_2nd_y = False
            dual_y_axis = enable_1st_y and enable_2nd_y

            qty_db = (Settings.plot_unit == self.UNIT_DB)
            qty_lin_mag = (Settings.plot_unit == self.UNIT_LIN_MAG)
            qty_log_mag = (Settings.plot_unit == self.UNIT_LOG_MAG)
            qty_re = (Settings.plot_unit in [self.UNIT_RE_IM_VS_F, self.UNIT_RE_VS_F])
            qty_im = (Settings.plot_unit in [self.UNIT_RE_IM_VS_F, self.UNIT_IM_VS_F])
            
            polar = (Settings.plot_unit == self.UNIT_RE_IM_POLAR)
            smith = (Settings.plot_unit in [self.UNIT_SMITH_Z, self.UNIT_SMITH_Y])
            timedomain = (Settings.plot_unit in [self.UNIT_IMPULSE, self.UNIT_STEP])
            stepresponse = (Settings.plot_unit == self.UNIT_STEP)
            tdr_z = (Settings.tdr_impedance)
            if Settings.plot_unit == self.UNIT_SMITH_Z:
                smith_type = 'z'
            else:
                smith_type = 'y'
            
            if enable_2nd_y:
                qty_phase = (Settings.plot_unit2 in [self.UNIT2_PHASE, self.UNIT2_PHASE_UNWRAP, self.UNIT2_PHASE_REMLIN])
                unwrap_phase = (Settings.plot_unit2 == self.UNIT2_PHASE_UNWRAP)
                remove_lin_phase = (Settings.plot_unit2 == self.UNIT2_PHASE_REMLIN)
                qty_group_delay = (Settings.plot_unit2 == self.UNIT2_GROUP_DELAY)
            else:
                qty_phase = False
                unwrap_phase = False
                remove_lin_phase = False
                qty_group_delay = False
            
            common_plot_args = dict(show_legend=Settings.show_legend, hide_single_item_legend=Settings.hide_single_item_legend, shorten_legend=Settings.shorten_legend_items)

            if polar:
                self.plot = PlotHelper(self.fig, smith=False, polar=True, x_qty='Real', x_fmt=SiFmt(), x_log=False, y_qty='Imaginary', y_fmt=SiFmt(), y_log=False, y2_fmt=None, y2_qty=None, z_qty='Frequency', z_fmt=SiFmt(unit='Hz'), **common_plot_args)
            elif smith:
                smith_z = 1.0
                self.plot = PlotHelper(fig=self.fig, smith=True, polar=False, x_qty='', x_fmt=SiFmt(), x_log=False, y_qty='', y_fmt=SiFmt(), y_log=False, y2_fmt=None, y2_qty=None, z_qty='Frequency', z_fmt=SiFmt(unit='Hz'), smith_type=smith_type, smith_z=smith_z, **common_plot_args)
            else:
                if timedomain:
                    xq,xf,xl = 'Time',SiFmt(unit='s',force_sign=True),False
                    if tdr_z:
                        yq,yf,yl = 'Step Response' if stepresponse else 'Impulse Response',SiFmt(unit='Ω', force_sign=True),False
                    else:
                        yq,yf,yl = 'Step Response' if stepresponse else 'Impulse Response',SiFmt(force_sign=True),False
                else:
                    xq,xf,xl = 'Frequency',SiFmt(unit='Hz'),Settings.log_freq
                    if qty_re or qty_im:
                        yq,yf,yl = 'Level',SiFmt(unit='',use_si_prefix=False,force_sign=True),False
                    elif qty_lin_mag:
                        yq,yf,yl = 'Magnitude',SiFmt(unit='',use_si_prefix=False),False
                    elif qty_log_mag:
                        yq,yf,yl = 'Magnitude',SiFmt(unit=''),True
                    else:
                        yq,yf,yl = 'Magnitude',SiFmt(unit='dB',use_si_prefix=False,force_sign=True),False
                    if qty_phase:
                        if Settings.phase_unit=='deg':
                            y2q,y2f = 'Phase',SiFmt(unit='°',use_si_prefix=False,force_sign=True)
                        else:
                            y2q,y2f = 'Phase',SiFmt(use_si_prefix=False,force_sign=True)
                    elif qty_group_delay:
                        y2q,y2f = 'Group Delay',SiFmt(unit='s',force_sign=True)
                    else:
                        y2q,y2f = None, None
                self.plot = PlotHelper(self.fig, False, False, xq, xf, xl, yq, yf, yl, y2q, y2f, **common_plot_args)


            def add_to_plot(f, sp, z0, name, style=None):

                if style is None:
                    style = '-'

                style2 = '-.'
                if style=='-':
                    style2 = '-.'
                elif style=='-.':
                    style2 = ':'
                if Settings.plot_mark_points:
                    style += 'o'
                    style2 += 'o'
                if dual_y_axis:
                    style_y2 = ':'
                else:
                    style_y2 = style
                
                def transform_phase(radians):
                    if Settings.phase_unit=='deg':
                        return radians * 180 / math.pi
                    return radians

                if polar or smith:
                    self.plot.add(np.real(sp), np.imag(sp), f, name, style)
                else:
                    if timedomain:
                        t,lev = sparam_to_timedomain(f, sp, step_response=stepresponse, shift=Settings.tdr_shift, window_type=Settings.window_type, window_arg=Settings.window_arg, min_size=Settings.tdr_minsize)
                        if tdr_z:
                            lev[lev==0] = 1e-20 # avoid division by zero in the next step
                            imp = z0 * (1+lev) / (1-lev) # convert to impedance
                            self.plot.add(t, np.real(imp), None, name, style)
                        else:
                            self.plot.add(t, lev, None, name, style)
                    elif qty_db:
                        self.plot.add(f, v2db(sp), None, name, style)
                    elif qty_lin_mag or qty_log_mag:
                        self.plot.add(f, np.abs(sp), None, name, style)
                    elif qty_re and qty_im:
                        self.plot.add(f, np.real(sp), None, name+' re', style)
                        self.plot.add(f, np.imag(sp), None, name+' im', style2)
                    elif qty_re:
                        self.plot.add(f, np.real(sp), None, name, style)
                    elif qty_im:
                        self.plot.add(f, np.imag(sp), None, name, style)
                    
                    if qty_phase:
                        if remove_lin_phase:
                            self.plot.add(f, transform_phase(scipy.signal.detrend(np.unwrap(np.angle(sp)),type='linear')), None, name, style_y2, prefer_2nd_yaxis=True)
                        elif unwrap_phase:
                            self.plot.add(f, transform_phase(np.unwrap(np.angle(sp))), None, name, style_y2, prefer_2nd_yaxis=True)
                        else:
                            self.plot.add(f, transform_phase(np.angle(sp)), None, name, style_y2, prefer_2nd_yaxis=True)
                    elif qty_group_delay:
                        self.plot.add(f, group_delay(f,sp), None, name, style_y2, prefer_2nd_yaxis=True)
                    
            selected_files = self.get_selected_files()
            touched_files = []

            if data_expr_based:

                raw_exprs = TkText.get_text(self.text_expr)
                Settings.expression = raw_exprs

                ExpressionParser.touched_files = []
                ExpressionParser.eval(raw_exprs, self.files, selected_files, add_to_plot)  
                touched_files.extend(ExpressionParser.touched_files)

            else:

                if Settings.plot_mode == self.MODE_ALL:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif Settings.plot_mode == self.MODE_ALL_RECIPROCAL:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif Settings.plot_mode == self.MODE_IL_ALL:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot()'
                elif Settings.plot_mode == self.MODE_IL_RECIPROCAL:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot()'
                elif Settings.plot_mode == self.MODE_RL:
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot()'
                elif Settings.plot_mode == self.MODE_S21:
                    self.generated_expressions += 'sel_nws().s(2,1).plot()'
                elif Settings.plot_mode == self.MODE_S11:
                    self.generated_expressions += 'sel_nws().s(1,1).plot()'
                elif Settings.plot_mode == self.MODE_S22:
                    self.generated_expressions += 'sel_nws().s(2,2).plot()'
                elif Settings.plot_mode == self.MODE_S33:
                    self.generated_expressions += 'sel_nws().s(3,3).plot()'
                elif Settings.plot_mode == self.MODE_S44:
                    self.generated_expressions += 'sel_nws().s(4,4).plot()'

                try:
                    ExpressionParser.eval(self.generated_expressions, self.files, selected_files, add_to_plot)  
                    self.show_error(None)              
                except Exception as ex:
                    logging.error(f'Unable to parse expressions: {ex} (trace: {traceback.format_exc()})')
                    self.fig.clf()
                    self.show_error(f'ERROR: {ex}')
                
                touched_files = selected_files
            
            for f in touched_files:
                self.update_file_in_list(f)
            
            log_entries_after = len(LogHandler.inst().get_messages(logging.WARNING))
            n_new_entries = log_entries_after - n_log_entries_before
            if n_new_entries > 0:
                self.show_error(LogHandler.inst().get_messages(logging.WARNING)[-1])

            self.plot.render()

            #if not polar and not smith and not timedomain and not qty_group_delay:
            #    if data_include_rl and self.plot.y_range[1]<=0:
            #        self.plot.plot.set_ylim((None,max(0,self.plot.y_range[1]+1)))
            #    if (data_include_fwd_il or data_include_rev_il) and self.plot.y_range[1]<=-10 and self.plot.y_range[1]-self.plot.y_range[1]>=5:
            #        self.plot.plot.set_ylim((None,max(0,self.plot.y_range[1]+1)))
            
            self.plot.finish()

            if self.plot_axes_are_valid:
                if self.lock_xaxis and prev_xlim is not None:
                    self.plot.plot.set_xlim(prev_xlim)
                if self.lock_yaxis and prev_ylim is not None:
                    self.plot.plot.set_ylim(prev_ylim)

            self.canvas.draw()

            if self.cursor_dialog is not None:
                self.cursor_dialog.clear()
                self.cursor_dialog.repopulate(self.plot.plots)
            
            self.plot_axes_are_valid = True

        except Exception as ex:
            logging.exception(f'Plotting failed: {ex}')
            self.fig.clf()
            self.show_error(f'ERROR: {ex}')
            raise ex
