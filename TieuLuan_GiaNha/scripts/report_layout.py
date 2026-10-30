"""Tạo báo cáo từ mẫu giảng viên và các kết quả đã chạy; dùng python-docx."""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/template_reference.docx"
OUTPUT = ROOT / "docs/6_Nguyễn Duy Trường_24150180.docx"
doc = Document(REFERENCE)
body = doc.element.body
original_parts = {n: b for n, b in []}
with ZipFile(REFERENCE) as z:
    original_parts = {n: z.read(n) for n in z.namelist()}


def font(run, size=13, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold, run.italic = bold, italic
    run.font.color.rgb = RGBColor(0, 0, 0)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Times New Roman")


def replace(paragraph, text, size, bold=False):
    # Preserve pPr, including the cover section break and drawing-free layout.
    for child in list(paragraph._p):
        if child.tag != qn("w:pPr"):
            paragraph._p.remove(child)
    font(paragraph.add_run(text), size, bold)


for p in list(doc.paragraphs):
    text = p.text
    if text == "<TÊN ĐỀ TÀI >":
        replace(p, "PHÂN TÍCH DỮ LIỆU BẤT ĐỘNG SẢN\nVÀ XÂY DỰNG ỨNG DỤNG\nDỰ ĐOÁN GIÁ NHÀ TẠI MỸ", 18, True)
    elif text.startswith("Ngành:"):
        replace(p, "Ngành: CÔNG NGHỆ THÔNG TIN", 16, True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif text.startswith("Chuyên ngành"):
        replace(p, "Chuyên ngành: KỸ THUẬT PHẦN MỀM", 16, True)
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif text.startswith("Sinh viên thực hiện:"):
        replace(p, "Sinh viên thực hiện: NGUYỄN DUY TRƯỜNG", 14, True)
    elif text.startswith("MSSV:"):
        replace(p, "MSSV: 24150180  |  STT: 6  |  Nhóm: 8", 14, True)
    elif text.startswith("Họ và tên sinh viên:"):
        replace(p, "Họ và tên: Nguyễn Duy Trường          MSSV: 24150180", 13)
    elif text == "(Chữ đậm, in hoa, cỡ chữ 30)":
        body.remove(p._p)

# Remove only the source's empty content slots after the grading signature.
signature = next(p for p in doc.paragraphs if p.text == "(Ký và ghi rõ họ tên)")
after = list(body).index(signature._p) + 1
for child in list(body)[after:]:
    if child.tag != qn("w:sectPr"):
        body.remove(child)

# Topic is longer than its placeholder; reclaim three empty paragraphs before it.
topic = next(p for p in doc.paragraphs if p.text.startswith("PHÂN TÍCH DỮ LIỆU"))
for _ in range(3):
    prev = topic._p.getprevious()
    if prev is not None and not prev.xpath('.//w:t|.//w:drawing|.//w:pict'):
        body.remove(prev)

for name, size, bold in [("Report Body", 13, False), ("Heading 1", 14, True), ("Heading 2", 13, True),
                         ("Figure Caption", 11, False), ("Table Caption", 11, False)]:
    style = doc.styles[name] if name in doc.styles else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_after = Pt(6)
    style.paragraph_format.line_spacing = 1.3 if name == "Report Body" else 1.1
    if name == "Report Body":
        style.paragraph_format.first_line_indent = Cm(.8)
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if name.startswith("Heading"):
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.keep_with_next = True
    if name.endswith("Caption"):
        style.font.italic = True
        style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        style.paragraph_format.first_line_indent = Cm(0)

for style_name in ["TOC 1", "TOC 2", "TOC Heading"]:
    if style_name in doc.styles:
        doc.styles[style_name].font.name = "Times New Roman"
        doc.styles[style_name].font.size = Pt(12)
        doc.styles[style_name].font.color.rgb = RGBColor(0, 0, 0)

story = []
figure_counter = 0
table_counter = 0


def paragraph(text):
    p = doc.add_paragraph(text, "Report Body")
    p.paragraph_format.widow_control = True
    story.append(text)
    return p


def heading(text, level=1, new_page=False):
    p = doc.add_paragraph(text, f"Heading {level}")
    p.paragraph_format.page_break_before = new_page
    story.append("#" * (level + 1) + " " + text)
    return p


def front_heading(text):
    p = doc.add_paragraph()
    p.paragraph_format.page_break_before = True
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(18)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run(text), 13, True)
    return p


def field(instruction):
    p = doc.add_paragraph()
    f = OxmlElement("w:fldSimple")
    f.set(qn("w:instr"), instruction)
    p._p.append(f)


def table(title, headers, rows, widths=None):
    global table_counter
    table_counter += 1
    caption = f"Bảng {table_counter}. {title}"
    p = doc.add_paragraph(caption, "Table Caption")
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    widths = widths or [15 / len(headers)] * len(headers)
    for col, width in zip(t.columns, widths):
        col.width = Cm(width)
    for i, values in enumerate([headers] + rows):
        row = t.rows[0] if i == 0 else t.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        if i == 0:
            row._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Cm(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.line_spacing = 1.0
            font(p.add_run(str(value)), 11, i == 0)
            prop = cell._tc.get_or_add_tcPr()
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "E8ECEF" if i == 0 else ("F7F8F9" if i % 2 == 0 else "FFFFFF"))
            prop.append(shade)
            margins = OxmlElement("w:tcMar")
            for side in ["top", "left", "bottom", "right"]:
                el = OxmlElement("w:" + side)
                el.set(qn("w:w"), "90")
                el.set(qn("w:type"), "dxa")
                margins.append(el)
            prop.append(margins)
    borders = OxmlElement("w:tblBorders")
    for side in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        el = OxmlElement("w:" + side)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "D9D9D9")
        borders.append(el)
    t._tbl.tblPr.append(borders)
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = Pt(2)
    story.append(caption + "\n" + " | ".join(headers) + "\n" + "\n".join(" | ".join(map(str, row)) for row in rows))


def figure(filename, title, width=14.6):
    global figure_counter
    figure_counter += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(ROOT / "artifacts/us/figures" / filename), width=Cm(width))
    caption = f"Hình {figure_counter}. {title}"
    doc.add_paragraph(caption, "Figure Caption")
    story.append(f"![{caption}](../artifacts/us/figures/{filename})")




def save_report():
    # Numbering for the report body, while leaving the source cover unchanged.
    section = doc.sections[1]
    section.footer.is_linked_to_previous = False
    section.footer_distance = Cm(1)
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    font(p.add_run(""), 11)
    f = OxmlElement("w:fldSimple")
    f.set(qn("w:instr"), "PAGE")
    p._p.append(f)
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    doc.settings.element.append(update)
    doc.core_properties.author = "Nguyễn Duy Trường"
    doc.core_properties.title = "Phân tích dữ liệu bất động sản và xây dựng ứng dụng dự đoán giá nhà"
    doc.core_properties.subject = "Tiểu luận Lập trình Python – Nhóm 8"
    buffer = BytesIO()
    doc.save(buffer)
    # Preserve source package parts unless they were intentionally edited or new.
    editable = {"word/document.xml", "word/styles.xml", "word/settings.xml", "word/_rels/document.xml.rels",
                "[Content_Types].xml", "docProps/core.xml", "docProps/app.xml"}
    with ZipFile(buffer) as created, ZipFile(OUTPUT, "w", ZIP_DEFLATED) as final:
        for name in created.namelist():
            payload = original_parts[name] if name in original_parts and name not in editable else created.read(name)
            final.writestr(name, payload)
        for name in set(original_parts) - set(created.namelist()):
            final.writestr(name, original_parts[name])
    (ROOT / "docs/noi_dung_bao_cao.md").write_text("\n\n".join(story), encoding="utf-8")
