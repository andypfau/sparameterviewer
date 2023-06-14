S-Parameter Viewer Changelog
============================


0.11b2 (2023-06-14)
-------------------

- new: `s2m` and `m2s`  for single-ended / mixed-mode S-parameter conversion
- new: `quick` methods on Network objects


0.11b1 (2023-06-09)
-------------------

- new: `quick` plot function


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
