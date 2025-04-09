from .info_dialog_ui import InfoDialogUi


class InfoDialog(InfoDialogUi):

    def __init__(self):
        super().__init__()
    

    def show(self, title: str, text: str):
        super().ui_show(title, text)
