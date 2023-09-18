from lib import AppGlobal

from .settings import Settings
from .axes_dialog_pygubu import PygubuApp



# extend auto-generated UI code
class SparamviewerAxesDialog(PygubuApp):
    def __init__(self, master, callback, x0, x1, xauto, y0, y1, yauto):
        super().__init__(master)
        self.callback = callback

        self.x0.set(x0)
        self.x1.set(x1)
        self.xauto.set('auto' if xauto else 'manual')
        self.y0.set(y0)
        self.y1.set(y1)
        self.yauto.set('auto' if yauto else 'manual')

        def on_input_change(var, index, mode):
            self.callback(self.x0.get(), self.x1.get(), self.xauto.get()=='auto', self.y0.get(), self.y1.get(), self.yauto.get()=='auto')
        
        for elem in [self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto]:
            elem.trace('w', on_input_change)
