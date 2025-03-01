Additional Tools
================

Tablular

Optimum RL Calculator
---------------------

Allows you to calculate the maximum achievable return loss (RL), if matched optimally.

This is done by calculating the integral of the RL over a given (wide) freqeuncy interval, and then calculating the mean RL in a narrower freqeuncy interval (Bode-Fano limit).

Example: you have an RF structure that must be operational from 4 GHz to 6 GHz. You measure the S-parameters from 10 MHz to 8 GHz, and the calculated mean RL (result of the integration) is 10 dB. With optimum matching, using only reactive components, you could theoretically achieve 39.95 dB RL in the 4..6 GHz region. This of course would mean that the frequencies below 4 GHz, and above 6 GHz would then have to be completely mismatched.

One theoretical example of such a scenario could be an inductive series element, which ruins the match. Adding capacitve pads to either end of the inductive element could form a band-pass structure, which has the same or at least similar integrated RL, but a much better RL within a narrow frequency interval, while outside of that interval the RL becomes worse.

This tool can make no suggestions about *how* to achieve the matching.
