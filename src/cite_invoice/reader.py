from __future__ import annotations

import argparse
import json
import mimetypes
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import PurePosixPath
from typing import Any

from .engine import validate_and_convert
from .models import EngineResult, FieldValue, Invoice, Party

HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the CITE invoice reader GUI.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run the local reader on.")
    parser.add_argument("--no-open", action="store_true", help="Start the server without opening a browser.")
    args = parser.parse_args()

    server = _make_server(args.port)
    url = f"http://{HOST}:{server.server_port}"

    print(f"CITE invoice reader running at {url}")
    print("Press Ctrl+C to stop.")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()

    return 0


class ReaderHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = PurePosixPath(self.path.split("?", 1)[0])
        if str(path) in {"/", "/index.html"}:
            self._send_asset("index.html")
            return

        if len(path.parts) == 2 and path.parts[1] in {"styles.css", "app.js"}:
            self._send_asset(path.parts[1])
            return

        self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/convert":
            self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
            return

        length = int(self.headers.get("Content-Length", "0"))
        xml_text = self.rfile.read(length).decode("utf-8")
        result = validate_and_convert(xml_text)

        self._send_json(_result_payload(result))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_asset(self, filename: str) -> None:
        asset = resources.files("cite_invoice").joinpath("web", filename)
        if not asset.is_file():
            self._send_json({"error": "asset not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content = asset.read_bytes()
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        self._send_response(content, content_type=content_type)

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload).encode("utf-8")
        self._send_response(content, status=status, content_type="application/json")

    def _send_response(
        self,
        content: bytes,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str = "text/plain",
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def _make_server(port: int) -> ThreadingHTTPServer:
    for candidate in range(port, port + 20):
        try:
            return ThreadingHTTPServer((HOST, candidate), ReaderHandler)
        except OSError:
            continue

    raise OSError(f"Could not find a free port from {port} to {port + 19}")


def _result_payload(result: EngineResult) -> dict[str, Any]:
    return {
        "isValid": result.is_valid,
        "issues": [
            {
                "rule": issue.rule,
                "field": issue.field,
                "message": issue.message,
                "line": issue.line,
            }
            for issue in result.issues
        ],
        "invoice": _invoice_payload(result.invoice),
        "document": result.json_document,
    }


def _invoice_payload(invoice: Invoice | None) -> dict[str, Any] | None:
    if invoice is None:
        return None

    return {
        "invoiceNumber": _value(invoice.invoice_number),
        "orderNumber": _value(invoice.order_number),
        "invoiceDate": _value(invoice.invoice_date),
        "taxPointDate": _value(invoice.tax_point_date),
        "currency": _value(invoice.currency),
        "totalAmount": _value(invoice.total_amount),
        "totalGoodsAmount": _value(invoice.total_goods_amount),
        "totalTaxableAmount": _value(invoice.total_taxable_amount),
        "totalTaxAmount": _value(invoice.total_tax_amount),
        "sender": _party_payload(invoice.sender),
        "receiver": _party_payload(invoice.receiver),
        "lineItems": [
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
            for line in invoice.line_items
        ],
        "taxSummaries": [
            {
                "taxCode": _value(summary.tax_code),
                "effectiveTaxRate": _value(summary.effective_tax_rate),
                "taxAmount": _value(summary.tax_amount),
            }
            for summary in invoice.tax_summaries
        ],
    }


def _party_payload(party: Party | None) -> dict[str, str | None] | None:
    if party is None:
        return None

    return {
        "name": _value(party.name),
        "line1": _value(party.line1),
        "line2": _value(party.line2),
        "line3": _value(party.line3),
        "line4": _value(party.line4),
        "postalCode": _value(party.postal_code),
        "countryCode": _value(party.country_code),
        "contactName": _value(party.contact_name),
        "emailAddress": _value(party.email_address),
        "phone": _value(party.phone),
        "taxNumber": _value(party.tax_number),
    }


def _value(field: FieldValue) -> str | None:
    return field.value


if __name__ == "__main__":
    raise SystemExit(main())
