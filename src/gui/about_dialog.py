from .about_dialog_ui import AboutDialogUi


class AboutDialog(AboutDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
    

    def show_dialog(self):
        super().ui_show()
