S-Parameter Viewer Changelog
============================


0.42b2 (2026-01-20)
--------------------

- new: option to show cursor readout in the plot
- new: setting to enable window restore
- enhancement: improved the window size restore mechanism
- bugfix: pasting formatted text into the expression editor now drops the formatting, and properly applies syntax highlighting


0.42b1 (2026-01-15)
--------------------

- new: filesystem viewer context menu items to change label, color and style of plots
- new: restoring main window size after starting application
- bugfix: fixed a matpltotlib warning


0.41b8 (2026-01-05)
--------------------

- new: GUI option to manually choose legend position
- new: access to Python's `logging` module in expressions


0.41b7 (2026-01-02)
--------------------

- new: `Networks.nf()` and `Networks.noisefactor()` now have optional argument `z` to explicitly set the reference impedance for noise calculation
- bugfix: `Networks.nf()` and `Networks.noisefactor()` now display the correct noise figure/factor


0.41b6 (2025-12-24)
--------------------

- new: option to show grid
- bugfix: displaying S11 and S22 at the same time, for a network with more than 2 dimensions
- bugfix: plotting Sii as dashed line if both Sii and Sij are displayed, for a network with more than 2 dimensions


0.41b5 (2025-12-07)
--------------------

- new: centered range input, e.g. "10G +- 1G" (instead of "9G - 11 G")


0.41b4 (2025-12-04)
--------------------

- new: `Networks.nf()` and `Networks.noisefactor()`


0.41b3 (2025-12-02)
--------------------

- new: templates for statistics
- new: hold CTRL when selecting a template to toggle commenting of existing code
- change: standard deviations are now calculated on data-in-dB by default


0.41b2 (2025-12-01)
--------------------

- new: `Networks.plot_stab()` and `Networks.plot_noise()` accept array arguments


0.41b1 (2025-11-30)
--------------------

- new: access to new `Comp` namespace from expressions, to generate paramtric components; the methods `Networks.add_r()` etc. are marked as obsolete
- new: access to `cmath` from expressions
- new: enhanced the `Networks.plot_stab()` method, it can now plot muiltiple stability circles
- new: button to scale polar and Smith diagrams to the unit circle
- new: stability functions `Networks.delta()` and `Networks.b1()`
- new: noise functions `Networks.f_min()`, `Networks.nf_min()`, `Networks.gamma_opt()`, `Networks.z_opt()`, `Networks.rn()`, `Networks.plot_noise()`
- change: improved the legend title shortening algorithm
- bugfix: line/marker styling in Smith diagrams


0.40b32 (2025-11-24)
--------------------

- bugfix: fixed orientation of stability circles
- bugfix: treating parameters as vector-like (e.g. S-parameters), magnitude-like, or scalar-like (e.g. k or µ), so that e.g. the k-factor can no longer be converted to dB


0.40b31 (2025-11-20)
--------------------

- new: open file with external default application from filesystem browser contetxt menu
- new: buttons to save/load expressions, with file history
- change: nicer file info
- bugfix: filtering with wildcards is working again


0.40b30 (2025-11-19)
--------------------

- bugfix: changing the trace of a cursor now properly updates the readout


0.40b29 (2025-10-22)
--------------------

- change: showing absolute path in 2nd colum to make the filesystem browser a bit less wide
- new: showing dummy element in filesystem browser if files are filtered out; can disable filter via context menu


0.40b28 (2025-10-21)
--------------------

- new: a real "filter" feature; the old feature is now a "select" feature, but kept the same shortcut
- new: feature to choose light or dark color scheme


0.40b27 (2025-10-14)
--------------------

- new: checkbox to toggle fine cursor placement
- new: marking the template reference file with "REF" in the "Info" column in the filesystem browser
- new: buttons to zoom in/out


0.40b26 (2025-10-10)
--------------------

- new: cursor can now be fine-placed at an interpolated position, if zoomed in deep enough


0.40b25 (2025-10-09)
--------------------

- new: can now zoom/pan while cursors are active


0.40b24 (2025-09-30)
--------------------

- new: when clicked items are not selected, you can now double-click a file to select it
- change: fixed tab order of the X- and Y-axis combo boxes
- bugfix: removing locked axes when changing chart


0.40b23 (2025-09-26)
--------------------

- new: more keys to check or un-check items in the filesystem browser


0.40b22 (2025-09-24)
--------------------

- new: press spacebar to toggle checked-state of selected items in filesystem view
- new: option to disable the feature that selected items are checked


0.40b21 (2025-09-23)
--------------------

- change: allowing operations `+ - * @ /` between `Networks` objects


0.40b20 (2025-09-18)
--------------------

- bugfix: properly activating expressions when using a template


0.40b19 (2025-09-02)
--------------------

- bugfix: showing *.cti-files in file list


0.40b18 (2025-09-01)
--------------------

- new: traces with only one point are always shown as point, even when "Mark Data Points" off
- new: when a file fails to load, its file path and other info is now shown in the file info dialog
- bugfix: fixed some crashes when loading files with less than two points


0.40b17 (2025-08-09)
--------------------

- new: re-loading all paths on startup


0.40b16 (2025-07-31)
--------------------

- new: option to make the parameter selector still clickable when there are too many elements; double-click to expand


0.40b15 (2025-07-22)
--------------------

- new: `SParams` methods `min()`, `max()` and `rsdev()`
- new: creating a meaningful log message when `nws()` does not match any network
- bugfix: creating a proper `SParams` object from empty input dataset


0.40b14 (2025-07-09)
--------------------

- bugfix: de-selecting items that are un-checked, to prevent unexpected behavior


0.40b13 (2025-07-07)
--------------------

- bugfix: fixed expressions of format `SParams / const`, e.g. `(sel_nws().s(2,1) / 2).plot()`


0.40b12 (2025-07-02)
--------------------

- new: setting to select between static and dynamic references in templates
- enhancement: workaround for some non-standard touchstone file formats


0.40b11 (2025-06-25)
--------------------

- enhancement: better handling of manual zooming/panning


0.40b10 (2025-06-19)
--------------------

- enhancement: better dB scaling (now tries to distinguish insertion loss parameters, which are fully shown, from reutrn loss / isolation parameters, which are scaled)
- enhancement: better string shortening (can no elide multiple segments of the name)
- bugfix: binary operators on `SParams` work again (e.g. `(nw("a.s2p").s(2,1) / nw("b.s2p").s(2,1)).plot()` crashed before)
- bugfix: fixed `SParams.ml()` (didn't take square root, which resulted in wrong level when using dB scale)
- bugfix: the help-button and the F1-shortcut work again
- bugfix: showing all comment lines of a file


0.40b9 (2025-06-15)
-------------------

- new: `Networks.sel_params()` and `SParams.norm()` methods
- new: by right-clicking a file in the filesystem browser, it can now be saved to be used in templates
- bugfix: various small fixes


0.40b8 (2025-06-10)
-------------------

- enhancement: can now manually override selection in the filter dialog
- bugfix: various small fixes


0.40b7 (2025-06-09)
-------------------

- bugfix: various small fixes


0.40b6 (2025-06-05)
-------------------

- change: when loading takes too long, a red button appears in the toolbar (instead of the messagebox)
- enhancement: template for normalization, better templates for de-embedding, added function to multiply or divide networks


0.40b5 (2025-06-04)
-------------------

- enhancement: better syntax highlighting, better comment function in text editor
- change: highlight of expressions tab when active
- new: tooltips in settings dialog
- bugfix: better input handling of text boxes


0.40b4 (2025-06-03)
-------------------

- change: various UI tweaks and fixes


0.40b3 (2025-05-28)
-------------------

- new: more compact menu and toolbar
- new: option to plot semi-transparent
- new: remembering last cursors
- change: warning when loading takes too long (rather than just counting files)
- bugfix: many UI-related bugfixes and enhancements


0.40b2 (2025-05-24)
-------------------

- new: options for simplified UI
- new: ultra-wide layout
- new: can move cursor by entering X-position
- new: enhanced file filtering
- new: `Networks.plot_sel_params()`
- change: simplified and unified the functions for reciprocity/stability/symmetry/losslessness
- bugfix: many UI-related bugfixes and enhancements


0.40b1 (2025-05-17)
-------------------

- new: new UI (unified file browser; toolbar; more dynamic statusbar; flexible parameter selection; wide mode)


0.32b1 (2025-05-14)
-------------------

- new: revised filesystem browser
- new: option to assing trace colors by parameter, file path, or file location


0.31b2 (2025-05-11)
-------------------

- new: breadcrumb bar for filesystem browser
- new: warn when too many files are loaded
- bugfix: prevent files from being added multiple times


0.31b1 (2025-05-10)
-------------------

- new: parameters `color` and `width` for `plot()`
- change: more flexible arguments for `Networks.s()`
- new: added `z()`, `y()`, `abcd()` and `t()` to `Networks`
- change: removed `s2z()`, `s2y()` from `Networks`
- new: filesystem browser


0.30b1 (2025-04-14)
-------------------

- change: migrated from Tk to Qt


0.29b1 (2025-04-03)
-------------------

- new: seconary Y-axis for phase or group delay
- new: setting to change unit of phase


0.28b2 (2025-03-18)
-------------------

- new: method `SParams.map()`, which allows to apply arbitrary NumPy functions to S-parameters
- new: method `SParams.rename()` to rename a trace
- new: method `Networks.rewire()`, which allows to re-map port numbers


0.28b1 (2025-03-11)
-------------------

- new: statistical methods `mean()`, `median()`, `sdev()`
- new: frequency interpolation methods `interpolate()`, `interpolate_lin()`, `interpolate_log()`


0.27b4 (2025-03-09)
-------------------

- bugfix: preventing tabular dialog from re-sizing automatically


0.27b3 (2025-03-06)
-------------------

- bugfix: loading recent now working properly
- change: cleaned up the RL calculator


0.27b2 (2025-03-04)
-------------------

- new: interpolation of time-axis for impulse/step response
- new: copy tabular data for use with Pandas
- change: better format when copying data for use with NumPy


0.27b1 (2025-03-02)
-------------------

- new: filters in tabular dialog
- change: more intuitive input handling of frequency ranges, e.g. "1G - 10G"


0.26b1 (2025-02-28)
-------------------

- new: load .zip-files
- change: improved information from delta cursors


0.25b3 (2025-02-24)
-------------------

- new: function `vswr()` to calculate VSWR
- new: new sample `dipole.s1p`
- new: histogram in RL integrator
- new: option to comment exisiting expressions, when adding a new expression from a template (previously this way always the case)
- bugfix: no longer showing losslessness ij metric for 1-ports

0.25b2 (2025-02-23)
-------------------

- new: function `ml()` to calculate mismatch loss
- new: added `src/env/Pipfile`
- change: adapted to latest scipy (`trapz` no longer exists)
- change: using packet `copykitten` to copy images to clipboard cross-platform


0.25b1 (2024-10-21)
-------------------

- new: functions and templates for impedance and admittance
- new: most recent directories in main menu


0.24b1 (2024-09-05)
-------------------

- new: copy tabular data in different formats


0.23b1 (2024-08-29)
-------------------

- new: more detailed info about frequency spacing
- new: allow to mark data points via menu command
- new: allow to select plot theme
- change: finer resolution of frequency in tabular data dialog


0.22b1 (2024-08-21)
-------------------

- new: expression `add_ltl()` to add a lossy transmission line


0.21b2 (2024-08-20)
-------------------

- change: revised expresion templates
- new: more detailed display of CITI file coordinates and data variables
- new: more convenient selection of external editor
- change: new/fixed keyboard shortcuts
- bugfix: Y-axis unit is now degrees when plotting de-trended phase


0.21b1 (2024-08-19)
-------------------

- new: info dialog show frequency spacing


0.20b2 (2024-08-15)
-------------------

- bugfix: better reporting when error happens in expression
- bugfix: `nw()` now raises a warning instead of an exception when it does not match exactly a single network


0.20b1 (2024-08-11)
-------------------

- new: simple CITI support


0.19b1 (2024-07-22)
-------------------

- new: finished functionality of the tabular data dialog, removed all redundant functionality (i.e. menu commands for export data and copy data)


0.18b3 (2024-07-19)
-------------------

- new: allow to select which file or plot to show in tabular dialog


0.18b2 (2024-07-18)
-------------------

- bugfix: "type object 'Frequency' has no attribute 'fromf'" on certain expressions


0.18b1 (2024-07-16)
-------------------

- new: selectable tabular format, copy table to clipboard


0.17b2 (2024-06-25)
-------------------

- new: power operation on S-parameter expressions


0.17b1 (2024-06-24)
-------------------

- bugfix: showing export dialog when clicking that export item, added new menu item to view tabular data
- bugfix: fixed frequency interpolation, and improved names of processed networks
- new: using selected networks for some templates, and added a template for selected networks only


0.16b4 (2024-05-24)
-------------------

- new: open file with external editor


0.16b3 (2024-05-23)
-------------------

- new: `renorm()` function to renormalize impedance.
- new: better handling of corrupted files.


0.16b2 (2024-05-18)
-------------------

- new: more useful generate-button


0.16b1 (2024-05-17)
-------------------

- change: changed syntax for port order of mixed-mode conversion, e.g. `sel_nws().s2m(inp=['p1','p2','n1','n2']).s(2,1).plot()`
- new: allow to name S-parameters in expressions, eg. `sel_nws().s(2,1,name='SDD21').plot()`


0.15b1 (2023-09-18)
-------------------

- new: manual axis scaling
- new: allow to select GUI theme in settings dialog


0.14b1 (2023-09-08)
-------------------

- new: `losslessness`, `passivity` and `reciprocity` functions
- bugfix: the directional coupler samples are now actually passive networks


0.13b1 (2023-07-27)
-------------------

- new: improved and enhanced TDR


0.12b1 (2023-07-12)
-------------------

- new: `phase()` function
- new: plot phase with linear phase removed


0.11b2 (2023-06-14)
-------------------

- new: `s2m()` and `m2s()` for single-ended / mixed-mode S-parameter conversion
- new: `quick()` methods on Network objects


0.11b1 (2023-06-09)
-------------------

- new: `quick()` plot function


0.10b14 (2023-06-05)
-------------------

- new: append directory


0.10b13 (2023-05-31)
-------------------

- bugfix: escaping path names, so that files in paths with certain special characters are found


0.10b12 (2023-03-31)
-------------------

- new: splash screen


0.10b11 (2023-03-17)
-------------------

- enhancement: using the DC extrapolation method from IEEE370, to get more accurate time-domain responses


0.10b10 (2023-03-15)
-------------------

- new: allowing to sync cursors
- bugfix: formatting of cursor status text


0.10b9 (2023-03-06)
-------------------

- new: displaying frequency in polar and Smith plots
- bugfix: properly handling abort when selecting directory
- bugfix: don't attempt to re-apply locked axis scale when plot format has changed


0.10b8 (2023-02-09)
-------------------

- new: remembering geometry of main window
- new: copy plot image or data to clipboard


0.10b7 (2023-01-06)
-------------------

- new: error log dialog


0.10b6 (2023-01-05)
-------------------

- bugfix: fixed loading of pattern-matched networks when using expressions
- bugfix: removed constructor of Networks object from docs (not supposed to be called directly)
- bugfix: fixed "Reload Directory" menu command
- new: highlight of integrated area in RL calculator


0.10b5 (2022-12-23)
-------------------

- new: added search bar
- new: files are now lazy-loaded (this speeds up the app start when opening large directories, especially when those are network- or cloud-hosted)
- bugfix: fixed / documented workarounds for pyinstaller
- bugfix: fixed app icon loading


0.10b4 (2022-11-18)
-------------------

- change: development environment switched to Python 3.11.0
- new: menu option to export plot as graphic
- new: menu option to show error log
- enhancement: minor UI scaling improvements
- enhancement: improved readme


0.10b3 (2022-11-04)
-------------------

- bugfix: fixed binary operations on S-parameters in expressions
- bugfix: fixed addition of S-parameters in expressions


0.10b2 (2022-09-19)
-------------------

- enhancement: updated docs of Network expression class.
- bugfix: fixed save/load expression dialog
- enhancement: smarter handling and shortening of the legend
- enhancement: ignoring case of the .snp file extension (important under Linux)
- new: option to lock X/Y axes
- enhancement: updated documentation
- bugfix: misc small fixes


0.9b2 (2022-09-04)
------------------

- change: Networks.half() now uses IEEE-370 by default


0.9b1 (2022-09-03)
------------------

- change: expressions now work on sets of multiple networks and S-parameters
- change: dropped the function wrappers for expressions
- change: dropped name shortening


0.8b2 (2022-09-02)
------------------

- new: can now directly plot S21 only, as well as S11/22/33/44
- new: command to reload current directory
- new: option to lock axes scaling


0.7b2 (2022-07-15)
------------------

- new: implemented Bode-Fano as expressions
- new: implemented stability circles as expressions
- enhancement: better scaling of Smith charts
- bugfix: fixed filename shortening


0.6b1 (2022-06-01)
------------------

- enhancement: more detailed file info


0.5b1 (2022-05-29)
------------------

- new: first published version
