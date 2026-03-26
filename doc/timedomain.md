Time-Domain Transformation
==========================

The time-domain response is calculated as follows:

1. Extrapolate frequency axis to DC. Three algorithms are available:
    - No extrapolation. Requires a slow DFT algorithm.
    - Extrapolation using [IEEE370, Annex T](https://standards.ieee.org/ieee/370/6165/). Works well for many networks.
        - Makes the assumption that the spectrum must be Hermitean, i.e. real part is mirrored, and imaginary part must cross zero.
    - Extrapolation in polar coordinates. May work better for electicrally long networks.
        - Makes the assumption that the phase at DC must be 0° or 180°, to ensure the DC component is real-valued.
        - A real-valued DC can also be ensured by a zero magnitude:
            - Choosing "Zero" always assumes a zero magnitude at DC (and makes no further assumption on the phase).
            - Choosing "Auto" checks if the magnitude roughly extrapolates to zero, and if so, makes that assumption (and makes no further assumption on the phase).
            - Choosing "None" never makes an assumptio about the magitude, and assumes a 0° or 180° DC phase.
2. Interpolate frequency axis to get equidistant scaling.
    - Interpolation is done in polar domain (i.e. interpolation of magnitude and of unwrapped phase separately).
    - This step is skipped when extrapolation is turned off.
3. Apply window function.
    - Window function can be chosen in the menu.
    - If you see excess ringing in the time-domain response, you may try to use e.g. a Kaiser window, and increase the parameter.
        - If the time-domain response is too much smoothed-out, decrease the parameter.
4. Apply zero-padding.
    - In the menu, a minimum number of samples, to which is zero-padded, can be chosen.
    - Increase this setting to get finer interpolation of the time axis.
5. Apply inverse FFT.
    - The result is the time-domain impulse response.
    - Only possible if the spectrum starts at DC, and frequencies are equidistant; otherwise, a slower DFT algorithm is used. Use extrapolation and interpolation to ensure using the faster FFT algorithm is possible.
6. Shift samples.
    - The amount of shift can be chosen in the menu.
    - If this setting is chosen too small, the vertical dimension of the time-domain transformation may be incorrect. Increase this setting until the time-domain signal appears to be "stable".
7. Optional: get the step response by integrating over the impulse response.
8. Optional: get the impedance by applying $Z(S)=Z_0 \cdot \frac{1+S}{1-S}$.
    - Use this on Sii, together with step response, to estimate the DUT's impedance distribution.
