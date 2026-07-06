from __future__ import annotations

from typing import Any

from .models import FieldValue, Invoice, LineItem, Party, TaxSummary


def invoice_to_json(invoice: Invoice) -> dict[str, Any]:
    # keep this boring on purpose: parsed model in, expected json field names out
    document: dict[str, Any] = {
        "invoiceNumber": _value(invoice.invoice_number),
        "orderNumber": _value(invoice.order_number),
        "invoiceDate": _value(invoice.invoice_date),
        "taxPointDate": _value(invoice.tax_point_date),
        "currency": _value(invoice.currency),
        "totalAmount": _value(invoice.total_amount),
        "totalGoodsAmount": _value(invoice.total_goods_amount),
        "totalTaxableAmount": _value(invoice.total_taxable_amount),
        "totalTaxAmount": _value(invoice.total_tax_amount),
        "sender": _sender_to_json(invoice.sender),
        "receiver": _receiver_to_json(invoice.receiver),
        "lineItems": [_line_to_json(line) for line in invoice.line_items],
        "taxSummaries": [_tax_summary_to_json(summary) for summary in invoice.tax_summaries],
    }

    return document


def _sender_to_json(sender: Party | None) -> dict[str, Any]:
    if sender is None:
        return {}

    return _without_empty(
        {
            "taxNumber": _value(sender.tax_number),
            "phone": _value(sender.phone),
            "addresses": [_address_to_json("Billing", sender)],
        }
    )


def _receiver_to_json(receiver: Party | None) -> dict[str, Any]:
    if receiver is None:
        return {}

    return _without_empty(
        {
            "contactName": _value(receiver.contact_name),
            "emailAddress": _value(receiver.email_address),
            "addresses": [_address_to_json("InvoiceTo", receiver)],
        }
    )


def _address_to_json(address_type: str, party: Party) -> dict[str, str | None]:
    return _without_empty(
        {
            "type": address_type,
            "name": _value(party.name),
            "line1": _value(party.line1),
            "line2": _value(party.line2),
            "line3": _value(party.line3),
            "line4": _value(party.line4),
            "postalCode": _value(party.postal_code),
            "countryCode": _value(party.country_code),
        }
    )


def _line_to_json(line: LineItem) -> dict[str, str | None]:
    return _without_empty(
        {
            "lineNumber": _value(line.line_number),
            "itemCode": _value(line.item_code),
            "description": _value(line.description),
            "quantity": _value(line.quantity),
            "unitOfMeasure": _value(line.unit_of_measure),
            "unitAmount": _value(line.unit_amount),
            "totalAmount": _value(line.total_amount),
            "taxAmount": _value(line.tax_amount),
            "taxCode": _value(line.tax_code),
            "effectiveTaxRate": _value(line.effective_tax_rate),
        }
    )


def _tax_summary_to_json(summary: TaxSummary) -> dict[str, str | None]:
    return _without_empty(
        {
            "taxCode": _value(summary.tax_code),
            "effectiveTaxRate": _value(summary.effective_tax_rate),
            "taxAmount": _value(summary.tax_amount),
        }
    )


def _value(field: FieldValue) -> str | None:
    return field.value


def _without_empty(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}
