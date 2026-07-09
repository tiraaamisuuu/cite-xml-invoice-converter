# CITE invoice validator

A small Python tool for checking CITE XML sales invoices and turning the valid
ones into a cleaner JSON format.

CITE XML is pretty noisy, so this project keeps the moving parts separate:

```text
CITE XML
  -> parser
  -> internal invoice model
  -> validator
  -> JSON converter
  -> CLI wrapper
```

The command line bit is just a wrapper. The actual parsing, validation, and
conversion code lives in `src/cite_invoice`, so another interface could reuse the
same logic later.

## Current status

This is a barebones version, but it already handles the supplied sample invoice
end to end.

What it does right now:

- Parses the sample CITE XML fixture.
- Extract invoice number, dates, currency, supplier, buyer, totals, line items,
  and VAT summary data.
- Validates mandatory fields, currency, future dates, line maths, header totals,
  and VAT totals.
- Converts the known-good fixture to the expected JSON shape.
- Runs against a single XML file or a folder of XML files.
- Includes tests for the good sample and a few deliberately broken versions.

Things still worth checking:

- Exact CITE segment-group nesting against a real Tradex CITE document.
- Full field-by-field coverage from the Confluence mapping specification.
- Final rounding and VAT edge-case rules.

## Requirements

- Python 3.11+
- No third-party runtime dependencies

The parser uses Python's built-in SAX parser so validation errors can include
source line numbers.

## Setup

Run these from the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Run the sample

```bash
cite-invoice tests/fixtures/sample-invoice.cite.xml --out sample-invoice.out.json
```

Expected console result:

```text
PASS tests/fixtures/sample-invoice.cite.xml -> sample-invoice.out.json

Summary: 1 passed, 0 failed
```

## Run a folder

```bash
cite-invoice tests/fixtures --out converted-json
```

For each valid invoice, the CLI writes a JSON file to the output folder. If a
file fails validation, it prints the errors and skips the JSON output for that
file.

## Run tests

```bash
python -m unittest
```

If you are not running from the repo root, use:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Engine API

The engine can also be used directly from Python:

```python
from cite_invoice import validate_and_convert

with open("invoice.cite.xml", encoding="utf-8") as file:
    result = validate_and_convert(file.read())

if result.is_valid:
    print(result.json_document)
else:
    for issue in result.issues:
        print(issue)
```

## Validation rules

The validator currently checks:

- Mandatory header fields: document number, document date, currency, supplier,
  and buyer.
- Currency is a known ISO 4217 code.
- Document date parses and is not in the future.
- Every line item has a line number, quantity, and unit price.
- Line total equals `quantity * unit price` within `0.01`.
- Header goods total equals the sum of line totals.
- Invoice total equals goods total plus tax total.
- VAT summaries have a code and/or rate.
- VAT totals match line VAT and tax summary VAT.

## Project structure

```text
src/cite_invoice/
  engine.py       main validate-and-convert API
  parser.py       CITE XML -> internal invoice model
  validator.py    Business validation rules
  converter.py    Internal model -> canonical JSON dict
  xml_tree.py     Tiny SAX-backed XML tree with line numbers
  models.py       Dataclasses used by the engine
  __main__.py     CLI wrapper

tests/
  fixtures/       sample CITE XML and expected JSON
  test_engine.py  Unit tests

docs/
  design.md       Design notes
  limitations.md  Known limitations and next steps
  prompt-log.md   Short AI collaboration log
```

## Notes

Before treating this as finished, every extracted CITE tag and qualifier should
be cross-checked against the official mapping specification. Right now this repo
uses the sample invoice and fixture README as its source of truth.
