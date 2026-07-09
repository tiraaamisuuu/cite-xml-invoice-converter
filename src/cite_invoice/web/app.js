const fileInput = document.querySelector("#fileInput");
const openButton = document.querySelector("#openButton");
const downloadButton = document.querySelector("#downloadButton");
const dropZone = document.querySelector("#dropZone");
const fileName = document.querySelector("#fileName");
const statusPill = document.querySelector("#statusPill");
const statusText = document.querySelector("#statusText");
const invoiceDetails = document.querySelector("#invoiceDetails");
const partyDetails = document.querySelector("#partyDetails");
const issueList = document.querySelector("#issueList");
const lineItems = document.querySelector("#lineItems");
const lineCount = document.querySelector("#lineCount");
const jsonPreview = document.querySelector("#jsonPreview");
const jsonState = document.querySelector("#jsonState");

let currentDocument = null;
let currentFileName = "invoice";

openButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) readFile(file);
});

downloadButton.addEventListener("click", () => {
  if (!currentDocument) return;

  const blob = new Blob([JSON.stringify(currentDocument, null, 2) + "\n"], {
    type: "application/json",
  });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = jsonFileName(currentFileName);
  link.click();
  URL.revokeObjectURL(link.href);
});

for (const eventName of ["dragenter", "dragover"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragging");
  });
}

for (const eventName of ["dragleave", "drop"]) {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragging");
  });
}

dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (file) readFile(file);
});

async function readFile(file) {
  currentFileName = file.name;
  fileName.textContent = file.name;
  setStatus("neutral", "reading", "checking the invoice...");
  currentDocument = null;
  downloadButton.disabled = true;

  try {
    const xmlText = await file.text();
    const response = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/xml" },
      body: xmlText,
    });

    if (!response.ok) throw new Error(`reader returned ${response.status}`);

    const payload = await response.json();
    render(payload);
  } catch (error) {
    setStatus("fail", "error", "could not read that file.");
    issueList.replaceChildren();
    const item = document.createElement("div");
    item.className = "issue";
    item.textContent = error.message;
    issueList.append(item);
    jsonPreview.textContent = "no json output.";
    jsonState.textContent = "error";
  }
}

function render(payload) {
  currentDocument = payload.document;
  downloadButton.disabled = !payload.isValid;

  if (payload.isValid) {
    setStatus("pass", "valid", "invoice passed validation.");
    jsonPreview.textContent = JSON.stringify(payload.document, null, 2);
    jsonState.textContent = "ready";
  } else {
    setStatus("fail", "invalid", "invoice needs attention.");
    jsonPreview.textContent = "no json output because validation failed.";
    jsonState.textContent = "blocked";
  }

  renderInvoice(payload.invoice);
  renderIssues(payload.issues || [], payload.isValid);
  renderLines(payload.invoice?.lineItems || []);
}

function renderInvoice(invoice) {
  invoiceDetails.replaceChildren();
  partyDetails.replaceChildren();

  if (!invoice) {
    addRows(invoiceDetails, [["invoice", "not parsed"]]);
    return;
  }

  addRows(invoiceDetails, [
    ["number", invoice.invoiceNumber],
    ["order", invoice.orderNumber],
    ["date", invoice.invoiceDate],
    ["tax point", invoice.taxPointDate],
    ["currency", invoice.currency],
    ["goods", invoice.totalGoodsAmount],
    ["vat", invoice.totalTaxAmount],
    ["total", invoice.totalAmount],
  ]);

  addRows(partyDetails, [
    ["supplier", invoice.sender?.name],
    ["buyer", invoice.receiver?.name],
    ["supplier vat", invoice.sender?.taxNumber],
    ["buyer email", invoice.receiver?.emailAddress],
  ]);
}

function renderIssues(issues, isValid) {
  issueList.replaceChildren();

  if (isValid) {
    const item = document.createElement("div");
    item.className = "issue pass";
    item.textContent = "no validation issues found.";
    issueList.append(item);
    return;
  }

  if (!issues.length) {
    const item = document.createElement("div");
    item.className = "issue";
    item.textContent = "something went wrong, but no validation issue came back.";
    issueList.append(item);
    return;
  }

  for (const issue of issues) {
    const item = document.createElement("div");
    item.className = "issue";
    const line = issue.line ? ` line ${issue.line}` : "";
    item.textContent = `${issue.rule} - ${issue.field}${line}: ${issue.message}`;
    issueList.append(item);
  }
}

function renderLines(lines) {
  lineItems.replaceChildren();
  lineCount.textContent = `${lines.length} ${lines.length === 1 ? "line" : "lines"}`;

  if (!lines.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 8;
    cell.textContent = "no line items";
    row.append(cell);
    lineItems.append(row);
    return;
  }

  for (const line of lines) {
    const row = document.createElement("tr");
    addCells(row, [
      line.lineNumber,
      line.itemCode,
      line.description,
      line.quantity,
      line.unitOfMeasure,
      line.unitAmount,
      line.totalAmount,
      line.taxAmount,
    ]);
    lineItems.append(row);
  }
}

function addRows(list, rows) {
  for (const [label, value] of rows) {
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = label;
    detail.textContent = value || "-";
    list.append(term, detail);
  }
}

function addCells(row, values) {
  values.forEach((value, index) => {
    const cell = document.createElement("td");
    cell.textContent = value || "-";
    if (index >= 3) cell.className = "number";
    row.append(cell);
  });
}

function setStatus(kind, label, message) {
  statusPill.className = `status-pill ${kind}`;
  statusPill.textContent = label;
  statusText.textContent = message;
}

function jsonFileName(name) {
  return name.replace(/(\.cite)?\.xml$/i, "") + ".json";
}
