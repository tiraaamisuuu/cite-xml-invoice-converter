from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FieldValue:
    value: str | None = None
    line: int | None = None

    @property
    def is_present(self) -> bool:
        return self.value is not None and self.value.strip() != ""


@dataclass
class Party:
    name: FieldValue = field(default_factory=FieldValue)
    line1: FieldValue = field(default_factory=FieldValue)
    line2: FieldValue = field(default_factory=FieldValue)
    line3: FieldValue = field(default_factory=FieldValue)
    line4: FieldValue = field(default_factory=FieldValue)
    postal_code: FieldValue = field(default_factory=FieldValue)
    country_code: FieldValue = field(default_factory=FieldValue)
    contact_name: FieldValue = field(default_factory=FieldValue)
    email_address: FieldValue = field(default_factory=FieldValue)
    phone: FieldValue = field(default_factory=FieldValue)
    tax_number: FieldValue = field(default_factory=FieldValue)
    line: int | None = None


@dataclass
class LineItem:
    line_number: FieldValue = field(default_factory=FieldValue)
    item_code: FieldValue = field(default_factory=FieldValue)
    description: FieldValue = field(default_factory=FieldValue)
    quantity: FieldValue = field(default_factory=FieldValue)
    unit_of_measure: FieldValue = field(default_factory=FieldValue)
    unit_amount: FieldValue = field(default_factory=FieldValue)
    total_amount: FieldValue = field(default_factory=FieldValue)
    tax_amount: FieldValue = field(default_factory=FieldValue)
    tax_code: FieldValue = field(default_factory=FieldValue)
    effective_tax_rate: FieldValue = field(default_factory=FieldValue)
    line: int | None = None


@dataclass
class TaxSummary:
    tax_code: FieldValue = field(default_factory=FieldValue)
    effective_tax_rate: FieldValue = field(default_factory=FieldValue)
    tax_amount: FieldValue = field(default_factory=FieldValue)
    line: int | None = None


@dataclass
class Invoice:
    invoice_number: FieldValue = field(default_factory=FieldValue)
    order_number: FieldValue = field(default_factory=FieldValue)
    invoice_date: FieldValue = field(default_factory=FieldValue)
    tax_point_date: FieldValue = field(default_factory=FieldValue)
    currency: FieldValue = field(default_factory=FieldValue)
    total_amount: FieldValue = field(default_factory=FieldValue)
    total_goods_amount: FieldValue = field(default_factory=FieldValue)
    total_taxable_amount: FieldValue = field(default_factory=FieldValue)
    total_tax_amount: FieldValue = field(default_factory=FieldValue)
    sender: Party | None = None
    receiver: Party | None = None
    line_items: list[LineItem] = field(default_factory=list)
    tax_summaries: list[TaxSummary] = field(default_factory=list)


@dataclass(frozen=True)
class ValidationIssue:
    rule: str
    field: str
    message: str
    line: int | None = None

    def format(self) -> str:
        location = f" line {self.line}" if self.line is not None else ""
        return f"[{self.rule}] {self.field}{location}: {self.message}"


@dataclass
class EngineResult:
    invoice: Invoice | None
    issues: list[ValidationIssue]
    json_document: dict[str, Any] | None = None

    @property
    def is_valid(self) -> bool:
        return not self.issues and self.json_document is not None
