#!/bin/python3

from tkinter import *
from tkinter import filedialog, messagebox, simpledialog

import os, glob, appdirs, math, copy, logging, traceback, datetime, io
import numpy as np
import re

import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from lib.si import SiFmt
import scipy.signal

from .main_window_pygubu import PygubuApp
from .info_dialog import SparamviewerInfoDialog
from .rl_dialog import SparamviewerReturnlossDialog
from .cursor_dialog import SparamviewerCursorDialog
from .log_dialog import SparamviewerLogDialog, LogHandler
from .settings_dialog import SparamviewerSettingsDialog
from .settings import Settings
from info import Info

from lib import sparam_to_timedomain, get_sparam_name
from lib import Si, DataExport
from lib import SParamFile, PlotHelper
from lib import ExpressionParser
from lib import TkText, TkCommon, AppGlobal


# extend auto-generated UI code
class SparamviewerMainDialog(PygubuApp):
    def __init__(self, filenames: "list[str]"):
        super().__init__()

        try:
            self.directories = []
            self.next_file_tag = 1
            self.files = [] # type: list[SParamFile]
            self.generated_expressions = ''
            self.plot_mouse_down = False
            self.cursor_dialog = None # type: SparamviewerCursorDialog
            self.plot_axes_are_valid = False
            self.lock_xaxis = False
            self.lock_yaxis = False
            self.eval_error_list = []

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
                'dB',
                'Log. Magnitude',
                'Linear Magnitude',
                'Re/Im vs. Freq.',
                'Re vs. Freq.',
                'Im vs. Freq.',
                'Re/Im Polar',
                'Smith (Impedance)',
                'Smith (Admittance)',
                'Phase',
                'Unwrapped Phase',
                'Linear Phase Removed',
                'Group Delay',
                'Impulse Response',
                'Step Response',
            )
            self.UNIT_DB = 0
            self.UNIT_LOG_MAG = 1
            self.UNIT_LIN_MAG = 2
            self.UNIT_RE_IM_VS_F = 3
            self.UNIT_RE_VS_F = 4
            self.UNIT_IM_VS_F = 5
            self.UNIT_RE_IM_POLAR = 6
            self.UNIT_SMITH_Z = 7
            self.UNIT_SMITH_Y = 8
            self.UNIT_DEG = 9
            self.UNIT_DEG_UNWRAP = 10
            self.UNIT_DEG_REMLIN = 11
            self.UNIT_GROUP_DELAY = 12
            self.UNIT_IMPULSE = 13
            self.UNIT_STEP = 14
            self.combobox_unit.current(Settings.plot_unit)
            TkText.set_text(self.text_expr, Settings.expression.strip())
            def on_click_errors(event):
                self.open_error_dialog()
            self.entry_err.bind('<Button-1>', on_click_errors)

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
                pyplot.style.use('bmh')
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
            self.on_click_info()
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
        if key=='e' and ctrl_only:
            self.on_export()
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
                if yf.unit=='dB' or yf.unit=='°':
                    dy = self.plot.cursors[1].y - self.plot.cursors[0].y
                    readout += f'Delta: {Si(dx,si_fmt=xf)} | {Si(dy,si_fmt=yf)}\n'
                else:
                    if self.plot.cursors[0].y==0:
                        dys = '[error]'
                    else:
                        dy = self.plot.cursors[1].y / self.plot.cursors[0].y
                        dys = Si.to_significant_digits(dy, 4)
                    readout += f'Delta: {Si(dx,si_fmt=self.plot.x_fmt)} | Ratio: {dys}\n'
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


    def on_gen_expr(self):
        
        if len(self.generated_expressions)<1:
            return
        
        current = TkText.get_text(self.text_expr).strip()
        
        new = self.generated_expressions
        for line in current.splitlines():
            commented = '# ' + line.strip() if not line.startswith('#') else line.strip()
            if len(new)>0:
                new += '\n'
            new += commented

        Settings.expression = new

        TkText.set_text(self.text_expr, new)


    def on_expr_help(self):
        dlg = SparamviewerInfoDialog(self.toplevel_main, title='Expression Help', text=ExpressionParser.help())


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
        
        try:
            size = f'{os.path.getsize(sparam_file.file_path):,.0f} B'
            fmt_tstamp = lambda ts: f'{datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M:%S}'
            created = fmt_tstamp(os.path.getctime(sparam_file.file_path))
            modified = fmt_tstamp(os.path.getmtime(sparam_file.file_path))
        except:
            size = 'unknown'
            created = 'unknown'
            modified = 'unknown'
        f0, f1 = sparam_file.nw.f[0], sparam_file.nw.f[-1]
        n_pts = len(sparam_file.nw.f)
        dir, fname = os.path.split(sparam_file.file_path)
        dir = os.path.abspath(dir)
        comm = sparam_file.nw.comments.strip()
        n_ports = sparam_file.nw.s.shape[1]
        if (sparam_file.nw.z0 == sparam_file.nw.z0[0,0]).all():
            z0 = str(Si(sparam_file.nw.z0[0,0],'Ohm'))
        else:
            z0 = 'different for each port and/or frequency'
        
        info = f'{fname}\n'
        info += '-'*len(fname)+'\n\n'
        
        if len(comm)>0:
            info += comm + '\n\n'
        info += f'Ports: {n_ports}, reference impedance: {z0}\n'
        info += f'Frequency range: {Si(f0,"Hz")} to {Si(f1,"Hz")}, {n_pts:,.0f} point{"s" if n_pts!=0 else ""}\n\n'

        info += f'File created: {created}, last modified: {modified}\n'
        info += f'File size: {size}\n'
        info += f'File path: {os.path.join(dir, fname)}'

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


    def on_lock_yaxis(self):
        self.lock_yaxis = (self.lock_plot_yaxis.get() == '1')
        if not self.lock_yaxis:
            self.update_plot()
    

    def on_rescale_locked_axes(self):
        self.invalidate_axes_lock()

    
    def invalidate_axes_lock(self, update: bool = True):
        self.plot_axes_are_valid = False
        if update:
            self.update_plot()

    
    def on_export(self):

        if len(self.plot.plots)<1:
            return

        try:
            filename = filedialog.asksaveasfilename(
                title='Export Trace Data', confirmoverwrite=True, defaultextension='.csv',
                filetypes=(
                    ('CSV','.csv'),
                    ('Spreadsheet','.xlsx'),
                    ('All Files','*'),
                ))
            if not filename:
                return
            DataExport.auto(self.plot.plots, filename)
        except Exception as ex:
            logging.exception(f'Exporting failed: {ex}')
            messagebox.showerror('Error', str(ex))


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
            import io
            import win32clipboard
            from PIL import Image

            rgba_buffer = self.plot.fig.canvas.buffer_rgba()
            w = int(self.plot.fig.get_figwidth() * self.plot.fig.dpi)
            h = int(self.plot.fig.get_figheight() * self.plot.fig.dpi)
            im = Image.frombuffer('RGBA', (w,h), rgba_buffer)
            
            io_buffer = io.BytesIO()
            im.convert("RGB").save(io_buffer, "BMP")
            data = io_buffer.getvalue()[14:]
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            io_buffer.close()
            
        except Exception as ex:
            logging.exception(f'Copying plot to clipboard failed: {ex}')
            messagebox.showerror('Error', str(ex))
    

    def on_copy_plot_data_to_clipboard(self):

        if not self.plot.fig:
            return

        try:
            df = DataExport.to_pandas(self.plot.plots)
            df.to_clipboard(index=False)

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
            absdir = os.path.abspath(filenames_or_directory[0])
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(only_select_first=True)
        else:
            absdir = os.path.split(filenames_or_directory[0])[0]
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(selected_filenames=filenames_or_directory)


    def load_files_in_directory(self, dir: str):

        try:
            
            absdir = os.path.abspath(dir)
            all_files = sorted(list(glob.glob(f'{glob.escape(absdir)}/*.[Ss]*[Pp]')))
            
            for filename in all_files:
                try:
                    tag = f'file{self.next_file_tag}'
                    file = SParamFile(filename, tag=tag)
                    self.files.append(file)
                    self.next_file_tag += 1
                except Exception as ex:
                    logging.info(f'Ignoring file <{filename}>: {ex}')
        
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
        name_str = os.path.split(file.file_path)[1]
        prop_str = self.get_file_prop_str(file)
        
        self.treeview_files.item(tag, values=(name_str,prop_str))


    def get_file_prop_str(self, file: "SParamFile") -> str:
        return f'{file.nw.number_of_ports}-port, {Si(min(file.nw.f),"Hz")} to {Si(max(file.nw.f),"Hz")}'
    

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
        for i,file in enumerate(self.files):
            
            tag = file.tag
            name_str = os.path.split(file.file_path)[1]
            if file.loaded():
                prop_str = self.get_file_prop_str(file)
            else:
                prop_str = '[not loaded]'
            
            self.treeview_files.insert('', 'end', tag, values=(name_str,prop_str))
            
            do_select = False
            if only_select_first and i==0:
                do_select = True
            elif file.tag in [s.tag for s in previously_selected_files]:
                do_select = True
            elif os.path.abspath(file.file_path) in [os.path.abspath(f) for f in selected_filenames]:
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

            try:
                prev_xlim = self.plot.plot.get_xlim()
                prev_ylim = self.plot.plot.get_ylim()
            except:
                prev_xlim, prev_ylim = None, None
            
            self.fig.clf()
            self.generated_expressions = ''
            self.plot = None

            def v2db(v):
                return 20*np.log10(np.maximum(1e-15, np.abs(v)))
            
            def group_delay(f,sp):
                gd = -np.diff(np.unwrap(np.angle(sp)))/np.diff(f)
                gd = np.insert(gd, 0, gd[0]) # repeat 1st value, so that the f-axis is correct
                return gd

            data_expr_based = Settings.plot_mode==self.MODE_EXPR
            qty_db = (Settings.plot_unit == self.UNIT_DB)
            qty_lin_mag = (Settings.plot_unit == self.UNIT_LIN_MAG)
            qty_log_mag = (Settings.plot_unit == self.UNIT_LOG_MAG)
            qty_group_delay = (Settings.plot_unit == self.UNIT_GROUP_DELAY)
            qty_re = (Settings.plot_unit == self.UNIT_RE_IM_VS_F) or (Settings.plot_unit == self.UNIT_RE_VS_F)
            qty_im = (Settings.plot_unit == self.UNIT_RE_IM_VS_F) or (Settings.plot_unit == self.UNIT_IM_VS_F)
            qty_phase = (Settings.plot_unit == self.UNIT_DEG) or (Settings.plot_unit == self.UNIT_DEG_UNWRAP)
            unwrap_phase = (Settings.plot_unit == self.UNIT_DEG_UNWRAP)
            remove_lin_phase = (Settings.plot_unit == self.UNIT_DEG_REMLIN)
            polar = (Settings.plot_unit == self.UNIT_RE_IM_POLAR)
            smith = (Settings.plot_unit == self.UNIT_SMITH_Z) or (Settings.plot_unit == self.UNIT_SMITH_Y)
            timedomain = (Settings.plot_unit == self.UNIT_IMPULSE) or (Settings.plot_unit == self.UNIT_STEP)
            stepresponse = (Settings.plot_unit == self.UNIT_STEP)
            tdr_z = (Settings.tdr_impedance)
            if Settings.plot_unit == self.UNIT_SMITH_Z:
                smith_type = 'z'
            else:
                smith_type = 'y'
            
            common_plot_args = dict(show_legend=Settings.show_legend, hide_single_item_legend=Settings.hide_single_item_legend, shorten_legend=Settings.shorten_legend_items)

            if polar:
                self.plot = PlotHelper(self.fig, smith=False, polar=True, x_qty='Real', x_fmt=SiFmt(), x_log=False, y_qty='Imaginary', y_fmt=SiFmt(), y_log=False, z_qty='Frequency', z_fmt=SiFmt(unit='Hz'), **common_plot_args)
            elif smith:
                smith_z = 1.0
                self.plot = PlotHelper(fig=self.fig, smith=True, polar=False, x_qty='', x_fmt=SiFmt(), x_log=False, y_qty='', y_fmt=SiFmt(), y_log=False, z_qty='Frequency', z_fmt=SiFmt(unit='Hz'), smith_type=smith_type, smith_z=smith_z, **common_plot_args)
            else:
                if timedomain:
                    xq,xf,xl = 'Time',SiFmt(unit='s',force_sign=True),False
                    if tdr_z:
                        yq,yf,yl = 'Step Response' if stepresponse else 'Impulse Response',SiFmt(unit='Ω', force_sign=True),False
                    else:
                        yq,yf,yl = 'Step Response' if stepresponse else 'Impulse Response',SiFmt(force_sign=True),False
                else:
                    xq,xf,xl = 'Frequency',SiFmt(unit='Hz'),Settings.log_freq
                    if qty_group_delay:
                        yq,yf,yl = 'Group Delay',SiFmt(unit='s',force_sign=True),False
                    elif qty_phase:
                        yq,yf,yl = 'Phase',SiFmt(unit='°',use_si_prefix=False,force_sign=True),False
                    elif qty_re or qty_im:
                        yq,yf,yl = 'Level',SiFmt(unit='',use_si_prefix=False,force_sign=True),False
                    elif qty_lin_mag:
                        yq,yf,yl = 'Magnitude',SiFmt(unit='',use_si_prefix=False),False
                    elif qty_log_mag:
                        yq,yf,yl = 'Magnitude',SiFmt(unit=''),True
                    else:
                        yq,yf,yl = 'Magnitude',SiFmt(unit='dB',use_si_prefix=False,force_sign=True),False
                self.plot = PlotHelper(self.fig, False, False, xq, xf, xl, yq, yf, yl, **common_plot_args)


            def add_to_plot(f, sp, name, style=None):

                if style is None:
                    style = '-'

                style2 = '-.'
                if style=='-':
                    style2 = '-.'
                elif style=='-.':
                    style2 = ':'

                if polar or smith:
                    self.plot.add(np.real(sp), np.imag(sp), f, name, style)
                else:
                    if timedomain:
                        t,lev = sparam_to_timedomain(f, sp, step_response=stepresponse, shift=Settings.tdr_shift, window_type=Settings.window_type, window_arg=Settings.window_arg)
                        if tdr_z:
                            lev[lev==0] = 1e-20
                            z = 50 * (1+lev) / (1-lev)
                            self.plot.add(t, z, None, name, style)
                        else:
                            self.plot.add(t, lev, None, name, style)
                    elif qty_db:
                        self.plot.add(f, v2db(sp), None, name, style)
                    elif qty_lin_mag or qty_log_mag:
                        self.plot.add(f, np.abs(sp), None, name, style)
                    elif qty_group_delay:
                        self.plot.add(f, group_delay(f,sp), None, name, style)
                    elif qty_re and qty_im:
                        self.plot.add(f, np.real(sp), None, name+' re', style)
                        self.plot.add(f, np.imag(sp), None, name+' im', style2)
                    elif qty_re:
                        self.plot.add(f, np.real(sp), None, name, style)
                    elif qty_im:
                        self.plot.add(f, np.imag(sp), None, name, style)
                    elif remove_lin_phase:
                        self.plot.add(f, scipy.signal.detrend(np.unwrap(np.angle(sp))*180/math.pi,type='linear'), None, name, style)
                    elif unwrap_phase:
                        self.plot.add(f, np.unwrap(np.angle(sp))*180/math.pi, None, name, style)
                    else:
                        self.plot.add(f, np.angle(sp)*180/math.pi, None, name, style)
            
            selected_files = self.get_selected_files()
            touched_files = []

            if data_expr_based:

                raw_exprs = TkText.get_text(self.text_expr)
                Settings.expression = raw_exprs

                self.show_error(None)              
                self.eval_error_list = []
                log_entries_before = len(LogHandler.instance.entries)
                ex_msg = None
                try:
                    touched_files = ExpressionParser.eval(raw_exprs, self.files, selected_files, add_to_plot)  
                except Exception as ex:
                    logging.exception(ex)
                    ex_msg = str(ex)
                log_entries_after = len(LogHandler.instance.entries)
                n_new_entries = log_entries_after - log_entries_before
                if n_new_entries > 0:
                    self.eval_error_list = LogHandler.instance.entries[-n_new_entries:]
                    self.fig.clf()
                    if ex_msg is not None:
                        self.show_error(ex_msg)
                    else:
                        self.show_error('Error while parsing expressions')

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
            raise ex
