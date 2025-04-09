from .tabular_dialog_ui import TabularDialogUi


class TabularDialog(TabularDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
    

    def show_dialog(self):
        super().ui_show()
