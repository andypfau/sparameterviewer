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
        from PIL import Image
        import copykitten

        rgba_buffer = fig.canvas.buffer_rgba()
        w = int(fig.get_figwidth() * fig.dpi)
        h = int(fig.get_figheight() * fig.dpi)
        img = Image.frombuffer('RGBA', (w,h), rgba_buffer)
        
        img_data = img.tobytes()
        copykitten.copy_image(img_data, img.width, img.height)
