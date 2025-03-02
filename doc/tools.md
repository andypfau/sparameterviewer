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

Allows you to calculate the maximum achievable return loss (RL), if matched optimally.

In the main window go *Tools* → *Optimum RL Calculator*.

This is done by calculating the integral of the RL over a given (wide) freqeuncy interval, and then calculating the mean RL in a narrower freqeuncy interval (Bode-Fano limit).

Example: you have an RF structure that must be operational from 4 GHz to 6 GHz. You measure the S-parameters from 10 MHz to 8 GHz, and the calculated mean RL (result of the integration) is 10 dB. With optimum matching, using only reactive components, you could theoretically achieve 39.95 dB RL in the 4..6 GHz region. This of course would mean that the frequencies below 4 GHz, and above 6 GHz would then have to be completely mismatched.

One theoretical example of such a scenario could be an inductive series element, which ruins the match. Adding capacitve pads to either end of the inductive element could form a band-pass structure, which has the same or at least similar integrated RL, but a much better RL within a narrow frequency interval, while outside of that interval the RL becomes worse.

This tool can make no suggestions about *how* to achieve the matching.
