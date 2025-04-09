from .info_dialog_ui import InfoDialogUi


class InfoDialog(InfoDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
    

    def show_dialog(self, title: str, text: str):
        super().ui_show(title, text)


    def on_select_level(self):
        pass
