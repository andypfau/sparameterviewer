import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrollbarhelper import ScrollbarHelper
import math
import cmath



class TabularDialog:

    def __init__(self, column_names, row_data, master=None):
        
        self.columns_names, self.row_data = column_names, row_data
        self.clipboard_data = ''
        
        self.toplevel_info = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_info.configure(height=600, width=800)
        self.toplevel_info.title("Tabular Data")
        
        self.frame1 = ttk.Frame(self.toplevel_info)
        self.frame1.configure(padding=10)
        self.frame1.pack(expand="true", fill="x", side="top")
        self.combobox_format = ttk.Combobox(self.frame1)
        self.combobox_format.configure(state="readonly")
        self.combobox_format.grid(column=1, row=0)
        self.combobox_format.bind("<<ComboboxSelected>>", self.on_change_format, add="")
        self.combobox_format['values'] = ['Mag / dB', 'Mag (linear)', 'Complex', 'Phase / Rad', 'Phase / Deg']
        self.combobox_format.current(0)
        self.combobox_format.pack(side='left')
        self.button_copy = ttk.Button(self.frame1)
        self.button_copy.configure(text='Copy')
        self.button_copy.configure(command=self.on_copy)
        self.button_copy.pack(side='right')
        
        self.frame2 = ttk.Frame(self.toplevel_info)
        self.frame2.configure(padding=10)
        self.scrollbarhelper1 = ScrollbarHelper(self.frame2, scrolltype="both")
        self.scrollbarhelper1.configure(usemousewheel=False)
        self.listbox = ttk.Treeview(self.scrollbarhelper1.container, columns=column_names)
        self.listbox.pack(expand="true", fill="both", side="top")
        self.listbox.column("#0", width=0, stretch=tk.NO)
        self.listbox.heading("#0", text="", anchor=tk.W)
        for col in column_names:
            self.listbox.column(col, anchor=tk.E, width=120)
            self.listbox.heading(col, text=col, anchor=tk.E)
        self.scrollbarhelper1.add_child(self.listbox)
        self.scrollbarhelper1.pack(expand="true", fill="both", side="bottom")
        self.frame2.pack(expand="true", fill="both", side="top")
        
        self.mainwindow = self.toplevel_info
        
        self.update_data()
    

    def run(self):
        self.mainwindow.mainloop()
    

    def on_change_format(self, event=None):
        self.update_data()
    

    def update_data(self):
        
        f_formatter = lambda f,u: f'{f/1e9:.4g} GHz' if u else f'{f:.4g}'

        format_selection = self.combobox_format.current()
        if format_selection==0:
            formatter = lambda x,u: f'{20*math.log10(max(1e-15,abs(x))):+.4g}' + (' dB' if u else '')
        elif format_selection==1:
            formatter = lambda x,u: f'{abs(x):.4g}'
        elif format_selection==2:
            formatter = lambda x,u: f'{x.real:.4g}{x.imag:+.4g}j'
        elif format_selection==3:
            formatter = lambda x,u: f'{cmath.phase(x):4g}'
        elif format_selection==4:
            formatter = lambda x,u: f'{cmath.phase(x)*math.pi/180:.4g}' + ('°' if u else '')
        else:
            raise ValueError(f'Invalid combobox selection: {format}')
        
        self.listbox.delete(*self.listbox.get_children())
        self.clipboard_data = '\t'.join(self.columns_names) + '\n'
        for row in self.row_data:
            formatted_row = [f_formatter(row[0],True)] + ['\t'+formatter(x,True) for x in row[1:]]
            self.listbox.insert('', 'end', values=formatted_row)
            self.clipboard_data += '\t'.join([f_formatter(row[0],False)] + [formatter(x,False) for x in row[1:]]) + '\n'
    

    def on_copy(self):
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(self.clipboard_data)
        r.update()
        r.destroy()
