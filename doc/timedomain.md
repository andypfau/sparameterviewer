Time-Domain Transformation
==========================

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
