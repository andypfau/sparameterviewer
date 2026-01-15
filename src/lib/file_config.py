from .path_ext import PathExt



class FileConfig:


    # TODO: save the last 100 labels/colors/styles or so to settings?


    _labels: dict[str,str] = dict()

    @staticmethod
    def set_label(path: PathExt, new_label: str):
        FileConfig._labels[str(path)] = new_label
    
    @staticmethod
    def clear_label(path: PathExt):
        if str(path) in FileConfig._labels:
            del FileConfig._labels[str(path)]
    
    @staticmethod
    def get_label(path: PathExt, default: str|None = None) -> str|None:
        return FileConfig._labels.get(str(path), default)


    _colors: dict[str,str] = dict()

    @staticmethod
    def set_color(path: PathExt, new_color: str):
        FileConfig._colors[str(path)] = new_color
    
    @staticmethod
    def clear_color(path: PathExt):
        if str(path) in FileConfig._colors:
            del FileConfig._colors[str(path)]
    
    @staticmethod
    def get_color(path: PathExt, default: str|None = None) -> str|None:
        return FileConfig._colors.get(str(path), default)


    _styles: dict[str,str] = dict()

    @staticmethod
    def set_style(path: PathExt, new_style: str):
        FileConfig._styles[str(path)] = new_style
    
    @staticmethod
    def clear_style(path: PathExt):
        if str(path) in FileConfig._styles:
            del FileConfig._styles[str(path)]
    
    @staticmethod
    def get_style(path: PathExt, default: str|None = None) -> str|None:
        return FileConfig._styles.get(str(path), default)
