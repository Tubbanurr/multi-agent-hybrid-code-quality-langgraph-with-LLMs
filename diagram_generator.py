"""
HAVELSAN - Hybrid Code Generator
Sistem Akis Semasi v3
- Ajanlar net etiketli
- Threshold sadece "Kalite Esigi"
- Feedback dongusu tamamen ayri sol koridor
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

# --------------------------------------------------------------------------
# RENK PALETI
# --------------------------------------------------------------------------
BG         = '#111820'
C_WHITE    = '#E8EAF0'
C_GRAY     = '#8899AA'
C_DIM      = '#5A6A7A'
C_ACCENT   = '#E8B84B'

COL_USER   = ('#0E2E1A', '#2EA85A')
COL_GEN    = ('#0C1E30', '#2E85C8')
COL_MDL1   = ('#0A2A1C', '#28A86A')
COL_MDL2   = ('#0A1E38', '#2870C8')
COL_MDL3   = ('#22103C', '#8840D8')
COL_STAT   = ('#180C2E', '#7840C8')
COL_SA     = ('#130924', '#5830A8')
COL_LLM    = ('#281A00', '#C88A18')
COL_JDG    = ('#201200', '#C88A18')
COL_HYB    = ('#081828', '#2870C8')
COL_CATS   = ('#081828', '#2870C8')
COL_CATL   = ('#201200', '#C88A18')
COL_DEC    = ('#280808', '#D04040')
COL_FIN    = ('#082818', '#28A850')
COL_LOG    = ('#141C24', '#445566')
COL_FEED   = ('#281200', '#C87018')
COL_ROLL   = ('#082010', '#28A840')
COL_AGENT  = ('#0A2040', '#3A90E0')  # ajan etiketi kutusu

A_MAIN  = '#4A9FD4'
A_FEED  = '#C87018'
A_YES   = '#28A850'
A_NO    = '#D04040'

# --------------------------------------------------------------------------
fig = plt.figure(figsize=(32, 52))
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 32)
ax.set_ylim(0, 52)
ax.axis('off')
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)

# --------------------------------------------------------------------------
# YARDIMCILAR
# --------------------------------------------------------------------------

def box(x, y, w, h, fc, ec, lw=1.8, r=0.3, zo=3):
    p = FancyBboxPatch((x - w/2, y - h/2), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       facecolor=fc, edgecolor=ec,
                       linewidth=lw, zorder=zo)
    ax.add_patch(p)

def tx(x, y, s, sz=9.5, c=C_WHITE, bold=False, ha='center', va='center', zo=5):
    ax.text(x, y, s, fontsize=sz, color=c,
            fontweight='bold' if bold else 'normal',
            ha=ha, va=va, zorder=zo)

def arr_v(x, y1, y2, c=A_MAIN, lw=2.2):
    """Dikey ok, y1'den y2'ye."""
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=c, lw=lw,
                                connectionstyle='arc3,rad=0'),
                zorder=6)

def arr_h(x1, y, x2, c=A_MAIN, lw=2.2):
    """Yatay ok."""
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=c, lw=lw,
                                connectionstyle='arc3,rad=0'),
                zorder=6)

def line_v(x, y1, y2, c=A_MAIN, lw=2.2):
    """Ok basi olmayan dikey cizgi."""
    ax.plot([x, x], [y1, y2], color=c, lw=lw, zorder=5)

def line_h(x1, y, x2, c=A_MAIN, lw=2.2):
    """Ok basi olmayan yatay cizgi."""
    ax.plot([x1, x2], [y, y], color=c, lw=lw, zorder=5)

def side_note(x, y, s, c=C_DIM, sz=8.5):
    ax.text(x, y, s, fontsize=sz, color=c, ha='center', va='center', zorder=6,
            bbox=dict(boxstyle='round,pad=0.22', facecolor=BG,
                      edgecolor='none', alpha=0.9))

def agent_tag(x, y, label):
    """Ajan etiketi - koyu mavi pill kutu."""
    box(x, y, len(label)*0.18 + 1.5, 0.46, COL_AGENT[0], COL_AGENT[1], lw=1.2, r=0.2, zo=6)
    tx(x, y, label, sz=8.5, c='#90C8F0', bold=True, zo=7)

def hline(y):
    ax.plot([0.5, 31.5], [y, y], color='#2A3A4A', lw=0.7, ls='--', zorder=2)

# ── LAYOUT SABITLERI ─────────────────────────────────────────────────────
# Sol feedback koridoru: x = 2.2  (dikey hat)
# Ana akis dugumler: merkez x = 17.5,  genislik = 22 (sol kenar x=6.5)
# Dugum sol kenari: x = 6.5
MX   = 17.5   # merkez x
NW   = 22.0   # node genislik
FX   = 2.2    # feedback dikey hat

# ==========================================================================
# BASLIK
# ==========================================================================
box(16, 51.2, 31.5, 1.55, '#091628', C_ACCENT, lw=2.5, r=0.5)
tx(16, 51.52, 'HAVELSAN  -  HIBRIT KOD URETIM SISTEMI', sz=19, c=C_ACCENT, bold=True)
tx(16, 51.0,  'Cok Ajanli Sistem Akis Semasi  |  Ajan Mimarisi & Arac Cagrilari', sz=10.5, c=C_DIM)

hline(50.3)

# Renk anahtari
legend = [
    (COL_GEN[0],  COL_GEN[1],  'Kod Uretici Ajanlar'),
    (COL_STAT[0], COL_STAT[1], 'Statik Analiz Araclari'),
    (COL_LLM[0],  COL_LLM[1],  'LLM Yargici Ajani'),
    (COL_FEED[0], A_FEED,      'Geri Bildirim Ajani'),
    (COL_DEC[0],  COL_DEC[1],  'Karar Noktasi'),
    (COL_FIN[0],  COL_FIN[1],  'Sonlandirma'),
]
for i, (fc, ec, lbl) in enumerate(legend):
    bx = 4.0 + i * 4.7
    box(bx, 49.72, 0.65, 0.40, fc, ec, lw=1.1, r=0.12)
    tx(bx + 1.9, 49.72, lbl, sz=8.5, c=C_GRAY, ha='left')

hline(49.22)

# ==========================================================================
# KULLANICI GIRISI
# ==========================================================================
box(MX, 48.35, 12, 1.28, COL_USER[0], COL_USER[1], lw=2.2, r=0.5)
tx(MX, 48.65, 'KULLANICI', sz=13, c='#6EE7A0', bold=True)
tx(MX, 48.2,  '"Python kodu yaz:  binary search algoritmasi"', sz=9.5, c='#A8E6C0')

arr_v(MX, 47.72, 47.1, A_MAIN, lw=2.5)
side_note(MX + 5.0, 47.4, 'HTTP POST /generate   (FastAPI)', C_DIM, 8.5)

# ==========================================================================
# DUGUM 1  -  GENERATOR
# ==========================================================================
G_Y = 44.9
box(MX, G_Y, NW, 3.6, COL_GEN[0], COL_GEN[1], lw=2.5, r=0.5)

# Baslik seridi
box(MX, G_Y + 1.44, NW - 0.12, 0.82, COL_GEN[1], COL_GEN[1], lw=0, r=0.38)
tx(MX, G_Y + 1.44, 'DUGUM 1  -  GENERATOR   |   generator_node()', sz=13, c='#12181F', bold=True)

tx(MX, G_Y + 0.77,
   'Kullanicinin istegi 3 farkli yapay zeka modeline ES ZAMANLI gonderilir  (ThreadPoolExecutor).',
   sz=9.2, c=C_WHITE)
tx(MX, G_Y + 0.38,
   'Her model bagimsiz Python kodu uretir.  Halusinasyon tespit edilirse model otomatik yeniden cagrilir.',
   sz=9.2, c=C_GRAY)

# Ajan etiketi
agent_tag(MX - 7.5, G_Y + 1.44, 'AKTIF AJANLAR:  Kod Uretici Ajan x3')

# 3 model kutusu
m_data = [
    ('Llama 3.3 70B',    'Groq API  (call_codellama)',   'Kod Uretici Ajan 1', COL_MDL1),
    ('DeepSeek V3',      'DeepSeek API  (call_deepseek)','Kod Uretici Ajan 2', COL_MDL2),
    ('Gemini 2.0 Flash', 'Google API  (call_gemini)',    'Kod Uretici Ajan 3', COL_MDL3),
]
for i, (name, env, role, col) in enumerate(m_data):
    mx = 9.5 + i * 6.2
    box(mx, G_Y - 0.78, 5.6, 1.28, col[0], col[1], lw=1.8, r=0.28)
    tx(mx, G_Y - 0.35, name, sz=10.5, c=C_WHITE, bold=True)
    tx(mx, G_Y - 0.75, env,  sz=7.5,  c=C_GRAY)
    tx(mx, G_Y - 1.1,  role, sz=8.5,  c=C_ACCENT, bold=True)

arr_v(MX, G_Y - 1.43, G_Y - 1.95, A_MAIN, lw=2.5)
side_note(MX + 6.5, G_Y - 1.68, '3 ayri Python kodu uretildi', C_DIM, 8.5)

# ==========================================================================
# DUGUM 2  -  STATIK ANALIZOR
# ==========================================================================
S_Y = 39.5
box(MX, S_Y, NW, 5.5, COL_STAT[0], COL_STAT[1], lw=2.5, r=0.5)

box(MX, S_Y + 2.3, NW - 0.12, 0.82, COL_STAT[1], COL_STAT[1], lw=0, r=0.38)
tx(MX, S_Y + 2.3, 'DUGUM 2  -  STATIK ANALIZOR   |   static_analyzer_node()', sz=13, c='#12181F', bold=True)

# Ajan etiketi - statik araclara ajan denmiyor, "araclar" diyoruz
agent_tag(MX - 7.5, S_Y + 2.3, 'ARACLAR:  6 Statik Analiz Motoru')

tx(MX, S_Y + 1.65,
   'Kod gecici bir dosyaya yazilir  (TempCodeManager).  6 arac AYNI dosya uzerinde sirayla calisir.',
   sz=9.2, c=C_WHITE)
tx(MX, S_Y + 1.27, 'Maksimum toplam puan: 70', sz=9.2, c=C_ACCENT)

# 6 analizor - 2 satirda 3'er tane, daha okunabilir
sa_data = [
    ('ASTAnalyzer',           'Python AST',  'Syntax (+5)\nType Hints\nHata Yonetimi (+10)'),
    ('ComplexityAnalyzer',    'Radon CC',    'Dongusel Karmasiklik\navg<=5: +15\navg<=10: +12'),
    ('LintAnalyzer\n(Pylint)','Pylint',      'Genel kalite 0-10\n15 puana olceklenir\n(+15 puan)'),
    ('LintAnalyzer\n(Flake8)','Flake8',      'PEP8 ihlal sayisi\n< 20 kalirsa\nmaks puan (+15)'),
    ('ContentAnalyzer',       'Saf Python',  'Yorum yogunlugu\n%5-65 arasi (+5)\nKod tekrari (+5)'),
    ('SecurityAnalyzer',      'Bandit',      'HIGH/MED/LOW\nguvenlik acigi\n* Skora dahil degil'),
]
sa_xs = [7.8, 12.0, 16.2, 20.4, 24.6, 28.8]
for idx, ((cls, tool, pts), sx) in enumerate(zip(sa_data, sa_xs)):
    is_sec = idx == 5
    ec_c = '#D04040' if is_sec else COL_SA[1]
    box(sx, S_Y - 0.22, 3.9, 2.2, COL_SA[0], ec_c, lw=1.4, r=0.25)
    for j, cl in enumerate(cls.split('\n')):
        tx(sx, S_Y + 0.75 - j*0.38, cl, sz=8.8, c=C_WHITE, bold=True)
    tx(sx, S_Y + 0.12, f'Arac: {tool}', sz=7.8, c=C_ACCENT)
    for j, pl in enumerate(pts.split('\n')):
        tx(sx, S_Y - 0.28 - j*0.35, pl, sz=7.5, c=C_GRAY)

arr_v(MX, S_Y - 2.48, S_Y - 3.02, A_MAIN, lw=2.5)
side_note(MX + 6.5, S_Y - 2.74, 'Statik analiz sonuclari  ->  bir sonraki dugume', C_DIM, 8.5)

# ==========================================================================
# DUGUM 3  -  LLM JUDGE
# ==========================================================================
L_Y = 33.3
box(MX, L_Y, NW, 4.6, COL_LLM[0], COL_LLM[1], lw=2.5, r=0.5)

box(MX, L_Y + 1.92, NW - 0.12, 0.82, COL_LLM[1], COL_LLM[1], lw=0, r=0.38)
tx(MX, L_Y + 1.92, 'DUGUM 3  -  LLM JUDGE   |   llm_judge_node()', sz=13, c='#12181F', bold=True)

agent_tag(MX - 7.5, L_Y + 1.92, 'AKTIF AJAN:  Yargici Ajan  —  Semantik Kod Degerlendirmesi')

tx(MX, L_Y + 1.28,
   'Llama 3.3 70B (Groq)  kodu ANLAMSAL olarak degerlendirir.  Yerel modda Ollama DeepSeek-R1 kullanilir.',
   sz=9.5, c=C_WHITE)
tx(MX, L_Y + 0.88,
   'Once <think> blogu ile adim adim dusunur  (Chain-of-Thought),  sonra JSON formatinda 4 kritere gore puan verir.',
   sz=9.2, c=C_GRAY)

# Model kutusu (sol)
box(9.2, L_Y - 0.5, 7.8, 1.85, COL_JDG[0], COL_JDG[1], lw=2.0, r=0.35)
tx(9.2, L_Y + 0.35, 'DeepSeek-R1  14B', sz=12, c='#F0D070', bold=True)
tx(9.2, L_Y - 0.05, 'OLLAMA_JUDGE_MODEL', sz=9, c=C_GRAY)
tx(9.2, L_Y - 0.45, 'call_deepseek_r1_judge()', sz=9, c=C_ACCENT)
tx(9.2, L_Y - 0.82, 'call_ollama_chat()  format_json=True', sz=8.2, c=C_GRAY)

# 4 degerl. kriteri (sag)
crit_data = [
    ('Identifier\nClarity',  '0-5',   'Degisken\nnetligi'),
    ('Prompt\nAdherence',    '0-10',  'Istege\nuyum'),
    ('Naming\nAlignment',    '0-5',   'Domain\nterminoloji'),
    ('Logic &\nReliability', '0-10',  'Kod\nmantiği'),
]
crit_xs = [16.2, 19.8, 23.4, 27.0]
for (cn, cp, cd), cx in zip(crit_data, crit_xs):
    box(cx, L_Y - 0.5, 3.2, 1.85, COL_JDG[0], COL_JDG[1], lw=1.3, r=0.25)
    for j, cl in enumerate(cn.split('\n')):
        tx(cx, L_Y + 0.45 - j*0.36, cl, sz=8.8, c='#F0D070', bold=True)
    tx(cx, L_Y - 0.1, cp + ' puan', sz=10, c=C_ACCENT, bold=True)
    for j, dl in enumerate(cd.split('\n')):
        tx(cx, L_Y - 0.52 - j*0.36, dl, sz=7.8, c=C_GRAY)

# Toplam kutusu
box(MX, L_Y - 2.0, 14, 0.65, '#180E00', COL_LLM[1], lw=1.5, r=0.25)
tx(MX, L_Y - 2.0, 'TOPLAM MAKSIMUM:  30 PUAN   (Semantik / Anlamsal Degerlendirme)', sz=10, c='#F0D070', bold=True)

arr_v(MX, L_Y - 2.33, L_Y - 2.88, A_MAIN, lw=2.5)
side_note(MX + 6.5, L_Y - 2.6, 'Semantik puanlar  ->  bir sonraki dugume', C_DIM, 8.5)

# ==========================================================================
# DUGUM 4  -  HYBRID SCORER
# ==========================================================================
H_Y = 26.9
box(MX, H_Y, NW, 5.3, COL_HYB[0], COL_HYB[1], lw=2.5, r=0.5)

box(MX, H_Y + 2.22, NW - 0.12, 0.82, COL_HYB[1], COL_HYB[1], lw=0, r=0.38)
tx(MX, H_Y + 2.22, 'DUGUM 4  -  HYBRID SCORER   |   hybrid_scorer_node()', sz=13, c='#12181F', bold=True)

agent_tag(MX - 7.5, H_Y + 2.22, 'AKTIF AJAN:  Hibrit Skorlayici  —  6 Kategoride 100 Puan Hesabi')

tx(MX, H_Y + 1.58,
   'Statik analiz (%70 agirlik)  +  LLM semantik puani (%30 agirlik)  birlestirilerek  TOPLAM SKOR  (0-100)  hesaplanir.',
   sz=9.2, c=C_WHITE)
tx(MX, H_Y + 1.18,
   'Ilk tur: 3 modelin skoru karsilastirilir,  en yuksek skoru alan KAZANIR.  Sonraki turlarda: iyilesmis kod tekrar olculur.',
   sz=9.2, c=C_GRAY)

# 6 kategori — alt metriklerle
cat_data = [
    ('Kat.1', 'KOD\nKALITESI',   '20',
     'CC: Radon (max 15)\nYorum yogunlugu (max 5)\navg CC <= 5 → tam puan', 'Statik'),
    ('Kat.2', 'TEKNIK\nBORC',     '20',
     'Pylint 0-10 (max 15)\nDuplication (max 5)\nType Hints (bonus)', 'Statik'),
    ('Kat.3', 'TEST &\nBUILD',    '15',
     'Syntax gecerli (5 pt)\ntry-except bloklar (10 pt)\nAST derleme kontrolu', 'Statik'),
    ('Kat.4', 'STIL &\nSTANDART', '15',
     'Flake8 PEP8 ihlalleri\n< 5 ihlal → 15 pt\nFormat & bosluk', 'Statik'),
    ('Kat.5', 'SEMANTIC\nUYUM',   '15',
     'Prompt Adherence (10)\nNaming Alignment (5)\nLLM Yargici degerlend.', 'LLM'),
    ('Kat.6', 'SAGLAMLIK\n& GUVEN', '15',
     'Logic & Reliability (10)\nIdentifier Clarity (5)\nLLM Yargici degerlend.', 'LLM'),
]
cat_xs = [7.8, 11.8, 15.7, 19.6, 23.5, 27.5]
for (cno, cn, puan, cdesc, src), cx in zip(cat_data, cat_xs):
    is_llm = src == 'LLM'
    face = COL_CATL[0] if is_llm else COL_CATS[0]
    edge = COL_CATL[1] if is_llm else COL_CATS[1]
    box(cx, H_Y - 0.6, 3.7, 3.4, face, edge, lw=1.4, r=0.25)
    tx(cx, H_Y + 1.0, cno, sz=7.8, c=C_DIM)
    for j, cl in enumerate(cn.split('\n')):
        tx(cx, H_Y + 0.62 - j*0.36, cl, sz=9, c=C_WHITE, bold=True)
    tx(cx, H_Y + 0.0, puan + ' pt', sz=13, c=C_ACCENT, bold=True)
    for j, dl in enumerate(cdesc.split('\n')):
        tx(cx, H_Y - 0.55 - j*0.38, dl, sz=7.2, c=C_GRAY)
    tx(cx, H_Y - 1.92, f'Kaynak: {src}', sz=7.2, c=C_DIM)

# Toplam kutusu
box(MX, H_Y - 3.08, 15, 0.68, '#060E1A', COL_HYB[1], lw=1.8, r=0.25)
tx(MX, H_Y - 3.08, 'TOPLAM HIBRIT SKOR = 100 PUAN   |   En yuksek skoru alan model KAZANIR', sz=10.5, c=C_ACCENT, bold=True)

# Geri Bildirim Ajani yan kutusu (sag) — CoT Feedback Agent
box(29.5, H_Y + 0.55, 4.6, 3.8, COL_FEED[0], A_FEED, lw=2.0, r=0.38)
tx(29.5, H_Y + 2.2,  'CoT FEEDBACK',       sz=10,   c=A_FEED, bold=True)
tx(29.5, H_Y + 1.78, 'AJANI',              sz=10,   c=A_FEED, bold=True)
tx(29.5, H_Y + 1.35, 'Cloud: Llama 3.3 70B',sz=8,  c='#F0D070')
tx(29.5, H_Y + 0.97, '(Groq API)',         sz=7.8,  c=C_GRAY)
tx(29.5, H_Y + 0.60, 'Lokal: DeepSeek-R1', sz=8,   c='#F0D070')
tx(29.5, H_Y + 0.22, '(Ollama)',           sz=7.8,  c=C_GRAY)
tx(29.5, H_Y - 0.18, 'generate_cot_feedback()',sz=7.8,c=C_ACCENT)
tx(29.5, H_Y - 0.58, 'Koda ozgu iyilestirme',sz=7.8,c=C_GRAY)
tx(29.5, H_Y - 0.96, 'onerileri (JSON)',   sz=7.8,  c=C_GRAY)
arr_h(28.5, H_Y + 0.5, 27.65, A_FEED, lw=1.8)

arr_v(MX, H_Y - 3.42, H_Y - 3.98, A_MAIN, lw=2.5)

# ==========================================================================
# KARAR NOKTASI
# ==========================================================================
DEC_Y = 22.65
dw, dh = 9.8, 2.2
diamond = plt.Polygon([
    [MX,          DEC_Y + dh/2],
    [MX + dw/2,   DEC_Y],
    [MX,          DEC_Y - dh/2],
    [MX - dw/2,   DEC_Y],
], closed=True, facecolor='#200808', edgecolor='#D04040', lw=3.0, zorder=3)
ax.add_patch(diamond)
tx(MX, DEC_Y + 0.36, 'KARAR NOKTASI  -  should_continue()', sz=12, c='#E06060', bold=True)
tx(MX, DEC_Y - 0.26, 'Hibrit Skor  >=  Kalite Esigi  ?', sz=11, c=C_WHITE)

# Kalite esigi kutusu (sag)
box(MX + 9.8, DEC_Y, 5.8, 1.9, '#200808', COL_DEC[1], lw=1.5, r=0.35)
tx(MX + 9.8, DEC_Y + 0.66, 'THRESHOLD', sz=11, c=COL_DEC[1], bold=True)
tx(MX + 9.8, DEC_Y + 0.24, 'Kullanici tarafindan belirlenir.', sz=8.8, c=C_GRAY)
tx(MX + 9.8, DEC_Y - 0.16, 'Esik gecilemezse maksimum', sz=8.8, c=C_GRAY)
tx(MX + 9.8, DEC_Y - 0.56, '11 iterasyon sonra sonlanir.', sz=8.8, c=C_GRAY)
arr_h(MX + dw/2 + 0.1, DEC_Y, MX + 6.9, COL_DEC[1], lw=1.5)

# ── EVET (asagi -> Finalize) ──────────────────────────────────────────────
arr_v(MX, DEC_Y - dh/2, DEC_Y - 1.65, A_YES, lw=3.0)
side_note(MX + 6.0, DEC_Y - 1.15, 'EVET:  Skor yeterli  ->  SONLANDIR', '#6EE7A0', 10)

# ── HAYIR (sol -> feedback koridoru) ─────────────────────────────────────
# Adim 1: elmastan sola yatay git
line_h(MX - dw/2, DEC_Y, FX, A_NO, lw=2.8)
# Adim 2: FX noktasina ok ucu koy (noktadan bitti hissi icin)
ax.plot(FX, DEC_Y, 'o', color=A_NO, markersize=8, zorder=7)
side_note(FX - 1.5, DEC_Y + 0.5, 'HAYIR', A_NO, 11)

hline(21.4)

# ==========================================================================
# ---- SOL FEEDBACK KORIDORU (tamamen ayri, temiz) ----
# Koridr x = FX = 2.2
# Asagidan yukari:
#   DEC_Y  -> ROLLBACK KUTUSU -> DURMA KOSULLARI -> GENERATOR
# ==========================================================================

# Adim A: DEC_Y'den asagi git -> Rollback kutusu
ROLL_Y = 19.65
line_v(FX, DEC_Y, ROLL_Y + 0.88, A_NO, lw=2.8)

# Rollback kutusu
box(FX, ROLL_Y, 4.2, 1.6, COL_ROLL[0], COL_ROLL[1], lw=2.0, r=0.35)
tx(FX, ROLL_Y + 0.56, 'ROLLBACK', sz=10, c=COL_ROLL[1], bold=True)
tx(FX, ROLL_Y + 0.18, 'Yeni skor dusuk ciktiysa', sz=8.5, c=C_GRAY)
tx(FX, ROLL_Y - 0.20, 'ONCEKI KODA geri don.', sz=8.5, c=C_GRAY)
tx(FX, ROLL_Y - 0.58, 'En iyi skor korunur.', sz=8.5, c='#A8E6C0')

# Adim B: Rollback'ten yukari git -> Durma Kosullari kutusu
STOP_Y = 17.1
arr_v(FX, ROLL_Y + 0.88, STOP_Y + 0.92, A_FEED, lw=2.8)

# Durma kosullari kutusu
box(FX, STOP_Y, 4.2, 1.7, COL_FEED[0], A_FEED, lw=2.0, r=0.35)
tx(FX, STOP_Y + 0.64, 'ERKEN DURMA', sz=10, c=A_FEED, bold=True)
tx(FX, STOP_Y + 0.25, 'Art arda 4 iterasyonda', sz=8.5, c=C_GRAY)
tx(FX, STOP_Y - 0.12, 'iyilesme yoksa dur.', sz=8.5, c=C_GRAY)
tx(FX, STOP_Y - 0.50, 'Max iterasyon: 11', sz=8.5, c=C_GRAY)

# Adim C: Durma'dan yukari git -> Generator dugumune geri don
# Generator'un sol kenari: MX - NW/2 = 17.5 - 11 = 6.5
GEN_LEFT = MX - NW / 2   # = 6.5
GEN_ENTRY_Y = G_Y - 0.8  # generator'un orta alt bolumu

arr_v(FX, STOP_Y + 0.88, GEN_ENTRY_Y, A_FEED, lw=2.8)
# Yatay gec: FX -> GEN_LEFT
arr_h(FX, GEN_ENTRY_Y, GEN_LEFT, A_FEED, lw=2.8)

# Koridor etiketi ve bilgi kutulari (sol kenar)
FEED_MID_Y = (GEN_ENTRY_Y + STOP_Y) / 2  # ~30.6

tx(FX, FEED_MID_Y + 7.8, 'FEEDBACK', sz=10, c=A_FEED, bold=True, ha='center')
tx(FX, FEED_MID_Y + 7.2, 'DONGUSU',  sz=10, c=A_FEED, bold=True, ha='center')

# CoT Feedback Agent bilgi kutusu
box(FX, FEED_MID_Y + 4.0, 4.2, 4.6, COL_FEED[0], A_FEED, lw=1.8, r=0.3)
tx(FX, FEED_MID_Y + 6.1, 'CoT FEEDBACK', sz=9, c=A_FEED, bold=True)
tx(FX, FEED_MID_Y + 5.65,'AJANI', sz=9, c=A_FEED, bold=True)
tx(FX, FEED_MID_Y + 5.15,'Cloud: Llama 3.3 70B', sz=7.5, c='#F0D070')
tx(FX, FEED_MID_Y + 4.7, '(Groq API)', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y + 4.2, 'Lokal: DeepSeek-R1', sz=7.5, c='#F0D070')
tx(FX, FEED_MID_Y + 3.75,'(Ollama)', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y + 3.25,'generate_cot_feedback()', sz=7.2, c=C_ACCENT)
tx(FX, FEED_MID_Y + 2.75,'Koda ozgu Turkce', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y + 2.28,'iyilestirme onerileri', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y + 1.82,'JSON formatinda uretir.', sz=7.2, c=C_GRAY)

# Donguye giren veriler kutusu
box(FX, FEED_MID_Y - 1.0, 4.2, 3.6, '#081020', '#3A6A9A', lw=1.5, r=0.28)
tx(FX, FEED_MID_Y + 0.8, 'DONGUYE GIREN', sz=8.2, c='#90C8F0', bold=True)
tx(FX, FEED_MID_Y + 0.38,'VERILER:', sz=8.2, c='#90C8F0', bold=True)
tx(FX, FEED_MID_Y - 0.08,'• Kazanan kodun kendisi', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y - 0.52,'• Onceki statik analiz puani', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y - 0.96,'• Onceki LLM semantik puani', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y - 1.40,'• CoT onerileri (JSON)', sz=7.2, c=C_GRAY)
tx(FX, FEED_MID_Y - 1.84,'• 6 kategori karsılastirma', sz=7.2, c=C_GRAY)

# Alt not
tx(FX, FEED_MID_Y - 3.2, 'Kazanan model', sz=8, c=C_GRAY, ha='center')
tx(FX, FEED_MID_Y - 3.6, 'iyilestirilmis', sz=8, c=C_GRAY, ha='center')
tx(FX, FEED_MID_Y - 4.0, 'prompt ile', sz=8, c=C_GRAY, ha='center')
tx(FX, FEED_MID_Y - 4.4, 'yeniden uretir.', sz=8, c=C_GRAY, ha='center')

hline(15.7)

# ==========================================================================
# DUGUM 5  -  FINALIZE
# ==========================================================================
FIN_Y = 14.65
box(MX, FIN_Y, NW, 2.5, COL_FIN[0], COL_FIN[1], lw=2.5, r=0.5)

box(MX, FIN_Y + 0.92, NW - 0.12, 0.82, COL_FIN[1], COL_FIN[1], lw=0, r=0.38)
tx(MX, FIN_Y + 0.92, 'DUGUM 5  -  FINALIZE   |   finalize_node()', sz=13, c='#12181F', bold=True)

fields = [
    ('final_code',           'En iyi Python kodu'),
    ('final_score',          'Son kalite puani / 100'),
    ('winner_model',         'Kazanan modelin adi'),
    ('feedback_iterations',  'Tum iterasyon gecmisi'),
]
for i, (k, v) in enumerate(fields):
    fx = 8.0 + i * 6.2
    box(fx, FIN_Y - 0.45, 5.6, 0.88, '#072010', COL_FIN[1], lw=1.2, r=0.22)
    tx(fx, FIN_Y - 0.2,  k, sz=9,   c='#A8E6C0', bold=True)
    tx(fx, FIN_Y - 0.62, v, sz=8.5, c=C_DIM)

arr_v(MX, FIN_Y - 1.25, FIN_Y - 1.85, A_MAIN, lw=2.2)

# ==========================================================================
# LOGLAMA
# ==========================================================================
LOG_Y = 12.55
box(MX, LOG_Y, NW, 1.85, '#111820', '#3A4A5A', lw=1.8, r=0.4)
tx(MX, LOG_Y + 0.66, 'LOGLAMA   -   _log_workflow_result()', sz=12, c='#7799AA', bold=True)
for i, (fn, fd) in enumerate([
    ('workflow_log.csv',       'Her istek kayit altina alinir'),
    ('workflow_report.xlsx',   'Excel raporuna aktarilir'),
    ('benchmark_results.xlsx', 'Benchmark karsilastirma'),
]):
    lx = 8.5 + i * 7.8
    tx(lx, LOG_Y + 0.06, fn, sz=9,   c=C_ACCENT, bold=True)
    tx(lx, LOG_Y - 0.38, fd, sz=8.5, c=C_DIM)

arr_v(MX, LOG_Y - 0.93, LOG_Y - 1.52, A_MAIN, lw=2.2)

# ==========================================================================
# KULLANICIYA CIKTI
# ==========================================================================
OUT_Y = 10.75
box(MX, OUT_Y, 22, 1.55, COL_USER[0], COL_USER[1], lw=2.2, r=0.5)
tx(MX, OUT_Y + 0.42, 'KULLANICIYA DONEN SONUC   (HTTP JSON Response)', sz=13, c='#6EE7A0', bold=True)
for i, of in enumerate(['final_code', 'final_score', 'winner_model', 'feedback_iterations', 'status']):
    tx(7.5 + i * 4.8, OUT_Y - 0.35, of, sz=8.8, c='#3DAA67', bold=True)

hline(9.85)

# ==========================================================================
# BENCHMARK
# ==========================================================================
BM_Y = 8.95
box(MX, BM_Y, 28, 1.75, '#101820', '#3A4A5A', lw=1.8, r=0.4)
tx(MX, BM_Y + 0.58, 'BENCHMARK SISTEMI   -   benchmark_runner.py', sz=12, c='#6688AA', bold=True)
tx(MX, BM_Y + 0.16, '108 adet Python sorusu  (Kolay / Orta / Zor)  sistematik olarak sisteme gonderilir ve sonuclar karsilastirilir.', sz=9, c=C_WHITE)
tx(MX, BM_Y - 0.26, 'Kaynak: benchmark-gemini.xlsx    |    Cikti: benchmark_results.xlsx    |    Ilerleme: benchmark_progress.json', sz=8.5, c=C_ACCENT)

hline(7.95)

# ==========================================================================
# TASARIM PRENSIPLERI
# ==========================================================================
PR_Y = 6.65
box(MX, PR_Y, 31.5, 3.55, '#090F18', C_ACCENT, lw=2.2, r=0.5)
tx(MX, PR_Y + 1.5, 'TEMEL TASARIM PRENSİPLERİ', sz=14, c=C_ACCENT, bold=True)
pr_data = [
    ('TAMAMEN OFFLINE',
     'Internet baglantisi gerekmez.\nTum modeller Ollama ile\nyerel makinede calisir.'),
    ('PARALEL URETIM',
     '3 model ayni anda calisir.\nThreadPoolExecutor ile\n3 is parcacigi.'),
    ('OTOMATIK DONGU',
     'Kalite esigine ulasilana dek\notomatik iyilestirme.\nMaks 11 iterasyon.'),
    ('ROLLBACK KORUMA',
     'Skor duserse onceki iyi\nkod otomatik geri yuklenir.\nEn iyi hic kaybolmaz.'),
    ('CHAIN-OF-THOUGHT',
     'DeepSeek-R1 once <think>\nblogunda dusunur, sonra\nJSON puan verir.'),
    ('HIBRIT PUANLAMA',
     '%70 Statik Analiz\n%30 LLM Semantik\n= 100 toplam puan'),
]
pr_xs = [3.5, 9.0, 14.4, 19.8, 25.2, 30.2]
for (pt, pd), px in zip(pr_data, pr_xs):
    box(px, PR_Y - 0.22, 4.8, 2.15, '#0C1A2E', '#2A3E56', lw=1.2, r=0.28)
    tx(px, PR_Y + 0.65, pt, sz=9, c='#90C4E8', bold=True)
    for j, dl in enumerate(pd.split('\n')):
        tx(px, PR_Y + 0.18 - j * 0.42, dl, sz=8.5, c=C_GRAY)

# Teknoloji cubugu
box(MX, 4.55, 31.5, 0.78, '#06101A', '#1E2E3E', lw=0.8, r=0.2)
tx(MX, 4.55,
   'FastAPI  |  LangGraph (StateGraph)  |  Ollama (Yerel LLM)  '
   '|  Radon  |  Pylint  |  Flake8  |  Bandit  |  pytest-cov  |  Python AST',
   sz=8.5, c='#2E3E4E')

# --------------------------------------------------------------------------
plt.savefig('/Users/tuba/Desktop/ap/sistem_akis_semasi.png', dpi=180,
            bbox_inches='tight', facecolor=BG, edgecolor='none')
plt.savefig('/Users/tuba/Desktop/ap/sistem_akis_semasi.pdf',
            bbox_inches='tight', facecolor=BG, edgecolor='none')
print("Sema kaydedildi:")
print("  PNG -> /Users/tuba/Desktop/ap/sistem_akis_semasi.png")
print("  PDF -> /Users/tuba/Desktop/ap/sistem_akis_semasi.pdf")
plt.close()
