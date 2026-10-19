"""Small tolerant HTML tree built on the Python standard library."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Iterator


@dataclass(slots=True)
class Node:
    tag: str
    attrs: dict[str, str]
    parent: "Node | None" = None
    children: list["Node | str"] = field(default_factory=list)

    def elements(self, tag: str | None = None) -> Iterator["Node"]:
        for child in self.children:
            if not isinstance(child, Node):
                continue
            if tag is None or child.tag == tag:
                yield child
            yield from child.elements(tag)

    def closest(self, tag: str | None = None, class_name: str | None = None) -> "Node | None":
        current = self.parent
        while current is not None:
            if (tag is None or current.tag == tag) and (
                class_name is None or class_name in current.classes
            ):
                return current
            current = current.parent
        return None

    @property
    def classes(self) -> set[str]:
        return set(self.attrs.get("class", "").split())

    def text(self) -> str:
        parts: list[str] = []
        for child in self.children:
            if isinstance(child, str):
                parts.append(child)
            elif child.tag == "br":
                parts.append(" ")
            else:
                if child.tag in _BLOCK_TAGS:
                    parts.append(" ")
                parts.append(child.text())
                if child.tag in _BLOCK_TAGS:
                    parts.append(" ")
        return " ".join("".join(parts).split())

    def inner_html(self) -> str:
        return "".join(_serialize(child) for child in self.children)


_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
_BLOCK_TAGS = {
    "address", "article", "blockquote", "caption", "dd", "div", "dl", "dt",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3",
    "h4", "h5", "h6", "header", "li", "main", "ol", "p", "section", "table",
    "tbody", "td", "tfoot", "th", "thead", "tr", "ul",
}
_AUTO_CLOSE = {
    "td": {"td", "th"},
    "th": {"td", "th"},
    "tr": {"tr"},
    "li": {"li"},
    "option": {"option"},
}


class _TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {})
        self.stack = [self.root]

    def _close_nearest(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        for target in _AUTO_CLOSE.get(tag, ()):
            self._close_nearest(target)
        if tag == "tr":
            self._close_nearest("td")
            self._close_nearest("th")
        if tag in {"td", "th"}:
            self._close_nearest("td")
            self._close_nearest("th")
        node = Node(tag, {key.lower(): value or "" for key, value in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in _VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in _VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        self._close_nearest(tag.lower())

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)

    def handle_comment(self, data: str) -> None:
        parent = self.stack[-1]
        comment = Node("#comment", {"text": data}, parent)
        # TLIDB closes table rows implicitly and puts the stable family ID in a
        # comment immediately after the row, before the next <tr>.
        if parent.tag in {"tbody", "table"} and parent.children:
            previous = parent.children[-1]
            if isinstance(previous, Node) and previous.tag == "tr" and _family_comment(data):
                comment.parent = previous
                previous.children.append(comment)
                return
        parent.children.append(comment)


def parse_html(source: str) -> Node:
    parser = _TreeParser()
    parser.feed(source)
    parser.close()
    return parser.root


def _serialize(node: Node | str) -> str:
    if isinstance(node, str):
        from html import escape

        return escape(node, quote=False)
    if node.tag == "#comment":
        return f"<!--{node.attrs.get('text', '')}-->"
    attributes = "".join(
        f' {key}="{_escape_attr(value)}"' for key, value in node.attrs.items()
    )
    if node.tag in _VOID_TAGS:
        return f"<{node.tag}{attributes}/>"
    return f"<{node.tag}{attributes}>{node.inner_html()}</{node.tag}>"


def _escape_attr(value: str) -> str:
    from html import escape

    return escape(value, quote=True)


def _family_comment(value: str) -> bool:
    import re

    return re.search(r"<\s*td\s*>\s*\d+", value, re.IGNORECASE) is not None


def descendants_with_class(node: Node, tag: str, class_name: str) -> list[Node]:
    return [child for child in node.elements(tag) if class_name in child.classes]
