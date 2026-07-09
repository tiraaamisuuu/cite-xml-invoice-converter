from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cite_invoice import validate_and_convert
from cite_invoice.reader import _result_payload


FIXTURES = ROOT / "tests" / "fixtures"


class EngineTests(unittest.TestCase):
    def test_sample_invoice_converts_to_expected_json(self) -> None:
        xml = _fixture_text("sample-invoice.cite.xml")
        expected = json.loads(_fixture_text("sample-invoice.expected.json"))

        result = validate_and_convert(xml, today=date(2026, 7, 6))

        self.assertTrue(result.is_valid, [issue.format() for issue in result.issues])
        self.assertEqual(expected, result.json_document)

    def test_invalid_currency_is_reported(self) -> None:
        xml = _fixture_text("sample-invoice.cite.xml").replace(
            'E.6345.Currency.C="GBP"',
            'E.6345.Currency.C="ZZZ"',
        )

        result = validate_and_convert(xml, today=date(2026, 7, 6))

        self.assertIssue(result, "InvalidCurrency")

    def test_future_document_date_is_reported(self) -> None:
        xml = _fixture_text("sample-invoice.cite.xml").replace("15 Jan 2026", "15 Jan 2099")

        result = validate_and_convert(xml, today=date(2026, 7, 6))

        self.assertIssue(result, "FutureDocumentDate")

    def test_bad_line_total_is_reported(self) -> None:
        xml = _fixture_text("sample-invoice.cite.xml").replace(
            'E.5025.MonetaryAmountType.Q="203" E.5004.MonetaryAmount.D="60.00"',
            'E.5025.MonetaryAmountType.Q="203" E.5004.MonetaryAmount.D="61.00"',
            1,
        )

        result = validate_and_convert(xml, today=date(2026, 7, 6))

        self.assertIssue(result, "LineTotalMismatch")

    def test_missing_buyer_is_reported(self) -> None:
        xml = _fixture_text("sample-invoice.cite.xml").replace(
            'E.3035.Party.Q="BY"',
            'E.3035.Party.Q="XX"',
            1,
        )

        result = validate_and_convert(xml, today=date(2026, 7, 6))

        self.assertIssue(result, "MissingBuyer")

    def test_bad_header_total_is_reported(self) -> None:
        xml = _fixture_text("sample-invoice.cite.xml").replace(
            'E.5025.MonetaryAmountType.Q="77" E.5004.MonetaryAmount.D="96.00"',
            'E.5025.MonetaryAmountType.Q="77" E.5004.MonetaryAmount.D="95.00"',
            1,
        )

        result = validate_and_convert(xml, today=date(2026, 7, 6))

        self.assertIssue(result, "HeaderTotalMismatch")

    def test_reader_payload_has_summary_and_json(self) -> None:
        xml = _fixture_text("sample-invoice.cite.xml")

        result = validate_and_convert(xml, today=date(2026, 7, 6))
        payload = _result_payload(result)

        self.assertTrue(payload["isValid"])
        self.assertEqual("18499569", payload["invoice"]["invoiceNumber"])
        self.assertEqual("Speedy Hire", payload["invoice"]["sender"]["name"])
        self.assertEqual(2, len(payload["invoice"]["lineItems"]))
        self.assertEqual("18499569", payload["document"]["invoiceNumber"])

    def assertIssue(self, result, rule: str) -> None:
        rules = [issue.rule for issue in result.issues]
        self.assertIn(rule, rules, [issue.format() for issue in result.issues])


def _fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
