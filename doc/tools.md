Additional Tools
================

Tabular Data
------------

Shows the data as a table.

In the main window go *File* → *View Tabular Data*.

You may select:
- Which file to display, and 
- How to display the data, e.g. as real/imaginary, db/degrees, etc.

You can also apply filters by checking the corresponding checkboxes:
- *X*: filter X-values (typically the frequency):
    - E.g. "1e9-10e9" to filter from 1 GHz to 10 GHz.
    - E.g. "1e9-*" to filter from 1 GHz, and anything above.
    - E.g. "*-1e9" to filter to 1 GHz, and anything below.
- *Cols*: filter for cols; just use the name you see in the table columns, separated by whitespace:
    - E.g. "S2,1 S2,2" to filter for these two S-parameters.
    - This filter is ignored for plotted data (which only has one column).
- Clear the filter text to disable filtering (i.e. show all X-values / columns).
- Any invalid filter will result in empty table data.
- Filters are also used when saving files, and when copying data (see below).

From the menu, you can:
- *Save*: export as .csv (tab-separated) or as .xlsx (spreadsheet).
- *Edit*: copy to clipboard, either as CSV-data (comma- or tab-separated), or as Python code which can be used with [NumPy](https://numpy.org/).
- Filters are applied to saved/copied data (see above).

Trace Cursors
-------------

Allows you to read values from the plot using cursors.

In the main window go *Tools* → *Trace Cursors*.

Just click in the plot, and the reading is shown in the dialog. You may select one of two cursors, or let the tool select the closest cursor automatically (*Auto*). You may specify a specific trace, or let the tool snap the cursor to the closest trace (*Auto*).

⚠️ Pitfall: if you selected a tool the pan or zoom tool in the plot, it will pan/zoom! De-select the tools in the plot before using cursors.


Optimum RL Calculator
---------------------

Allows you to calculate the maximum achievable return loss (RL), if matched optimally with a *reactive* component.

In the main window go *Tools* → *Optimum RL Calculator*.

This is done by calculating the integral of the RL over a given (wide) freqeuncy interval, and then calculating the mean RL in a narrower freqeuncy interval. This is based on the idea of the [the Bode-Fano limit](https://eng.libretexts.org/Bookshelves/Electrical_Engineering/Electronics/Microwave_and_RF_Design_III_-_Networks_(Steer)/07%3A_Chapter_7/7.2%3A_Fano-Bode_Limits).

### Theoretical Background

Example: you have an RF structure that must be operational from 4 GHz to 6 GHz. You measure the S-parameters from 10 MHz to 8 GHz (i.e. the intgration range), and the calculated mean RL (result of the integration) is 10 dB. When matching the network with a single reactive component, you could theoretically achieve 39.95 dB RL in the 4..6 GHz region (i.e. the target range). This of course would mean that the frequencies below 4 GHz, and above 6 GHz would then have to be completely mismatched.

A more practical example would be a bond wire. A bond wire will inherently behave inductively, thus deterioraring match (worse RL) towards higher frequencies. By adding a stub capacitor to GND (e.g. a small metal patch), match can be improved (better RL). However, this will also inherently reduce the bandwidth of the circuit. In this example:
- The integration range is the frequency range over which you measure the return loss of the bond wire structure.
- The target range is the frequency range over which you want to achieve optimum match. It is inherently lower than the integration range.

You may also ask the opposite question: if I have a good match over a given integration range, what match could I achive oder a *wider* target range? This would of course yield an inferior match (worse RL).

Note that:
- This tool can make no suggestions about *how* the reactive matching network may look like.
- With resistive matching, typically even better match can be achieved, at the expense of additional loss.
- Even with purely reactive matching, sometimes even better match can be achieved when using *multiple* reactive elements.

### Usage

Valid entries for the integrtion range:
- E.g. "1e9-10e9" to integrate from 1 GHz to 10 GHz.
- E.g. "1e9-*" to integrate from 1 GHz, to the highest frequency of the data.
- E.g. "*-10e9" to integrate from the lowest frequency of the data, to 10 GHz.

Valid entries for the target range are the same, except that "*" is not allowed.

The diagram can be switched between a Bode plot, and a histogram.
