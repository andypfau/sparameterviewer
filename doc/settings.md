Settings
========

In the main window, go *Tools* → *Settings*.

Formats
-------

- *Trace Color*:
    - *Defeault*: each trace gets a color assinged by the plotting library.
    - *By Parameter*: distinguish parameter types (e.g. S11, S21, ...) by color.
    - *By File*: distinguish files by color.
    - *By File Location*: distinguish files from different directories/archives by color.
    - For even more flexibility, you may use expressions, e.g. `nws("*filter*").s(2,1).plot(color="red")` (see [Expressions](expressions.md))
- *Phase*: unit (degrees or radians) of the phase of a parameter.
- *CSV Separator*: the separator for CSV-files (see [Tabular Data](tools.md))


Time-Domain
-----------

These settings apply to the impulse- and step response of parameters. See [Time-Domain Transformation](main.md) to learn more about the impact of these settings.

- *Window*: the window function to apply to the spectrum before time-domain transformation.
    - All [SciPy window functions](https://docs.scipy.org/doc/scipy/reference/signal.windows.html) are supported.
- *Parameter*: parameter for the window. This depends on the selected window.
    - E.g. the Kaiser window has a parameter $\alpha$. Many windows, e.g. Hann, do not have any parameter (in which case it is ignored).
- *Min. Size*: the minimum number of samples to which is zero-padded.
- *Shift*: Shift of the time-domain transformation.
- *Convert to Impedance*: convert the vertical dimension of the time-domain transform to an impedance, in Ohm.

Files
-----

- *Extract .zip-Files*: when this option is enabled, when you load a directory, .zip-files are inspected for supported data files.
- *Show Files in Filesystem*: Show or hide files in the filesystem browser.
- *Doubleclick Filesystem*: When double-clicking an item in the [filesystem browser](main.md), switch to that directory (i.e. remove all current files from the file list), or append all files from that directory to the files list.
- *Recent Directory*: Same as previous option, but for the main menu item *File* → *Recent Directories*.

Misc
-----

- *Comment-Out Existing Expressions*: in the main window, under *Expression*, when you click *Template...*, automatically generated code is added to the expression editor. When this option is enabled, the already existing expressions are commented out (`#`).
- *Cursor Snap*: how to move the [cursors](main.md); either move the cursor to the X-coordinate of the mouse pointer, or find the point on the trace that is closest to the mouse pointer.
- *Plot Style*: Select a [matplotlib](https://matplotlib.org/stable/users) theme for the plots.
- *Editor Font*: select a font for all plaintext-editors in the app.
- *External Editor*: select the executable of an external editor, which is used when you go File → Open File Externally in the main window.
