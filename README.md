S-Parameter Viewer
==================

A cross-platform S-parameter Viewer written in Python.

<img src="./doc/screenshot_mainwin_s2p.png" width="250" /> <img src="./doc/screenshot_mainwin_markers.png" width="300" /> <img src="./doc/screenshot_mainwin_expr.png" width="250" />


Main Features
-------------

- Various flexible ways of displaying S-parameters, e.g. IL (all/reciprocal) only / RL only, linear/dB/Smith-chart/re-im, impulse/step response, Phase (normal/unwrapped), Group Delay
- Plotting of Python-based expressions, including functions for stability factors and stability circles, for adding passive elements, checking for passivity/reciprocity/losslessness, and for Bode-Fano optimum RL estimation
    - to learn more about this feature, open the "Expressions" tab, and click "Help"
- Export to CSV or XLSX


Prerequisites
-------------

- Python 3.12 (might work with 3.7 or newer, but not tested)
- Packet dependencies: `numpy scipy scikit-rf matplotlib tk pygubu openpyxl appdirs pillow pandas`
    - Under Feodora Linux, you may have to install `python3-pillow-tk` via `dnf`
- Optional packet dependencies:
    - `pyinstaller`: to compile a binary
    - `pywin32`: to copy plot image to clipboard (Windows only)


Usage
-----

- you can just start the app (execute the Python script) and load a directory
    - optional: compile the Python script (see instructions below)
- or you can open one or more file with the app


### Compiling

Compiling is optional. You can just as well run the Python script.

Compiling was successfully tested under Windows 10 and under Fedora 37 with the following command:
- `cd src`
- `pyinstaller pyinstaller.spec`
    - clean build without overwrite-confirmations: `pyinstaller --noconfirm --clean pyinstaller.spec`

Under Fedora 37 at least, I had to fix matplitlib by coping the contents of `src/dist/sparamviewer/matplotlib/mpl-data/` to `share/matplotlib/mpl-data/`.


### File Type Association

#### Linux

To register S-parameter files with this application under Linux:

1. Register a mime-type for S-parameter files using `res/application-x-scatteringparameter.xml` (for instructions, see e.g. <https://help.gnome.org/admin/system-admin-guide/stable/mime-types-custom-user.html>).
2. Double-click any .s#p-file, and select the script `src/sparamviewer.py` (or the binary, if you compiled it) as the application.

#### Windows

To register S-parameter files with this application under Windows:

- If you compiled the script (see instructions above): just Double-click any .s#p-file, and select `src/dist/sparamviewer/sparamviewer.exe` as the application.
- If you want to run the script directly without compiling:
    1. Open `res/sparamviewer.bat` in a text editor.
    2. Adapt the paths to your Python interpreter, as well as the path where `src/sparamviewer.py` is, in the 1st line.
    3. Double-click any .s#p-file, and select the batch-file `res/sparamviewer.bat` as the application .

Uou have to repeat this step for every type of .s#p-file, e.g. .s1p, .s2p, ...


Roadmap
-------


### Missing Features

- Display: more presets, to quickly scroll through all S-parameters
- Add transformations in GUI: TDR, Z, Y, H, ABCD, Reciprocity, Passivity, Losslessness
    - The idea is that the GUI has 3 steps: transform -> select parameter -> plot format
    - The plot format for step/impulse response would have to be changed to a transformation
- Allow user to select between generic and file-specific generated expressions
- Equation-based plot type
- Log output for equations (so that you can also print some data or status)
- Allow to provide regex to strip names in expression plots
- File type registration script for Windows (using `assoc` and `ftype`)


### Known Issues

- Under Fedora Linux, Gnome freezes when you open a non-Touchstone file, then open the same file again with a proper viewer reason unknown


Development
-----------

To modify the UI, you need `pygubu-designer` 0.39.

There are sample .json-files in the `res` folder for VS Code.
