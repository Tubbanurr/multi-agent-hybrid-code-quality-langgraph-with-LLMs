"""
generate_thesis_tables.py  v2
Seçilen 9 benchmark promptu için modern, kompakt tez tabloları (DOCX).
"""

import re
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

RESULTS_FILE = "logs/benchmark_results.xlsx"
OUTPUT_FILE  = "logs/thesis_benchmark_tables.docx"

SELECTED = [
    {"id": 5,  "cat": "Kolay", "label": "K-1"},   # 99→99 (direct, aritmetik ortalama + loglama)
    {"id": 1,  "cat": "Kolay", "label": "K-2"},   # 96→96 (direct, float dönüşüm + PEP8 + loglama)
    {"id": 22, "cat": "Orta",  "label": "O-1"},   # 93→93 (direct, Strategy pattern / JSON formatter)
    {"id": 25, "cat": "Orta",  "label": "O-2"},   # 90→90 (direct, threading + race condition + Lock)
    {"id": 54, "cat": "Zor",   "label": "Z-1"},   # 86→95 (+9, 1 iter — 50GB dosya işleme)
    {"id": 49, "cat": "Zor",   "label": "Z-2"},   # 88→93 (+5, 1 iter — asyncio rate limiter)
]

# Renk paleti — minimal / modern
C = {
    # Tablo 1 başlık
    "t1_hdr":       "0F172A",   # koyu slate
    # Zebra satırlar
    "row_even":     "F8FAFC",
    "row_odd":      "FFFFFF",
    # Kategori badge renkleri (yazı)
    "cat_kolay":    "166534",   # yeşil
    "cat_orta":     "1D4ED8",   # mavi
    "cat_zor":      "7E22CE",   # mor
    # Prompt başlık satırı (prompt-level header)
    "ph_bg":        "1E293B",   # koyu slate
    # Kod sütun başlıkları
    "code_hdr_a":   "1E293B",   # başlangıç kodu header
    "code_hdr_b":   "14532D",   # final kod header
    # Kod arka planları (dark mode)
    "code_bg_a":    "1C1C1E",   # VS Code dark
    "code_bg_b":    "052E16",   # koyu yeşil terminal
    # Kod yazı renkleri
    "code_fg_a":    "D4D4D4",   # VS Code açık gri
    "code_fg_b":    "86EFAC",   # yeşil
    # Analiz sütun başlıkları
    "ana_hdr_a":    "7F1D1D",   # kırmızı
    "ana_hdr_b":    "1E3A5F",   # mavi
    # Analiz içerik arka planı
    "ana_bg_a":     "FFF7ED",   # amber
    "ana_bg_b":     "F0FDF4",   # yeşil
    # Global
    "white":        "FFFFFF",
    "border":       "CBD5E1",   # slate-300
    "text_dark":    "0F172A",
    "text_mid":     "374151",
}

CAT_COLORS = {"Kolay": C["cat_kolay"], "Orta": C["cat_orta"], "Zor": C["cat_zor"]}
CAT_BADGE  = {"Kolay": "DCFCE7",       "Orta": "DBEAFE",      "Zor": "F3E8FF"}


# ---------------------------------------------------------------------------
# XML / hücre yardımcıları
# ---------------------------------------------------------------------------

def strip_fences(text: str) -> str:
    t = str(text).strip()
    t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
    t = re.sub(r"\n?```$", "", t)
    return t.strip()


def cell_bg(cell, hex_color: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def cell_border(cell, color="CBD5E1", sz="4"):
    tcPr = cell._tc.get_or_add_tcPr()
    tcB = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"),   "single")
        el.set(qn("w:sz"),    sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcB.append(el)
    tcPr.append(tcB)


def cell_padding(cell, top=40, left=60, bottom=40, right=60):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"),    str(val))
        el.set(qn("w:type"), "dxa")
        tcMar.append(el)
    tcPr.append(tcMar)


def tight_spacing(para):
    pPr = para._p.get_or_add_pPr()
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:before"),   "0")
    sp.set(qn("w:after"),    "0")
    sp.set(qn("w:line"),     "220")
    sp.set(qn("w:lineRule"), "auto")
    pPr.append(sp)


def write(cell, text: str, bold=False, italic=False, size=9,
          color="0F172A", align=WD_ALIGN_PARAGRAPH.LEFT, mono=False):
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    para = cell.paragraphs[0]
    para.alignment = align
    tight_spacing(para)
    cell_padding(cell, 50, 70, 50, 70)
    run = para.add_run(str(text))
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = "Courier New" if mono else "Calibri"
    run.font.color.rgb = RGBColor.from_string(color)


def write_code(cell, code: str, fg: str, size=7.2):
    code = strip_fences(code)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
    para = cell.paragraphs[0]
    tight_spacing(para)
    cell_padding(cell, 60, 80, 60, 80)
    run = para.add_run(code)
    run.font.name = "Consolas"
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(fg)


def merge_row(table, row_idx: int):
    row = table.rows[row_idx]
    row.cells[0].merge(row.cells[-1])
    return row.cells[0]


def set_widths(table, widths_cm):
    for row in table.rows:
        for i, cell in enumerate(row.cells[:len(widths_cm)]):
            cell.width = Cm(widths_cm[i])


def no_gap(doc):
    p = doc.add_paragraph()
    tight_spacing(p)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after  = Pt(0)


# ---------------------------------------------------------------------------
# Tablo 1 — Prompt özeti
# ---------------------------------------------------------------------------

def build_table1(doc: Document, data: list):
    h = doc.add_heading("Tablo 1 — Test Edilen Benchmark Promptları", level=2)
    h.paragraph_format.space_before = Pt(0)
    h.paragraph_format.space_after  = Pt(4)

    cols = ["No", "Zorluk", "Prompt Metni", "Baş. Skor", "Final Skor", "Δ Skor", "Durum"]
    w    = [1.1, 1.4, 9.0, 1.7, 1.7, 1.4, 2.6]

    tbl = doc.add_table(rows=1, cols=len(cols))
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    for cell, h_txt in zip(tbl.rows[0].cells, cols):
        cell_bg(cell, C["t1_hdr"])
        cell_border(cell, color="0F172A", sz="4")
        write(cell, h_txt, bold=True, color=C["white"], size=8.5,
              align=WD_ALIGN_PARAGRAPH.CENTER)

    for idx, row in enumerate(data):
        bg  = C["row_even"] if idx % 2 == 0 else C["row_odd"]
        tr  = tbl.add_row()
        cat = row["cat"]
        d   = row["score_change"]

        vals = [
            row["label"],
            cat,
            row["prompt"][:420],
            str(row["initial_score"]),
            str(row["final_score"]),
            f"+{d}" if d > 0 else str(d),
            "İyileştirme Yapıldı" if row["status"] == "improved_via_feedback" else "İlk Çıktı Yeterli",
        ]
        badge_bg = CAT_BADGE.get(cat, "F1F5F9")
        badge_fg = CAT_COLORS.get(cat, C["text_dark"])

        for i, (val, cell) in enumerate(zip(vals, tr.cells)):
            cell_bg(cell, badge_bg if i == 1 else bg)
            cell_border(cell, color=C["border"])
            align = WD_ALIGN_PARAGRAPH.CENTER if i in (0, 3, 4, 5) else WD_ALIGN_PARAGRAPH.LEFT
            fc = badge_fg if i == 1 else C["text_dark"]
            write(cell, val, bold=(i == 0), size=8.2, color=fc, align=align)

    set_widths(tbl, w)
    no_gap(doc)


# ---------------------------------------------------------------------------
# Tablo 2 — Kod karşılaştırma + analiz
# ---------------------------------------------------------------------------

def build_table2(doc: Document, data: list):
    h = doc.add_heading("Tablo 2 — Kod Karşılaştırması ve İyileştirme Analizi", level=2)
    h.paragraph_format.space_before = Pt(0)
    h.paragraph_format.space_after  = Pt(4)

    W_HALF = 12.35  # her sütun (landscape A4, 2cm margin her yanda)

    for row in data:
        cat      = row["cat"]
        cat_clr  = CAT_COLORS.get(cat, C["text_dark"])

        # ── Prompt başlık satırı ──────────────────────────────────
        tbl = doc.add_table(rows=5, cols=2)
        tbl.style = "Table Grid"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Satır 0: birleşik başlık
        hdr_cell = merge_row(tbl, 0)
        cell_bg(hdr_cell, C["ph_bg"])
        cell_border(hdr_cell, color=C["ph_bg"], sz="6")
        d = row["score_change"]
        label_txt = (
            f"{row['label']}  ·  {cat.upper()}"
            f"  |  Başlangıç: {row['initial_score']}  →  Final: {row['final_score']}"
            f"  |  Δ = {d:+}"
            f"  |  {'İyileştirme Yapıldı' if row['status'] == 'improved_via_feedback' else 'İlk Çıktı Yeterli'}"
        )
        write(hdr_cell, label_txt, bold=True, color=C["white"],
              size=9, align=WD_ALIGN_PARAGRAPH.LEFT)

        # Satır 1: kod sütun başlıkları
        h_a, h_b = tbl.rows[1].cells
        cell_bg(h_a, C["code_hdr_a"])
        cell_bg(h_b, C["code_hdr_b"])
        cell_border(h_a, color="FFFFFF", sz="4")
        cell_border(h_b, color="FFFFFF", sz="4")
        write(h_a, "Başlangıç Kodu  —  Kazanan LLM Çıktısı",
              bold=True, color=C["white"], size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        write(h_b, "Final Kod  —  İyileştirme Döngüsü Sonrası",
              bold=True, color=C["white"], size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)

        # Satır 2: kod içerikleri
        c_a, c_b = tbl.rows[2].cells
        cell_bg(c_a, C["code_bg_a"])
        cell_bg(c_b, C["code_bg_b"])
        cell_border(c_a, color="334155", sz="4")
        cell_border(c_b, color="14532D", sz="4")
        write_code(c_a, row["initial_code"], fg=C["code_fg_a"])
        write_code(c_b, row["final_code"],   fg=C["code_fg_b"])

        # Satır 3: analiz sütun başlıkları
        a_a, a_b = tbl.rows[3].cells
        cell_bg(a_a, C["ana_hdr_a"])
        cell_bg(a_b, C["ana_hdr_b"])
        cell_border(a_a, color="FFFFFF", sz="4")
        cell_border(a_b, color="FFFFFF", sz="4")
        write(a_a, "Tespit Edilen Kalite Eksiklikleri",
              bold=True, color=C["white"], size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
        write(a_b, "Yapılan İyileştirmeler",
              bold=True, color=C["white"], size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)

        # Satır 4: analiz içerikleri
        b_a, b_b = tbl.rows[4].cells
        cell_bg(b_a, C["ana_bg_a"])
        cell_bg(b_b, C["ana_bg_b"])
        cell_border(b_a, color=C["border"], sz="4")
        cell_border(b_b, color=C["border"], sz="4")
        write(b_a, row["deficiencies"], size=8.2, color=C["text_dark"])
        write(b_b, row["improvements"], size=8.2, color=C["text_dark"])

        # Genişlikler
        set_widths(tbl, [W_HALF, W_HALF])

        # Promtlar arası küçük boşluk
        gap = doc.add_paragraph()
        tight_spacing(gap)
        gap.paragraph_format.space_before = Pt(3)
        gap.paragraph_format.space_after  = Pt(3)


# ---------------------------------------------------------------------------
# Ana
# ---------------------------------------------------------------------------

def main():
    df   = pd.read_excel(RESULTS_FILE)
    rows = []

    for sel in SELECTED:
        pid   = sel["id"]
        match = df[df["Prompt_ID"] == pid].drop_duplicates(subset="Prompt_ID")
        if match.empty:
            print(f"  ⚠  ID {pid} bulunamadı.")
            continue
        r = match.iloc[0]

        i_sc = float(r.get("Initial_Score", 0) or 0)
        f_sc = float(r.get("Final_Score",   0) or 0)

        rows.append({
            "id":            pid,
            "label":         sel["label"],
            "cat":           sel["cat"],
            "prompt":        str(r.get("Benchmark_Prompt", "")).strip()[:450],
            "initial_score": int(i_sc),
            "final_score":   int(f_sc),
            "score_change":  round(f_sc - i_sc),
            "status":        str(r.get("Status", "")),
            "initial_code":  str(r.get("Initial_Code", "")).strip()[:1400],
            "final_code":    str(r.get("Final_Code",   "")).strip()[:1400],
            "deficiencies":  str(r.get("LLM_Deficiencies",  "")).strip()[:700],
            "improvements":  str(r.get("Improvements_Made", "")).strip()[:700],
        })

    doc = Document()

    # Yatay A4 sayfa yapısı
    sec = doc.sections[0]
    sec.page_width    = Cm(29.7)
    sec.page_height   = Cm(21.0)
    sec.left_margin   = Cm(1.8)
    sec.right_margin  = Cm(1.8)
    sec.top_margin    = Cm(1.5)
    sec.bottom_margin = Cm(1.5)
    sec.orientation   = 1  # landscape

    # Varsayılan paragraf boşluklarını sıfırla
    style = doc.styles["Normal"]
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.space_after  = Pt(0)

    # Belge başlığı
    title = doc.add_heading("Deneysel Sonuçlar — Benchmark Test Tabloları", level=1)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(2)

    desc = doc.add_paragraph(
        "9 prompt test edilmiştir (3 Kolay · 3 Orta · 3 Zor)  ·  "
        "Koyu arka plan: kod editörü görünümü  ·  Amber: tespit edilen eksiklikler  ·  Yeşil: iyileştirmeler"
    )
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tight_spacing(desc)
    desc.paragraph_format.space_after = Pt(6)
    for run in desc.runs:
        run.font.size = Pt(8.5)
        run.italic = True
        run.font.color.rgb = RGBColor.from_string("64748B")

    build_table1(doc, rows)
    doc.add_page_break()
    build_table2(doc, rows)

    doc.save(OUTPUT_FILE)
    print(f"✅ {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
