import csv
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from config import JiraConfig
from query import stream_hierarchy_data
from openpyxl.styles import Alignment

def clean_date_num(date_str):
    if not date_str: return "ALL"
    return re.sub(r'\D', '', date_str.split()[0])

def main():
    jira = JiraConfig.get_client()
    if not jira: return

    # 1. Filename Setup
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    start_fn = clean_date_num(JiraConfig.START_DATE)
    end_fn = clean_date_num(JiraConfig.END_DATE if JiraConfig.END_DATE else datetime.now().strftime("%Y-%m-%d"))
    
    ext = "csv" if JiraConfig.EXPORT_FORMAT == "CSV" else "xlsx"
    filename = f"jira_exports_{start_fn}_{end_fn}.{ext}"
    output_path = export_dir / filename

    print(f"Mode: {JiraConfig.EXPORT_FORMAT} | Format: {ext}")
    print(f"Extracting {JiraConfig.PARENT_TYPE} -> {JiraConfig.CHILD_TYPE}...")

    fieldnames = ["parent_id", "parent_desc", "created_at", "child_id", 
                  "child_desc", "child_steps", "expected_results", 
                  "child_status", "blocked_by"]

    count = 0

    # 2. Execution Path A: CSV (True Load-Agnostic / Appending)
    if JiraConfig.EXPORT_FORMAT == "CSV":
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in stream_hierarchy_data(jira, JiraConfig):
                writer.writerow(row)
                count += 1
                if count % 20 == 0: print(f"  Exported {count} rows...")

    # 3. Execution Path B: Excel (Formatted / Memory-Buffered)
    else:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # We must accumulate data to write into Excel properly
            # but we do it as a single block to minimize IO complexity
            data_list = []
            for row in stream_hierarchy_data(jira, JiraConfig):
                data_list.append(row)
                count += 1
                if count % 20 == 0: print(f"  Extracted {count} rows...")
            
            if data_list:
                df = pd.DataFrame(data_list)
                df.to_excel(writer, index=False, sheet_name='JiraData')
                ws = writer.sheets['JiraData']
                # Apply Wrapping/Formatting
                for r in ws.iter_rows(min_row=2):
                    for cell in r:
                        cell.alignment = Alignment(wrapText=True, vertical='top')

    if count > 0:
        print(f"\nSUCCESS! Total Records: {count}")
        print(f"File Saved: {output_path}")
    else:
        print("\nNo data found for the selected criteria.")

if __name__ == "__main__":
    main()