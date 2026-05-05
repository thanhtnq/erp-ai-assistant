"""Debug parse_docx body walk"""
from pathlib import Path
from docx import Document
from lxml import etree
import re

FILE_PATH = "documents/_global/Sales/GLOBE3 ERP MANUAL 2019 - SALES VERSION 2.1.docx"
RE = re.compile(r"^(\d+(?:\.\d+)*)[\s\t]+(.+)$")

doc  = Document(FILE_PATH)
body = doc.element.body

WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

print("[1] First 5 non-empty body paragraphs with XML structure:")
found = 0
for body_idx, element in enumerate(body):
    tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
    if tag != "p":
        continue

    # Extract text
    text = ""
    for node in element.iter():
        ntag = node.tag.split("}")[-1] if "}" in node.tag else node.tag
        if ntag == "t" and node.text:
            text += node.text
    text = text.replace("\t", " ").strip()

    if not text:
        continue

    found += 1
    if found <= 5:
        print(f"\n  body[{body_idx}] text={text[:60]!r}")
        # Show pStyle
        pStyle = element.find(f".//{{{WNS}}}pStyle")
        if pStyle is not None:
            print(f"    pStyle val={pStyle.get(f'{{{WNS}}}val')!r}")
        else:
            print(f"    pStyle: NOT FOUND")
        # Show bold
        b_tags = element.findall(f".//{{{WNS}}}b")
        print(f"    bold tags: {len(b_tags)}")
        # Check RE match
        m = RE.match(text)
        if m:
            print(f"    RE match: number={m.group(1)} heading={m.group(2)[:30]}")
        # Show raw XML
        print(f"    XML: {etree.tostring(element, encoding='unicode')[:200]}")

print(f"\n[2] Total non-empty paragraphs scanned: {found}")

# Quick count headings
headings = 0
for body_idx, element in enumerate(body):
    tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag
    if tag != "p":
        continue
    text = "".join(
        node.text for node in element.iter()
        if node.tag.split("}")[-1] == "t" and node.text
    ).replace("\t", " ").strip()
    pStyle = element.find(f".//{{{WNS}}}pStyle")
    style  = (pStyle.get(f"{{{WNS}}}val") or "").lower() if pStyle is not None else ""
    m = RE.match(text)
    if m and "heading" in style:
        headings += 1
        if headings <= 5:
            print(f"  heading body[{body_idx}] [{m.group(1)}] {m.group(2)[:40]!r} style={style!r}")

print(f"[3] Total headings found: {headings}")