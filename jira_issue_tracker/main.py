import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from config import JiraConfig
from query import fetch_hierarchy_data
from openpyxl.styles import Alignment

def clean_date_num(date_str):
    """Strips non-digits for filename usage."""
    if not date_str: return "ALL"
    return re.sub(r'\D', '', date_str.split()[0])

def main():
    # 1. Init Connection
    jira = JiraConfig.get_client()
    if not jira: return

    # 2. Date Logic for Filename and Query
    current_date_obj = datetime.now()
    current_date_str = current_date_obj.strftime("%Y-%m-%d")
    
    start_val = JiraConfig.START_DATE
    # Default to current date if END_DATE is empty in .env
    end_val = JiraConfig.END_DATE if JiraConfig.END_DATE else f"{current_date_str} 23:59"

    # 3. Directory & Naming
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    fn_start = clean_date_num(start_val)
    fn_end = clean_date_num(end_val)
    filename = f"jira_exports_{fn_start}_{fn_end}.xlsx"
    output_path = export_dir / filename

    print(f"\n--- Jira Generic Extractor ---")
    print(f"Mapping: {JiraConfig.PARENT_TYPE} -> {JiraConfig.CHILD_TYPE}")
    print(f"Range: {start_val if start_val else 'Beginning'} to {end_val}")
    
    # 4. Run Logic
    data = fetch_hierarchy_data(jira, JiraConfig)
    
    if not data:
        print("No related items found for this criteria.")
        return

    # 5. Export to Excel with Column Ordering
    cols = ["parent_id", "parent_desc", "created_at", "child_id", 
            "child_desc", "child_steps", "expected_results", 
            "child_status", "blocked_by"]
    
    df = pd.DataFrame(data, columns=cols)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
        ws = writer.sheets['Report']
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrapText=True, vertical='top')

    print(f"\nSUCCESS: {len(df)} rows exported.")
    print(f"File: {output_path}\n")

if __name__ == "__main__":
    main()