import pandas as pd
import os
from datetime import datetime

def export_to_excel():
    """
    Converts logs/workflow_log.csv to logs/workflow_report.xlsx with basic formatting.
    """
    csv_path = "logs/workflow_log.csv"
    excel_path = "logs/workflow_report.xlsx"
    
    if not os.path.exists(csv_path):
        print(f"  ⚠️ Excel Güncelleme: CSV dosyası bulunamadı ({csv_path})")
        return
        
    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(excel_path), exist_ok=True)
        
        # Write to Excel with styling
        # Defaulting to openpyxl since we verified it exists
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Workflow_Report')
            
            from openpyxl.styles import Font, PatternFill, Alignment
            worksheet = writer.sheets['Workflow_Report']
            
            # Header styling
            header_fill = PatternFill(start_color='D7E4BC', end_color='D7E4BC', fill_type='solid')
            header_font = Font(bold=True)
            
            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            # Auto-adjust column widths
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)
        
        print(f"  ✅ Excel raporu başarıyla güncellendi: {excel_path}")
        
    except Exception as e:
        print(f"  ❌ Excel güncelleme hatası: {e}")

if __name__ == "__main__":
    export_to_excel()
