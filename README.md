# CITE invoice validator and JSON converter

Barebones Python implementation of the graduate starter project: read a CITE XML
sales invoice, validate the important business rules, and convert valid invoices
into the canonical Causeway JSON shape.

The project is deliberately split into a reusable engine plus thin interfaces:

```text
CITE XML
  -> parser
  -> internal invoice model
  -> validator
  -> JSON converter
  -> CLI wrapper
```

The CLI is only a wrapper. The validation and conversion logic lives in
`src/cite_invoice`, so a future drag-and-drop UI can call the same engine.

## Current status

This is a starter version, not the final submission.

Implemented:

- Parse the supplied sample CITE XML fixture.
- Extract invoice number, dates, currency, supplier, buyer, totals, line items,
  and VAT summary data.
- Validate mandatory fields, currency, future dates, line maths, header totals,
  and VAT totals.
- Convert the known-good fixture to the expected JSON shape.
- Run against a single XML file or a folder of XML files.
- Unit tests for the known-good fixture and a few deliberately broken variants.

Still to confirm:

- Exact CITE segment-group nesting against a real Tradex CITE document.
- Full field-by-field coverage from the Confluence mapping specification.
- Final rounding and VAT edge-case rules.

## Requirements

- Python 3.11+
- No third-party runtime dependencies

The parser uses Python's standard-library SAX parser so validation errors can
include source line numbers.

## Setup

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

For each valid invoice, the CLI writes a JSON file to the output folder. Invalid
invoices print validation errors and do not produce JSON.

## Run tests

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## Engine API

The engine can be used directly from Python:

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

The current validator checks:

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
  engine.py       Public validate-and-convert API
  parser.py       CITE XML -> internal invoice model
  validator.py    Business validation rules
  converter.py    Internal model -> canonical JSON dict
  xml_tree.py     Tiny SAX-backed XML tree with line numbers
  models.py       Dataclasses used by the engine
  __main__.py     CLI wrapper

tests/
  fixtures/       Supplied sample CITE XML and expected JSON
  test_engine.py  Unit tests

docs/
  design.md       Design notes
  limitations.md  Known limitations and next steps
  prompt-log.md   Short AI collaboration log
```

## Notes for the final project

Before treating this as finished, cross-check every extracted CITE tag and
qualifier against the official mapping specification. This repo currently uses
only the supplied sample and fixture README as its source of truth.
