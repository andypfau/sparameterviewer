S-Parameter Viewer
==================

A cross-platform S-parameter Viewer written in Python.

<img src="./doc/screenshot_mainwin.png" width="250" /> <img src="./doc/screenshot_mainwin_expr.png" width="250" />

Main Features
-------------

- Visualize touchstone and Citi files, including those inside of .zip-files.
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

- Samples: a CITI file.
- Expressions: review the examples for the `map()` function, I think they do not work. Is the `map()` function really intuitive to use?
- GUI: find a way to present the large matrix in a bigger form, e.g. as a dialog.
- GUI: find a way to set define fixed size for saved/copied plots.
- GUI: for the documentations, find a nicer representation than plain markdown files.
- General: "TODO"-comments in code.
- File handling: show correct parameter names of mixed-mode parameters in `Networks.s()`, and in the GUI.
- Expressions: `f_arg` parameter for `SParams.map()`.
- Expressions: add more metadata to each SParams object, so I can track the origin (file, parameter, equstion) separately; then I could add a function to e.g. define the color by origin file.
- Expressions: function to set plot type (i.e. when I run that equation, it automatically sets up the plot type).
- File type registration script for Windows (using `assoc` and `ftype`).


### Known Issues

- The Smith chart is based on Scikit RF, and behaves a bit different from other plots, e.g. it will always display the grid, regardless of whether "Show Grid" is selected or not.
