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

- GUI: a control to select individual parameters when grid is too large.
- GUI: allow to enter frequency to set cursor position.
- GUI: allow to re-arrange the three main components (toolbar, plot, files) in a "T".
- GUI: simplified UI options (dropdowns for parameters and plots; hide expressions; simplified file browser).
- GUI: equation file history.
- Expressions: better interaction with Numpy.
- Expressions: function to set plot type (i.e. when I run that equation, it automatically sets up the plot type).
- Expressions: log output for equations (so that you can also print some data or status).
- File type registration script for Windows (using `assoc` and `ftype`).


### Known Issues

- Under Fedora Linux, Gnome freezes when you open a non-Touchstone file, then open the same file again with a proper viewer reason unknown
