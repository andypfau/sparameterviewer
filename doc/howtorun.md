How To Run
==========


Quickstart
----------

Install [Pytho](https://www.python.org/), [Pipenv](https://pipenv.pypa.io/en/latest/) and [pyenv](https://github.com/pyenv/pyenv), then run
```bash
python -m pipenv run python src/sparamviewer.py
```

Optionally, build the HTML documentation, and compile the application into a binary, see next sections.

Requirements
------------

With [Pipenv](https://pipenv.pypa.io/en/latest/) and [pyenv](https://github.com/pyenv/pyenv), you can simply install the requirements from the `Pipfile`:
```bash
python -m pipenv install
```

Note: if you want to use `pipenv` without `pyenv`, you can comment out ("`#`") the "`[requires]`" section in <`Pipfile`>.

You can also install the required Python packets manually:

- Mandatory: `python -m pip install PyQt6 numpy scipy scikit-rf matplotlib openpyxl pandas CITIfile`.
- Optional: `python -m pip install pyinstaller`: to compile a binary.
- Optional: `python -m pip install markdown`: to convert Markdown docs to HTML (using `doc/make_html_docs.py`).

S-parameter Viewer was tested with:

- Python 3.13 (might work with 3.7 or newer, but was not tested).
- Windows 11, Fedora Linux 44.


HTML Documentation
------------------

The documentation exists in the form of .md-files (Markdown). As an experimental, **optional** feature, you can compile it to HTML via [MkDocs](https://www.mkdocs.org/):

1. Install additional packets: `python -m pipenv install --categories docs`.
2. Run `mkdocs build` from the main directory to create HTML documentation files.


Compiling
---------

Compiling is **optional**. You can just as well run the Python script without compiling.

1. Install additional packets: `python -m pipenv install --categories dev`.
2. Run `pyinstaller --clean pyinstaller.spec` from the `./src` directory to compile.

The flag `--clean` triggers a fresh build. Cou can add the flag `--noconfirm` to overwrite existing files without confirmation.


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
