import pandas as pd
import os
import csv
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

LOG_FILE = "logs/workflow_log.csv"
EXCEL_FILE = "logs/workflow_report.xlsx"

def export_to_excel(csv_path=LOG_FILE, excel_path=EXCEL_FILE):
    """
    Converts the workflow CSV log to a formatted Excel report.
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return

    print(f"🔄 Reading CSV: {csv_path}...")
    try:
        # quoting=QUOTE_ALL ile yazılmış CSV'yi düzgün oku
        # on_bad_lines='warn' ile bozuk satırları atla, hata verme
        df = pd.read_csv(
            csv_path,
            quoting=csv.QUOTE_ALL,
            on_bad_lines='warn',
            engine='python'
        )

        
        # Write to Excel with Pandas first
        writer = pd.ExcelWriter(excel_path, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Workflow Logs')
        
        # Get workbook and worksheet for formatting
        workbook = writer.book
        worksheet = writer.sheets['Workflow Logs']
        
        print("🎨 Formatting Excel file...")
        
        # Define styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        
        wrap_alignment = Alignment(wrap_text=True, vertical="top")
        top_alignment = Alignment(vertical="top")
        
        # Iterate over columns
        for idx, col in enumerate(df.columns):
            col_letter = get_column_letter(idx + 1)
            cell_header = worksheet[f"{col_letter}1"]
            
            # Apply header style
            cell_header.font = header_font
            cell_header.fill = header_fill
            
            # Set column widths and wrapping
            if col in ["User_Prompt", "Generated_Code", "Judge_Reasoning"]:
                worksheet.column_dimensions[col_letter].width = 60
                
                # Apply wrap text to all cells in this column
                for cell in worksheet[col_letter]:
                    cell.alignment = wrap_alignment
            elif col in ["Metric_Weights"]:
                worksheet.column_dimensions[col_letter].width = 30
                for cell in worksheet[col_letter]:
                    cell.alignment = wrap_alignment
            else:
                worksheet.column_dimensions[col_letter].width = 15
                for cell in worksheet[col_letter]:
                    cell.alignment = top_alignment

        # Save
        writer.close()
        print(f"✅ Excel report generated: {excel_path}")
        
    except Exception as e:
        print(f"❌ Error exporting Excel: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    export_to_excel()
