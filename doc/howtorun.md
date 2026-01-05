How To Run
==========

Prerequisites
-------------

Either install the required Python packets:
- Mandatory: `python -m pip install PyQt6 numpy scipy scikit-rf matplotlib openpyxl pandas CITIfile`.
- Optional: `python -m pip install pyinstaller`: to compile a binary.
- Optional: `python -m pip install markdown`: to convert Markdown docs to HTML (using `doc/make_html_docs.py`).

Then run
```bash
cd src
python ../sparamviewer.py
```

Alternatively, install the packets `pipenv pyenv`, then use the environment:
```bash
cd src/pipenv
python -m pipenv shell
python ../sparamviewer.py
``` 
Note: if you want to use `pipenv` without `pyenv`, you can comment out ("`#`") the "`[requires]`" section in <`srv/pipenv/Pipfile`>.

Optionally, compile it, see next section.

S-parameter Viewer was tested with:
- Python 3.13.
    - Might work with 3.7 or newer, but was not tested.
- Windows 11, Fedora Linux 43.


Compiling
---------

Compiling is **optional**. You can just as well run the Python script without compiling.

Make sure the dependencies, including `pyinstaller`, are installed. You may use the [pipenv](https://pipenv.pypa.io/) environment in `src/pipenv`.

To compile, run:
```bash
cd src
pyinstaller --noconfirm --clean pyinstaller.spec
```

The flag `--noconfirm` overwrites existing files, the flag `--clean` triggers a fresh build.


File Type Association
---------------------

If you want to set up the app such that supported files are automatically opened with it...


### Linux

To register S-parameter files with this application under Linux:

1. Register a mime-type for S-parameter files using `res/application-x-scatteringparameter.xml` (for instructions, see e.g. <https://help.gnome.org/admin/system-admin-guide/stable/mime-types-custom-user.html>).
2. Double-click any .s#p-file, and select the script `src/sparamviewer.py` (or the binary, if you compiled it) as the application.


### Windows

To register S-parameter files with this application under Windows:

- If you compiled the script (see instructions above): just Double-click any .s#p-file, and select `src/dist/sparamviewer/sparamviewer.exe` as the application.
- If you want to run the script directly without compiling:
    1. Open `res/sparamviewer.bat` in a text editor.
    2. Adapt the paths to your Python interpreter, as well as the path where `src/sparamviewer.py` is, in the 1st line.
    3. Double-click any .s#p-file, and select the batch-file `res/sparamviewer.bat` as the application .

Uou have to repeat this step for every type of .s#p-file, e.g. `.s1p`, `.s2p`, etc.


Development
-----------

There are sample .json-files in the `res` folder for VS Code.
