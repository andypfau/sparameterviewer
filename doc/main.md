S-Parameter Viewer Documentation
================================


Getting Started
---------------

1. Start the app (see [readme](../README.md)).
2. Go *File* → *Open Directory*, and open a directory that contains S-parameter files.
    - Supported format: Touchstone (`.s1p`, `.s2p`...), CITI (`.cti`/`.citi`).
3. At the bottom of the main window, select one or multiple files (hold CTRL to select multiple).
4. Select the parameters you want to see, e.g. *Insertion Loss*, and a format, e.g. *dB*.

### Plottable Parameters

- *All S-Params*: all terms
- *Insertion Loss*: only the $S_{i,j}$-terms, e.g. $S_{21}$ or $S_{12}$.
- *reciprocal/1st only*: e.g. include $S_{21}$, but not $S_{12}$.
- *Return Loss*: only the $S_{i,i}$-terms, e.g. $S_{11}$ or $S_{22}$.
- *Expression-Based*: use expressions (see later section).

### Plot Formats
- *dB*: logarithmic magnitude in decibels (20⋅log10), vs. frequency.
- *Log. Magnitude*: logarithmic magnitude vs. frequency.
- *Linear Magnitude*: linear magnitude vs. frequency; useful to plot some metrics like e.g. VSWR, stability, etc.
- *Re/Im vs. Freq.*: real and imaginary part vs. frequency.
- *Re vs. Freq.*: same as before, but only real part.
- *Im vs. Freq.*: same as before, but only imaginary part.
- *Re/Im Polar*: complex number locus in polar chart (essentially the same as a Smith chart, but with a different grid. visualization)
- *Smith (Impedance)*: Smith chart.
- *Smith (Admittance)*: same as before, but as admittance instead of impedance.
- *Phase*: phase vs. frequency.
- *Unwrapped Phase*: same as before, but phase unwrapped.
- *Linear Phase Removed*: same as before, but with the linear part of the phase removed; useful for physically very long devices.
- *Group Delay*: group delay vs. frequency.
- *Impulse Response*: impulse response vs. time (i.e. time-domain transformation). See also notes below.
- *Step Response*: same as before, but integrated to get step response.

Supported Formats
-----------------

- Touchtone files (.s1p, .s2p, etc.): standard S-parameter files.
- CITI files (.cti or .citi): a data format for n-dimensional data. Since there is no hard specification on the variable names, the following names are assumed (case-insensitive):
    - Frequency: `f`, `freq` or `frequency`.
    - S-parameters: `Sij`, `Si,j`, `S(ij)`, `S(i,j)`, `S[ij]` or `S[i,j]` (where `ij` or `i,j` are the port numbers `i` and `j`), e.g. "S21" or "S[2,1]".
- Zip files (.zip): touchstone and CITI files inside of .zip-files can be extracted as well (see [Settings](settings.md)).

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

Additional Tools
----------------

[See here](tools.md).

Settings
-----------

[See here](settings.md).
