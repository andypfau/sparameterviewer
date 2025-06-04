S-Parameter Viewer Documentation
================================


Getting Started
---------------

Quick start:
1. Select files you want to plot in the filesystem browser.
2. Select which parameters to plot, and how to plot them, in the toolbar.

### Toolbar

The toolbar has several sections, from left-to right:
1. Main menu.
2. Parameter Selection:
    - The buttons allow to qickly select the most important parameters. Hold *Ctrl* to toggle.
    - The matrix allows to select individual parameters. Hold *Ctrl* to toggle, hold *Shift* to select diagonal/triangular.
3. Plot Selection:
    - Cartesian (vs. frequency), time-domain, Smith, or polar.
    - Cartesian allows to use a secondary Y-axis.
    - The menu provides additional options.
4. Axis Ranges:
    - Enter a range, e.g. "0..20G" for 0 to 20 GHz, or "*" for auto-scale.
    - Use the lock buttons to toggle between a fixed range, or auto-scale.
    - You can enable smart dB scaling (only if Y-axis is in dB), which attempts to focus on the upper region of the S-parameters.
5. Plot Options: legend, trace options, plot tools; additional options in the menu.
6. Tools: quickly filter files, show/copy/save different representations, copy/save image; additional tools in the menu.
7. Miscellaneous: help, settings dialog.

### Filesystem Browser

How to navigate:
- Use the breadcrumb bar (hidden when multiple/no directories are selected), or the buttons next to it.
- Use "Open Directory" from the main menu.
- Right-click a directory (hidden when simplified filesystem browser is enabled in settings).

How to select files for plotting:
- All checked files are plotted.
- To check a range of files, just select them (hold *Ctrl* to select multiple files, or to select a range).

### Cartesian Plot Formats

You can choose between decibels, magnitude, real or imaginary values on the Y-axis. Additionally, the phase or group delay can be plotted on a secondary Y-axis. Phase can be unwrapped, or un-wrapped and de-trended. The latter may be useful to see phase variations on physically long devices.

When expressions are used, the plotted data may already be purely real-valued data. In that case, the value is plotted directly. In the settings you can override this behavior, so that even real-valued expressions are converted to decibels/magnitude/phase/etc.

#### Time-Domain Transformation

The impulse response is calculated as follows:
1. Extrapolate frequency axis to DC.
    - The algorithm from [IEEE370](https://standards.ieee.org/ieee/370/6165/), Annex T is used.
2. Interpolate frequency axis to get equidistant scaling.
    - Interpolation is done in polar domain (i.e. interpolation of magnitude and of unwrapped phase separately).
3. Apply window function.
    - Window function can be chosen in the menu.
    - If you see excess ringing in the time-domain response, you may try to use e.g. a Kaiser window, and increase the parameter.
    - If the time-domain response is too much smoothed-out, you may try to use e.g. a Kaiser window, and decrease the parameter.
4. Apply zero-padding.
    - In the menu, a minimum number of samples, to which is zero-padded, can be chosen.
    - Increase this setting to get finer interpolation of the time axis.
5. Apply inverse FFT.
6. Shift samples.
    - The amount of shift can be chosen in the menu.
    - If this setting is chosen too small, the vertical dimension of the time-domain transformation may be incorrect. Increase this setting until the time-domain signal appears to be "stable".

The step response works the same, except that the result is integrated over time.

### Other Visualizations

- *File* → *View/Export Tabular Data*: show data as table, and export data in various formats; see [Tools](tools.md).
- *File* → *View Plaintext Data*: show file contents as plaintext.
- *File* → *Open Externally*: load file in external editor.
- *Tools* → *Return Loss Integrator*: see [Tools](tools.md).

Plot Menu
---------

In the main window, the *Plot* menu has some useful functions:
- *Show Legend*: show legend in plot.
- *Hide Single-Item Legend*: hide the legend if only one single trace is shown.
- *Shorten Legen Items*: attempt to shorten the legend such that it is still readable an unambiguous.
- *Copy Image to Clipboard*: copy the plot to clipboard (requires the optional `copykitten` Python package).
- *Logarithmic Frequency*: X-axis is logarithmic; otherwise it is linear.
- *Lock Y-Axis* / *Lock Y-Axis* / *Lock both Axes*: keep the current scale of the X/Y axis, even when selecting differnet files.
- *Unlock both Axes*: reverts axis locking.
- *Re-scale locked Axes*: when scales are locked, re-scale them once, then keep them locked again.
- *Manual axes...*: opens a dialog where you can specify exact axis ranges.
- *Mark points*: show markers on every data point.
- *Update Plot From Expressions*: when you edit expressions (see next section), the plot is only updated after you click this (or press F5).

Expressions
-----------

[See here](expressions.md).


Cursors
-------

Allows you to read values from the plot using cursors.

Just click in the plot, and the reading is shown in the dialog. You may select one of two cursors, or let the tool select the closest cursor automatically (*Auto*). You may specify a specific trace, or let the tool snap the cursor to the closest trace (*Auto*).

Note that you can only apply cursors to traces on the primary (left) Y-axis. If you want to use cursors on e.g. phase, disable the primary unit.

Additional Tools
----------------

[See here](tools.md).

Settings
--------

You can open the settings from the toolbar, or by pressing F4.

Most settings become active immediately.

Use the mouse-over tooltips to learn more about each setting in the settings dialog.

Supported File Formats
----------------------

- Touchtone files (.s1p, .s2p, etc.): standard S-parameter files.
- CITI files (.cti or .citi): a data format for n-dimensional data. Since there is no hard specification on the variable names, the following names are assumed (case-insensitive):
    - Frequency: `f`, `Freq` or `Frequency`.
    - S-parameters: `Sij`, `Si,j`, `S(ij)`, `S(i,j)`, `S[ij]` or `S[i,j]` (where `ij` or `i,j` are the port numbers `i` and `j`), e.g. "S21" or "S[2,1]".
- Zip files (.zip): touchstone and CITI files inside of .zip-files can be extracted as well (can be configured in the settings dialog).
