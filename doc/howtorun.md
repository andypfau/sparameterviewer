How To Run
==========

Prerequisites
-------------

- Tested under Windows and under Fedora Linux.
- Tested with Python 3.13.
    - Might work with 3.7 or newer, but was not tested.
- Python packet dependencies:
    - Mandatory: `PyQt6 numpy scipy scikit-rf matplotlib openpyxl pandas CITIfile`.
    - Optional: `pyinstaller`: to compile a binary.

Execution
---------

Make sure the dependencies are installed. You may use the [pipenv](https://pipenv.pypa.io/) environment in `src/pipenv`.

Then just run `python sparameterviewer.py`.

Optionally, compile it, see next section.

Compiling
---------

Compiling is **optional**. You can just as well run the Python script.

Make sure the dependencies, including `pyinstaller`, are installed. You may use the [pipenv](https://pipenv.pypa.io/) environment in `src/pipenv`.

Compiling was successfully tested under Windows 10 and under Fedora 37 with the following command:
- `cd src`
- `pyinstaller pyinstaller.spec`
    - clean build without overwrite-confirmations: `pyinstaller --noconfirm --clean pyinstaller.spec`

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

Uou have to repeat this step for every type of .s#p-file, e.g. .s1p, .s2p, ...

Development
-----------

There are sample .json-files in the `res` folder for VS Code.
