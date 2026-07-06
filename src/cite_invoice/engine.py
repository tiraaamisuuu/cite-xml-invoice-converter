from __future__ import annotations

from datetime import date
from xml.sax import SAXParseException

from .converter import invoice_to_json
from .models import EngineResult, ValidationIssue
from .parser import parse_invoice
from .validator import validate_invoice


def validate_and_convert(xml_text: str, today: date | None = None) -> EngineResult:
    try:
        invoice = parse_invoice(xml_text)
    except SAXParseException as exc:
        issue = ValidationIssue(
            rule="XmlParseError",
            field="xml",
            line=exc.getLineNumber(),
            message=exc.getMessage(),
        )
        return EngineResult(invoice=None, issues=[issue])
    except Exception as exc:
        issue = ValidationIssue(
            rule="ParseError",
            field="xml",
            message=str(exc),
        )
        return EngineResult(invoice=None, issues=[issue])

    issues = validate_invoice(invoice, today=today)
    json_document = None if issues else invoice_to_json(invoice)

    return EngineResult(invoice=invoice, issues=issues, json_document=json_document)
