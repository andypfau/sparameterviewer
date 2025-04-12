Settings
========

In the main window, go *Tools* → *Settings*.

Time-Domain Transformation
--------------------------

See [Time-Domain Transformation](main.md) to learn more about the impact of these settings.

- Window: the window function to apply to the spectrum before time-domain transformation.
    - All [SciPy window functions](https://docs.scipy.org/doc/scipy/reference/signal.windows.html) are supported.
- Parameter: parameter for the window. This depends on the selected window.
    - E.g. the Kaiser window has a parameter $\alpha$. Many windows, e.g. Hann, do not have any parameter (in which case it is ignored).
- Min. Size: the minimum number of samples to which is zero-padded.
- Shift: Shift of the time-domain transformation.
- Convert to Impedance: convert the vertical dimension of the time-domain transform to an impedance, in Ohm.

Theme
-----

- Plot: Select a [matplotlib](https://matplotlib.org/stable/users) theme for the plots.

Miscellaneous
-------------

- Comment-Out Existing Expressions: in the main window, under *Expression*, when you click *Template...*, automatically generated code is added to the expression editor. When this option is enabled, the already existing expressions are commented out (`#`).
- Extract .zip-Files: when this option is enabled, when you load a directory, .zip-files are inspected for supported data files.

External Editor
---------------

Select the executable of an external editor, which is used when you go File -> Open File Externally in the main window.

