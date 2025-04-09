from .cursor_dialog_ui import CursorDialogUi


class CursorDialog(CursorDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
    

    def show_dialog(self):
        super().show()
