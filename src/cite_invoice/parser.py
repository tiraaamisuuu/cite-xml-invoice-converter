from __future__ import annotations

from datetime import datetime

from .models import FieldValue, Invoice, LineItem, Party, TaxSummary
from .xml_tree import CiteNode, parse_xml


def parse_invoice(xml_text: str) -> Invoice:
    root = parse_xml(xml_text)

    # cite is mostly "same tag, different qualifier", so the code below reads by codes
    invoice = Invoice(
        invoice_number=_document_number(root),
        order_number=_header_reference(root, "ON"),
        invoice_date=_header_date(root, "137"),
        tax_point_date=_header_date(root, "131"),
        currency=_currency(root),
        total_goods_amount=_header_moa(root, "79"),
        total_taxable_amount=_header_moa(root, "125"),
        total_tax_amount=_header_moa(root, "176"),
        total_amount=_header_moa(root, "77"),
        sender=_party(root, "SU"),
        receiver=_party(root, "BY"),
        line_items=[_line_item(node) for node in root.children_named("S.LIN.LineItem")],
        tax_summaries=_tax_summaries(root),
    )

    return invoice


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _field(value: str | None, line: int | None) -> FieldValue:
    return FieldValue(value=_clean(value), line=line)


def _document_number(root: CiteNode) -> FieldValue:
    # the sample has the number twice; prefer the document wrapper, then fall back to bgm
    root_value = root.attr("DocNumber")
    if root_value:
        return _field(root_value, root.line)

    bgm = root.first_child("S.BGM.BeginingOfMessage")
    if bgm is not None:
        return _field(bgm.attr("E.1004.DocumentNumber.D"), bgm.line)

    return FieldValue()


def _header_date(root: CiteNode, qualifier: str) -> FieldValue:
    for dtm in root.children_named("S.DTM.DateTimePeriod"):
        composite = dtm.first_child("C.C507.DateTimePeriod")
        if composite and composite.attr("E.2005.DateTimePeriod.Q") == qualifier:
            raw = composite.attr("E.2380.DateTimePeriod.D")
            return _field(_normalise_date(raw), composite.line)

    return FieldValue()


def _normalise_date(raw: str | None) -> str | None:
    value = _clean(raw)
    if value is None:
        return None

    # keep json dates boring even when cite sends friendly dates like "15 jan 2026"
    for date_format in ("%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue

    return value


def _header_reference(root: CiteNode, qualifier: str) -> FieldValue:
    for rff in root.children_named("S.RFF.Reference"):
        composite = rff.first_child("C.C506.Reference")
        if composite and composite.attr("E.1153.Reference.Q") == qualifier:
            return _field(composite.attr("E.1154.ReferenceNumber.D"), composite.line)

    return FieldValue()


def _currency(root: CiteNode) -> FieldValue:
    cux = root.first_child("S.CUX.Currencies")
    if cux is None:
        return FieldValue()

    details = cux.first_child("C.C504.CurrencyDetails")
    if details is None:
        return FieldValue(line=cux.line)

    return _field(details.attr("E.6345.Currency.C"), details.line)


def _party(root: CiteNode, qualifier: str) -> Party | None:
    for node in root.children_named("S.NAD.NameAndAddress"):
        if node.attr("E.3035.Party.Q") == qualifier:
            return _parse_party(node)

    return None


def _parse_party(node: CiteNode) -> Party:
    # c058 repeats: first value is the name, then the address lines follow
    address_values = [
        _field(child.attr("E.3124.NameAndAddress.D"), child.line)
        for child in node.children_named("C.C058.NameAndAddress")
    ]

    fallback_name = FieldValue()
    party_id = node.first_child("C.C082.PartyIdentification")
    if party_id is not None:
        fallback_name = _field(party_id.attr("E.3039.PartyIdentification.D"), party_id.line)

    street = node.first_child("C.C059.Street")
    contact = _party_contact(node)
    communications = _party_communications(node)
    tax_number = _party_reference(node, "VA")

    return Party(
        name=_pick(address_values, 0, fallback_name),
        line1=_pick(address_values, 1),
        line2=_pick(address_values, 2),
        line3=_pick(address_values, 3),
        line4=_pick(address_values, 4),
        postal_code=_field(street.attr("E.3251.PostCode.D"), street.line) if street else FieldValue(),
        country_code=_field(street.attr("E.3207.Country.C"), street.line) if street else FieldValue(),
        contact_name=contact,
        email_address=communications.get("EM", FieldValue()),
        phone=communications.get("TE", FieldValue()),
        tax_number=tax_number,
        line=node.line,
    )


def _pick(values: list[FieldValue], index: int, fallback: FieldValue | None = None) -> FieldValue:
    if index < len(values) and values[index].is_present:
        return values[index]
    return fallback or FieldValue()


def _party_contact(node: CiteNode) -> FieldValue:
    cta = node.first_child("S.CTA.ContactInformation")
    if cta is None:
        return FieldValue()

    employee = cta.first_child("C.C056.DepartmentOrEmployee")
    if employee is None:
        return FieldValue(line=cta.line)

    return _field(employee.attr("E.3412.DepartmentOrEmployee.D"), employee.line)


def _party_communications(node: CiteNode) -> dict[str, FieldValue]:
    communications: dict[str, FieldValue] = {}

    for com in node.children_named("S.COM.CommunicationContact"):
        contact = com.first_child("C.C076.CommunicationContact")
        if contact is None:
            continue

        channel = contact.attr("E.3155.CommunicationChannel.Q")
        if channel:
            communications[channel] = _field(contact.attr("E.3148.CommunicationNumber.D"), contact.line)

    return communications


def _party_reference(node: CiteNode, qualifier: str) -> FieldValue:
    for rff in node.children_named("S.RFF.Reference"):
        composite = rff.first_child("C.C506.Reference")
        if composite and composite.attr("E.1153.Reference.Q") == qualifier:
            return _field(composite.attr("E.1154.ReferenceNumber.D"), composite.line)

    return FieldValue()


def _line_item(node: CiteNode) -> LineItem:
    # line child segments are grouped under lin in the starter fixture
    item_id = node.first_child("C.C212.ItemNumberIdentification")
    description_segment = node.first_child("S.IMD.ItemDescription")
    description = description_segment.first_child("C.C273.ItemDescription") if description_segment else None
    quantity_segment = node.first_child("S.QTY.Quantity")
    quantity = quantity_segment.first_child("C.C186.Quantity") if quantity_segment else None
    price_segment = node.first_child("S.PRI.Price")
    price = price_segment.first_child("C.C509.PriceIformation") if price_segment else None
    tax_segment = node.first_child("S.TAX.DutyTaxFee")
    tax = tax_segment.first_child("C.C243.DutyTaxFee") if tax_segment else None

    return LineItem(
        line_number=_field(node.attr("E.1082.LineItemNumber.D"), node.line),
        item_code=_field(item_id.attr("E.7140.ItemNumber.D"), item_id.line) if item_id else FieldValue(),
        description=_field(description.attr("E.7008.ItemDescription.D"), description.line) if description else FieldValue(),
        quantity=_field(quantity.attr("E.6060.Quantity.D"), quantity.line) if quantity else FieldValue(),
        unit_of_measure=_field(quantity.attr("E.6411.UnitOfMeasurement.Q"), quantity.line) if quantity else FieldValue(),
        unit_amount=_field(price.attr("E.5118.Price.D"), price.line) if price else FieldValue(),
        total_amount=_node_moa(node, "203"),
        tax_amount=_node_moa(node, "150"),
        tax_code=_field(tax.attr("E.5305.DutyTaxFeeCategory.C"), tax.line) if tax else FieldValue(),
        effective_tax_rate=_field(tax.attr("E.5278.DutyTaxFeeRate.D"), tax.line) if tax else FieldValue(),
        line=node.line,
    )


def _header_moa(root: CiteNode, qualifier: str) -> FieldValue:
    return _node_moa(root, qualifier)


def _node_moa(node: CiteNode, qualifier: str) -> FieldValue:
    # moa is just "an amount" until the qualifier tells us which amount it is
    for moa in node.children_named("S.MOA.MonetaryAmount"):
        composite = moa.first_child("C.C516.MonetaryAmount")
        if composite and composite.attr("E.5025.MonetaryAmountType.Q") == qualifier:
            return _field(composite.attr("E.5004.MonetaryAmount.D"), composite.line)

    return FieldValue()


def _tax_summaries(root: CiteNode) -> list[TaxSummary]:
    summaries: list[TaxSummary] = []
    children = root.children

    # in the sample, a header tax segment is followed by the matching moa 150 amount
    for index, node in enumerate(children):
        if node.name != "S.TAX.DutyTaxFee":
            continue

        tax_detail = node.first_child("C.C243.DutyTaxFee")
        amount = _following_tax_amount(children, index)

        summaries.append(
            TaxSummary(
                tax_code=_field(tax_detail.attr("E.5305.DutyTaxFeeCategory.C"), tax_detail.line)
                if tax_detail
                else FieldValue(),
                effective_tax_rate=_field(tax_detail.attr("E.5278.DutyTaxFeeRate.D"), tax_detail.line)
                if tax_detail
                else FieldValue(),
                tax_amount=amount,
                line=node.line,
            )
        )

    return summaries


def _following_tax_amount(children: list[CiteNode], start_index: int) -> FieldValue:
    for node in children[start_index + 1 :]:
        if node.name == "S.TAX.DutyTaxFee":
            return FieldValue()

        if node.name != "S.MOA.MonetaryAmount":
            continue

        composite = node.first_child("C.C516.MonetaryAmount")
        if composite and composite.attr("E.5025.MonetaryAmountType.Q") == "150":
            return _field(composite.attr("E.5004.MonetaryAmount.D"), composite.line)

    return FieldValue()
