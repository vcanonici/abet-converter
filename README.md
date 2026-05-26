# ABET CONVERTER

ABET CONVERTER is a cross-platform command-line interface (CLI) tool for exporting data from Lafayette Instrument's ABET (**A**nimal **B**ehavior **E**nvironment **T**est) software — used to program and run behavioral experiments. Converts `.ABETdb` and `.mdb` database files into easier formats:

- SQLite
- SQL
- CSV
- XLSX

You do not need to install `mdbtools` yourself. ABET CONVERTER includes the needed runtime files and chooses the correct one automatically for Windows, macOS, or Linux.

## What This Tool Does

Use this tool when you have an `.ABETdb` or `.mdb` file and want a file that is easier to open, inspect, or share.

For example, you can turn:

```text
input.ABETdb
```

into:

```text
input.sqlite
```

## Install Python

You need Python 3.11 or newer.

Download Python here:

```text
https://www.python.org/downloads/
```

During Python installation on Windows, enable:

```text
Add python.exe to PATH
```

## Install ABET Converter

Open a terminal.

On Windows, open PowerShell.

On macOS or Linux, open Terminal.

Run:

```bash
python -m pip install abet-converter
```

ABET CONVERTER is installed from PyPI, the official Python package website.

You do not need to choose a Windows, macOS, or Linux installer. The same Python package works on all supported systems. When you run the command, ABET CONVERTER detects your system and uses the correct bundled runtime:

- Windows: `vendor/mdbtools/windows/...`
- macOS: `vendor/mdbtools/macos/...`
- Linux: `vendor/mdbtools/linux/...`

## Check That It Works

Run:

```bash
abet-converter --help
```

If you see help text, the installation worked.

## Convert One File

This example converts one ABET database into one SQLite file:

```bash
abet-converter --input input.ABETdb --output input.sqlite
```

You can replace `input.ABETdb` with the path to your own file.

## Convert A Folder

This example converts all supported files in a folder:

```bash
abet-converter --input incoming-folder --output converted-folder --recursive
```

## Export Other Formats

SQLite is the default format.

To export CSV files:

```bash
abet-converter --input input.ABETdb --output output-folder --format csv
```

To export several formats at once:

```bash
abet-converter --input input.ABETdb --output output-folder --format sqlite --format csv --format xlsx
```

## Large XLSX Files

Excel has a row limit for each sheet.

If a database table is too large for one Excel sheet, ABET CONVERTER automatically splits that table into more sheets.

For example:

```text
tbl_Data
tbl_Data_2
tbl_Data_3
```

This keeps all rows instead of silently dropping data.

## Windows Notes

If this command does not work:

```powershell
python -m pip install abet-converter
```

try:

```powershell
py -m pip install abet-converter
```

Then check:

```powershell
abet-converter --help
```

Windows users do not need to install extra database tools.

## macOS Notes

If this command does not work:

```bash
python -m pip install abet-converter
```

try:

```bash
python3 -m pip install abet-converter
```

Then check:

```bash
abet-converter --help
```

macOS users do not need to install extra database tools.

## Linux Notes

If this command does not work:

```bash
python -m pip install abet-converter
```

try:

```bash
python3 -m pip install abet-converter
```

Then check:

```bash
abet-converter --help
```

Linux users do not need to install extra database tools on supported architectures.

## What Is A Coding Agent?

A coding agent is an AI tool that can help with a software project.

It can read files, explain code, run commands, edit files, run tests, and help fix errors.

You can use a coding agent even if you are not a programmer. You can ask it to do practical tasks in plain language.

## Using A Coding Agent To Install Or Modify This Project

You can ask a coding agent things like:

```text
Install this project on my computer.
Run the tests and explain any failure.
Convert this ABETdb file to SQLite.
Add a new output format.
```

If you want to work on the project itself, ask the agent to clone the repository, install it, run the tests, and explain the files before making changes.

## Project Links

- GitHub: `https://github.com/vcanonici/abet-converter`
- PyPI: `https://pypi.org/project/abet-converter/`

## Citation

If you use ABET CONVERTER in research, please cite the repository.

```bibtex
@software{canonici_abet_converter_2026,
  author = {Canonici, Vinicius Garcia and Pinto, Carlos},
  title = {ABET CONVERTER},
  year = {2026},
  version = {0.3.4},
  url = {https://github.com/vcanonici/abet-converter},
  note = {Cross-platform CLI to convert ABET and MDB databases into SQLite, SQL, CSV, and XLSX}
}
```

## License

GNU GPL v3 or later
