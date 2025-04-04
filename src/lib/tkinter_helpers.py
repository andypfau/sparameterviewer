import logging
from tkinter import *


class TkCommon:


    @staticmethod
    def default_keyhandler(tk_obj: Toplevel, custom_handler: callable = None):
        
        def on_key(event):

            # see <https://stackoverflow.com/a/19863837>
            shift = (event.state & 0x01) != 0
            ctrl = (event.state & 0x04) != 0
            alt_left = (event.state & 0x08) != 0
            alt_right = (event.state & 0x80) != 0
            alt = alt_left or alt_right
            key = event.keysym
            
            if custom_handler is not None:
                return custom_handler(key=key, ctrl=ctrl, shift=shift, alt=alt)
        
        tk_obj.bind("<Key>", lambda e: on_key(e))


class TkText:


    @staticmethod
    def default_keyhandler(tk_text: Text, readonly: bool = False, custom_handler: callable = None):
        
        def on_key_handler(key, ctrl, shift, alt):

            # Ctrl+A to select all
            if ctrl and key=='a':
                tk_text.tag_add(SEL, "1.0", END)
                tk_text.mark_set(INSERT, "1.0")
                tk_text.see(INSERT)
                return 'break'
            
            if readonly:

                # allow copying
                if ctrl and (key=='c' or key=='Insert'):
                    return
                
                # allow all cursor movement
                if key=='Up' or key=='Down' or key=='Left' or key=='Right':
                    return
                if key=='Home' or key=='End':
                    return
                if key=='Prior' or key=='Next':
                    return

                if custom_handler is not None:
                    return custom_handler(key=key, ctrl=ctrl, shift=shift, alt=alt)
                
                # ignore default handlers
                return 'break'
            
            else: # editable

                if custom_handler is not None:
                    return custom_handler(key=key, ctrl=ctrl, shift=shift, alt=alt)
                
                # allow default handlers
                return
        
        TkCommon.default_keyhandler(tk_text, on_key_handler)
    

    @staticmethod
    def set_text(tk_text: Text, text: str):
        disabled = tk_text.cget('state') == 'disabled'
        if disabled:
            tk_text.config(state=NORMAL)

        tk_text.delete(0.0, END)
        tk_text.insert(END, text)
        
        if disabled:
            tk_text.config(state=DISABLED)
    

    @staticmethod
    def get_text(tk_text: Text) -> str:
        return tk_text.get(0.0, END)
