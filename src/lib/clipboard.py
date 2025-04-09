import matplotlib.figure
from PyQt6.QtGui import QGuiApplication, QClipboard, QImage



class Clipboard:

    @staticmethod
    def copy_string(s: str):
        clipboard = QGuiApplication.clipboard()
        clipboard.clear(mode=QClipboard.Mode.Clipboard)
        clipboard.setText(s, mode=QClipboard.Mode.Clipboard)


    @staticmethod
    def copy_figure(fig: matplotlib.figure.Figure):
        rgba_buffer = fig.canvas.buffer_rgba()
        width = int(fig.get_figwidth() * fig.dpi)
        height = int(fig.get_figheight() * fig.dpi)

        image = QImage(rgba_buffer, width, height, QImage.Format.Format_ARGB32)

        clipboard = QGuiApplication.clipboard()
        clipboard.clear(mode=QClipboard.Mode.Clipboard)
        clipboard.setImage(image, mode=QClipboard.Mode.Clipboard)
