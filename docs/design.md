# Design notes

## Goal

Build a small standalone engine that accepts CITE XML invoice text and returns:

- a validation report, and
- the canonical JSON invoice document when validation succeeds.

The command-line tool is intentionally thin. A future UI should call the same
engine instead of duplicating validation or mapping logic.

## Main design choice

CITE XML is EDIFACT-like XML: the same segment names appear in several places,
and the meaning usually comes from qualifier attributes.

Examples:

- `S.NAD.NameAndAddress` with `E.3035.Party.Q="SU"` means supplier.
- `S.NAD.NameAndAddress` with `E.3035.Party.Q="BY"` means buyer.
- `S.MOA.MonetaryAmount` with `E.5025.MonetaryAmountType.Q="77"` means invoice
  total.
- `S.MOA.MonetaryAmount` with `E.5025.MonetaryAmountType.Q="203"` means line net
  amount.

Because of that, the parser centralises the qualifier lookups instead of
spreading raw XML searches through the validator and converter.

## Data flow

```text
xml_tree.parse_xml()
  -> parser.parse_invoice()
  -> validator.validate_invoice()
  -> converter.invoice_to_json()
  -> engine.validate_and_convert()
```

## Error shape

Validation errors use a small structured shape:

```text
rule
field
message
line
```

This keeps console output human-readable while still making it possible for a UI
or API to render the same result cleanly.

## Why no third-party dependencies yet?

The starter version uses Python's standard-library SAX parser to keep setup
simple and to capture source line numbers. A production version might use
`lxml`, but avoiding dependencies makes the first demo easier to run.
