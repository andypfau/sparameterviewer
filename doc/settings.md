Settings
========

In the main window, go Tools -> Settings.

Time-Domain Transformation
--------------------------

- Window: the window function to apply to the spectrum before time-domain transformation.
    - All [SciPy window functions](https://docs.scipy.org/doc/scipy/reference/signal.windows.html) are supported.
- Parameter: parameter for the window. This depends on the selected window.
    - E.g. the Kaiser window has a parameter $\alpha$. Increasing this parameter makes the time-domain transformation more smooth, while reducing it can lead to ringing artifacts.
- Shift: Shift of the time-domain transformation. If this is chosen too small, the vertical dimension of the time-domain transformation may be incorrect. Increase this until the time-domain signal appears to be "stable".
- Convert to Impedance: convert the vertical dimension of the time-domain transform to an impedance, in Ohm.

Theme
-----

- GUI: Select a [Tk](https://tkdocs.com/) theme for the graphical user interface.
- Plot: Select a [matplotlib](https://matplotlib.org/stable/users) theme for the plots.

Miscellaneous
-------------

- Comment-Out Existing Expressions: in the main window, under *Expression*, when you click *Template...*, automatically generated code is added to the expression editor. When this option is enabled, the already existing expressions are commented out (`#`).
- Extract .zip-Files: when this option is enabled, when you load a directory, .zip-files are inspected for supported data files.

External Editor
---------------

Select the executable of an external editor, which is used when you go File -> Open File Externally in the main window.

