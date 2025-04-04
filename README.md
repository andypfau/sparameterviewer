S-Parameter Viewer
==================

A cross-platform S-parameter Viewer written in Python.

<img src="./doc/screenshot_mainwin_s2p.png" width="250" /> <img src="./doc/screenshot_mainwin_markers.png" width="300" /> <img src="./doc/screenshot_mainwin_expr.png" width="250" />

Main Features
-------------

- Read touchstone (.s#p) and CITI (.cti/.citi) files, including those in .zip-files.
- Various flexible ways of displaying S-parameters, e.g. IL (all/reciprocal) only / RL only, linear/dB/Smith-chart/re-im, impulse/step response, Phase (normal/unwrapped), Group Delay.
- Plotting of Python-based expressions, including functions for stability factors and stability circles, for adding passive elements, checking for passivity/reciprocity/losslessness.
    - to learn more about this feature [see here](./doc/expressions.md).
- Viewing data n various table formats.
- Export data to .csv or .xlsx, copy data as Python code, save plots as images.

Documentation
-------------

[See here](./doc/main.md).

Roadmap
-------


### Missing Features

- Display: more presets, to quickly scroll through all S-parameters
- Add transformations in GUI: TDR, Z, Y, H, ABCD, Reciprocity, Passivity, Losslessness
    - The idea is that the GUI has 3 steps: transform → select parameter → plot format
    - The plot format for step/impulse response would have to be changed to a transformation
- Allow user to select between generic and file-specific generated expressions
- Equation-based plot type
- Log output for equations (so that you can also print some data or status)
- Allow to provide regex to strip names in expression plots
- File type registration script for Windows (using `assoc` and `ftype`)


### Known Issues

- Under Fedora Linux, Gnome freezes when you open a non-Touchstone file, then open the same file again with a proper viewer reason unknown
