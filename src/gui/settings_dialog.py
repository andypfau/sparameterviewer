from .settings_dialog_ui import SettingsDialogUi


class SettingsDialog(SettingsDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
    

    def show_dialog(self, category: str = None):
        # TODO: select the correct tab
        super().ui_show()


    def let_user_select_ext_editor() -> bool:
        # TODO: implement
        return False
