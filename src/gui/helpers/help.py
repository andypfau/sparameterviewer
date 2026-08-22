from lib import AppPaths, open_file_in_default_viewer
from .simple_dialogs import error_dialog
import pathlib



def show_help(doc: str = 'index'):

    def locate_helpfile(doc: str):
        try:
            path = pathlib.Path(AppPaths.get_htmldoc_dir()) / (doc + '.html')
            if path.exists():
                return path
            path = pathlib.Path(AppPaths.get_doc_dir()) / (doc + '.md')
            if path.exists():
                return path
            raise RuntimeError(f'<{str(path)}> not exists')
        except Exception as ex:
            error_dialog('Unable to locate documentation', 'Unable to locate documentation.', f'Try to locate <sparameterviewer/docs> manually ({ex}).')

    def open_doc(path: str):
        try:
            open_file_in_default_viewer(str(path))
        except Exception as ex:
            error_dialog('Unable to show documentation', f'Unable to show documentation.', f'Try to open <{str(path)}> manually ({ex}).')
    
    path = locate_helpfile(doc)
    open_doc(path)
