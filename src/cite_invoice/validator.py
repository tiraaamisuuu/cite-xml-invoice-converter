from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from .models import FieldValue, Invoice, LineItem, TaxSummary, ValidationIssue

ROUNDING_TOLERANCE = Decimal("0.01")

ISO_4217_CODES = {
    "AED",
    "AFN",
    "ALL",
    "AMD",
    "ANG",
    "AOA",
    "ARS",
    "AUD",
    "AWG",
    "AZN",
    "BAM",
    "BBD",
    "BDT",
    "BGN",
    "BHD",
    "BIF",
    "BMD",
    "BND",
    "BOB",
    "BOV",
    "BRL",
    "BSD",
    "BTN",
    "BWP",
    "BYN",
    "BZD",
    "CAD",
    "CDF",
    "CHE",
    "CHF",
    "CHW",
    "CLF",
    "CLP",
    "CNY",
    "COP",
    "COU",
    "CRC",
    "CUC",
    "CUP",
    "CVE",
    "CZK",
    "DJF",
    "DKK",
    "DOP",
    "DZD",
    "EGP",
    "ERN",
    "ETB",
    "EUR",
    "FJD",
    "FKP",
    "GBP",
    "GEL",
    "GHS",
    "GIP",
    "GMD",
    "GNF",
    "GTQ",
    "GYD",
    "HKD",
    "HNL",
    "HTG",
    "HUF",
    "IDR",
    "ILS",
    "INR",
    "IQD",
    "IRR",
    "ISK",
    "JMD",
    "JOD",
    "JPY",
    "KES",
    "KGS",
    "KHR",
    "KMF",
    "KPW",
    "KRW",
    "KWD",
    "KYD",
    "KZT",
    "LAK",
    "LBP",
    "LKR",
    "LRD",
    "LSL",
    "LYD",
    "MAD",
    "MDL",
    "MGA",
    "MKD",
    "MMK",
    "MNT",
    "MOP",
    "MRU",
    "MUR",
    "MVR",
    "MWK",
    "MXN",
    "MXV",
    "MYR",
    "MZN",
    "NAD",
    "NGN",
    "NIO",
    "NOK",
    "NPR",
    "NZD",
    "OMR",
    "PAB",
    "PEN",
    "PGK",
    "PHP",
    "PKR",
    "PLN",
    "PYG",
    "QAR",
    "RON",
    "RSD",
    "RUB",
    "RWF",
    "SAR",
    "SBD",
    "SCR",
    "SDG",
    "SEK",
    "SGD",
    "SHP",
    "SLE",
    "SOS",
    "SRD",
    "SSP",
    "STN",
    "SVC",
    "SYP",
    "SZL",
    "THB",
    "TJS",
    "TMT",
    "TND",
    "TOP",
    "TRY",
    "TTD",
    "TWD",
    "TZS",
    "UAH",
    "UGX",
    "USD",
    "USN",
    "UYI",
    "UYU",
    "UYW",
    "UZS",
    "VED",
    "VES",
    "VND",
    "VUV",
    "WST",
    "XAF",
    "XAG",
    "XAU",
    "XBA",
    "XBB",
    "XBC",
    "XBD",
    "XCD",
    "XDR",
    "XOF",
    "XPD",
    "XPF",
    "XPT",
    "XSU",
    "XTS",
    "XUA",
    "YER",
    "ZAR",
    "ZMW",
    "ZWL",
}


def validate_invoice(invoice: Invoice, today: date | None = None) -> list[ValidationIssue]:
    today = today or date.today()
    issues: list[ValidationIssue] = []

    # start with the easy missing-field checks, then do the maths
    _require(invoice.invoice_number, "MissingDocumentNumber", "invoiceNumber", issues)
    _require(invoice.invoice_date, "MissingDocumentDate", "invoiceDate", issues)
    _require(invoice.currency, "MissingCurrency", "currency", issues)

    if invoice.sender is None:
        issues.append(ValidationIssue("MissingSupplier", "sender", "Supplier party SU is missing."))

    if invoice.receiver is None:
        issues.append(ValidationIssue("MissingBuyer", "receiver", "Buyer party BY is missing."))

    _validate_currency(invoice.currency, issues)
    _validate_document_date(invoice.invoice_date, today, issues)
    _validate_lines(invoice.line_items, issues)
    _validate_totals(invoice, issues)
    _validate_tax_summaries(invoice, issues)

    return issues


def _require(
    field: FieldValue,
    rule: str,
    field_name: str,
    issues: list[ValidationIssue],
    message: str | None = None,
) -> None:
    if not field.is_present:
        issues.append(
            ValidationIssue(
                rule=rule,
                field=field_name,
                line=field.line,
                message=message or f"{field_name} is required.",
            )
        )


def _validate_currency(currency: FieldValue, issues: list[ValidationIssue]) -> None:
    if not currency.is_present:
        return

    code = currency.value.upper()
    if code not in ISO_4217_CODES:
        issues.append(
            ValidationIssue(
                rule="InvalidCurrency",
                field="currency",
                line=currency.line,
                message=f"{currency.value} is not a recognised ISO 4217 currency code.",
            )
        )


def _validate_document_date(
    document_date: FieldValue,
    today: date,
    issues: list[ValidationIssue],
) -> None:
    if not document_date.is_present:
        return

    parsed = _date_value(document_date)
    if parsed is None:
        issues.append(
            ValidationIssue(
                rule="InvalidDocumentDate",
                field="invoiceDate",
                line=document_date.line,
                message=f"{document_date.value} is not a valid document date.",
            )
        )
        return

    if parsed > today:
        issues.append(
            ValidationIssue(
                rule="FutureDocumentDate",
                field="invoiceDate",
                line=document_date.line,
                message=f"{document_date.value} is after today's date {today.isoformat()}.",
            )
        )


def _validate_lines(lines: list[LineItem], issues: list[ValidationIssue]) -> None:
    if not lines:
        issues.append(ValidationIssue("MissingLineItems", "lineItems", "Invoice must contain at least one line item."))
        return

    for index, line in enumerate(lines, start=1):
        label = line.line_number.value or str(index)
        # use the invoice line number in messages when we have it, because humans read those
        prefix = f"lineItems[{label}]"

        _require(line.line_number, "MissingLineNumber", f"{prefix}.lineNumber", issues)
        _require(line.quantity, "MissingLineQuantity", f"{prefix}.quantity", issues)
        _require(line.unit_amount, "MissingLineUnitPrice", f"{prefix}.unitAmount", issues)
        _require(line.total_amount, "MissingLineTotal", f"{prefix}.totalAmount", issues)

        quantity = _decimal_value(line.quantity, f"{prefix}.quantity", issues)
        unit_amount = _decimal_value(line.unit_amount, f"{prefix}.unitAmount", issues)
        total_amount = _decimal_value(line.total_amount, f"{prefix}.totalAmount", issues)

        if quantity is None or unit_amount is None or total_amount is None:
            continue

        # money stays as decimal so 0.1 + 0.2 nonsense never gets invited in
        expected = quantity * unit_amount
        if not _close_enough(expected, total_amount):
            issues.append(
                ValidationIssue(
                    rule="LineTotalMismatch",
                    field=f"{prefix}.totalAmount",
                    line=line.total_amount.line,
                    message=f"{quantity} * {unit_amount} = {expected}, but line total is {total_amount}.",
                )
            )


def _validate_totals(invoice: Invoice, issues: list[ValidationIssue]) -> None:
    line_totals = [_decimal_value(line.total_amount, "lineItems.totalAmount", issues) for line in invoice.line_items]
    line_tax_amounts = [_decimal_value(line.tax_amount, "lineItems.taxAmount", issues) for line in invoice.line_items]

    # if a line amount is broken, don't pile on with noisy header-total guesses
    if any(value is None for value in line_totals):
        return

    line_total_sum = sum((value for value in line_totals if value is not None), Decimal("0"))
    line_tax_sum = sum((value for value in line_tax_amounts if value is not None), Decimal("0"))

    goods_total = _decimal_value(invoice.total_goods_amount, "totalGoodsAmount", issues)
    tax_total = _decimal_value(invoice.total_tax_amount, "totalTaxAmount", issues)
    invoice_total = _decimal_value(invoice.total_amount, "totalAmount", issues)

    # three simple checks: lines -> goods, line vat -> vat total, goods + vat -> invoice
    if goods_total is not None and not _close_enough(line_total_sum, goods_total):
        issues.append(
            ValidationIssue(
                rule="HeaderGoodsTotalMismatch",
                field="totalGoodsAmount",
                line=invoice.total_goods_amount.line,
                message=f"Sum of line totals is {line_total_sum}, but goods total is {goods_total}.",
            )
        )

    if tax_total is not None and not _close_enough(line_tax_sum, tax_total):
        issues.append(
            ValidationIssue(
                rule="VatTotalMismatch",
                field="totalTaxAmount",
                line=invoice.total_tax_amount.line,
                message=f"Sum of line VAT is {line_tax_sum}, but tax total is {tax_total}.",
            )
        )

    if goods_total is not None and tax_total is not None and invoice_total is not None:
        expected = goods_total + tax_total
        if not _close_enough(expected, invoice_total):
            issues.append(
                ValidationIssue(
                    rule="HeaderTotalMismatch",
                    field="totalAmount",
                    line=invoice.total_amount.line,
                    message=f"Goods {goods_total} + tax {tax_total} = {expected}, but invoice total is {invoice_total}.",
                )
            )


def _validate_tax_summaries(invoice: Invoice, issues: list[ValidationIssue]) -> None:
    for index, summary in enumerate(invoice.tax_summaries, start=1):
        prefix = f"taxSummaries[{index}]"

        # a vat row without a code or rate is too vague to trust
        if not summary.tax_code.is_present and not summary.effective_tax_rate.is_present:
            issues.append(
                ValidationIssue(
                    rule="MissingVatCodeOrRate",
                    field=prefix,
                    line=summary.line,
                    message="Tax summary must include a tax code and/or effective tax rate.",
                )
            )

        _require(summary.tax_amount, "MissingVatSummaryAmount", f"{prefix}.taxAmount", issues)

    summary_amounts = [
        _decimal_value(summary.tax_amount, "taxSummaries.taxAmount", issues) for summary in invoice.tax_summaries
    ]
    tax_total = _decimal_value(invoice.total_tax_amount, "totalTaxAmount", issues)

    if tax_total is None or any(value is None for value in summary_amounts):
        return

    summary_sum = sum((value for value in summary_amounts if value is not None), Decimal("0"))
    if invoice.tax_summaries and not _close_enough(summary_sum, tax_total):
        issues.append(
            ValidationIssue(
                rule="VatSummaryMismatch",
                field="taxSummaries",
                line=invoice.total_tax_amount.line,
                message=f"Sum of VAT summaries is {summary_sum}, but tax total is {tax_total}.",
            )
        )


def _decimal_value(field: FieldValue, field_name: str, issues: list[ValidationIssue]) -> Decimal | None:
    if not field.is_present:
        return None

    try:
        return Decimal(field.value)
    except InvalidOperation:
        issues.append(
            ValidationIssue(
                rule="InvalidNumber",
                field=field_name,
                line=field.line,
                message=f"{field.value} is not a valid number.",
            )
        )
        return None


def _date_value(field: FieldValue) -> date | None:
    if not field.is_present:
        return None

    try:
        return date.fromisoformat(field.value)
    except ValueError:
        return None


def _close_enough(left: Decimal, right: Decimal) -> bool:
    return abs(left - right) <= ROUNDING_TOLERANCE
