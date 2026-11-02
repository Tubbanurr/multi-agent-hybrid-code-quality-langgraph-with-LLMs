"""
benchmark_runner.py
====================
Benchmark veri setindeki promptları sırasıyla mevcut agentic workflow'a gönderir
ve sonuçları benchmark_results.xlsx / benchmark_results.csv dosyalarına kaydeder.

Mevcut proje koduna (module/, main.py vb.) HİÇBİR DEĞİŞİKLİK YAPILMAZ.
Bu script tamamen bağımsız çalışır.

Kullanım:
    cd /Users/tuba/Desktop/ap/agentic_nodes_loop
    source venv/bin/activate
    python benchmark_runner.py

Özellikler:
- Benchmark'taki her satıra otomatik prompt_id (1'den başlayarak) atanır
- Zaten test edilmiş prompt_id'ler atlanır (logs/benchmark_progress.json aracılığıyla)
- Devam edebilirlik: script her çalıştırıldığında kaldığı yerden devam eder
- workflow_log.csv'deki mevcut kayıtlar prompt_id ile eşleştirilir
- Sonuçlar logs/benchmark_results.xlsx ve logs/benchmark_results.csv'ye yazılır
"""

import os
import sys
import json
import csv
import time
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ---------------------------------------------------------------------------
# YAPILANDIRMA
# ---------------------------------------------------------------------------
BENCHMARK_FILE   = "logs/benchmark-gemini.xlsx"
BENCHMARK_HEADER = 1          # Kolon başlıkları hangi satırda (0-indexed: 1 = 2. satır)

# Sadece belirli satır aralığını çalıştır (None = hepsini çalıştır)
RUN_FROM_ID = None
RUN_TO_ID   = None

PROMPT_COL       = "Promt(GEMİNİ)"     # Benchmark prompt kolonu
CATEGORY_COL     = "Unnamed: 0"        # Zorluk (Kolay/Orta/Zor)

RESULTS_CSV      = "logs/benchmark_results.csv"
RESULTS_XLSX     = "logs/benchmark_results.xlsx"
PROGRESS_FILE    = "logs/benchmark_progress.json"
EXISTING_LOG_CSV = "logs/workflow_log.csv"

# Workflow parametreleri
WORKFLOW_PARAMS = {
    "quality_threshold": 95.0,   # UI (main.py) ile aynı sabit eşik
    "max_iterations":    11,
    "static_weight":     0.7,
    "llm_weight":        0.3,
    "metric_weights":    None,
}

# Promptlar arası bekleme süresi (saniye)
SLEEP_BETWEEN_PROMPTS = 5

# True → workflow_log.csv'yi görmezden gel, tüm 108 promptu sıfırdan çalıştır
# False → mevcut workflow_log'daki kayıtları tamamlanmış say, kaldığı yerden devam et
FRESH_START = False

# ---------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------------------------

def load_progress() -> set:
    """Tamamlanan prompt_id'leri yükle."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("completed_ids", []))
    return set()


def save_progress(completed_ids: set) -> None:
    """Tamamlanan prompt_id'leri kaydet."""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "completed_ids": sorted(list(completed_ids)),
                "last_updated": datetime.now().isoformat(),
                "total_completed": len(completed_ids),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def load_existing_log_as_completed() -> dict:
    """
    Mevcut workflow_log.csv'deki kayıtları okuyup
    prompt_id → satır eşlemesi döndür.
    Satır sırası = prompt_id (1-indexed).
    """
    existing = {}
    if not os.path.exists(EXISTING_LOG_CSV):
        return existing

    try:
        df = pd.read_csv(EXISTING_LOG_CSV)
        for idx, row in df.iterrows():
            prompt_id = idx + 1  # 1-indexed
            existing[prompt_id] = row.to_dict()
        print(f"  ℹ️  Mevcut log'dan {len(existing)} kayıt okundu (prompt_id 1-{len(existing)})")
    except Exception as e:
        print(f"  ⚠️  Mevcut log okunamadı: {e}")

    return existing


def append_result_to_csv(row_data: dict) -> None:
    """Sonucu benchmark_results.csv'ye ekle."""
    os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)
    file_exists = os.path.isfile(RESULTS_CSV)

    fieldnames = list(row_data.keys())

    with open(RESULTS_CSV, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)


def rebuild_excel_from_csv() -> None:
    """CSV'den Excel dosyasını yeniden oluştur."""
    try:
        df = pd.read_csv(RESULTS_CSV)

        with pd.ExcelWriter(RESULTS_XLSX, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Benchmark_Results")
            ws = writer.sheets["Benchmark_Results"]

            # Başlık stili
            header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            thin_border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )

            for cell in ws[1]:
                cell.fill      = header_fill
                cell.font      = header_font
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border    = thin_border

            # Kolon genişlikleri
            col_widths = {
                "Prompt_ID":         10,
                "Kategori":          12,
                "Benchmark_Prompt":  50,
                "Winner_Model":      20,
                "Initial_Score":     14,
                "Final_Score":       12,
                "Score_Change":      14,
                "Iteration_Count":   14,
                "Status":            18,
                "Initial_Code":      60,
                "Final_Code":        60,
                "LLM_Deficiencies":  50,
                "Improvements_Made": 50,
                "Judge_Model":       22,
                "Run_Timestamp":     20,
                "Error":             40,
            }

            wrap_align   = Alignment(wrap_text=True, vertical="top")
            center_align = Alignment(horizontal="center", vertical="top", wrap_text=True)

            for col_idx, col_cells in enumerate(ws.columns, 1):
                col_letter = get_column_letter(col_idx)
                header_val = ws.cell(row=1, column=col_idx).value
                width = col_widths.get(header_val, 30)
                ws.column_dimensions[col_letter].width = width

                for cell in col_cells:
                    if cell.row > 1:
                        cell.border = thin_border
                        if header_val in ("Prompt_ID", "Initial_Score", "Final_Score",
                                          "Iteration_Count", "Score_Change"):
                            cell.alignment = center_align
                        else:
                            cell.alignment = wrap_align

            # Satır yükseklikleri
            for row_idx in range(2, ws.max_row + 1):
                ws.row_dimensions[row_idx].height = 80
            ws.row_dimensions[1].height = 30

            # Başlık dondur
            ws.freeze_panes = "A2"

        print(f"  ✅ Excel güncellendi → {RESULTS_XLSX}")

    except Exception as e:
        print(f"  ⚠️  Excel güncellenemedi: {e}")
        traceback.print_exc()


def format_result_row(
    prompt_id: int,
    category: str,
    prompt_text: str,
    workflow_result: dict = None,
    error_msg: str = None,
    timestamp: str = None,
    judge_model: str = "",
) -> dict:
    """Workflow sonucunu CSV satırına dönüştür."""
    ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if error_msg:
        return {
            "Prompt_ID":         prompt_id,
            "Kategori":          category,
            "Benchmark_Prompt":  prompt_text[:2000],
            "Winner_Model":      "ERROR",
            "Initial_Score":     "",
            "Final_Score":       "",
            "Score_Change":      "",
            "Iteration_Count":   "",
            "Status":            "ERROR",
            "Initial_Code":      "",
            "Final_Code":        "",
            "LLM_Deficiencies":  "",
            "Improvements_Made": "",
            "Judge_Model":       judge_model,
            "Run_Timestamp":     ts,
            "Error":             str(error_msg)[:500],
        }

    r = workflow_result
    winner_score   = r.get("winner_score", 0.0)
    final_score    = r.get("final_score", 0.0)
    score_diff     = final_score - winner_score
    iteration_cnt  = max(0, r.get("iteration_count", 0) - 1)

    # round1 kazanının deficiency reasoning'i
    round1_scores = r.get("round1_scores", {})
    winner_model  = r.get("winner_model", "")
    winner_data   = round1_scores.get(winner_model, {})
    deficiencies  = winner_data.get("reasoning", "")

    # Yapılan iyileştirmeler
    feedback_iters = r.get("feedback_iterations", [])
    improvements_parts = []
    for i, it in enumerate(feedback_iters, 1):
        actions = [s.get("action", "") for s in it.get("suggestions", []) if s.get("action")]
        if actions:
            improvements_parts.append(f"İter {i}:\n" + "\n".join(f"- {a}" for a in actions))
    improvements = "\n\n".join(improvements_parts) if improvements_parts else "İyileştirme gerekmedi."

    return {
        "Prompt_ID":         prompt_id,
        "Kategori":          category,
        "Benchmark_Prompt":  prompt_text[:2000],
        "Winner_Model":      winner_model,
        "Initial_Score":     round(winner_score, 2),
        "Final_Score":       round(final_score, 2),
        "Score_Change":      f"{score_diff:+.2f}",
        "Iteration_Count":   iteration_cnt,
        "Status":            r.get("status", ""),
        "Initial_Code":      r.get("winner_code", ""),
        "Final_Code":        r.get("final_code", ""),
        "LLM_Deficiencies":  deficiencies,
        "Improvements_Made": improvements,
        "Judge_Model":       judge_model,
        "Run_Timestamp":     ts,
        "Error":             "",
    }


def migrate_existing_log_to_results(existing_log: dict, benchmark_df: pd.DataFrame) -> None:
    """
    Mevcut workflow_log.csv'deki kayıtları benchmark_results.csv'ye
    prompt_id ile aktarır (zaten orada değilse).
    """
    if not existing_log:
        return

    already_migrated = set()
    if os.path.exists(RESULTS_CSV):
        try:
            df_res = pd.read_csv(RESULTS_CSV)
            already_migrated = set(df_res["Prompt_ID"].tolist())
        except Exception:
            pass

    migrated_count = 0
    for prompt_id, log_row in existing_log.items():
        if prompt_id in already_migrated:
            continue

        bench_idx = prompt_id - 1
        if bench_idx >= len(benchmark_df):
            continue

        bench_row = benchmark_df.iloc[bench_idx]
        category  = str(bench_row.get(CATEGORY_COL, "")).strip()
        prompt    = str(bench_row.get(PROMPT_COL, "")).strip()

        # "96.0 -> 96.0 (+0.0)" formatından parse
        score_change_raw = str(log_row.get("Score_Change", "0 -> 0 (+0.0)"))
        try:
            parts         = score_change_raw.split("->")
            initial_score = float(parts[0].strip())
            final_part    = parts[1].strip().split("(")[0].strip()
            final_score   = float(final_part)
        except Exception:
            initial_score = 0.0
            final_score   = 0.0

        score_diff = final_score - initial_score

        row_data = {
            "Prompt_ID":         prompt_id,
            "Kategori":          category,
            "Benchmark_Prompt":  prompt[:2000],
            "Winner_Model":      log_row.get("Winner_Model", ""),
            "Initial_Score":     round(initial_score, 2),
            "Final_Score":       round(final_score, 2),
            "Score_Change":      f"{score_diff:+.2f}",
            "Iteration_Count":   log_row.get("Iteration_Count", 0),
            "Status":            "migrated_from_log",
            "Initial_Code":      log_row.get("Initial_Code", ""),
            "Final_Code":        log_row.get("Final_Code", ""),
            "LLM_Deficiencies":  log_row.get("LLM_Deficiencies", ""),
            "Improvements_Made": log_row.get("Improvements_Made", ""),
            "Judge_Model":       log_row.get("Judge_Model", ""),
            "Run_Timestamp":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Error":             "",
        }

        append_result_to_csv(row_data)
        migrated_count += 1

    if migrated_count > 0:
        print(f"  ✅ {migrated_count} mevcut kayıt prompt_id ile benchmark_results'a aktarıldı")
        rebuild_excel_from_csv()


# ---------------------------------------------------------------------------
# ANA ÇALIŞMA MANTIĞI
# ---------------------------------------------------------------------------

def run_benchmark():
    print("\n" + "="*70)
    print("🚀 BENCHMARK RUNNER BAŞLIYOR")
    print("="*70)
    print(f"  Benchmark  : {BENCHMARK_FILE}")
    print(f"  Çıktı CSV  : {RESULTS_CSV}")
    print(f"  Çıktı XLSX : {RESULTS_XLSX}")
    print(f"  Progress   : {PROGRESS_FILE}")
    print("="*70 + "\n")

    # 1) Benchmark dosyasını yükle
    print("📂 Benchmark yükleniyor...")
    try:
        benchmark_df = pd.read_excel(BENCHMARK_FILE, header=BENCHMARK_HEADER)
    except Exception as e:
        print(f"❌ Benchmark dosyası okunamadı: {e}")
        sys.exit(1)

    benchmark_df = benchmark_df[benchmark_df[PROMPT_COL].notna()].reset_index(drop=True)
    total = len(benchmark_df)
    print(f"  Toplam geçerli prompt: {total}\n")

    # 2) Mevcut log'daki kayıtları migrate et (sadece FRESH_START=False ise)
    if FRESH_START:
        print("🆕 FRESH START modu — workflow_log.csv atlanıyor, prompt 1'den başlanıyor")
        existing_log  = {}
        completed_ids = set()
    else:
        print("📋 Mevcut workflow_log.csv okunuyor...")
        existing_log = load_existing_log_as_completed()
        migrate_existing_log_to_results(existing_log, benchmark_df)
        completed_ids = load_progress()
        existing_ids  = set(existing_log.keys())
        completed_ids = completed_ids | existing_ids

    save_progress(completed_ids)

    pending = [
        i + 1 for i in range(total)
        if (i + 1) not in completed_ids
        and (RUN_FROM_ID is None or (i + 1) >= RUN_FROM_ID)
        and (RUN_TO_ID   is None or (i + 1) <= RUN_TO_ID)
    ]

    print(f"\n📊 Durum:")
    print(f"  Tamamlanan : {len(completed_ids)}/{total}")
    print(f"  Bekleyen   : {len(pending)}/{total}")

    if not pending:
        print("\n✅ Tüm promptlar zaten test edilmiş!")
        return

    # 4) Workflow modülünü import et (mevcut koda dokunulmaz)
    print("\n⚙️  Workflow modülü yükleniyor...")
    try:
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from module.agentic_workflow import run_hybrid_workflow
        from module.llm_judge import LLMJudge

        judge_model_name = LLMJudge().get_model_name()
        print(f"  ✅ Yüklendi. Judge model: {judge_model_name}\n")
    except Exception as e:
        print(f"❌ Workflow modülü yüklenemedi: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 5) Sırasıyla çalıştır
    print("="*70)
    print(f"▶️  TEST BAŞLIYOR — {len(pending)} prompt kaldı")
    print("="*70 + "\n")

    for prompt_id in pending:
        bench_idx   = prompt_id - 1
        bench_row   = benchmark_df.iloc[bench_idx]
        category    = str(bench_row.get(CATEGORY_COL, "")).strip()
        prompt_text = str(bench_row.get(PROMPT_COL, "")).strip()

        if not prompt_text or prompt_text.lower() == "nan":
            print(f"⏭️  Prompt ID {prompt_id:3d} — Boş prompt, atlanıyor.")
            completed_ids.add(prompt_id)
            save_progress(completed_ids)
            continue

        print(f"\n{'─'*70}")
        print(f"🔹 Prompt ID: {prompt_id:3d}/{total}  |  Kategori: {category}")
        print(f"📝 {prompt_text[:120]}{'...' if len(prompt_text) > 120 else ''}")
        print(f"{'─'*70}")

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            result = run_hybrid_workflow(prompt=prompt_text, **WORKFLOW_PARAMS)

            row_data = format_result_row(
                prompt_id=prompt_id,
                category=category,
                prompt_text=prompt_text,
                workflow_result=result,
                timestamp=ts,
                judge_model=judge_model_name,
            )
            print(f"\n  ✅ ID {prompt_id} tamamlandı → Final Score: {row_data['Final_Score']}/100")

        except Exception as e:
            print(f"\n  ❌ ID {prompt_id} HATA: {e}")
            traceback.print_exc()
            row_data = format_result_row(
                prompt_id=prompt_id,
                category=category,
                prompt_text=prompt_text,
                error_msg=str(e),
                timestamp=ts,
                judge_model=judge_model_name,
            )

        # Kaydet
        append_result_to_csv(row_data)
        rebuild_excel_from_csv()

        # Progress güncelle
        completed_ids.add(prompt_id)
        save_progress(completed_ids)

        remaining = len(pending) - pending.index(prompt_id) - 1
        print(f"  💾 Kaydedildi. Kalan: {remaining} prompt")

        if remaining > 0:
            print(f"  ⏳ {SLEEP_BETWEEN_PROMPTS}s bekleniyor...")
            time.sleep(SLEEP_BETWEEN_PROMPTS)

    # 6) Tamamlandı
    print("\n" + "="*70)
    print("🎉 TÜM BENCHMARK TESTLERİ TAMAMLANDI!")
    print(f"  CSV  → {RESULTS_CSV}")
    print(f"  XLSX → {RESULTS_XLSX}")
    print("="*70 + "\n")


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    run_benchmark()
