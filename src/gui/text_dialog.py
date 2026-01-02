from .text_dialog_ui import TextDialogUi
from .settings_dialog import SettingsDialog
from .helpers.simple_dialogs import save_file_dialog, error_dialog
from lib import Clipboard, AppPaths, start_process, PathExt, Settings, ArchiveFileLoader


class TextDialog(TextDialogUi):

    def __init__(self, parent):
        self.text: str = ''
        self.title: str = ''
        self.filetypes: list = None
        self.file_path: str = None
        super().__init__(parent)
    

    def show_modal_dialog(self, title: str, *, text: str = None, file_path: PathExt = None, save_filetypes = None):
        self.title = title
        self.file_path = file_path
        self.filetypes = save_filetypes

        def load_file_contents(path: PathExt):
            if path.is_in_arch():
                try:
                    with ArchiveFileLoader(str(path), path.arch_path) as extracted_path:
                        with open(extracted_path, 'r') as fp:
                            return fp.read()
                except Exception as ex:
                    raise RuntimeError(f'Unable to extract and load <{path.arch_path}> from archive <{str(path)}> ({ex})')
            else:
                with open(path, 'r') as fp:
                    return fp.read()

        if file_path:
            assert text is None, f'Expected not text, got "{text}"'
            try:
                self.text = load_file_contents(file_path)
            except Exception as ex:
                error_dialog('Error', 'Unable to read file contents', detailed_text=str(ex))
        else:
            assert file_path is None, f'Expected no file path, got <{file_path}>'
            self.text = text
        
        self.ui_set_title(title)
        self.ui_set_text(self.text)
        self.ui_show_open_button(self.file_path is not None)

        super().ui_show_modal()


    def on_copy(self):
        try:
            Clipboard.copy_string(self.text)
        except Exception as ex:
            error_dialog('Copying Failed', 'Unable to copy text.', detailed_text=str(ex))


    def on_save(self):
        filename = save_file_dialog(self, title=f'Save {self.title}', filetypes=self.filetypes, initial_filename=self.file_path)
        if not filename:
            return
        try:
            with open(filename, 'w') as fp:
                fp.write(self.text)
        except Exception as ex:
            error_dialog('Saving Failed', 'Unable to save file.', detailed_text=str(ex))


    def on_open_ext(self):

        if not SettingsDialog.ensure_external_editor_is_set(self):
            return

        try:
            start_process(Settings.ext_editor_cmd, self.file_path)
        except Exception as ex:
            error_dialog('Open File Externally', 'Unable to open file with external editor.', detailed_text=str(ex))
