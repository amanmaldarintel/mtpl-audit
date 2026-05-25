# MTPL Audit - FUN_CORE_CBB SBFT Analyzer

A Python utility that parses MTPL files and generates an interactive HTML audit report for FUN_CORE_CBB SBFT test instances.

## What It Does

- Parses .mtpl files to extract all SBFT test instances (excluding IDIBIST)
- Categorizes tests by type (SRH, CHK, VMAX, LTTC), frequency, instruction set, and cache type
- Resolves DIE/QUAL variant-specific parameters (UCCX1 vs UCCAP)
- Generates a rich interactive HTML report with summary stats, tabbed views, keyword highlighting

## Usage

1. Edit mtpl_audit.py and set the mtpl_file path to your .mtpl file
2. Set is_uccx1 = True (or False for UCCAP)
3. Run: python mtpl_audit.py
4. Open the generated FUN_CORE_CBB_SBFT_audit_report.html in a browser

## Requirements

- Python 3.6+
- No external dependencies (uses only re, os, collections, datetime)

