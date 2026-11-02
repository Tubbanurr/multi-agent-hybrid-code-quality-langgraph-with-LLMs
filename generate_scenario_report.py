"""
Akıllı Belge İşleme Sistemi — Senaryo Analiz Raporu PDF Üretici
Düzenlenebilir, metin seçilebilir PDF
Türkçe karakter desteği + Akademik rapor stili
"""

import os, warnings
warnings.filterwarnings('ignore')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from datetime import datetime

# ──────────────────────────────────────────────────────────────
#  FONT PATHS
# ──────────────────────────────────────────────────────────────
MPL_FONT_DIR = '/Users/tuba/Library/Python/3.9/lib/python/site-packages/matplotlib/mpl-data/fonts/ttf/'
FONT_REG     = MPL_FONT_DIR + 'DejaVuSans.ttf'
FONT_BOLD    = MPL_FONT_DIR + 'DejaVuSans-Bold.ttf'
FONT_ITALIC  = MPL_FONT_DIR + 'DejaVuSans-Oblique.ttf'

from matplotlib import font_manager as fm
fm.fontManager.addfont(FONT_REG)
fm.fontManager.addfont(FONT_BOLD)
plt.rcParams['font.family'] = 'DejaVu Sans'

# ──────────────────────────────────────────────────────────────
#  RENK PALETİ
# ──────────────────────────────────────────────────────────────
BG_DARK     = '#111820'
C_WHITE     = '#E8EAF0'
C_GRAY      = '#8899AA'
C_DIM       = '#5A6A7A'
C_ACCENT    = '#E8B84B'

# Kutu renkleri
COL_INPUT   = ('#0E2E1A', '#2EA85A')
COL_SECURITY= ('#1A0A2E', '#8840D8')
COL_ROUTER  = ('#0C1E30', '#2E85C8')
COL_FAST    = ('#082818', '#28A850')
COL_HARD    = ('#281A00', '#C88A18')
COL_LLM     = ('#22103C', '#8840D8')
COL_JUDGE   = ('#280808', '#D04040')
COL_ERP     = ('#082818', '#28A850')
COL_UI      = ('#281200', '#C87018')
COL_FINE    = ('#0A2040', '#3A90E0')
COL_FEED    = ('#281200', '#C87018')

OUTPUT_DIR = 'scenario_report_charts'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────────────────────────
#  MATEMATİKSEL YARDIMCILAR (Matplotlib kutu/ok çizim)
# ──────────────────────────────────────────────────────────────
def _box(ax, x, y, w, h, fc, ec, lw=1.8, r=0.3, zo=3):
    p = FancyBboxPatch((x - w/2, y - h/2), w, h,
                       boxstyle=f"round,pad=0,rounding_size={r}",
                       facecolor=fc, edgecolor=ec, linewidth=lw, zorder=zo)
    ax.add_patch(p)

def _tx(ax, x, y, s, sz=9.5, c=C_WHITE, bold=False, ha='center', va='center', zo=5):
    ax.text(x, y, s, fontsize=sz, color=c,
            fontweight='bold' if bold else 'normal',
            ha=ha, va=va, zorder=zo)

def _arr_v(ax, x, y1, y2, c='#4A9FD4', lw=2.2):
    ax.annotate('', xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle='->', color=c, lw=lw), zorder=6)

def _arr_h(ax, x1, y, x2, c='#4A9FD4', lw=2.2):
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle='->', color=c, lw=lw), zorder=6)

def _line_v(ax, x, y1, y2, c='#4A9FD4', lw=2.2):
    ax.plot([x, x], [y1, y2], color=c, lw=lw, zorder=5)

def _line_h(ax, x1, y, x2, c='#4A9FD4', lw=2.2):
    ax.plot([x1, x2], [y, y], color=c, lw=lw, zorder=5)

def _diamond(ax, x, y, w, h, fc, ec, lw=2.5):
    d = plt.Polygon([[x, y+h/2], [x+w/2, y], [x, y-h/2], [x-w/2, y]],
                     closed=True, facecolor=fc, edgecolor=ec, lw=lw, zorder=3)
    ax.add_patch(d)

def _setup_ax(fig, ax, xmax, ymax):
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.axis('off')
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_DARK)

def _save(fig, name):
    p = os.path.join(OUTPUT_DIR, name)
    fig.savefig(p, dpi=200, bbox_inches='tight', facecolor=BG_DARK, edgecolor='none')
    plt.close(fig)
    print(f'   ✅ {name}')
    return p

# ══════════════════════════════════════════════════════════════
#  DİYAGRAM 1: SABİT GİRİŞ — Paralel Güvenlik
# ══════════════════════════════════════════════════════════════
def fig_sabit_giris():
    fig = plt.figure(figsize=(22, 14))
    ax = fig.add_axes([0, 0, 1, 1])
    _setup_ax(fig, ax, 22, 14)

    # Başlık
    _box(ax, 11, 13.2, 21.5, 1.2, '#091628', C_ACCENT, lw=2.5, r=0.4)
    _tx(ax, 11, 13.5, 'SABİT BİLEŞEN — PARALEL GÜVENLİK & META VERİ (TRİYAJ)', sz=14, c=C_ACCENT, bold=True)
    _tx(ax, 11, 12.9, 'Tüm Senaryolarda Ortak | Adım 1', sz=10, c=C_DIM)

    # Belge Girişi
    _box(ax, 11, 11.3, 8, 1.2, COL_INPUT[0], COL_INPUT[1], lw=2.2, r=0.4)
    _tx(ax, 11, 11.6, 'BELGE GİRİŞİ', sz=13, c='#6EE7A0', bold=True)
    _tx(ax, 11, 11.0, 'API  /  E-Posta  /  Klasör İzleyici (watchdog)', sz=9.5, c='#A8E6C0')

    # Paralel çatal
    _arr_v(ax, 11, 10.7, 10.1, '#4A9FD4', 2.5)
    _box(ax, 11, 9.8, 4, 0.6, '#0f3460', '#4A9FD4', lw=1.5, r=0.25)
    _tx(ax, 11, 9.8, '⚡ PARALEL İŞLEM BAŞLAT', sz=10, c=C_WHITE, bold=True)

    # Fork 1A sol — QR
    _line_h(ax, 9, 9.5, 4.5, '#8840D8', 2)
    _arr_v(ax, 4.5, 9.5, 8.8, '#8840D8', 2)
    _box(ax, 4.5, 7.8, 6.5, 1.8, COL_SECURITY[0], COL_SECURITY[1], lw=2, r=0.35)
    _tx(ax, 4.5, 8.45, 'pyzbar — QR Kod Okuyucu', sz=11, c=C_WHITE, bold=True)
    _tx(ax, 4.5, 8.0, 'QR kod var mı? İçindeki tutar nedir?', sz=9, c=C_GRAY)
    _tx(ax, 4.5, 7.55, 'Çıktı: {qr_tutar: 15000, belge_uuid: "..."}', sz=8.5, c=C_ACCENT)
    _tx(ax, 4.5, 7.15, 'Araç: pyzbar (deterministik)', sz=8, c=C_DIM)

    # Fork 1A sağ — İmza
    _line_h(ax, 13, 9.5, 17.5, '#8840D8', 2)
    _arr_v(ax, 17.5, 9.5, 8.8, '#8840D8', 2)
    _box(ax, 17.5, 7.8, 6.5, 1.8, COL_SECURITY[0], COL_SECURITY[1], lw=2, r=0.35)
    _tx(ax, 17.5, 8.45, 'YOLO / OpenCV — İmza & Kaşe Tespiti', sz=11, c=C_WHITE, bold=True)
    _tx(ax, 17.5, 8.0, 'Islak imza veya kaşe var mı?', sz=9, c=C_GRAY)
    _tx(ax, 17.5, 7.55, 'Çıktı: {imza_var: true, kase_var: true}', sz=8.5, c=C_ACCENT)
    _tx(ax, 17.5, 7.15, 'Araç: YOLO v8 veya OpenCV contour', sz=8, c=C_DIM)

    # Fork 1B — Router
    _arr_v(ax, 11, 9.5, 5.7, '#2E85C8', 2.5)
    _box(ax, 11, 4.8, 8, 1.6, COL_ROUTER[0], COL_ROUTER[1], lw=2.2, r=0.35)
    _tx(ax, 11, 5.35, 'ROUTER (Yönlendirici)', sz=12, c=C_WHITE, bold=True)
    _tx(ax, 11, 4.9, 'python-magic ile dosya türü & karmaşıklık tespiti', sz=9.5, c=C_GRAY)
    _tx(ax, 11, 4.45, 'mime_type + uzantı + metin varlığı analizi', sz=9, c=C_ACCENT)
    _tx(ax, 11, 4.05, '→ Hangi dönüşüm yoluna gidecek?', sz=9, c='#6EE7A0')

    # Sonuç kutuları
    _arr_v(ax, 4.5, 6.9, 3.3, '#8840D8', 2)
    _box(ax, 4.5, 2.6, 6.5, 1.2, '#141C24', '#445566', lw=1.5, r=0.25)
    _tx(ax, 4.5, 2.9, 'META VERİ JSON', sz=10, c='#90C8F0', bold=True)
    _tx(ax, 4.5, 2.4, 'QR verisi → Hakem Ajanına gönderilir', sz=8.5, c=C_GRAY)

    _arr_v(ax, 17.5, 6.9, 3.3, '#8840D8', 2)
    _box(ax, 17.5, 2.6, 6.5, 1.2, '#141C24', '#445566', lw=1.5, r=0.25)
    _tx(ax, 17.5, 2.9, 'FİZİKSEL KONTROL JSON', sz=10, c='#90C8F0', bold=True)
    _tx(ax, 17.5, 2.4, 'İmza verisi → Hakem Ajanına gönderilir', sz=8.5, c=C_GRAY)

    _arr_v(ax, 11, 4.0, 3.3, '#2E85C8', 2.5)
    _box(ax, 11, 2.6, 6.5, 1.2, '#0C1E30', '#2E85C8', lw=1.5, r=0.25)
    _tx(ax, 11, 2.9, 'YÖNLENDİRME KARARI', sz=10, c='#4A9FD4', bold=True)
    _tx(ax, 11, 2.4, 'Dosya türüne göre → Adım 2\'ye geçiş', sz=8.5, c=C_GRAY)

    # Etiketler
    _tx(ax, 4.5, 9.3, 'Fork 1A — Güvenlik', sz=8.5, c='#8840D8', bold=True)
    _tx(ax, 17.5, 9.3, 'Fork 1A — Güvenlik', sz=8.5, c='#8840D8', bold=True)
    _tx(ax, 12.8, 7.0, 'Fork 1B — Router', sz=8.5, c='#2E85C8', bold=True)

    # Alt bilgi
    _box(ax, 11, 1.2, 21.5, 0.7, '#091628', '#2A3A4A', lw=1, r=0.25)
    _tx(ax, 11, 1.2, 'NOT: Bu 3 paralel işlem belge metne çevrilmeden ÖNCE başlar. Sonuçlar Adım 4\'te (Hakem Ajanı) kullanılır.', sz=9, c=C_DIM)

    return _save(fig, 'fig_sabit_giris.png')


# ══════════════════════════════════════════════════════════════
#  DİYAGRAM 2: SABİT ÇIKIŞ — Hakem Ajanı
# ══════════════════════════════════════════════════════════════
def fig_sabit_cikis():
    fig = plt.figure(figsize=(22, 16))
    ax = fig.add_axes([0, 0, 1, 1])
    _setup_ax(fig, ax, 22, 16)

    # Başlık
    _box(ax, 11, 15.2, 21.5, 1.2, '#091628', C_ACCENT, lw=2.5, r=0.4)
    _tx(ax, 11, 15.5, 'SABİT BİLEŞEN — HAKEM AJANI & OTONOM YÖNLENDİRME', sz=14, c=C_ACCENT, bold=True)
    _tx(ax, 11, 14.9, 'Tüm Senaryolarda Ortak | Adım 4 & 5', sz=10, c=C_DIM)

    # LLM JSON giriş
    _box(ax, 11, 13.7, 10, 1.0, COL_LLM[0], COL_LLM[1], lw=2, r=0.35)
    _tx(ax, 11, 13.95, 'LLM Çıktı JSON', sz=11, c=C_WHITE, bold=True)
    _tx(ax, 11, 13.5, '{müşteri_adı, vkn, tutar, tarih, ...}', sz=9.5, c=C_ACCENT)

    # Hakem Ajanı
    _arr_v(ax, 11, 13.2, 12.5, '#D04040', 2.5)
    _box(ax, 11, 11.5, 14, 1.8, COL_JUDGE[0], COL_JUDGE[1], lw=2.5, r=0.4)
    _tx(ax, 11, 12.15, 'HAKEM AJANI (Judge Agent)', sz=14, c='#E06060', bold=True)
    _tx(ax, 11, 11.65, 'LLM çıktısını fiziksel kontrollerle çapraz doğrulama', sz=10, c=C_WHITE)
    _tx(ax, 11, 11.15, 'Adım 1\'deki meta veriler + Adım 3\'teki JSON → karşılaştırma', sz=9, c=C_GRAY)
    _tx(ax, 11, 10.75, 'Araç: Özel Python Agent (Deterministik Kurallar + API Çağrıları)', sz=8.5, c=C_ACCENT)

    # 3 kontrol kutusu
    kontroller = [
        ('Anti-Fraud', 'LLM Tutar == QR Tutar?', 'Sahtecilik tespiti', 4),
        ('Geçerlilik', 'İmza/Kaşe Bulundu mu?', 'Fiziksel kontrol', 11),
        ('API Doğrulama', 'VKN ↔ Şirket Eşleşiyor?', 'GİB/Kurum API', 18),
    ]
    for label, q, desc, cx in kontroller:
        _arr_v(ax, cx, 10.6, 9.8, '#D04040', 2)
        _box(ax, cx, 9.0, 6, 1.5, '#200808', '#D04040', lw=1.8, r=0.3)
        _tx(ax, cx, 9.55, label, sz=11, c='#E06060', bold=True)
        _tx(ax, cx, 9.1, q, sz=9.5, c=C_WHITE)
        _tx(ax, cx, 8.65, desc, sz=8.5, c=C_GRAY)
        _tx(ax, cx, 8.3, '✅ Eşleşiyor → +1   |   ❌ Eşleşmiyor → FAIL', sz=8, c=C_ACCENT)

    # Karar noktası
    _arr_v(ax, 4, 8.25, 7.2, '#D04040', 2)
    _arr_v(ax, 11, 8.25, 7.2, '#D04040', 2)
    _arr_v(ax, 18, 8.25, 7.2, '#D04040', 2)

    _diamond(ax, 11, 6.5, 8, 1.4, '#200808', '#D04040', 2.5)
    _tx(ax, 11, 6.7, 'TÜM KONTROLLER', sz=10, c='#E06060', bold=True)
    _tx(ax, 11, 6.3, 'BAŞARILI MI?', sz=10, c=C_WHITE)

    # PASS → ERP
    _arr_v(ax, 8, 5.8, 4.9, '#28A850', 3)
    _tx(ax, 6.5, 5.35, 'PASS ✅', sz=11, c='#28A850', bold=True)
    _box(ax, 5.5, 4.0, 7, 1.5, COL_ERP[0], COL_ERP[1], lw=2.2, r=0.35)
    _tx(ax, 5.5, 4.55, 'ERP SİSTEMİ', sz=12, c='#6EE7A0', bold=True)
    _tx(ax, 5.5, 4.1, 'HTTP POST → SAP / Logo / Mikro', sz=9.5, c=C_WHITE)
    _tx(ax, 5.5, 3.65, 'İnsan eli değmeden otomatik kayıt oluşur', sz=8.5, c='#A8E6C0')
    _tx(ax, 5.5, 3.3, '→ Otomatik Kayıt Oluşturuldu ✅', sz=9, c=C_ACCENT, bold=True)

    # FAIL → UI
    _arr_v(ax, 14, 5.8, 4.9, '#C87018', 3)
    _tx(ax, 15.5, 5.35, 'FAIL ❌', sz=11, c='#D04040', bold=True)
    _box(ax, 16.5, 4.0, 7, 1.5, COL_UI[0], COL_UI[1], lw=2.2, r=0.35)
    _tx(ax, 16.5, 4.55, 'İNSAN İNCELEME (Human-in-the-Loop)', sz=11, c='#F0A040', bold=True)
    _tx(ax, 16.5, 4.1, 'Web UI → Operatör ekranına düşer', sz=9.5, c=C_WHITE)
    _tx(ax, 16.5, 3.65, 'Hata nedeni gösterilir: "QR Tutar Uyuşmazlığı"', sz=8.5, c=C_GRAY)
    _tx(ax, 16.5, 3.3, 'Operatör: Onayla → ERP  |  Reddet → Arşiv', sz=8.5, c=C_ACCENT)

    # Feedback (Senaryo 3 notu)
    _box(ax, 16.5, 1.8, 7, 1.0, COL_FEED[0], COL_FEED[1], lw=1.5, r=0.25)
    _tx(ax, 16.5, 2.1, 'SENARYO 3: Operatör düzeltmeleri →', sz=9, c='#F0A040', bold=True)
    _tx(ax, 16.5, 1.6, 'training_data.jsonl (Fine-Tuning için)', sz=8.5, c=C_GRAY)
    _arr_v(ax, 16.5, 3.25, 2.35, '#C87018', 1.8)

    # Alt bilgi
    _box(ax, 11, 0.7, 21.5, 0.7, '#091628', '#2A3A4A', lw=1, r=0.25)
    _tx(ax, 11, 0.7, 'NOT: Hakem Ajanı deterministik kurallara dayalıdır. LLM kullanmaz, her zaman aynı girdi → aynı çıktı üretir.', sz=9, c=C_DIM)

    return _save(fig, 'fig_sabit_cikis.png')


# ══════════════════════════════════════════════════════════════
#  DİYAGRAM 3: SENARYO 1 — MarkItDown + Zero-Shot
# ══════════════════════════════════════════════════════════════
def fig_senaryo1():
    fig = plt.figure(figsize=(24, 22))
    ax = fig.add_axes([0, 0, 1, 1])
    _setup_ax(fig, ax, 24, 22)

    # Başlık
    _box(ax, 12, 21.3, 23.5, 1.0, '#091628', '#28A850', lw=2.5, r=0.4)
    _tx(ax, 12, 21.55, 'SENARYO 1 — ZERO-SHOT + MarkItDown AĞIRLIKLI', sz=15, c='#28A850', bold=True)
    _tx(ax, 12, 21.05, 'En Hızlı ve Kaynak Tasarruflu Yaklaşım | Fine-Tuning Gerektirmez', sz=10, c=C_DIM)

    MX = 12

    # 1. Belge Girişi
    _box(ax, MX, 20.0, 8, 0.9, COL_INPUT[0], COL_INPUT[1], lw=2, r=0.35)
    _tx(ax, MX, 20.2, 'BELGE GİRİŞİ', sz=11, c='#6EE7A0', bold=True)
    _tx(ax, MX, 19.8, 'API / E-Posta / Klasör', sz=9, c='#A8E6C0')

    # 2. Paralel Güvenlik
    _arr_v(ax, MX, 19.55, 19.0, '#4A9FD4', 2)
    _box(ax, MX, 18.3, 18, 1.2, COL_SECURITY[0], COL_SECURITY[1], lw=2, r=0.35)
    _tx(ax, MX, 18.65, 'ADIM 1 — PARALEL GÜVENLİK (SABİT)', sz=12, c='#8840D8', bold=True)
    _tx(ax, MX, 18.2, 'pyzbar (QR Tutar)  +  YOLO (İmza Tespiti)  +  python-magic (Router)', sz=9.5, c=C_WHITE)
    _tx(ax, MX, 17.8, '→ Meta veriler saklanır, Hakem Ajanına gönderilecek', sz=9, c=C_GRAY)

    # 3. Router karar
    _arr_v(ax, MX, 17.7, 17.0, '#2E85C8', 2.5)
    _diamond(ax, MX, 16.5, 7, 1.0, '#0C1E30', '#2E85C8', 2)
    _tx(ax, MX, 16.6, 'DOSYA TÜRÜ?', sz=10, c=C_WHITE, bold=True)
    _tx(ax, MX, 16.3, 'Router Kararı', sz=8, c=C_DIM)

    # Hızlı Yol — MarkItDown (sol)
    _line_h(ax, MX - 3.5, 16.5, 5, '#28A850', 2.5)
    _arr_v(ax, 5, 16.5, 15.7, '#28A850', 2.5)
    _box(ax, 5, 14.8, 8, 1.6, COL_FAST[0], COL_FAST[1], lw=2.2, r=0.35)
    _tx(ax, 5, 15.4, '⚡ HIZLI YOL', sz=11, c='#28A850', bold=True)
    _tx(ax, 5, 15.0, 'MarkItDown', sz=13, c=C_WHITE, bold=True)
    _tx(ax, 5, 14.55, '.docx / .xlsx / .eml / .html / Dijital PDF', sz=8.5, c=C_GRAY)
    _tx(ax, 5, 14.2, '~0.1s | CPU Düşük | 15+ format desteği', sz=8, c=C_ACCENT)

    # Zor Yol — Docling (sağ)
    _line_h(ax, MX + 3.5, 16.5, 19, '#C88A18', 2.5)
    _arr_v(ax, 19, 16.5, 15.7, '#C88A18', 2.5)
    _box(ax, 19, 14.8, 8, 1.6, COL_HARD[0], COL_HARD[1], lw=2.2, r=0.35)
    _tx(ax, 19, 15.4, '🤖 ZOR YOL', sz=11, c='#C88A18', bold=True)
    _tx(ax, 19, 15.0, 'Docling', sz=13, c=C_WHITE, bold=True)
    _tx(ax, 19, 14.55, 'Taranmış PDF / Fotoğraf / Karmaşık Tablo', sz=8.5, c=C_GRAY)
    _tx(ax, 19, 14.2, '~2-5s | AI Layout + TableFormer', sz=8, c=C_ACCENT)

    # Birleşim → Markdown
    _arr_v(ax, 5, 14.0, 13.2, '#4A9FD4', 2)
    _arr_v(ax, 19, 14.0, 13.2, '#4A9FD4', 2)
    _line_h(ax, 5, 13.2, 19, '#4A9FD4', 2)
    _arr_v(ax, MX, 13.2, 12.7, '#4A9FD4', 2)
    _box(ax, MX, 12.2, 8, 0.8, '#141C24', '#4A9FD4', lw=1.5, r=0.25)
    _tx(ax, MX, 12.2, '📝 MARKDOWN METNİ', sz=11, c='#90C8F0', bold=True)

    # 4. LLM Çıkarım
    _arr_v(ax, MX, 11.8, 11.0, '#8840D8', 2.5)
    _box(ax, MX, 10.0, 18, 1.8, COL_LLM[0], COL_LLM[1], lw=2.2, r=0.35)
    _tx(ax, MX, 10.7, 'ADIM 3 — ZERO-SHOT VERİ ÇIKARIMI', sz=12, c='#8840D8', bold=True)
    _tx(ax, MX, 10.25, 'Qwen 3.5 (Ollama) + Pydantic Schema + Güçlü Prompt', sz=10, c=C_WHITE)
    _tx(ax, MX, 9.8, '"Sen bir finans asistanısın. Markdown belgesinden şu alanları çıkar..."', sz=9, c=C_GRAY)
    _tx(ax, MX, 9.35, 'Çıktı: {müşteri_adı, vkn, tutar, tarih} → Yapısal JSON', sz=9, c=C_ACCENT)

    # 5. Hakem
    _arr_v(ax, MX, 9.1, 8.3, '#D04040', 2.5)
    _box(ax, MX, 7.3, 18, 1.8, COL_JUDGE[0], COL_JUDGE[1], lw=2.2, r=0.4)
    _tx(ax, MX, 8.0, 'ADIM 4 — HAKEM AJANI (SABİT)', sz=12, c='#E06060', bold=True)
    _tx(ax, MX, 7.55, 'Anti-Fraud (Tutar Eşleşme) + Geçerlilik (İmza) + API (VKN Doğrulama)', sz=10, c=C_WHITE)
    _tx(ax, MX, 7.1, 'LLM JSON + Adım 1 Meta Verileri → Çapraz Doğrulama', sz=9, c=C_GRAY)
    _tx(ax, MX, 6.65, 'Deterministik kurallar — LLM kullanmaz', sz=8.5, c=C_ACCENT)

    # 6. Karar
    _arr_v(ax, MX, 6.4, 5.7, '#D04040', 2.5)
    _diamond(ax, MX, 5.2, 8, 1.0, '#200808', '#D04040', 2.5)
    _tx(ax, MX, 5.35, 'TÜM KONTROLLER', sz=10, c='#E06060', bold=True)
    _tx(ax, MX, 5.05, 'BAŞARILI MI?', sz=9, c=C_WHITE)

    # PASS → ERP
    _line_h(ax, MX - 4, 5.2, 4, '#28A850', 2.5)
    _arr_v(ax, 4, 5.2, 4.5, '#28A850', 2.5)
    _box(ax, 4, 3.7, 6, 1.3, COL_ERP[0], COL_ERP[1], lw=2.2, r=0.35)
    _tx(ax, 4, 4.15, '✅ ERP POST', sz=12, c='#6EE7A0', bold=True)
    _tx(ax, 4, 3.7, 'Otomatik Kayıt', sz=9, c='#A8E6C0')
    _tx(ax, 4, 3.3, 'SAP / Logo / Mikro', sz=8.5, c=C_GRAY)
    _tx(ax, 3, 5.5, 'PASS ✅', sz=10, c='#28A850', bold=True)

    # FAIL → UI
    _line_h(ax, MX + 4, 5.2, 20, '#D04040', 2.5)
    _arr_v(ax, 20, 5.2, 4.5, '#D04040', 2.5)
    _box(ax, 20, 3.7, 6, 1.3, COL_UI[0], COL_UI[1], lw=2.2, r=0.35)
    _tx(ax, 20, 4.15, '❌ İNSAN İNCELEME', sz=12, c='#F0A040', bold=True)
    _tx(ax, 20, 3.7, 'Human-in-the-Loop', sz=9, c=C_WHITE)
    _tx(ax, 20, 3.3, 'Hata detayı gösterilir', sz=8.5, c=C_GRAY)
    _tx(ax, 21, 5.5, 'FAIL ❌', sz=10, c='#D04040', bold=True)

    # Avantajlar kutusu
    _box(ax, MX, 1.8, 23.5, 2.2, '#091628', '#28A850', lw=1.5, r=0.35)
    _tx(ax, MX, 2.7, 'SENARYO 1 — AVANTAJLAR', sz=11, c='#28A850', bold=True)
    _tx(ax, 5, 2.2, '✓ En hızlı dönüşüm (<0.1s)', sz=9, c=C_GRAY)
    _tx(ax, 5, 1.7, '✓ Fine-tuning gerektirmez', sz=9, c=C_GRAY)
    _tx(ax, 12, 2.2, '✓ 15+ format desteği (MarkItDown)', sz=9, c=C_GRAY)
    _tx(ax, 12, 1.7, '✓ Düşük kurulum karmaşıklığı', sz=9, c=C_GRAY)
    _tx(ax, 19.5, 2.2, '⚠ Her çağrıda uzun prompt (token)', sz=9, c=C_ACCENT)
    _tx(ax, 19.5, 1.7, '⚠ Nadir formatlarda halüsinasyon', sz=9, c=C_ACCENT)

    return _save(fig, 'fig_senaryo1.png')


# ══════════════════════════════════════════════════════════════
#  DİYAGRAM 4: SENARYO 2 — PyMuPDF4LLM + Zero-Shot
# ══════════════════════════════════════════════════════════════
def fig_senaryo2():
    fig = plt.figure(figsize=(24, 22))
    ax = fig.add_axes([0, 0, 1, 1])
    _setup_ax(fig, ax, 24, 22)

    _box(ax, 12, 21.3, 23.5, 1.0, '#091628', '#2E85C8', lw=2.5, r=0.4)
    _tx(ax, 12, 21.55, 'SENARYO 2 — ZERO-SHOT + PyMuPDF4LLM AĞIRLIKLI', sz=15, c='#2E85C8', bold=True)
    _tx(ax, 12, 21.05, 'PDF-Native Performans | 3 Yollu Router', sz=10, c=C_DIM)

    MX = 12

    # 1. Belge Girişi
    _box(ax, MX, 20.0, 8, 0.9, COL_INPUT[0], COL_INPUT[1], lw=2, r=0.35)
    _tx(ax, MX, 20.2, 'BELGE GİRİŞİ', sz=11, c='#6EE7A0', bold=True)
    _tx(ax, MX, 19.8, 'API / E-Posta / Klasör', sz=9, c='#A8E6C0')

    # 2. Paralel Güvenlik
    _arr_v(ax, MX, 19.55, 19.0, '#4A9FD4', 2)
    _box(ax, MX, 18.3, 18, 1.2, COL_SECURITY[0], COL_SECURITY[1], lw=2, r=0.35)
    _tx(ax, MX, 18.65, 'ADIM 1 — PARALEL GÜVENLİK (SABİT)', sz=12, c='#8840D8', bold=True)
    _tx(ax, MX, 18.2, 'pyzbar (QR Tutar)  +  YOLO (İmza Tespiti)  +  python-magic (Router)', sz=9.5, c=C_WHITE)
    _tx(ax, MX, 17.8, '→ Meta veriler saklanır, Hakem Ajanına gönderilecek', sz=9, c=C_GRAY)

    # 3. Router karar — 3 yollu
    _arr_v(ax, MX, 17.7, 17.0, '#2E85C8', 2.5)
    _diamond(ax, MX, 16.5, 7, 1.0, '#0C1E30', '#2E85C8', 2)
    _tx(ax, MX, 16.6, 'DOSYA TÜRÜ?', sz=10, c=C_WHITE, bold=True)
    _tx(ax, MX, 16.3, '3 Yollu Router', sz=8, c=C_DIM)

    # Yol A — PyMuPDF4LLM (sol)
    _line_h(ax, MX - 3.5, 16.5, 3.5, '#2E85C8', 2.5)
    _arr_v(ax, 3.5, 16.5, 15.7, '#2E85C8', 2.5)
    _box(ax, 3.5, 14.7, 6, 1.8, '#0C1E30', '#2E85C8', lw=2.2, r=0.35)
    _tx(ax, 3.5, 15.4, '⚡ HIZLI YOL', sz=10, c='#2E85C8', bold=True)
    _tx(ax, 3.5, 15.0, 'PyMuPDF4LLM', sz=13, c=C_WHITE, bold=True)
    _tx(ax, 3.5, 14.55, 'Metni seçilebilen dijital PDF', sz=8.5, c=C_GRAY)
    _tx(ax, 3.5, 14.15, '~0.2s | PDF-native | Tablo algılama', sz=8, c=C_ACCENT)

    # Yol B — Docling (orta-sağ)
    _arr_v(ax, MX, 16.0, 15.7, '#C88A18', 2.5)
    _box(ax, MX, 14.7, 6, 1.8, COL_HARD[0], COL_HARD[1], lw=2.2, r=0.35)
    _tx(ax, MX, 15.4, '🤖 ZOR YOL', sz=10, c='#C88A18', bold=True)
    _tx(ax, MX, 15.0, 'Docling', sz=13, c=C_WHITE, bold=True)
    _tx(ax, MX, 14.55, 'Taranmış PDF / Fotoğraf / Karmaşık', sz=8.5, c=C_GRAY)
    _tx(ax, MX, 14.15, '~2-5s | AI Layout + TableFormer', sz=8, c=C_ACCENT)

    # Yol C — MarkItDown (sağ)
    _line_h(ax, MX + 3.5, 16.5, 20.5, '#28A850', 2.5)
    _arr_v(ax, 20.5, 16.5, 15.7, '#28A850', 2.5)
    _box(ax, 20.5, 14.7, 6, 1.8, COL_FAST[0], COL_FAST[1], lw=2.2, r=0.35)
    _tx(ax, 20.5, 15.4, '📋 OFIS YOLU', sz=10, c='#28A850', bold=True)
    _tx(ax, 20.5, 15.0, 'MarkItDown', sz=13, c=C_WHITE, bold=True)
    _tx(ax, 20.5, 14.55, '.docx / .xlsx / .eml / .html', sz=8.5, c=C_GRAY)
    _tx(ax, 20.5, 14.15, '~0.1s | Ofis formatları uzmanı', sz=8, c=C_ACCENT)

    # Birleşim → Markdown
    _arr_v(ax, 3.5, 13.8, 13.2, '#4A9FD4', 2)
    _arr_v(ax, MX, 13.8, 13.2, '#4A9FD4', 2)
    _arr_v(ax, 20.5, 13.8, 13.2, '#4A9FD4', 2)
    _line_h(ax, 3.5, 13.2, 20.5, '#4A9FD4', 2)
    _arr_v(ax, MX, 13.2, 12.7, '#4A9FD4', 2)
    _box(ax, MX, 12.2, 8, 0.8, '#141C24', '#4A9FD4', lw=1.5, r=0.25)
    _tx(ax, MX, 12.2, '📝 MARKDOWN METNİ', sz=11, c='#90C8F0', bold=True)

    # LLM
    _arr_v(ax, MX, 11.8, 11.0, '#8840D8', 2.5)
    _box(ax, MX, 10.0, 18, 1.8, COL_LLM[0], COL_LLM[1], lw=2.2, r=0.35)
    _tx(ax, MX, 10.7, 'ADIM 3 — ZERO-SHOT VERİ ÇIKARIMI', sz=12, c='#8840D8', bold=True)
    _tx(ax, MX, 10.25, 'Qwen 3.5 / Llama 3 (Ollama) + LangChain Structured Output', sz=10, c=C_WHITE)
    _tx(ax, MX, 9.8, 'Pydantic şeması ile kesin JSON formatı garanti altında', sz=9, c=C_GRAY)
    _tx(ax, MX, 9.35, 'Çıktı: Yapısal JSON → Hakem Ajanına', sz=9, c=C_ACCENT)

    # Hakem
    _arr_v(ax, MX, 9.1, 8.3, '#D04040', 2.5)
    _box(ax, MX, 7.3, 18, 1.8, COL_JUDGE[0], COL_JUDGE[1], lw=2.2, r=0.4)
    _tx(ax, MX, 8.0, 'ADIM 4 — HAKEM AJANI (SABİT)', sz=12, c='#E06060', bold=True)
    _tx(ax, MX, 7.55, 'Anti-Fraud + Geçerlilik + API Doğrulama', sz=10, c=C_WHITE)
    _tx(ax, MX, 7.1, 'LLM JSON ↔ Adım 1 Meta Verileri', sz=9, c=C_GRAY)

    # Karar
    _arr_v(ax, MX, 6.4, 5.7, '#D04040', 2.5)
    _diamond(ax, MX, 5.2, 8, 1.0, '#200808', '#D04040', 2.5)
    _tx(ax, MX, 5.35, 'TÜM KONTROLLER', sz=10, c='#E06060', bold=True)
    _tx(ax, MX, 5.05, 'BAŞARILI MI?', sz=9, c=C_WHITE)

    # ERP / UI
    _line_h(ax, MX - 4, 5.2, 4, '#28A850', 2.5)
    _arr_v(ax, 4, 5.2, 4.5, '#28A850', 2.5)
    _box(ax, 4, 3.7, 6, 1.3, COL_ERP[0], COL_ERP[1], lw=2.2, r=0.35)
    _tx(ax, 4, 4.15, '✅ ERP POST', sz=12, c='#6EE7A0', bold=True)
    _tx(ax, 4, 3.6, 'Otomatik Kayıt', sz=9, c='#A8E6C0')
    _tx(ax, 3, 5.5, 'PASS ✅', sz=10, c='#28A850', bold=True)

    _line_h(ax, MX + 4, 5.2, 20, '#D04040', 2.5)
    _arr_v(ax, 20, 5.2, 4.5, '#D04040', 2.5)
    _box(ax, 20, 3.7, 6, 1.3, COL_UI[0], COL_UI[1], lw=2.2, r=0.35)
    _tx(ax, 20, 4.15, '❌ İNSAN İNCELEME', sz=12, c='#F0A040', bold=True)
    _tx(ax, 20, 3.6, 'Human-in-the-Loop', sz=9, c=C_WHITE)
    _tx(ax, 21, 5.5, 'FAIL ❌', sz=10, c='#D04040', bold=True)

    # Avantajlar
    _box(ax, MX, 1.8, 23.5, 2.2, '#091628', '#2E85C8', lw=1.5, r=0.35)
    _tx(ax, MX, 2.7, 'SENARYO 2 — AVANTAJLAR', sz=11, c='#2E85C8', bold=True)
    _tx(ax, 5, 2.2, '✓ PDF-native tablo algılama', sz=9, c=C_GRAY)
    _tx(ax, 5, 1.7, '✓ 3 yollu akıllı router', sz=9, c=C_GRAY)
    _tx(ax, 12, 2.2, '✓ LangChain Structured Output', sz=9, c=C_GRAY)
    _tx(ax, 12, 1.7, '✓ Her format için uzman araç', sz=9, c=C_GRAY)
    _tx(ax, 19.5, 2.2, '⚠ Senaryo 1\'den biraz daha karmaşık', sz=9, c=C_ACCENT)
    _tx(ax, 19.5, 1.7, '⚠ PDF-dışı formatlar için ek bağımlılık', sz=9, c=C_ACCENT)

    return _save(fig, 'fig_senaryo2.png')


# ══════════════════════════════════════════════════════════════
#  DİYAGRAM 5: SENARYO 3 — Fine-Tuning + Feedback Loop
# ══════════════════════════════════════════════════════════════
def fig_senaryo3():
    fig = plt.figure(figsize=(26, 28))
    ax = fig.add_axes([0, 0, 1, 1])
    _setup_ax(fig, ax, 26, 28)

    _box(ax, 13, 27.3, 25.5, 1.0, '#091628', '#C88A18', lw=2.5, r=0.4)
    _tx(ax, 13, 27.55, 'SENARYO 3 — FINE-TUNING + FEEDBACK LOOP (KULLANDIKÇA ÖĞRENEN SİSTEM)', sz=14, c='#C88A18', bold=True)
    _tx(ax, 13, 27.05, 'En Gelişmiş ve Uzun Vadeli Yaklaşım | Zamanla Artan Doğruluk', sz=10, c=C_DIM)

    MX = 13

    # 1. Belge Girişi
    _box(ax, MX, 26.0, 8, 0.9, COL_INPUT[0], COL_INPUT[1], lw=2, r=0.35)
    _tx(ax, MX, 26.2, 'BELGE GİRİŞİ', sz=11, c='#6EE7A0', bold=True)
    _tx(ax, MX, 25.8, 'API / E-Posta / Klasör', sz=9, c='#A8E6C0')

    # 2. Paralel Güvenlik
    _arr_v(ax, MX, 25.55, 25.0, '#4A9FD4', 2)
    _box(ax, MX, 24.3, 18, 1.2, COL_SECURITY[0], COL_SECURITY[1], lw=2, r=0.35)
    _tx(ax, MX, 24.65, 'ADIM 1 — PARALEL GÜVENLİK (SABİT)', sz=12, c='#8840D8', bold=True)
    _tx(ax, MX, 24.2, 'pyzbar + YOLO + python-magic', sz=9.5, c=C_WHITE)
    _tx(ax, MX, 23.8, '+ Güven Skoru Hesaplama (Router\'a ek bilgi)', sz=9, c=C_GRAY)

    # Router 3 yollu
    _arr_v(ax, MX, 23.7, 23.0, '#2E85C8', 2.5)
    _diamond(ax, MX, 22.5, 7, 1.0, '#0C1E30', '#2E85C8', 2)
    _tx(ax, MX, 22.6, 'DOSYA TÜRÜ?', sz=10, c=C_WHITE, bold=True)

    # 3 yol
    _line_h(ax, MX - 3.5, 22.5, 4, '#2E85C8', 2)
    _arr_v(ax, 4, 22.5, 21.7, '#2E85C8', 2)
    _box(ax, 4, 21.0, 6, 1.2, '#0C1E30', '#2E85C8', lw=1.8, r=0.3)
    _tx(ax, 4, 21.35, 'PyMuPDF4LLM', sz=11, c=C_WHITE, bold=True)
    _tx(ax, 4, 20.85, 'Dijital PDF', sz=8.5, c=C_GRAY)

    _arr_v(ax, MX, 22.0, 21.7, '#C88A18', 2)
    _box(ax, MX, 21.0, 6, 1.2, COL_HARD[0], COL_HARD[1], lw=1.8, r=0.3)
    _tx(ax, MX, 21.35, 'Docling', sz=11, c=C_WHITE, bold=True)
    _tx(ax, MX, 20.85, 'Taranmış / Karmaşık', sz=8.5, c=C_GRAY)

    _line_h(ax, MX + 3.5, 22.5, 22, '#28A850', 2)
    _arr_v(ax, 22, 22.5, 21.7, '#28A850', 2)
    _box(ax, 22, 21.0, 6, 1.2, COL_FAST[0], COL_FAST[1], lw=1.8, r=0.3)
    _tx(ax, 22, 21.35, 'MarkItDown', sz=11, c=C_WHITE, bold=True)
    _tx(ax, 22, 20.85, 'Office / E-posta', sz=8.5, c=C_GRAY)

    # Birleşim
    _arr_v(ax, 4, 20.4, 19.8, '#4A9FD4', 2)
    _arr_v(ax, MX, 20.4, 19.8, '#4A9FD4', 2)
    _arr_v(ax, 22, 20.4, 19.8, '#4A9FD4', 2)
    _line_h(ax, 4, 19.8, 22, '#4A9FD4', 2)
    _arr_v(ax, MX, 19.8, 19.3, '#4A9FD4', 2)
    _box(ax, MX, 18.9, 8, 0.7, '#141C24', '#4A9FD4', lw=1.5, r=0.25)
    _tx(ax, MX, 18.9, '📝 MARKDOWN METNİ', sz=11, c='#90C8F0', bold=True)

    # ★ MODEL SEÇİM KARARI (Senaryo 3'e özgü)
    _arr_v(ax, MX, 18.55, 17.9, '#3A90E0', 2.5)
    _diamond(ax, MX, 17.4, 9, 1.0, '#0A2040', '#3A90E0', 2.5)
    _tx(ax, MX, 17.55, 'BU BELGE TÜRÜ İÇİN', sz=9, c='#3A90E0', bold=True)
    _tx(ax, MX, 17.25, 'FINE-TUNED MODEL VAR MI?', sz=9, c=C_WHITE, bold=True)

    # Fine-Tuned Model (sol)
    _line_h(ax, MX - 4.5, 17.4, 4, '#28A850', 2.5)
    _arr_v(ax, 4, 17.4, 16.6, '#28A850', 2.5)
    _box(ax, 4, 15.6, 7, 1.8, COL_FAST[0], COL_FAST[1], lw=2.2, r=0.35)
    _tx(ax, 4, 16.3, '✅ EVET — Fine-Tuned Model', sz=10, c='#28A850', bold=True)
    _tx(ax, 4, 15.85, 'Fine-Tuned Qwen (LoRA)', sz=11, c=C_WHITE, bold=True)
    _tx(ax, 4, 15.4, 'Kısa prompt, düşük token', sz=9, c=C_GRAY)
    _tx(ax, 4, 15.0, 'Uzman model — şirkete özel', sz=8.5, c=C_ACCENT)

    # Base Model (sağ)
    _line_h(ax, MX + 4.5, 17.4, 22, '#8840D8', 2.5)
    _arr_v(ax, 22, 17.4, 16.6, '#8840D8', 2.5)
    _box(ax, 22, 15.6, 7, 1.8, COL_LLM[0], COL_LLM[1], lw=2.2, r=0.35)
    _tx(ax, 22, 16.3, '❌ HAYIR — Zero-Shot', sz=10, c='#8840D8', bold=True)
    _tx(ax, 22, 15.85, 'Base Qwen 3.5 (Ollama)', sz=11, c=C_WHITE, bold=True)
    _tx(ax, 22, 15.4, 'Uzun prompt + Pydantic Schema', sz=9, c=C_GRAY)
    _tx(ax, 22, 15.0, 'İlk kez görülen belge türleri', sz=8.5, c=C_ACCENT)

    # Birleşim → JSON
    _arr_v(ax, 4, 14.7, 14.2, '#4A9FD4', 2)
    _arr_v(ax, 22, 14.7, 14.2, '#4A9FD4', 2)
    _line_h(ax, 4, 14.2, 22, '#4A9FD4', 2)
    _arr_v(ax, MX, 14.2, 13.7, '#4A9FD4', 2)
    _box(ax, MX, 13.3, 8, 0.7, '#141C24', '#4A9FD4', lw=1.5, r=0.25)
    _tx(ax, MX, 13.3, '📊 YAPISAL JSON', sz=11, c='#90C8F0', bold=True)

    # Hakem
    _arr_v(ax, MX, 12.95, 12.2, '#D04040', 2.5)
    _box(ax, MX, 11.2, 18, 1.8, COL_JUDGE[0], COL_JUDGE[1], lw=2.2, r=0.4)
    _tx(ax, MX, 11.9, 'ADIM 4 — HAKEM AJANI (SABİT)', sz=12, c='#E06060', bold=True)
    _tx(ax, MX, 11.45, 'Anti-Fraud + Geçerlilik + API Doğrulama', sz=10, c=C_WHITE)
    _tx(ax, MX, 11.0, 'LLM JSON ↔ Adım 1 Meta Verileri', sz=9, c=C_GRAY)
    _tx(ax, MX, 10.55, 'Deterministik kurallar', sz=8.5, c=C_ACCENT)

    # Karar
    _arr_v(ax, MX, 10.3, 9.6, '#D04040', 2.5)
    _diamond(ax, MX, 9.1, 8, 1.0, '#200808', '#D04040', 2.5)
    _tx(ax, MX, 9.25, 'TÜM KONTROLLER', sz=10, c='#E06060', bold=True)
    _tx(ax, MX, 8.95, 'BAŞARILI MI?', sz=9, c=C_WHITE)

    # PASS → ERP
    _line_h(ax, MX - 4, 9.1, 4, '#28A850', 2.5)
    _arr_v(ax, 4, 9.1, 8.4, '#28A850', 2.5)
    _box(ax, 4, 7.5, 6, 1.5, COL_ERP[0], COL_ERP[1], lw=2.2, r=0.35)
    _tx(ax, 4, 8.05, '✅ ERP POST', sz=12, c='#6EE7A0', bold=True)
    _tx(ax, 4, 7.55, 'Otomatik Kayıt', sz=9, c='#A8E6C0')
    _tx(ax, 4, 7.1, 'Başarılı kayıt log\'a yazılır', sz=8, c=C_GRAY)
    _tx(ax, 3, 9.4, 'PASS ✅', sz=10, c='#28A850', bold=True)

    # FAIL → UI
    _line_h(ax, MX + 4, 9.1, 22, '#D04040', 2.5)
    _arr_v(ax, 22, 9.1, 8.4, '#D04040', 2.5)
    _box(ax, 22, 7.5, 7, 1.5, COL_UI[0], COL_UI[1], lw=2.2, r=0.35)
    _tx(ax, 22, 8.05, '❌ İNSAN İNCELEME', sz=12, c='#F0A040', bold=True)
    _tx(ax, 22, 7.55, 'Human-in-the-Loop UI', sz=9, c=C_WHITE)
    _tx(ax, 22, 7.1, 'Operatör düzeltmesi yapılır', sz=8, c=C_GRAY)
    _tx(ax, 23, 9.4, 'FAIL ❌', sz=10, c='#D04040', bold=True)

    # ★ FEEDBACK LOOP (Senaryo 3'e özgü)
    _box(ax, MX, 5.5, 23.5, 3.6, '#0A2040', '#3A90E0', lw=2.5, r=0.5)
    _tx(ax, MX, 7.05, 'FEEDBACK LOOP — KULLANDIKÇA ÖĞRENEN SİSTEM (SENARYO 3\'E ÖZGÜ)', sz=12, c='#3A90E0', bold=True)

    # Sol: Veri toplama
    _box(ax, 4.5, 5.2, 7, 1.6, '#081020', '#445566', lw=1.5, r=0.3)
    _tx(ax, 4.5, 5.8, '💾 VERİ TOPLAMA', sz=10, c='#90C8F0', bold=True)
    _tx(ax, 4.5, 5.3, 'Operatör düzeltmeleri +', sz=8.5, c=C_GRAY)
    _tx(ax, 4.5, 4.85, 'Başarılı ERP kayıtları', sz=8.5, c=C_GRAY)
    _tx(ax, 4.5, 4.45, '→ training_data.jsonl', sz=8, c=C_ACCENT)

    # Orta: Karar
    _diamond(ax, MX, 5.2, 5, 0.8, '#0A2040', '#3A90E0', 2)
    _tx(ax, MX, 5.35, 'VERİ ≥ 100?', sz=9, c=C_WHITE, bold=True)
    _tx(ax, MX, 5.05, 'Yeterli veri birikti mi?', sz=7.5, c=C_DIM)
    _arr_h(ax, 8, 5.2, 10.5, '#3A90E0', 2)

    # Sağ: Fine-Tuning
    _box(ax, 21.5, 5.2, 7, 1.6, COL_FEED[0], COL_FEED[1], lw=2, r=0.3)
    _tx(ax, 21.5, 5.8, '🔄 PERİYODİK FINE-TUNING', sz=10, c='#F0A040', bold=True)
    _tx(ax, 21.5, 5.3, 'LoRA / QLoRA eğitimi', sz=8.5, c=C_GRAY)
    _tx(ax, 21.5, 4.85, 'Yeni model ≥ eski → Deploy', sz=8.5, c=C_ACCENT)
    _tx(ax, 21.5, 4.45, 'Eski daha iyi → Rollback', sz=8.5, c=C_GRAY)
    _arr_h(ax, 15.5, 5.2, 18, '#C87018', 2)

    # Oklar (kaynaklardan veri toplamaya)
    _arr_v(ax, 4, 6.75, 6.05, '#445566', 1.5)
    _arr_v(ax, 22, 6.75, 6.05, '#445566', 1.5)

    # Alt bilgi
    _box(ax, MX, 2.7, 25.5, 3.0, '#091628', '#C88A18', lw=1.5, r=0.35)
    _tx(ax, MX, 3.95, 'SENARYO 3 — AVANTAJLAR & DEZAVANTAJLAR', sz=11, c='#C88A18', bold=True)
    _tx(ax, 5, 3.4, '✓ Zamanla artan doğruluk', sz=9, c=C_GRAY)
    _tx(ax, 5, 2.9, '✓ Daha az token tüketimi', sz=9, c=C_GRAY)
    _tx(ax, 5, 2.4, '✓ Şirkete özel belge öğrenme', sz=9, c=C_GRAY)
    _tx(ax, 5, 1.9, '✓ Uzun vadede en düşük maliyet', sz=9, c=C_GRAY)
    _tx(ax, 14, 3.4, '⚠ İlk kurulum karmaşıklığı yüksek', sz=9, c=C_ACCENT)
    _tx(ax, 14, 2.9, '⚠ Fine-tuning için GPU gerekli', sz=9, c=C_ACCENT)
    _tx(ax, 14, 2.4, '⚠ Min. ~100 eğitim verisi gerekli', sz=9, c=C_ACCENT)
    _tx(ax, 14, 1.9, '⚠ Model versiyonlama yönetimi', sz=9, c=C_ACCENT)
    _tx(ax, 22, 3.4, '⚠ Data drift riski', sz=9, c=C_ACCENT)
    _tx(ax, 22, 2.9, '⚠ A/B test altyapısı gerekli', sz=9, c=C_ACCENT)

    return _save(fig, 'fig_senaryo3.png')


# ══════════════════════════════════════════════════════════════
#  DİYAGRAM 6: KARŞILAŞTIRMA MATRİSİ (Tablo Grafik)
# ══════════════════════════════════════════════════════════════
def fig_karsilastirma():
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor('white')
    ax.axis('off')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)

    headers = ['Kriter', 'Senaryo 1\n(MarkItDown)', 'Senaryo 2\n(PyMuPDF4LLM)', 'Senaryo 3\n(Fine-Tuning)']
    data = [
        ['Kurulum Süresi',      '⭐⭐⭐⭐⭐ En hızlı', '⭐⭐⭐⭐',       '⭐⭐ En yavaş'],
        ['Başlangıç Maliyeti',  '💰 Düşük',           '💰💰 Orta',     '💰💰💰 Yüksek'],
        ['Çalışma Maliyeti',    '💰💰 (uzun prompt)', '💰💰 (benzer)', '💰 (kısa prompt)'],
        ['Format Desteği',      '🌍 15+ format',      '📄 PDF odaklı', '🌍 Geniş + öğrenen'],
        ['PDF Tablo Kalitesi',  '⭐⭐⭐',              '⭐⭐⭐⭐',       '⭐⭐⭐⭐'],
        ['Doğruluk (Başlangıç)','⭐⭐⭐',              '⭐⭐⭐',         '⭐⭐⭐ (aynı)'],
        ['Doğruluk (6 Ay)',     '⭐⭐⭐ (sabit)',      '⭐⭐⭐ (sabit)', '⭐⭐⭐⭐⭐ (artar)'],
        ['GPU İhtiyacı',        '❌ Yok',              '❌ Yok',         '✅ Gerekli'],
        ['Ölçeklenebilirlik',   '⭐⭐⭐⭐',            '⭐⭐⭐⭐',       '⭐⭐⭐⭐⭐'],
        ['Sektör Bağımsızlığı', '⭐⭐⭐⭐⭐',          '⭐⭐⭐⭐',       '⭐⭐⭐ (sektöre özel)'],
    ]

    col_widths = [3.2, 4.0, 4.0, 4.0]
    x_starts = [0.4]
    for w in col_widths[:-1]:
        x_starts.append(x_starts[-1] + w)

    # Başlık satırı
    for i, (hdr, xs, cw) in enumerate(zip(headers, x_starts, col_widths)):
        rect = plt.Rectangle((xs, 9.0), cw, 0.8, facecolor='#1A3A6B', edgecolor='#D1D5DB', lw=0.5)
        ax.add_patch(rect)
        ax.text(xs + cw/2, 9.4, hdr, ha='center', va='center', fontsize=9,
                fontweight='bold', color='white')

    # Veri satırları
    for r, row in enumerate(data):
        bg = '#F3F4F6' if r % 2 == 0 else 'white'
        y = 9.0 - (r + 1) * 0.75
        for i, (cell, xs, cw) in enumerate(zip(row, x_starts, col_widths)):
            rect = plt.Rectangle((xs, y), cw, 0.75, facecolor=bg, edgecolor='#D1D5DB', lw=0.5)
            ax.add_patch(rect)
            fc = '#1A3A6B' if i == 0 else '#374151'
            fw = 'bold' if i == 0 else 'normal'
            ax.text(xs + cw/2, y + 0.375, cell, ha='center', va='center',
                    fontsize=8.5, fontweight=fw, color=fc)

    # Başlık
    ax.text(8, 10.1, 'Üç Senaryo Karşılaştırma Matrisi', ha='center', va='center',
            fontsize=14, fontweight='bold', color='#1A3A6B')

    fig.tight_layout(pad=0.5)
    p = os.path.join(OUTPUT_DIR, 'fig_karsilastirma.png')
    fig.savefig(p, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'   ✅ fig_karsilastirma.png')
    return p


# ══════════════════════════════════════════════════════════════
#  PDF OLUŞTURMA (ReportLab)
# ══════════════════════════════════════════════════════════════
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, white, black

pdfmetrics.registerFont(TTFont('DV',     FONT_REG))
pdfmetrics.registerFont(TTFont('DV-B',   FONT_BOLD))
pdfmetrics.registerFont(TTFont('DV-I',   FONT_ITALIC))
pdfmetrics.registerFontFamily('DV', normal='DV', bold='DV-B', italic='DV-I')

W, H = A4
ML = 2.2*cm; MR = 2.2*cm; MT = 2.0*cm; MB = 2.5*cm
CW = W - ML - MR

C_NAVY   = HexColor('#1A3A6B')
C_BLUE   = HexColor('#2563EB')
C_LBLUE  = HexColor('#DBEAFE')
C_PGRAY  = HexColor('#374151')
C_LGRAY  = HexColor('#F3F4F6')
C_MGRAY  = HexColor('#9CA3AF')
C_GREEN  = HexColor('#059669')
C_PORANGE = HexColor('#D97706')
C_RED    = HexColor('#B91C1C')
C_PWHITE = white

def S(name, **kw):
    defaults = dict(fontName='DV', fontSize=10, leading=15,
                    textColor=C_PGRAY, spaceAfter=4)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

ST = {
    'sec_num':   S('sn', fontName='DV-B', fontSize=16, leading=22,
                   textColor=C_NAVY, spaceBefore=24, spaceAfter=4),
    'sec_sub':   S('ss', fontName='DV-B', fontSize=12, leading=16,
                   textColor=C_BLUE, spaceBefore=14, spaceAfter=6),
    'body':      S('b',  fontName='DV', fontSize=10, leading=16,
                   textColor=C_PGRAY, alignment=TA_JUSTIFY, spaceAfter=6),
    'body_bold': S('bb', fontName='DV-B', fontSize=10, leading=16,
                   textColor=C_PGRAY, alignment=TA_JUSTIFY, spaceAfter=6),
    'bullet':    S('bu', fontName='DV', fontSize=10, leading=15,
                   textColor=C_PGRAY, leftIndent=14, spaceAfter=3),
    'caption':   S('cap', fontName='DV-I', fontSize=8.5, leading=12,
                   textColor=C_MGRAY, alignment=TA_CENTER, spaceAfter=10),
    'th':        S('th',  fontName='DV-B', fontSize=9, textColor=white,
                   alignment=TA_CENTER),
    'td':        S('td',  fontName='DV', fontSize=9, textColor=C_PGRAY,
                   alignment=TA_CENTER),
    'td_left':   S('tdl', fontName='DV', fontSize=9, textColor=C_PGRAY,
                   alignment=TA_LEFT),
    'td_bold':   S('tdb', fontName='DV-B', fontSize=9, textColor=C_NAVY,
                   alignment=TA_CENTER),
    'note':      S('nt',  fontName='DV-I', fontSize=9, leading=13,
                   textColor=C_MGRAY, alignment=TA_JUSTIFY, spaceAfter=6),
    'highlight': S('hl',  fontName='DV-B', fontSize=11, leading=17,
                   textColor=C_NAVY, alignment=TA_JUSTIFY, spaceAfter=8),
}

def P(text, style='body'): return Paragraph(text, ST[style])
def Sp(h=0.3): return Spacer(1, h*cm)
def HR(): return HRFlowable(width='100%', thickness=0.8, color=HexColor('#E5E7EB'),
                              spaceBefore=8, spaceAfter=8)

def section_title(num, title):
    return [
        HRFlowable(width='100%', thickness=2.5, color=C_BLUE, spaceBefore=16, spaceAfter=0),
        Sp(0.15),
        P(f'{num}. {title}', 'sec_num'),
        Sp(0.1),
    ]

def make_table(header_row, data_rows, col_widths, col_aligns=None):
    h = [P(c, 'th') for c in header_row]
    rows = [h]
    for row in data_rows:
        if col_aligns:
            cells = [P(str(row[j]), col_aligns[j] if j < len(col_aligns) else 'td')
                     for j in range(len(row))]
        else:
            cells = [P(str(c), 'td') for c in row]
        rows.append(cells)

    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),  (-1,0),  C_NAVY),
        ('TEXTCOLOR',     (0,0),  (-1,0),  white),
        ('FONTNAME',      (0,0),  (-1,0),  'DV-B'),
        ('ROWBACKGROUNDS',(0,1),  (-1,-1), [C_LGRAY, white]),
        ('ALIGN',         (0,0),  (-1,-1), 'CENTER'),
        ('VALIGN',        (0,0),  (-1,-1), 'MIDDLE'),
        ('FONTSIZE',      (0,0),  (-1,-1), 9),
        ('TOPPADDING',    (0,0),  (-1,-1), 5),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 5),
        ('LEFTPADDING',   (0,0),  (-1,-1), 7),
        ('RIGHTPADDING',  (0,0),  (-1,-1), 7),
        ('GRID',          (0,0),  (-1,-1), 0.5, HexColor('#D1D5DB')),
    ]))
    return t

def img(path, w_ratio=1.0, caption=None):
    from PIL import Image as PILImage
    elems = []
    w = CW * w_ratio
    im = PILImage.open(path)
    aspect = im.height / im.width
    elems.append(RLImage(path, width=w, height=w * aspect))
    if caption:
        elems.append(P(caption, 'caption'))
    return elems

# ──────────────────────────────────────────────────────────────
class NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        rl_canvas.Canvas.__init__(self, *args, **kwargs)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            self._draw_footer(total)
            rl_canvas.Canvas.showPage(self)
        rl_canvas.Canvas.save(self)

    def _draw_footer(self, total):
        pg = self._pageNumber
        if pg == 1: return
        self.saveState()
        self.setFont('DV', 8)
        self.setFillColor(C_MGRAY)
        self.drawString(ML, 1.4*cm,
                        'Akıllı Belge İşleme Sistemi — Senaryo Analiz Raporu')
        self.drawRightString(W - MR, 1.4*cm, f'Sayfa {pg} / {total}')
        self.setStrokeColor(HexColor('#E5E7EB'))
        self.setLineWidth(0.5)
        self.line(ML, 1.7*cm, W-MR, 1.7*cm)
        self.restoreState()


# ══════════════════════════════════════════════════════════════
#  PDF İÇERİĞİ OLUŞTURMA
# ══════════════════════════════════════════════════════════════
def build_pdf(figs):
    out = '/Users/tuba/Desktop/belge_isleme_senaryo_raporu.pdf'
    doc = SimpleDocTemplate(
        out, pagesize=A4,
        leftMargin=ML, rightMargin=MR, topMargin=MT, bottomMargin=MB,
        title='Akıllı Belge İşleme Sistemi — Senaryo Analiz Raporu',
        author='Belge İşleme Projesi',
    )
    story = []

    # ═══════════════════════════════════════════════════════
    #  KAPAK SAYFASI
    # ═══════════════════════════════════════════════════════
    def _cp(txt, **kw):
        defaults = dict(fontName='DV', fontSize=11, leading=16,
                        textColor=C_PGRAY, alignment=TA_CENTER, spaceAfter=0)
        defaults.update(kw)
        return Paragraph(txt, ParagraphStyle('_cp_' + txt[:8].replace(' ','_'), **defaults))

    story += [
        Sp(5.0),
        _cp('Akıllı Belge İşleme Sistemi', fontSize=12, textColor=C_MGRAY),
        Sp(0.15),
        _cp('Otonom Denetim Asistanı Projesi', fontSize=11, textColor=C_MGRAY),
        Sp(1.8),
        HRFlowable(width='80%', thickness=1, color=HexColor('#D1D5DB'),
                   spaceBefore=0, spaceAfter=20),
        _cp('Senaryo, Karar Mekanizması ve', fontSize=22, fontName='DV-B',
            textColor=C_NAVY, leading=28),
        Sp(0.2),
        _cp('Mimari Analiz Raporu', fontSize=22, fontName='DV-B',
            textColor=C_NAVY, leading=28),
        Sp(0.4),
        _cp('3 Senaryo × 7 Karar Noktası × Akış Şemaları', fontSize=14,
            textColor=C_BLUE, fontName='DV-B'),
        Sp(0.3),
        _cp('Zero-Shot · PyMuPDF4LLM · Fine-Tuning · Feedback Loop', fontSize=12, textColor=C_PGRAY),
        HRFlowable(width='80%', thickness=1, color=HexColor('#D1D5DB'),
                   spaceBefore=20, spaceAfter=0),
        Sp(2.5),
        _cp(f'Rapor Tarihi: {datetime.now().strftime("%d.%m.%Y")}',
            fontSize=10, textColor=C_MGRAY),
        Sp(0.2),
        _cp('Dahili Kullanım İçin', fontSize=10, textColor=C_MGRAY),
        PageBreak(),
    ]

    # ═══════════════════════════════════════════════════════
    #  İÇİNDEKİLER
    # ═══════════════════════════════════════════════════════
    story += section_title('0', 'İçindekiler')
    toc_items = [
        ('1', 'Kapsam ve Genel Bakış'),
        ('2', 'Sabit Bileşenler (Tüm Senaryolarda Ortak)'),
        ('3', 'Senaryo 1 — Zero-Shot + MarkItDown Ağırlıklı'),
        ('4', 'Senaryo 2 — Zero-Shot + PyMuPDF4LLM Ağırlıklı'),
        ('5', 'Senaryo 3 — Fine-Tuning + Feedback Loop'),
        ('6', 'Üç Senaryo Karşılaştırma Matrisi'),
        ('7', 'Karar Mekanizmaları Özet Tablosu'),
        ('8', 'Teknoloji Yığını'),
        ('9', 'Önerilen Uygulama Yol Haritası'),
        ('10', 'Açık Sorular'),
    ]
    for num, title in toc_items:
        story.append(P(f'<b>{num}.</b>  {title}', 'bullet'))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  1. KAPSAM
    # ═══════════════════════════════════════════════════════
    story += section_title('1', 'Kapsam ve Genel Bakış')
    story.append(P(
        'Bu rapor, kurulmak istenen <b>Otonom Belge İşleme ve ERP Entegrasyon Sistemi</b>\'nin '
        'üç farklı senaryosunu analiz etmektedir. Sistem, fatura, irsaliye, sipariş formu gibi '
        'belgeleri otomatik olarak okuyup yapısal veriye dönüştürerek ERP sistemlerine '
        'kaydedecek bir <b>otonom denetim asistanı</b> olarak tasarlanmıştır.'
    ))
    story.append(P(
        'Sistemin vizyonu sadece bir "yazıyı metne çevirme" aracı değil; görerek, okuyarak, '
        'doğrulayarak ve çapraz kontroller yaparak şirketlerin finans/İK departmanlarındaki '
        'operasyonel yükü devralan <b>akıllı bir otomasyon platformu</b>dur.'
    ))
    story.append(Sp(0.2))
    story.append(P(
        '<b>Önemli:</b> Tüm senaryolarda <b>Adım 1 (Paralel Güvenlik Kontrolü)</b> ve '
        '<b>Adım 4-5 (Hakem Ajanı + Otonom Yönlendirme)</b> sabittir. '
        'Değişen kısım <b>Adım 2 (Dönüşüm Yolu)</b> ve <b>Adım 3 (Veri Çıkarım Stratejisi)</b>\'dir.',
        'highlight'
    ))

    # Senaryo özet tablosu
    story.append(Sp(0.2))
    story.append(make_table(
        ['Senaryo', 'Dönüşüm Aracı', 'LLM Stratejisi', 'Öğrenme'],
        [
            ['Senaryo 1', 'MarkItDown + Docling', 'Zero-Shot (Pydantic)', 'Yok'],
            ['Senaryo 2', 'PyMuPDF4LLM + Docling + MarkItDown', 'Zero-Shot (LangChain)', 'Yok'],
            ['Senaryo 3', 'PyMuPDF4LLM + Docling + MarkItDown', 'Zero-Shot → Fine-Tuned', 'Feedback Loop'],
        ],
        col_widths=[3*cm, 5*cm, 4.5*cm, 4*cm],
        col_aligns=['td_bold', 'td', 'td', 'td']
    ))
    story.append(P('<i>Tablo 1. Üç senaryonun temel farkları</i>', 'caption'))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  2. SABİT BİLEŞENLER
    # ═══════════════════════════════════════════════════════
    story += section_title('2', 'Sabit Bileşenler (Tüm Senaryolarda Ortak)')

    story.append(P('2.1. Paralel Güvenlik ve Meta Veri Çıkarımı (Triyaj)', 'sec_sub'))
    story.append(P(
        'Belge sisteme düştüğü anda, metne çevrilmeden önce iki deterministik Python betiği '
        '<b>paralel</b> olarak çalışır. Bu sayede güvenlik verileri, dönüşüm işlemiyle '
        'eş zamanlı toplanır ve zaman kaybı yaşanmaz.'
    ))

    giris_kontroller = [
        ['pyzbar', 'QR Kod Okuyucu', 'Belgedeki QR kodu tarar, tutar ve UUID çıkarır', '{qr_tutar: 15000}'],
        ['YOLO / OpenCV', 'İmza & Kaşe Tespiti', 'Islak imza veya kaşe varlığını tespit eder', '{imza_var: true}'],
        ['python-magic', 'Router (Yönlendirici)', 'Dosya türü ve karmaşıklığını analiz eder', 'mime_type → yol seçimi'],
    ]
    story.append(make_table(
        ['Araç', 'Görev', 'Açıklama', 'Çıktı Örneği'],
        giris_kontroller,
        col_widths=[3*cm, 3.5*cm, 5.5*cm, 4.5*cm],
        col_aligns=['td_bold', 'td_left', 'td_left', 'td']
    ))
    story.append(P('<i>Tablo 2. Paralel güvenlik kontrol araçları</i>', 'caption'))

    story.append(Sp(0.2))
    story += img(figs['giris'], 1.0,
                 'Şekil 1. Sabit Giriş — Paralel Güvenlik ve Meta Veri Çıkarımı akış şeması')
    story.append(PageBreak())

    story.append(P('2.2. Hakem Ajanı ve Otonom Yönlendirme', 'sec_sub'))
    story.append(P(
        'LLM\'in ürettiği JSON verisi doğrudan ERP\'ye yazılmaz. Adım 1\'de elde edilen '
        'fiziksel kontrollerle <b>çapraz doğrulama</b> yapılır. Bu katman tamamen '
        '<b>deterministik kurallarla</b> çalışır (LLM kullanmaz).'
    ))

    hakem_kontroller = [
        ['Anti-Fraud', 'LLM Tutar == QR Tutar?', 'Sahtecilik tespiti — belge üzerindeki tutar değiştirilmiş mi?'],
        ['Geçerlilik', 'İmza/Kaşe Bulundu mu?', 'Fiziksel belge otantikliği — ıslak imza zorunluluğu'],
        ['API Doğrulama', 'VKN ↔ Şirket Eşleşiyor?', 'GİB veya kurum API\'sine sorgu — gerçek veri kontrolü'],
    ]
    story.append(make_table(
        ['Kontrol', 'Soru', 'Amaç'],
        hakem_kontroller,
        col_widths=[3.5*cm, 5*cm, 8*cm],
        col_aligns=['td_bold', 'td', 'td_left']
    ))
    story.append(P('<i>Tablo 3. Hakem Ajanı kontrol noktaları</i>', 'caption'))

    story.append(Sp(0.1))
    story.append(P(
        '<b>Karar Mantığı:</b> Tüm kontroller başarılı → <b>ERP POST</b> (otomatik kayıt). '
        'En az biri başarısız → <b>İnsan İnceleme UI</b> (Human-in-the-Loop). '
        'Operatör onaylarsa ERP\'ye yazılır, reddederse arşive alınır.'
    ))
    story.append(Sp(0.2))
    story += img(figs['cikis'], 1.0,
                 'Şekil 2. Sabit Çıkış — Hakem Ajanı ve Otonom Yönlendirme akış şeması')
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  3. SENARYO 1
    # ═══════════════════════════════════════════════════════
    story += section_title('3', 'Senaryo 1 — Zero-Shot + MarkItDown Ağırlıklı')
    story.append(P(
        'En <b>hızlı ve kaynak-tasarruflu</b> yaklaşım. Fine-tuning gerekmez, '
        'dijital belgelerde milisaniye seviyesinde dönüşüm sağlar. '
        'PyMuPDF yerine <b>MarkItDown</b> tercih edilir.'
    ))

    story.append(P('3.1. Dönüşüm Katmanı', 'sec_sub'))
    story.append(P(
        '• <b>Hızlı Yol (MarkItDown):</b> Word (.docx), Excel (.xlsx), E-posta (.eml), '
        'HTML veya metni seçilebilen temiz dijital PDF → Saniyenin onda biri sürede Markdown. '
        '15+ format desteği.'
    ))
    story.append(P(
        '• <b>Zor Yol (Docling):</b> Taranmış PDF, fotoğraf (JPG/PNG) veya karmaşık tablolar '
        '(fatura çizgileri) → Docling\'in AI modelleri ile Markdown dönüşümü (2-5 saniye).'
    ))

    story.append(P('3.2. LLM Çıkarım Stratejisi', 'sec_sub'))
    story.append(P(
        'Markdown metni, Ollama üzerindeki <b>Qwen 3.5</b> modele gönderilir. '
        'Pydantic ile kesin bir şema ve güçlü bir prompt verilir. '
        'Model, Markdown\'daki tabloları ve metinleri okuyarak istenen veriyi '
        '<b>temiz JSON paketi</b> haline getirir.'
    ))
    story.append(P(
        '<i>Prompt Örneği: "Sen bir finans asistanısın. Aşağıdaki Markdown belgesinden '
        'şu alanları çıkar ve DİREKT olarak JSON formatında dön: Müşteri Adı, VKN, '
        'Fatura Tutarı, Fatura Tarihi. Yorum yapma."</i>', 'note'
    ))

    story.append(P('3.3. Karar Mekanizmaları', 'sec_sub'))
    s1_karar = [
        ['Router', 'mime_type + uzantı', 'MarkItDown (dijital)', 'Docling (taranmış)'],
        ['LLM Çıkarım', 'Pydantic Schema', 'JSON üret (alan varsa)', 'null dön (alan yoksa)'],
        ['Anti-Fraud', 'llm_tutar == qr_tutar', 'Devam ✓', 'Manuel İnceleme ✗'],
        ['Geçerlilik', 'imza_var == True', 'Devam ✓', 'Manuel İnceleme ✗'],
        ['VKN Doğrulama', 'API yanıtı eşleşiyor', 'Devam ✓', 'Manuel İnceleme ✗'],
        ['Hakem Kararı', 'Tüm kontroller PASS', '→ ERP POST', '→ Human-in-the-Loop'],
    ]
    story.append(make_table(
        ['Karar Noktası', 'Koşul', 'Yol A', 'Yol B'],
        s1_karar,
        col_widths=[3.5*cm, 4*cm, 4.5*cm, 4.5*cm],
        col_aligns=['td_bold', 'td', 'td', 'td']
    ))
    story.append(P('<i>Tablo 4. Senaryo 1 — Karar mekanizmaları</i>', 'caption'))

    story.append(P('3.4. Tam Akış Şeması', 'sec_sub'))
    story += img(figs['s1'], 1.0,
                 'Şekil 3. Senaryo 1 — MarkItDown + Zero-Shot tam akış şeması')

    story.append(P('3.5. Avantaj ve Dezavantajlar', 'sec_sub'))
    s1_ad = [
        ['✓ En hızlı dönüşüm (<0.1s)', '⚠ Her çağrıda uzun prompt (token tüketimi)'],
        ['✓ Fine-tuning gerektirmez', '⚠ Nadir belge formatlarında halüsinasyon riski'],
        ['✓ 15+ format desteği', '⚠ Docling yolu GPU gerektirebilir'],
        ['✓ Düşük kurulum karmaşıklığı', '⚠ Model güncellemelerinde prompt kalibrasyonu'],
    ]
    story.append(make_table(
        ['Avantajlar', 'Dezavantajlar'],
        s1_ad,
        col_widths=[8.5*cm, 8*cm],
        col_aligns=['td_left', 'td_left']
    ))
    story.append(P('<i>Tablo 5. Senaryo 1 — Avantaj/dezavantaj analizi</i>', 'caption'))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  4. SENARYO 2
    # ═══════════════════════════════════════════════════════
    story += section_title('4', 'Senaryo 2 — Zero-Shot + PyMuPDF4LLM Ağırlıklı')
    story.append(P(
        'Senaryo 1\'e benzer ancak dijital PDF\'ler için <b>PyMuPDF4LLM</b> tercih edilir. '
        'PDF-native performans sağlar. Office ve e-posta formatları için MarkItDown '
        'yardımcı araç olarak korunur. <b>3 yollu router</b> kullanılır.'
    ))

    story.append(P('4.1. 3 Yollu Router Mimarisi', 'sec_sub'))
    s2_router = [
        ['Dijital PDF (metin seçilebilen)', 'PyMuPDF4LLM', '~0.2s, CPU düşük, PDF-native tablo algılama'],
        ['Taranmış PDF / Fotoğraf / Karmaşık tablo', 'Docling', '~2-5s, AI Layout + TableFormer'],
        ['.docx / .xlsx / .eml / .html / Diğer', 'MarkItDown', '~0.1s, 15+ format desteği'],
    ]
    story.append(make_table(
        ['Dosya Türü', 'Yönlendirilen Araç', 'Performans'],
        s2_router,
        col_widths=[6*cm, 3.5*cm, 7*cm],
        col_aligns=['td_left', 'td_bold', 'td_left']
    ))
    story.append(P('<i>Tablo 6. Senaryo 2 — 3 yollu router yönlendirme tablosu</i>', 'caption'))

    story.append(P('4.2. LLM Çıkarım Stratejisi', 'sec_sub'))
    story.append(P(
        'Bu senaryoda <b>LangChain Structured Output</b> özelliği aktif olarak kullanılır. '
        'Modelin sadece ve sadece istenen JSON formatında yanıt vermesi garanti altına alınır. '
        'Model seçenekleri: Qwen 3.5 veya Llama 3 (Ollama).'
    ))

    story.append(P('4.3. Karar Mekanizmaları', 'sec_sub'))
    s2_karar = [
        ['Router', 'mime + metin testi', 'PyMuPDF4LLM', 'Docling', 'MarkItDown'],
        ['PDF Dijitallik', 'page.get_text() boş?', 'Metin var → PyMuPDF', 'Metin yok → Docling', '—'],
        ['Tablo Karmaşıklığı', 'Çizgi sayısı > eşik', 'Basit → PyMuPDF', 'Karmaşık → Docling', '—'],
        ['LLM Çıkarım', 'Structured Output', 'JSON üret', 'null dön', '—'],
        ['Hakem Kararı', '3 kontrol AND', '→ ERP', '→ Human-in-Loop', '—'],
    ]
    story.append(make_table(
        ['Karar Noktası', 'Koşul', 'Yol A', 'Yol B', 'Yol C'],
        s2_karar,
        col_widths=[3*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3*cm],
        col_aligns=['td_bold', 'td', 'td', 'td', 'td']
    ))
    story.append(P('<i>Tablo 7. Senaryo 2 — Karar mekanizmaları (3 yollu)</i>', 'caption'))

    story.append(P('4.4. Senaryo 1 vs 2 Karşılaştırması', 'sec_sub'))
    s12_kars = [
        ['PDF Dönüşüm Hızı', 'MarkItDown (genel amaçlı)', 'PyMuPDF4LLM (PDF-optimize)'],
        ['Format Desteği', 'Çok geniş (15+ format)', 'PDF odaklı, diğerleri ek araç'],
        ['PDF Tablo Koruması', 'Orta', 'İyi (native tablo algılama)'],
        ['Office Dosyaları', 'MarkItDown native', 'Ek kütüphane gerekli'],
        ['E-posta (.eml)', 'MarkItDown native', 'Ek parser gerekli'],
        ['Karmaşıklık', 'Düşük (tek araç)', 'Orta (3 yollu router)'],
        ['En İyi Kullanım', 'Çok çeşitli belge türleri', 'PDF-ağırlıklı iş akışları'],
    ]
    story.append(make_table(
        ['Özellik', 'Senaryo 1 (MarkItDown)', 'Senaryo 2 (PyMuPDF4LLM)'],
        s12_kars,
        col_widths=[4*cm, 6.2*cm, 6.2*cm],
        col_aligns=['td_bold', 'td_left', 'td_left']
    ))
    story.append(P('<i>Tablo 8. Senaryo 1 vs 2 detaylı karşılaştırma</i>', 'caption'))

    story.append(P('4.5. Tam Akış Şeması', 'sec_sub'))
    story += img(figs['s2'], 1.0,
                 'Şekil 4. Senaryo 2 — PyMuPDF4LLM + Zero-Shot tam akış şeması')
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  5. SENARYO 3
    # ═══════════════════════════════════════════════════════
    story += section_title('5', 'Senaryo 3 — Fine-Tuning + Feedback Loop')
    story.append(P(
        'En <b>gelişmiş ve uzun vadeli</b> yaklaşım. Sistem başlangıçta Zero-Shot çalışır, '
        'zamanla operatör düzeltmeleriyle kendi kendini eğitir. Fine-tuning ile her çağrıda '
        'daha az token tüketir ve daha yüksek doğruluk sağlar.'
    ))

    story.append(P('5.1. Model Seçim Mekanizması', 'sec_sub'))
    story.append(P(
        'Bu senaryoda Adım 3\'te bir <b>ek karar noktası</b> eklenir: '
        '"Bu belge türü için fine-tuned model var mı?" Eğer varsa, kısa prompt ile '
        'uzman model kullanılır. Yoksa, zero-shot olarak base model çalışır.'
    ))

    s3_model = [
        ['Fine-Tuned Model VAR', 'Kısa prompt, düşük token', 'Şirkete özel, yüksek doğruluk'],
        ['Fine-Tuned Model YOK', 'Uzun prompt + Pydantic Schema', 'İlk kez görülen belge türleri'],
    ]
    story.append(make_table(
        ['Durum', 'Prompt Stratejisi', 'Kullanım Senaryosu'],
        s3_model,
        col_widths=[4.5*cm, 5*cm, 7*cm],
        col_aligns=['td_bold', 'td_left', 'td_left']
    ))
    story.append(P('<i>Tablo 9. Model seçim mekanizması</i>', 'caption'))

    story.append(P('5.2. Feedback Loop (Kullandıkça Öğrenme)', 'sec_sub'))
    story.append(P(
        'Sistemin en yenilikçi bileşeni olan Feedback Loop şu şekilde çalışır:'
    ))
    feedback_steps = [
        '1. <b>Veri Toplama:</b> Operatör düzeltmeleri + başarılı ERP kayıtları → training_data.jsonl',
        '2. <b>Kalite Filtresi:</b> Tutarsız veya hatalı örnekler otomatik çıkarılır',
        '3. <b>Birikim Kontrolü:</b> Yeterli veri birikti mi? (eşik: ~100 örnek)',
        '4. <b>LoRA/QLoRA Eğitimi:</b> 4-bit quantized fine-tuning (GPU üzerinde)',
        '5. <b>Değerlendirme:</b> Test seti üzerinde accuracy kontrolü',
        '6. <b>Deploy/Rollback:</b> Yeni model ≥ eski → deploy, değilse eski korunur',
    ]
    for step in feedback_steps:
        story.append(P(f'• {step}', 'bullet'))

    story.append(P('5.3. Eğitim Verisi Formatı', 'sec_sub'))
    story.append(P(
        'Fine-tuning için kullanılan eğitim verisi instruction/input/output formatındadır:'
    ))
    story.append(P(
        '<i>"instruction": "Bu faturadan müşteri adı, VKN, tutar ve tarih bilgilerini çıkar."<br/>'
        '"input": "| Fatura No | Tarih | Müşteri |\\n| FTR-2026-001 | 15.07.2026 | ABC Ltd. |..."<br/>'
        '"output": "{\\"musteri_adi\\": \\"ABC Ltd.\\", \\"vkn\\": \\"1234567890\\", ...}"</i>', 'note'
    ))

    story.append(P('5.4. Karar Mekanizmaları', 'sec_sub'))
    s3_karar = [
        ['Router', 'Dosya türü + karmaşıklık', 'PyMuPDF4LLM / Docling / MarkItDown'],
        ['Model Seçimi', 'Fine-tuned model var mı?', 'Fine-Tuned (kısa prompt) / Base (zero-shot)'],
        ['Fine-Tuning Tetikleyici', 'len(training_data) >= 100', 'Eğitim başlat / Veri biriktir'],
        ['Model Değişim', 'Yeni accuracy > eski?', 'Deploy / Rollback'],
        ['Güven Skoru', 'Output confidence', 'Yüksek güven → ERP / Düşük → çift kontrol'],
        ['Hakem Kararı', '3 kontrol AND', '→ ERP / → Human-in-the-Loop'],
    ]
    story.append(make_table(
        ['Karar Noktası', 'Koşul', 'Sonuç'],
        s3_karar,
        col_widths=[4*cm, 5*cm, 7.5*cm],
        col_aligns=['td_bold', 'td', 'td_left']
    ))
    story.append(P('<i>Tablo 10. Senaryo 3 — Karar mekanizmaları</i>', 'caption'))

    story.append(P('5.5. Tam Akış Şeması', 'sec_sub'))
    story += img(figs['s3'], 1.0,
                 'Şekil 5. Senaryo 3 — Fine-Tuning + Feedback Loop tam akış şeması')

    story.append(P('5.6. Avantaj ve Dezavantajlar', 'sec_sub'))
    s3_ad = [
        ['✓ Zamanla artan doğruluk', '⚠ İlk kurulum karmaşıklığı yüksek'],
        ['✓ Daha az token tüketimi (fine-tuned)', '⚠ Fine-tuning için GPU gerekli'],
        ['✓ Şirkete özel belge formatlarını öğrenir', '⚠ Minimum ~100 eğitim verisi gerekli'],
        ['✓ Operatör düzeltmeleri otomatik değerlenir', '⚠ Model versiyonlama yönetimi gerekli'],
        ['✓ Uzun vadede en düşük çalışma maliyeti', '⚠ Data drift riski (format değişirse)'],
    ]
    story.append(make_table(
        ['Avantajlar', 'Dezavantajlar'],
        s3_ad,
        col_widths=[8.5*cm, 8*cm],
        col_aligns=['td_left', 'td_left']
    ))
    story.append(P('<i>Tablo 11. Senaryo 3 — Avantaj/dezavantaj analizi</i>', 'caption'))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  6. KARŞILAŞTIRMA MATRİSİ
    # ═══════════════════════════════════════════════════════
    story += section_title('6', 'Üç Senaryo Karşılaştırma Matrisi')
    story.append(P(
        'Aşağıdaki matris, üç senaryoyu 10 farklı kriter üzerinden karşılaştırmaktadır.'
    ))

    kars_data = [
        ['Kurulum Süresi',      '★★★★★ En hızlı', '★★★★',           '★★ En yavaş'],
        ['Başlangıç Maliyeti',  'Düşük',           'Orta',            'Yüksek'],
        ['Çalışma Maliyeti',    'Orta (uzun prompt)', 'Orta (benzer)', 'Düşük (kısa prompt)'],
        ['Format Desteği',      '15+ format',      'PDF odaklı',       'Geniş + öğrenen'],
        ['PDF Tablo Kalitesi',  '★★★',             '★★★★',            '★★★★'],
        ['Doğruluk (Başlangıç)','★★★',             '★★★',              '★★★ (aynı başlar)'],
        ['Doğruluk (6 Ay)',     '★★★ (sabit)',     '★★★ (sabit)',      '★★★★★ (artar)'],
        ['GPU İhtiyacı',        'Yok',              'Yok',              'Gerekli (Fine-tuning)'],
        ['Ölçeklenebilirlik',   '★★★★',            '★★★★',            '★★★★★'],
        ['Sektör Bağımsızlığı', '★★★★★',          '★★★★',            '★★★ (sektöre özel)'],
    ]
    story.append(make_table(
        ['Kriter', 'Senaryo 1 (MarkItDown)', 'Senaryo 2 (PyMuPDF4LLM)', 'Senaryo 3 (Fine-Tuning)'],
        kars_data,
        col_widths=[3.5*cm, 4.3*cm, 4.3*cm, 4.3*cm],
        col_aligns=['td_bold', 'td', 'td', 'td']
    ))
    story.append(P('<i>Tablo 12. Üç senaryo — 10 kriterli karşılaştırma matrisi</i>', 'caption'))

    story += img(figs['kars'], 1.0,
                 'Şekil 6. Karşılaştırma matrisi (görsel)')
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  7. KARAR MEKANİZMALARI ÖZET
    # ═══════════════════════════════════════════════════════
    story += section_title('7', 'Karar Mekanizmaları Özet Tablosu')
    story.append(P(
        'Aşağıdaki tablo, sistemdeki tüm karar noktalarını birleşik olarak göstermektedir. '
        'Her karar noktası hangi senaryoda aktif olduğunu belirtmektedir.'
    ))

    karar_ozet = [
        ['K1', 'Dosya Türü Nedir?', 'PDF / Office / Fotoğraf', 'Tümü', 'Router'],
        ['K1.1', 'PDF Dijital mi?', 'Metin var / Taranmış', 'S2, S3', 'Router'],
        ['K1.2', 'Tablo Karmaşık mı?', 'Basit / Karmaşık', 'S2, S3', 'Router'],
        ['K2', 'Fine-Tuned Model Var mı?', 'Evet → FT / Hayır → ZS', 'Sadece S3', 'Model Seçimi'],
        ['K3', 'LLM Tutar == QR Tutar?', 'Eşleşiyor / Eşleşmiyor', 'Tümü', 'Hakem'],
        ['K4', 'İmza Bulundu mu?', 'Evet / Hayır', 'Tümü', 'Hakem'],
        ['K5', 'VKN Doğrulandı mı?', 'Evet / Hayır', 'Tümü', 'Hakem'],
        ['K6', 'Tüm Kontroller OK?', 'PASS → ERP / FAIL → UI', 'Tümü', 'Hakem'],
        ['K7', 'Eğitim Verisi ≥ 100?', 'Eğitim / Bekle', 'Sadece S3', 'Feedback'],
    ]
    story.append(make_table(
        ['ID', 'Karar', 'Dallanma', 'Senaryo', 'Katman'],
        karar_ozet,
        col_widths=[1.5*cm, 4.5*cm, 4.5*cm, 2.5*cm, 3.5*cm],
        col_aligns=['td_bold', 'td_left', 'td_left', 'td', 'td']
    ))
    story.append(P('<i>Tablo 13. Birleşik karar mekanizmaları haritası (7 karar noktası)</i>', 'caption'))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  8. TEKNOLOJİ YIĞINI
    # ═══════════════════════════════════════════════════════
    story += section_title('8', 'Teknoloji Yığını')

    tech_data = [
        ['Güvenlik', 'pyzbar', '✓', '✓', '✓'],
        ['Güvenlik', 'YOLO / OpenCV', '✓', '✓', '✓'],
        ['Router', 'python-magic', '✓', '✓', '✓'],
        ['Dönüşüm (Hızlı)', 'MarkItDown', '✓ (Ana)', '✓ (Yardımcı)', '✓ (Yardımcı)'],
        ['Dönüşüm (Hızlı)', 'PyMuPDF4LLM', '—', '✓ (Ana)', '✓ (Ana)'],
        ['Dönüşüm (Zor)', 'Docling', '✓', '✓', '✓'],
        ['LLM', 'Qwen 3.5 (Ollama)', '✓ Zero-Shot', '✓ Zero-Shot', '✓ ZS + Fine-Tuned'],
        ['Şema', 'Pydantic', '✓', '✓', '✓'],
        ['Structured Output', 'LangChain', 'İsteğe bağlı', '✓', '✓'],
        ['Fine-Tuning', 'LoRA / QLoRA', '—', '—', '✓'],
        ['Hakem', 'Custom Python Agent', '✓', '✓', '✓'],
        ['VKN API', 'GİB / Şirket DB', '✓', '✓', '✓'],
        ['ERP', 'HTTP POST', '✓', '✓', '✓'],
        ['UI', 'Web Dashboard', '✓', '✓', '✓'],
        ['Feedback Loop', 'training_data.jsonl', '—', '—', '✓'],
    ]
    story.append(make_table(
        ['Katman', 'Araç', 'S1', 'S2', 'S3'],
        tech_data,
        col_widths=[3*cm, 4.5*cm, 3*cm, 3*cm, 3*cm],
        col_aligns=['td_left', 'td_bold', 'td', 'td', 'td']
    ))
    story.append(P('<i>Tablo 14. Teknoloji yığını — senaryo bazlı kullanım durumu</i>', 'caption'))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════
    #  9. YOL HARİTASI
    # ═══════════════════════════════════════════════════════
    story += section_title('9', 'Önerilen Uygulama Yol Haritası')
    story.append(P(
        'Önerilen strateji: <b>Faz 1 → Senaryo 1</b> ile başlayın (hızlı MVP), ardından '
        '<b>Faz 2 → Senaryo 2</b>\'ye geçin (PDF optimizasyonu), son olarak '
        '<b>Faz 3 → Senaryo 3</b>\'ü ekleyin (fine-tuning ile sürekli iyileşme).',
        'highlight'
    ))

    faz_data = [
        ['Faz 1 — MVP', '2-3 Hafta', 'Paralel güvenlik + MarkItDown + Docling + Zero-Shot LLM + Hakem + ERP POST'],
        ['Faz 2 — Optimizasyon', '2 Hafta', 'PyMuPDF4LLM entegrasyonu, 3 yollu router, LangChain Structured Output'],
        ['Faz 3 — Öğrenen Sistem', 'Sürekli', 'Operatör düzeltmelerinden veri toplama, LoRA eğitim, A/B test, model swap'],
    ]
    story.append(make_table(
        ['Faz', 'Süre', 'Kapsam'],
        faz_data,
        col_widths=[3.5*cm, 2.5*cm, 10.5*cm],
        col_aligns=['td_bold', 'td', 'td_left']
    ))
    story.append(P('<i>Tablo 15. Faz bazlı uygulama yol haritası</i>', 'caption'))
    story.append(Sp(0.3))

    # ═══════════════════════════════════════════════════════
    #  10. AÇIK SORULAR
    # ═══════════════════════════════════════════════════════
    story += section_title('10', 'Açık Sorular')
    story.append(P(
        'Aşağıdaki sorular, uygulamaya geçmeden önce netleştirilmesi gereken kritik kararları '
        'içermektedir:'
    ))

    acik_sorular = [
        ['Belge Türü Dağılımı', 'Sisteme girecek belgelerin yaklaşık yüzde kaçı PDF, yüzde kaçı Office, yüzde kaçı fotoğraf?', 'Senaryo 1 vs 2 seçimi'],
        ['GPU Erişimi', 'Fine-tuning için GPU kaynağı var mı? (NVIDIA RTX 3090+, A100 veya bulut GPU)', 'Senaryo 3 fizibilitesi'],
        ['ERP Sistemi', 'Hedef ERP hangisi? (SAP, Logo, Mikro, Netsis) API formatı ve auth yöntemi?', 'Entegrasyon tasarımı'],
        ['Sektör Odağı', 'Finans/muhasebe odaklı mı, yoksa İK/lojistik/sağlık da var mı?', 'Pydantic şema çeşitliliği'],
        ['VKN API', 'GİB API\'sine doğrudan erişim var mı, ara servis mi kullanılacak?', 'Hakem Ajanı VKN doğrulaması'],
    ]
    story.append(make_table(
        ['Soru', 'Detay', 'Etkilediği Karar'],
        acik_sorular,
        col_widths=[3.5*cm, 8.5*cm, 4.5*cm],
        col_aligns=['td_bold', 'td_left', 'td_left']
    ))
    story.append(P('<i>Tablo 16. Uygulamaya geçmeden önce cevaplanması gereken açık sorular</i>', 'caption'))

    story.append(Sp(0.5))
    story.append(HR())
    story.append(Sp(0.3))
    story.append(Paragraph(
        f'© {datetime.now().year} Akıllı Belge İşleme Sistemi — Dahili Kullanım İçin',
        ParagraphStyle('_footer', fontName='DV', fontSize=8,
                       textColor=C_MGRAY, alignment=TA_CENTER)))

    # BUILD
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f'\n   ✅ PDF oluşturuldu → {out}')
    return out


# ──────────────────────────────────────────────────────────────
#  ANA PROGRAM
# ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('\n🚀 Belge İşleme Senaryo Raporu Üreticisi v1.0')
    print('=' * 58)

    print('\n📈 Akış şemaları üretiliyor...')
    figs = {
        'giris': fig_sabit_giris(),
        'cikis': fig_sabit_cikis(),
        's1':    fig_senaryo1(),
        's2':    fig_senaryo2(),
        's3':    fig_senaryo3(),
        'kars':  fig_karsilastirma(),
    }

    print('\n📄 PDF oluşturuluyor...')
    pdf_path = build_pdf(figs)

    print('\n✨ TAMAMLANDI!')
    print(f'   PDF → {pdf_path}')
