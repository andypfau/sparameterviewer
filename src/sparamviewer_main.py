#!/bin/python3

from tkinter import *
from tkinter import filedialog, messagebox, simpledialog

import os, glob, appdirs, math, copy, logging, traceback, datetime
import numpy as np

import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from lib.buffer_log_handler import BufferLogHandler
from lib.si import SiFmt

from sparamviewer_main_pygubu import SparamviewerPygubuApp
from sparamviewer_info import SparamviewerInfoDialog
from sparamviewer_rl import SparamviewerReturnlossDialog
from sparamviewer_cursor import SparamviewerCursorDialog
from info import Info

from lib import sparam_to_timedomain, get_sparam_name
from lib import Si, DataExport
from lib import SParamFile, PlotHelper
from lib import ExpressionParser
from lib import TkText, TkCommon, AppGlobal
from lib import AppSettings


# extend auto-generated UI code
class SparamviewerMainDialog(SparamviewerPygubuApp):
    def __init__(self, filenames: "list[str]"):
        super().__init__()

        logging.basicConfig(level=logging.WARNING)
        logging.captureWarnings(True)
        self.bufferLogHandler = BufferLogHandler(logging.WARNING)
        logging.getLogger().addHandler(self.bufferLogHandler)

        try:
            self.dir = ''
            self.files = [] # type: list[SParamFile]
            self.generated_expressions = ''
            self.plot_mouse_down = False
            self.cursor_dialog = None # type: SparamviewerCursorDialog
            self.plot_axes_are_valid = False
            self.lock_xaxis = False
            self.lock_yaxis = False
            self.eval_error_list = []

            class SParamViewerAppSettings(AppSettings):
                plot_mode: int = 0
                plot_unit: int = 0
                show_legend: bool = True
                hide_single_item_legend: bool = True
                shorten_legend_items: bool = True
                log_freq: bool = False
                expression: str = ''
                td_kaiser: float = 35.0
            self.settings = SParamViewerAppSettings('apfau.de S-Parameter Viewer', 'apfau.de', '0.1')

            # init UI
            AppGlobal.set_toplevel_icon(self.toplevel_main)
            TkCommon.default_keyhandler(self.toplevel_main, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(**kwargs))
            TkText.default_keyhandler(self.text_expr, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(**kwargs))
            self.show_legend.set('1' if self.settings.show_legend else '0')
            self.hide_single_legend.set('1' if self.settings.hide_single_item_legend else '0')
            self.short_legend.set('1' if self.settings.shorten_legend_items else '0')
            self.logf.set('1' if self.settings.log_freq else '0')
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
            self.combobox_mode.current(self.settings.plot_mode)
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
            self.UNIT_GROUP_DELAY = 11
            self.UNIT_IMPULSE = 12
            self.UNIT_STEP = 13
            self.combobox_unit.current(self.settings.plot_unit)
            TkText.set_text(self.text_expr, self.settings.expression.strip())
            def on_click_errors(event):
                self.on_open_error_dialog()
            self.entry_err.bind('<Button-1>', on_click_errors)
            
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

            self.load_files(filenames)
            self.update_plot()
        
        except Exception as ex:
            self.settings.reset()
            self.settings.save()
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
            self.on_reload_dir()
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
                    plot, x, y = self.plot.get_closest_plot_point(x, y)
                    if plot is not None:
                        self.cursor_dialog.set_trace(target_cursor_index, plot.name)
                else:
                    selected_trace_name = self.cursor_dialog.selected_trace_name_1 if target_cursor_index == 0 else self.cursor_dialog.selected_trace_name_2
                    if selected_trace_name is not None:
                        plot, x, y = self.plot.get_closest_plot_point(x, y, name=selected_trace_name)
                    else:
                        plot, x, y = None, None, None

                if plot is not None:
                    target_cursor = self.plot.cursors[target_cursor_index]
                    target_cursor.set(x, y, enable=True, color=plot.color)
        
        readout = ''
        xf = copy.copy(self.plot.x_fmt)
        yf = copy.copy(self.plot.y_fmt)
        xf.significant_digits += 3
        yf.significant_digits += 3
        if self.cursor_dialog.enable_cursor_1:
            x,y = self.plot.cursors[0].x, self.plot.cursors[0].y
            readout += f'Cursor 1: {Si(x,si_fmt=xf)} | {Si(y,si_fmt=yf)}\n'
        if self.cursor_dialog.enable_cursor_2:
            x,y = self.plot.cursors[1].x, self.plot.cursors[1].y
            readout += f'Cursor 2: {Si(x,si_fmt=xf)} | {Si(y,si_fmt=yf)}\n'
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
        self.settings.plot_unit = self.combobox_unit.current()
        self.settings.plot_mode = self.combobox_mode.current()
        self.settings.save()
        self.update_plot()
    

    def on_open_dir(self):
        dir = filedialog.askdirectory(initialdir=self.dir)
        self.load_dir(dir)
    

    def on_reload_dir(self):
        self._load_all_files_in_dir(self.dir, select=[sf.filename for sf in self.get_selected_files()])


    def on_exit_cmd(self):
        self.toplevel_main.quit()

    
    def on_set_kaiser(self):
        kaiser = simpledialog.askfloat('Kaiser Window', 'Argument for Kaiser Window:', initialvalue=self.settings.td_kaiser, parent=self.toplevel_main, minvalue=0.0, maxvalue=1e3)
        if kaiser is None:
            return
        self.settings.td_kaiser = kaiser
        self.settings.save()
        self.update_plot()

    
    def on_use_expr(self):
        self.combobox_mode.current(self.MODE_EXPR)
        self.settings.plot_mode = self.MODE_EXPR
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

        self.settings.expression = new
        self.settings.save()

        TkText.set_text(self.text_expr, new)


    def on_expr_help(self):
        dlg = SparamviewerInfoDialog(self.toplevel_main, title='Expression Help', text=ExpressionParser.help())


    def on_load_expr(self):

        if len(TkText.get_text(self.text_expr).strip())>0:
            if not messagebox.askokcancel('Overwrite', 'Expressions are not empty and will be overwritten'):
                return

        try:
            fn = filedialog.askopenfilename(filetypes=(('Expressions','.py'),('All Files','*')))
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
            fn = filedialog.asksaveasfilename(confirmoverwrite=True, defaultextension='.py')
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
        self.settings.show_legend = (self.show_legend.get() == '1')
        self.settings.save()
        self.update_plot()


    def on_change_logf(self):
        self.settings.log_freq = (self.logf.get() == '1')
        self.settings.save()
        self.update_plot()


    def on_hide_single_legend(self):
        self.settings.hide_single_item_legend = (self.hide_single_legend.get() == '1')
        self.settings.save()
        self.update_plot()


    def on_short_legend(self):
        self.settings.shorten_legend_items = (self.short_legend.get() == '1')
        self.settings.save()
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
        self.plot_axes_are_valid = False
        self.update_plot()

    
    def on_export(self):

        if len(self.plot.plots)<1:
            return

        try:
            filename = filedialog.asksaveasfilename(title='Export Trace Data', confirmoverwrite=True, defaultextension='.csv', filetypes=(('CSV','.csv'), ('Spreadsheet','.xlsx'), ('All Files','*')))
            if not filename:
                return
            DataExport.auto(self.plot.plots, filename)
        except Exception as ex:
            logging.exception(f'Exporting failed: {ex}')
            messagebox.showerror('Error', str(ex))


    def on_menu_about(self):
        messagebox.showinfo('About', f'{Info.AppName}\n\nVersion: {Info.AppVersionStr}\nDate: {Info.AppDateStr}')


    def _load_all_files_in_dir(self, dir: "str|None", select: "list[str]" = [], select_first: bool = False):

        try:
            
            self.dir = appdirs.user_data_dir()
            self.files = [] # type: list[SParamFile]
            self.treeview_files.delete(*self.treeview_files.get_children())
            self.trace_data = []

            if dir is None:
                return
            
            self.dir = os.path.abspath(dir)
            all_files = sorted(list(glob.glob(f'{self.dir}/*.[Ss]*[Pp]')))
            
            for i,filename in enumerate(all_files):
                try:
                    tag = f'file{i}'
                    spar = SParamFile.load(filename, tag)
                    self.files.append(spar)
                    
                    name_str = os.path.split(filename)[1]
                    prop_str = f'{spar.nw.number_of_ports}-port, {Si(min(spar.nw.f),"Hz")} to {Si(max(spar.nw.f),"Hz")}'
                    
                    self.treeview_files.insert('', 'end', tag, values=(name_str,prop_str))
                    
                    do_select = False
                    if select_first and i==0:
                        do_select = True
                    for sel_fn in select:
                        if os.path.abspath(filename)==os.path.abspath(sel_fn):
                            do_select = True
                            break
                    if do_select:
                        self.treeview_files.selection_add(tag)

                except Exception as ex:
                    logging.info(f'Ignoring file <{filename}>: {ex}')
        
        except Exception as ex:
            logging.exception(f'Unable to load files: {ex}')
            raise ex


    def load_dir(self, dir: str):
        self._load_all_files_in_dir(dir, select_first=True)

    
    def load_files(self, filenames: "list[str]"):
        if len(filenames)<1:
            self._load_all_files_in_dir(None)
            return

        if os.path.isdir(filenames[0]):
            dir = filenames[0]
        else:
            dir = os.path.split(filenames[0])[0]
        dir = os.path.abspath(dir)
        self._load_all_files_in_dir(dir, select=filenames)


    def show_error(self, error: "str|None"):
        self.eval_err_msg.set('\u26A0 ' + error if error is not None else "No problems found")


    def on_open_error_dialog(self):
        errs = self.bufferLogHandler.entries if len(self.eval_error_list)== 0 else self.eval_error_list
        log = '\n'.join(errs)
        dlg = SparamviewerInfoDialog(self.toplevel_main, title='Error Log', text=log)
        dlg.run()


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

            data_expr_based = self.settings.plot_mode==self.MODE_EXPR
            qty_db = (self.settings.plot_unit == self.UNIT_DB)
            qty_lin_mag = (self.settings.plot_unit == self.UNIT_LIN_MAG)
            qty_log_mag = (self.settings.plot_unit == self.UNIT_LOG_MAG)
            qty_group_delay = (self.settings.plot_unit == self.UNIT_GROUP_DELAY)
            qty_re = (self.settings.plot_unit == self.UNIT_RE_IM_VS_F) or (self.settings.plot_unit == self.UNIT_RE_VS_F)
            qty_im = (self.settings.plot_unit == self.UNIT_RE_IM_VS_F) or (self.settings.plot_unit == self.UNIT_IM_VS_F)
            qty_phase = (self.settings.plot_unit == self.UNIT_DEG) or (self.settings.plot_unit == self.UNIT_DEG_UNWRAP)
            unwrap_phase = (self.settings.plot_unit == self.UNIT_DEG_UNWRAP)
            polar = (self.settings.plot_unit == self.UNIT_RE_IM_POLAR)
            smith = (self.settings.plot_unit == self.UNIT_SMITH_Z) or (self.settings.plot_unit == self.UNIT_SMITH_Y)
            timedomain = (self.settings.plot_unit == self.UNIT_IMPULSE) or (self.settings.plot_unit == self.UNIT_STEP)
            stepresponse = (self.settings.plot_unit == self.UNIT_STEP)
            if self.settings.plot_unit == self.UNIT_SMITH_Z:
                smith_type = 'z'
            else:
                smith_type = 'y'
            
            common_plot_args = dict(show_legend=self.settings.show_legend, hide_single_item_legend=self.settings.hide_single_item_legend, shorten_legend=self.settings.shorten_legend_items)

            if polar:
                self.plot = PlotHelper(self.fig, False, True, 'Real', SiFmt(), False, 'Imaginary', SiFmt(), False, False, **common_plot_args)
            elif smith:
                smith_z = 1.0
                self.plot = PlotHelper(self.fig, True, False, '', SiFmt(), False, '', SiFmt(), False, smith_type=smith_type, smith_z=smith_z, **common_plot_args)
            else:
                if timedomain:
                    xq,xf,xl = 'Time',SiFmt(unit='s',force_sign=True),False
                    yq,yf,yl = 'Step Response' if stepresponse else 'Impulse Response',SiFmt(force_sign=True),False
                else:
                    xq,xf,xl = 'Frequency',SiFmt(unit='Hz'),self.settings.log_freq
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
                    self.plot.add(np.real(sp), np.imag(sp), name, style)
                else:
                    if timedomain:
                        t,lev = sparam_to_timedomain(f, sp, step_response=stepresponse, kaiser=self.settings.td_kaiser)
                        self.plot.add(t, lev, name, style)
                    elif qty_db:
                        self.plot.add(f, v2db(sp), name, style)
                    elif qty_lin_mag or qty_log_mag:
                        self.plot.add(f, np.abs(sp), name, style)
                    elif qty_group_delay:
                        self.plot.add(f, group_delay(f,sp), name, style)
                    elif qty_re and qty_im:
                        self.plot.add(f, np.real(sp), name+' re', style)
                        self.plot.add(f, np.imag(sp), name+' im', style2)
                    elif qty_re:
                        self.plot.add(f, np.real(sp), name, style)
                    elif qty_im:
                        self.plot.add(f, np.imag(sp), name, style)
                    elif unwrap_phase:
                        self.plot.add(f, np.unwrap(np.angle(sp))*180/math.pi, name, style)
                    else:
                        self.plot.add(f, np.angle(sp)*180/math.pi, name, style)

            if data_expr_based:

                raw_exprs = TkText.get_text(self.text_expr)
                self.settings.expression = raw_exprs
                self.settings.save()

                self.show_error(None)              
                self.eval_error_list = []
                log_entries_before = self.bufferLogHandler.count
                ex_msg = None
                try:
                    ExpressionParser.eval(raw_exprs, self.files, self.get_selected_files(), add_to_plot)  
                except Exception as ex:
                    logging.exception(ex)
                    ex_msg = str(ex)
                log_entries_after = self.bufferLogHandler.count
                if log_entries_after > log_entries_before:
                    self.eval_error_list = self.bufferLogHandler.entries[log_entries_before:]
                    self.fig.clf()
                    if ex_msg is not None:
                        self.show_error(ex_msg)
                    else:
                        self.show_error('Error while parsing expressions')

            else:

                if self.settings.plot_mode == self.MODE_ALL:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif self.settings.plot_mode == self.MODE_ALL_RECIPROCAL:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif self.settings.plot_mode == self.MODE_IL_ALL:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot()'
                elif self.settings.plot_mode == self.MODE_IL_RECIPROCAL:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot()'
                elif self.settings.plot_mode == self.MODE_RL:
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot()'
                elif self.settings.plot_mode == self.MODE_S21:
                    self.generated_expressions += 'sel_nws().s(2,1).plot()'
                elif self.settings.plot_mode == self.MODE_S11:
                    self.generated_expressions += 'sel_nws().s(1,1).plot()'
                elif self.settings.plot_mode == self.MODE_S22:
                    self.generated_expressions += 'sel_nws().s(2,2).plot()'
                elif self.settings.plot_mode == self.MODE_S33:
                    self.generated_expressions += 'sel_nws().s(3,3).plot()'
                elif self.settings.plot_mode == self.MODE_S44:
                    self.generated_expressions += 'sel_nws().s(4,4).plot()'

                try:
                    ExpressionParser.eval(self.generated_expressions, self.files, self.get_selected_files(), add_to_plot)  
                    self.show_error(None)              
                except Exception as ex:
                    logging.error(f'Unable to parse expressions: {ex} (trace: {traceback.format_exc()})')
                    self.fig.clf()
                    self.show_error(f'ERROR: {ex}')
            
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
