import matplotlib.figure
import matplotlib.backends.backend_agg
from PyQt6.QtGui import QGuiApplication, QClipboard, QImage



class Clipboard:

    @staticmethod
    def copy_string(s: str):
        clipboard = QGuiApplication.clipboard()
        if not clipboard:
            raise RuntimeError('Cannot access clipboard')
        clipboard.clear(mode=QClipboard.Mode.Clipboard)
        clipboard.setText(s, mode=QClipboard.Mode.Clipboard)


    @staticmethod
    def copy_figure(fig: matplotlib.figure.Figure):
        canvas = fig.canvas
        if not hasattr(canvas, 'buffer_rgba'):
            canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)
        canvas.draw()
        rgba_buffer = canvas.buffer_rgba()
        width = int(fig.get_figwidth() * fig.dpi)
        height = int(fig.get_figheight() * fig.dpi)

        image_rgba = QImage(rgba_buffer, width, height, QImage.Format.Format_ARGB32)
        image = image_rgba.rgbSwapped()  # the format of matplotlib and Qt differ, must swap colors

        clipboard = QGuiApplication.clipboard()
        if not clipboard:
            raise RuntimeError('Cannot access clipboard')
        clipboard.clear(mode=QClipboard.Mode.Clipboard)
        clipboard.setImage(image, mode=QClipboard.Mode.Clipboard)
