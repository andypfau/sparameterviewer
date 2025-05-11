S-Parameter Viewer Documentation
================================


Getting Started
---------------

1. Start the app (see [readme](howtorun.md)).
2. Go *File* → *Open Directory*, and open a directory that contains S-parameter files.
    - Supported format: Touchstone (`.s1p`, `.s2p`...), CITI (`.cti`/`.citi`).
3. At the bottom of the main window, in the *Files* tab, select one or multiple files (hold *Ctrl* to select multiple).
4. Select the parameters you want to see, e.g. *Insertion Loss*, and a format, e.g. *dB*.

### Files Tab

A list of all available files is shown in the *Files* tab at the bottom of the main window. Select a file to plot it, or hold *Ctrl* and click multiple files.

You can also filter for files by pressing *Ctrl+F* (or in the main menu, go *View* → *Filter Files...*). Enter your search string, press enter, and all files that match the search string will be selected.

To switch to a different directory, or append files from another directory, go *File* → *Open Directory...* or *Append Directory...*. Alternatively, press *Ctrl+B* to show/hide the filesystem browser. Double-clicking a directory in the filesystem browser loads or appends that directory (behavior can be changed in [settings](settings.md)); alternatively, right-click in the filesystem browser to show a popup menu. You can navigate quickly using the breadcrumb bar above the filesystem browser; click a label to navigate, click into the blank area to reveal a textbox; press enter in the textbox to naivgate.

### Plottable Parameters

- *All S-Paramseters*: all terms
- *Insertion Loss*: only the $S_{i,j}$-terms, e.g. $S_{21}$ or $S_{12}$.
- *\* (reciprocal)*: include e.g. $S_{21}$, but not $S_{12}$.
- *Return Loss / Impedance*: only the $S_{i,i}$-terms, e.g. $S_{11}$ or $S_{22}$.
- *Expression-Based*: use expressions (see later section).

### Plot Formats

Primary:
- *dB*: logarithmic magnitude in decibels (20⋅log10), vs. frequency.
- *Log Mag*: logarithmic magnitude vs. frequency.
- *Lin Mag*: linear magnitude vs. frequency; useful to plot some metrics like e.g. VSWR, stability, etc.
- *Real/Imag*: real and imaginary part vs. frequency.
- *Real*: same as above, but only real part.
- *Imag*: same as above, but only imaginary part.
- *Re/Im Polar*: complex number locus in polar chart (essentially the same as a Smith chart, but with a different grid. visualization)
- *Smith (Z)*: Smith chart.
- *Smith (Y)*: same as above, but as admittance instead of impedance.
- *Impulse Resp.*: impulse response vs. time (i.e. time-domain transformation). See also notes below.
- *Step Resp.*: same as above, but integrated to get step response.

Secondary:
- *Phase*: phase vs. frequency.
- *Unwrapped*: same as above, but phase unwrapped.
- *Lin. Removed*: same as above, but with the linear part of the phase removed (de-trended); useful to see phase variations on physically long devices.
- *Group Delay*: group delay vs. frequency.

Primary and secondary format can be shown simultaneously (using a secondary Y-axis).

#### Time-Domain Transformation

The impulse response is calculated as follows:
1. Extrapolate frequency axis to DC.
    - The algorithm from [IEEE370](https://standards.ieee.org/ieee/370/6165/), Annex T is used.
2. Interpolate frequency axis to get equidistant scaling.
    - Interpolation is done in polar domain (i.e. interpolation of magnitude and of unwrapped phase separately).
3. Apply window function.
    - Window function can be chosen in [settings](settings.md).
    - If you see excess ringing in the time-domain response, you may try to use e.g. a Kaiser window, and increase the parameter.
    - If the time-domain response is too much smoothed-out, you may try to use e.g. a Kaiser window, and decrease the parameter.
4. Apply zero-padding.
    - Under [settings](settings.md), a minimum number of samples, to which is zero-padded, can be chosen.
    - Increase this setting to get finer interpolation of the time axis.
5. Apply inverse FFT.
6. Shift samples.
    - The amount of shift can be chosen in [settings](settings.md).
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
-----------

[See here](settings.md).

Supported File Formats
----------------------

- Touchtone files (.s1p, .s2p, etc.): standard S-parameter files.
- CITI files (.cti or .citi): a data format for n-dimensional data. Since there is no hard specification on the variable names, the following names are assumed (case-insensitive):
    - Frequency: `f`, `Freq` or `Frequency`.
    - S-parameters: `Sij`, `Si,j`, `S(ij)`, `S(i,j)`, `S[ij]` or `S[i,j]` (where `ij` or `i,j` are the port numbers `i` and `j`), e.g. "S21" or "S[2,1]".
- Zip files (.zip): touchstone and CITI files inside of .zip-files can be extracted as well (see [Settings](settings.md)).
