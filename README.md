# JU-TAN Office

JU-TAN Office is a Slovenian desktop business application built with Python,
PySide6 and SQLite. The project is currently in active development.

## Requirements

- Python 3.11 or newer
- Windows, macOS or Linux supported by PySide6

## Local setup

```bash
python -m venv .venv
```

Activate the virtual environment, then install and run the application:

```bash
python -m pip install -r requirements.txt
python app.py
```

The equivalent module entry point is:

```bash
python -m app.main
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Data safety

Local databases, logs, exports and backups are intentionally excluded from
Git. Never commit real customer, invoice or payment data.

## Current scope

Customer and article management are implemented. The offer editor supports
line items, discounts, VAT, exact totals and PDF export. Accepted offers can
be converted to invoices with due dates, payment tracking and invoice PDF
export. The dashboard and analytics views use live business data and can
export a formatted multi-sheet Excel report. Production packaging remains
under development.

## Windows build

On Windows PowerShell run:

```powershell
.\scripts\build_windows.ps1
```

The executable is created as `dist\JU-TAN-Office.exe`. Compile
`installer\JU-TAN-Office.iss` with Inno Setup 6 to create the installer.
