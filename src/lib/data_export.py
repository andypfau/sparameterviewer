from .spreadsheet import SpreadsheetGen
from .structs import PlotData, PlotDataQuantity

from openpyxl.worksheet.table import TableStyleInfo
from openpyxl.styles import Font


class DataExport:

    @staticmethod
    def auto(plots: "list[PlotData]", filename: str):
        if filename.lower().endswith('xlsx'):
            DataExport.to_spreadsheet(plots, filename)
        else:
            DataExport.to_csv(plots, filename)
            

    @staticmethod
    def to_csv(plots: "list[PlotData]", filename: str):

        if len(plots)<1:
            
            headers = []
            all_rows_sorted = []

        else:
            
            headers = [f'{plots[0].x.name}']
            if plots[0].x.format.unit!='':
                headers[0] += f' / {plots[0].x.format.unit}'

            rows = {}
            n_cols = 0
            for plot in plots:
                n_cols += 1
                hdr = f'{plot.name} {plot.y.name}'
                if plot.y.format.unit!='':
                    hdr += f' / {plot.y.format.unit}'
                headers.append(hdr)
                for f,v in zip(plot.x.values,plot.y.values):
                    if f not in rows:
                        rows[f] = []
                        while len(rows[f])<n_cols-1:
                            rows[f].append('')
                    rows[f].append(v)
                for f2,vs2 in rows.items():
                    while len(vs2)<n_cols:
                        rows[f2].append('')
            
            all_rows = [[k]+v for k,v in rows.items()]
            all_rows_sorted = sorted(all_rows, key=lambda row:row[0])
        
        COLUMN_SEPARATOR = ','
        with open(filename,'w') as fp:
            fp.write(COLUMN_SEPARATOR.join(headers))
            for vs in all_rows_sorted:
                fp.write('\n'+COLUMN_SEPARATOR.join([str(v) for v in vs]))
    

    @staticmethod
    def to_spreadsheet(plots: "list[PlotData]", filename: str):
        
        tbl_table = TableStyleInfo(name='MyTable', showRowStripes=True)
        fnt_title = Font(size=14, bold=True)
        fnt_header = Font(bold=True)

        xls = SpreadsheetGen()
        for plot in plots:
            ws = xls.add_sheet(plot.name)
            ws.add_row([plot.name], fnt_title)
            ws.add_row([])
            header_array = [
                plot.x.name + f' / {plot.x.format.unit}' if plot.x.format.unit!='' else '',
                plot.y.name + f' / {plot.y.format.unit}' if plot.y.format.unit!='' else '',
            ]
            table_array = list([[x,y] for x,y in zip(plot.x.values, plot.y.values)])
            ws.add_table(
                header_array, table_array, \
                header_font=fnt_header, name=plot.name+'Table', style=tbl_table)
            ws.col_widths([20, 20])

        xls.save(filename)    
