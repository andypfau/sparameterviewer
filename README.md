S-Parameter Viewer
==================

A cross-platform S-parameter Viewer written in Python.

<img src="./doc/screenshot_mainwin_s2p.png" width="250" /> <img src="./doc/screenshot_mainwin_markers.png" width="300" /> <img src="./doc/screenshot_mainwin_expr.png" width="250" />


Main Features
-------------

- Various flexible ways of displaying S-parameters, e.g. IL (all/reciprocal) only / RL only, linear/dB/Smith-chart/re-im, impulse/step response, Phase (normal/unwrapped), Group Delay
- Plotting of Python-based expressions, including functions for stability factors and stability circles, for adding passive elements, and for Bode-Fano optimum RL estimation
    - to learn more about this feature, open the "Expressions" tab, and click "Help"
- Export to CSV or XLSX


Prerequisites
-------------

- Python 3.7
- Packets: `numpy, scipy, skrf, matplotlib, tkinter, pygubu, openpyxl, appdirs`


Usage
-----

- you can just start the app and load a directory
- or you can open one or more file with the app

### Linux

To register S-parameter files with this application under Linux:

1. Register a mime-type for S-parameter files using `res/application-x-scatteringparameter.xml` (for instructions, see e.g. <https://help.gnome.org/admin/system-admin-guide/stable/mime-types-custom-user.html>).
2. Double-click any .s#p-file, and select the script `src/sparamviewer.py` as the application.

### Windows

To register S-parameter files with this application under Windows:

1. Open `res/sparamviewer.bat` in a text editor.
2. Adapt the paths to your Python interpreter, as well as the path where `src/sparamviewer.py` is, in the 1st line.
3. Double-click any .s#p-file, and select the batch-file `res/sparamviewer.bat` as the application (you have to repeat this step for every type of .s#p-file, e.g. .s1p, .s2p, ...).
	

Development
-----------

To modify the UI, you need `pygubu-designer`.

There are sample .json-files in the `res` folder for VS Code.


Known Issues and Missing Features
---------------------------------

- File type registration script for Windows (using `assoc` and `ftype`)
- Filter for listed files (e.g. only show *.s2p)
- Allow user to select between generic and file-specific generated expressions
- Equation-based plot type
- Log output for equations (so that you can also print some data or status)
- Table view of data
- Check if network is reciprocal, passive, lossless, unilateral
- Implement lazy-loading of files (would speed up loading a huge directory, especially when working with cloud-hosted files)
- Allow to provide regex to strip names in expression plots
- Menu command "Add files from directory..."
- Under Fedora Linux, Gnome freezes when you open a non-Touchstone file, then open the same file again with a proper viewer reason unknown
- Get it to work with `pyinstaller` or similar tool
