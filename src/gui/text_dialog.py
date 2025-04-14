from .text_dialog_ui import TextDialogUi
from .helpers.simple_dialogs import save_file_dialog, error_dialog
from .helpers.settings import Settings
from lib import Clipboard, AppPaths


class TextDialog(TextDialogUi):

    def __init__(self, parent):
        self.text = ''
        self.title = ''
        self.filetypes = None
        super().__init__(parent)
    

    def show_modal_dialog(self, title: str, text: str, save_filetypes = None):
        self.ui_set_title(title)
        self.ui_set_text(text)
        self.title, self.text = title, text
        self.filetypes = save_filetypes
        super().ui_show_modal()


    def on_copy(self):
        try:
            Clipboard.copy_string(self.text)
        except Exception as ex:
            error_dialog('Copying Failed', 'Unable to copy text.', str(ex))


    def on_save(self):
        filename = save_file_dialog(self, title=f'Save {self.title}', filetypes=self.filetypes)
        if not filename:
            return
        try:
            with open(filename, 'w') as fp:
                fp.write(self.text)
        except Exception as ex:
            error_dialog('Saving Failed', 'Unable to save file.', str(ex))
