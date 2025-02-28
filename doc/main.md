


Parameters:

- *All S-Params*: all terms
- *Insertion Loss*: only the $S_{i,j}$-terms, e.g. $S_{21}$ or $S_{12}$.
- *reciprocal/1st only*: e.g. include $S_{21}$, but not $S_{12}$.
- *Return Loss*: only the $S_{i,i}$-terms, e.g. $S_{11}$ or $S_{22}$.
- *Expression-Based*: use expressions (see later section).

Formats:
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

About time-domain: the transformation happens in the following stages:
- If requried, extrapolate S-parameters to DC (see see IEEE370, Annex T).
    - This step can be a major cause of uncertainty, if the data does not contain low frequencies.
- If requried, interpoate frequency axis to get equidistant spacing.
    - Interpolation is done on magnitude and on unwrapped phase separately, i.e. in polar coordinates.
- Apply windowing, apply FFT.
- Un-shift frequency-domain data.
- Optional: convert to impedance.

Typical pitfalls:
- If possible, use S-parameters that include lowest frequencies, and have an equdistant frequenc spacing.
- Settings in *Tools* → *Settings* → *Time-Domain Transform*:
    - If the time-domain response appears too noisy, try to incrase the window argument. If it appears too much smoothed out, try to decrease it.
    - If the time-domain response appears non-causal, or appears to have unreasonable Y-units, try to increase the shift.



Expression: