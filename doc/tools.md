Additional Tools
================

Tabular Data
------------

Shows the data as a table.

In the main window go *File* → *View Tabular Data*.

You may select:
- Which file to display, and 
- How to display the data, e.g. as real/imaginary, db/degrees, etc.

You can also apply filters:
- *X*: filter X-values (typically the frequency):
    - E.g. "1e9-10e9" to filter from 1 GHz to 10 GHz.
    - E.g. "1e9-*" to filter from 1 GHz, and anything above.
    - E.g. "*-1e9" to filter to 1 GHz, and anything below.
    - To disable filtering, use the wildcard "*".
- *Cols*: filter for columns; just use the name you see in the table columns, separated by whitespace:
    - E.g. "S2,1 S2,2" to filter for these two S-parameters.
    - This filter is ignored for plotted data (which only has one column).
- Clear the filter text to disable filtering (i.e. show all X-values / columns).
- Any invalid filter will result in empty table data.
- Filters are also used when saving files, and when copying data (see below).

From the menu, you can:
- *Save*: export as .csv (tab-separated) or as .xlsx (spreadsheet).
- *Edit*: copy to clipboard, either as CSV-data (comma- or tab-separated), or as Python code which can be used with [NumPy](https://numpy.org/) or with [Pandas](https://pandas.pydata.org/).
- Filters are applied to saved/copied data (see above).

Return Loss Integrator
----------------------

In the main window go *Tools* → *Return Loss Integrator*.

### Theoretical Background

The Bode-Fano limit states that there is an upper bound for the integral over the return loss (RL), from DC to infinite frequency, for a given load circuit (1-port), and an optimum reactive matching network.

This statement can be re-formulated as $BW / f_{center} \cdot RL_{avg} \le Q_{load}^{-1} \cdot const$. The maximum achievable average RL $RL_{avg}$ over a given fractional bandwidth $BW / f_{center}$ is limited by the Q-factor of the load $Q_{load}$ and some constant, such that a higher Q-factor means less (worse) achieavable RL. See also [the Bode-Fano limit](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_III_-_Networks_(Steer)/07%3A_Chapter_7/7.2%3A_Fano-Bode_Limits).

#### Example

You have a load with a series inductance, e.g. a wire-bonded termination. The bondwire behaves inductively, forming a resonant circuit (with some Q-factor) together with the termination. Adding a capacitive patch may improve RL at lower frequencies, at the expense of RL at higher frequencies

### How to Use

To analyze such circuit, you would do the following:
1. Select the circuit; if it is a multi-port, select the appropriate *port*.
2. Integrate over all frequencies, by setting the *Integration* range to "*" (or e.g "0 - 100 GHz").
3. Enter the *Target* range, in which you want to achieve best match, e.g. "1G - 2G" (the wildcard "*" is *not* allowed here).

This will display the following values, and also plot them:
- *Available*: the average return loss over the *integration* range.
- *Current*: the average return loss over the *tartget* range.
- *Achievable*: the theoretical average return loss over the *target* range, *if* an optimum reactive matching network were used.

Note that this tool cannot make any suggestions about *how* the matching network could look like. Neither can it estimate the achieavable RL for multi-ports, where a matching network could be added to each port individually.
