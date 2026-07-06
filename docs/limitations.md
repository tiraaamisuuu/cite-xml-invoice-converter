# Limitations and next steps

## Limitations

- The parser is based on the supplied reconstructed sample invoice, not a real
  production CITE document.
- Only Sales Invoice style data needed by the sample is currently mapped.
- The currency validator uses an embedded ISO 4217 code list. It should be
  reviewed if exact current ISO coverage becomes important.
- Date parsing currently supports the formats seen in the fixture plus ISO
  dates.
- VAT validation covers the simple single-rate case in the sample and should be
  expanded for multiple rates, zero-rated lines, and mixed VAT categories.
- The generated JSON shape matches the supplied expected fixture, but it has not
  yet been checked against the full Causeway JSON Sales Invoice documentation.

## Next steps

1. Confirm the real CITE segment-group nesting with a genuine Tradex invoice.
2. Cross-check each mapped field against the Confluence mapping specification.
3. Add more fixtures for missing fields, invalid dates, mixed VAT rates, and
   multiple tax summaries.
4. Decide the final rounding tolerance with the team.
5. Add a drag-and-drop UI as a thin wrapper over `validate_and_convert`.
6. Add a short demo script for the final show-and-tell.
