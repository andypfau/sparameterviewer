import tkinter as tk
import matplotlib
import matplotlib.figure



class Clipboard:

    @staticmethod
    def copy_string(s: str):
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(s)
        r.update()
        r.destroy()


    @staticmethod
    def copy_figure(fig: matplotlib.figure.Figure):
        import io
        import win32clipboard
        from PIL import Image

        rgba_buffer = fig.canvas.buffer_rgba()
        w = int(fig.get_figwidth() * fig.dpi)
        h = int(fig.get_figheight() * fig.dpi)
        im = Image.frombuffer('RGBA', (w,h), rgba_buffer)
        
        io_buffer = io.BytesIO()
        im.convert("RGB").save(io_buffer, "BMP")
        data = io_buffer.getvalue()[14:]
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        io_buffer.close()
