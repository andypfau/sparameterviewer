from .rl_dialog_ui import RlDialogUi
from .help import show_help
from lib import SParamFile, BodeFano, Si, parse_si_range, format_si_range, v2db

import logging



class RlDialog(RlDialogUi):

    def __init__(self, parent):
        self.files: list[SParamFile] = []
        super().__init__(parent)
        self.ui_intrange_presets([
            format_si_range(any, any, allow_total_wildcard=True),
            format_si_range(0, 10e9),
        ])
        self.ui_tgtrange_presets([
            format_si_range(1e9, 2e9),
        ])
    

    def show_modal_dialog(self, files: "list[SParamFile]", initial_selection: SParamFile):
        self.files = files
        self.ui_set_files_list([file.name for file in files], initial_selection.name)
        super().ui_show_modal()


    def update(self):
        if len(self.files) < 1:
            return

        file = next(file for file in self.files if file.name==self.ui_file)

        port = self.ui_port
        port_ok = port <= file.nw.nports
        self.ui_inidicate_port_error(not port_ok)
        
        (int0, int1) = parse_si_range(self.ui_intrange)
        intrange_ok = int0 is not None and int1 is not None
        self.ui_inidicate_intrange_error(not intrange_ok)
        
        (tgt0, tgt1) = parse_si_range(self.ui_tgtrange, wildcard_low=None, wildcard_high=None)
        tgtrange_ok = tgt0 is not None and tgt1 is not None
        self.ui_inidicate_tgtrange_error(not tgtrange_ok)
        
        plot_kind = 'hist' if self.ui_histogram else ''

        ok = port_ok and intrange_ok and tgtrange_ok
        if ok:
            try:
                self.calculate(file, port, int0, int1, tgt0, tgt1, plot_kind)
            except Exception as ex:
                logging.error(ex)
                self.ui_set_result(str(ex), True)
        else:
            self.ui_set_result('Invalid parameters', True)
            self.ui_plot.clear()


    def calculate(self, file: SParamFile, port: int, int0: float, int1: float, tgt0: float, tgt1: float, histogram: bool):
        
        bodefano = BodeFano.from_network(file.nw, port, int0, int1, tgt0, tgt1)

        int0, int1 = bodefano.f_integration_actual_start_hz, bodefano.f_integration_actual_stop_hz

        message = \
            f'Available: {bodefano.db_available:+.3g} dB ({Si(bodefano.f_integration_actual_start_hz,"Hz")}..{Si(bodefano.f_integration_actual_stop_hz,"Hz")})\n' + \
            f'Current: {bodefano.db_current:+.3g} dB ({Si(tgt0,"Hz")}..{Si(tgt1,"Hz")})\n' + \
            f'Achievable: {bodefano.db_achievable:+.3g} dB ({Si(tgt0,"Hz")}..{Si(tgt1,"Hz")})'
        self.ui_set_result(message)

        self.ui_plot.clear()
        plot = self.ui_plot.figure.add_subplot(111)

        if histogram:
            plot.hist(x=v2db(bodefano.nw_s_intrange), ls='-', color='darkblue', label=f'S{port}{port}')
            plot.axvline(x=bodefano.db_available, ls=':', color='blue', label=f'Available')
            plot.axvline(x=bodefano.db_current, ls='--', color='blue', label=f'Current')
            plot.axvline(x=bodefano.db_achievable, ls='-', color='green', label=f'Achievable')
            
            plot.set_xlabel('RL / dB')
            plot.set_ylabel('Histogram')
            plot.legend()
        
        else:
            plot.fill_between(bodefano.nw_f_intrange/1e9, v2db(bodefano.nw_s_intrange), color='chartreuse', alpha=0.1)
            plot.plot(bodefano.nw_f_intrange/1e9, v2db(bodefano.nw_s_intrange), '-', color='darkblue', label=f'S{port}{port}')
            plot.plot([bodefano.f_integration_actual_start_hz/1e9,bodefano.f_integration_actual_stop_hz/1e9], [bodefano.db_available,bodefano.db_available], ':', color='blue', label=f'Available')
            plot.plot([tgt0/1e9,tgt1/1e9], [bodefano.db_current,bodefano.db_current], '--', color='blue', label=f'Current')
            plot.plot([tgt0/1e9,tgt1/1e9], [bodefano.db_achievable,bodefano.db_achievable], '-', color='green', label=f'Achievable')
            
            plot.set_xlabel('f / GHz')
            plot.set_ylabel('RL / dB')
            plot.legend()

        self.ui_plot.draw()



    def on_file_changed(self):
        self.update()


    def on_port_changed(self):
        self.update()


    def on_intrange_changed(self):
        self.update()


    def on_tgtrange_changed(self):
        self.update()


    def on_plottype_changed(self):
        self.update()


    def on_help(self):
        show_help('tools.md')
