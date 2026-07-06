from __future__ import annotations

import io
from dataclasses import dataclass, field
from xml.sax import handler, make_parser
from xml.sax.xmlreader import AttributesImpl


@dataclass
class CiteNode:
    name: str
    attrs: dict[str, str]
    line: int | None
    children: list["CiteNode"] = field(default_factory=list)

    def attr(self, name: str) -> str | None:
        value = self.attrs.get(name)
        if value is None or value == "":
            return None
        return value

    def children_named(self, name: str) -> list["CiteNode"]:
        return [child for child in self.children if child.name == name]

    def first_child(self, name: str) -> "CiteNode | None":
        for child in self.children:
            if child.name == name:
                return child
        return None

    def descendants_named(self, name: str) -> list["CiteNode"]:
        matches: list[CiteNode] = []
        for child in self.children:
            if child.name == name:
                matches.append(child)
            matches.extend(child.descendants_named(name))
        return matches


class _TreeBuilder(handler.ContentHandler):
    def __init__(self) -> None:
        super().__init__()
        self.root: CiteNode | None = None
        self._stack: list[CiteNode] = []
        self._locator: handler.Locator | None = None

    def setDocumentLocator(self, locator: handler.Locator) -> None:
        self._locator = locator

    def startElement(self, name: str, attrs: AttributesImpl) -> None:
        line = self._locator.getLineNumber() if self._locator is not None else None
        node = CiteNode(name=name, attrs=dict(attrs.items()), line=line)

        if self._stack:
            self._stack[-1].children.append(node)
        else:
            self.root = node

        self._stack.append(node)

    def endElement(self, name: str) -> None:
        self._stack.pop()


def parse_xml(xml_text: str) -> CiteNode:
    builder = _TreeBuilder()
    parser = make_parser()

    try:
        parser.setFeature(handler.feature_external_ges, False)
        parser.setFeature(handler.feature_external_pes, False)
    except Exception:
        pass

    parser.setContentHandler(builder)
    parser.parse(io.StringIO(xml_text))

    if builder.root is None:
        raise ValueError("XML document did not contain a root element")

    return builder.root
