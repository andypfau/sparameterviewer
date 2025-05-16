S-Parameter Viewer
==================

A cross-platform S-parameter Viewer written in Python.

<img src="./doc/screenshot_mainwin_markers.png" width="250" /> <img src="./doc/screenshot_mainwin_expr.png" width="250" />

Main Features
-------------

- Read touchstone (.s1p, .s2p, ...) and CITI (.cti/.citi) files, including those in .zip-files.
- Various flexible ways of displaying S-parameters, e.g. IL (all/reciprocal) only / RL only, linear/dB/Smith-chart/re-im, impulse/step response, Phase (normal/unwrapped), Group Delay.
- Plotting of Python-based expressions, including functions for stability factors and stability circles, for adding passive elements, checking for passivity/reciprocity/losslessness.
    - to learn more about this feature [see here](./doc/expressions.md).
- Viewing data in various table formats (e.g. dB, linear, real/imaginary, phase).
- Export data to .csv or .xlsx, copy data as Python code, save plots as images.

Documentation
-------------

[See here](./doc/main.md).

Roadmap
-------


### Missing Features

- GUI: a toolbar/ribbon.
    - Also allow phase unit and trace color to be selected.
    - Try to merge the pan/zoom tools into toolbar.
- GUI: a control to qickly select individual parameters in a matrix-style visualization (e.g. a grid of checkboxes).
- GUI: allow to enter frequency to set cursor position.
- Display: more presets, to quickly scroll through all S-parameters.
- Add transformations in GUI: TDR, Z, Y, H, ABCD, Reciprocity, Passivity, Losslessness.
    - The idea is that the GUI has 3 steps: transform → select parameter → plot format.
    - The plot format for step/impulse response would have to be changed to a transformation.
- Allow user to select between generic and file-specific generated expressions.
- Equation file history.
- Equation-based plot type (i.e. when I run that equation, it automatically sets up the plot type).
- Log output for equations (so that you can also print some data or status).
- Allow to provide regex to strip names in expression plots.
- File type registration script for Windows (using `assoc` and `ftype`).


### Known Issues

- Under Fedora Linux, Gnome freezes when you open a non-Touchstone file, then open the same file again with a proper viewer reason unknown
