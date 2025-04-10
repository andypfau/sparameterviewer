from .rl_dialog_ui import RlDialogUi


class RlDialog(RlDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
    

    def show_modal_dialog(self):
        super().ui_show_modal()
