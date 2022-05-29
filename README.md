S-Parameter Viewer
==================

A cross-platform S-parameter Viewer written in Python.


Prerequisites
-------------

- Python 3.7
- Packets: `numpy, scipy, skrf, matplotlib, tkinter, pygubu, openpyxl`


Usage
-----

- you can just start the app and load a directory
- or you can open one or more file with the app
	- under Windows, you can use `sparamviewer_windows.bat` for this purpose
	

Development
-----------

To modify the UI, you need `pygubu-designer`.


Known Issues
------------

- Under Linux, Gnome freezes when you open a non-Touchstone file, then open the same file again with a proper viewer reason unknown


Missing Features
----------------

- Stability circles
- Sample files (a 1-port termination, a 2-port filter, 3- or 4-port coupler)
