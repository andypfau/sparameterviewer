S-Parameter Viewer
==================

A cross-platform S-parameter Viewer written in Python.

<img src="./doc/screenshot_mainwin_s2p.png" width="300" />


Main Features
-------------

- Various flexible ways of displaying S-parameters, e.g. IL (all/reciprocal) only / RL only, linear/dB/Smith-chart/re-im, impulse response, Phase (normal / unwrapped), Group Delay
- Export to CSV or Excel
- Plotting of Python-based expressions, including functions for stability factors and for adding passive elements
- Bode-Fano optimum RL estimation


Prerequisites
-------------

- Python 3.7
- Packets: `numpy, scipy, skrf, matplotlib, tkinter, pygubu, openpyxl`


Usage
-----

- you can just start the app and load a directory
- or you can open one or more file with the app

### Linux

Under Linux, you can use `res/application-x-scatteringparameter.xml` to register a mime-type for S-parameter files. For instructions, see e.g. <https://help.gnome.org/admin/system-admin-guide/stable/mime-types-custom-user.html>.

### Windows

Under Windows, you can use `res/sparamviewer.bat` to launch the app from "*Open With...*". You have to adapt the paths in the file.
	

Development
-----------

To modify the UI, you need `pygubu-designer`.


Known Issues
------------

- Under Linux, Gnome freezes when you open a non-Touchstone file, then open the same file again with a proper viewer reason unknown


Missing Features
----------------

- Implement the Bode-Fano limit as expression functions, e.g. `bodefano(1e9,10e9,'optimum')` to calculate the optimum achievable RL over a range of 1 GHz to 10 GHz.
- Stability circles, first as an expression function, maybe later as its own dialog for convenience
