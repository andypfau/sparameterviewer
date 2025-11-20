from lib import AppPaths, open_file_in_default_viewer
from .simple_dialogs import error_dialog
import pathlib



def show_help(doc: str = 'main.md'):
    try:
        helpfile_path = pathlib.Path(AppPaths.get_doc_dir()) / doc
        if not helpfile_path.exists():
            raise RuntimeError(f'<{str(helpfile_path)}> not exists')
    except Exception as ex:
        error_dialog('Unable to locate documentation', 'Unable to locate documentation.', f'Try to locate <sparameterviewer/docs> manually ({ex}).')
    
    try:
        open_file_in_default_viewer(str(helpfile_path))
    except Exception as ex:
        error_dialog('Unable to show documentation', f'Unable to show documentation.', f'Try to open <{str(helpfile_path)}> manually ({ex}).')
