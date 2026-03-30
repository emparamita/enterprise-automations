import os
import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from config import JiraConfig
from query import fetch_epic_hierarchy
from openpyxl.styles import Alignment

def format_date_for_file(date_str):
    """Extracts only digits from a date string (e.g., '2026-01-01' -> '20260101')."""
    if not date_str:
        return "ALL"
    return re.sub(r'\D', '', date_str.split()[0])

def main():
    # 1. Initialize Connection
    jira = JiraConfig.get_client()
    if not jira:
        return

    # 2. Retrieve Inputs from .env
    project = JiraConfig.PROJECT
    start = JiraConfig.START_DATE
    end = JiraConfig.END_DATE
    
    # 3. Logic for Empty/None Dates
    current_date = datetime.now().strftime("%Y-%m-%d")

    # If end_date is empty, use current date
    if not end:
        end = f"{current_date} 23:59"
    
    # If start_date is empty, JQL will handle 'everything till end'
    # but we need a string for the filename
    start_display = start if start else "START"

    # 4. Setup Export Directory
    export_dir = Path("exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    # 5. Build the Dynamic Filename
    # Pattern: jira_exports_<start_date_numbers>_<end_date_numbers>.xlsx
    start_num = format_date_for_file(start)
    end_num = format_date_for_file(end)
    filename = f"jira_exports_{start_num}_{end_num}.xlsx"
    output_path = export_dir / filename

    # 6. Fetch Data
    print(f"Targeting Project: {project}")
    print(f"Extraction Range: {start if start else 'Beginning'} to {end}")
    
    raw_data = fetch_epic_hierarchy(jira, project, start, end)
    
    if not raw_data:
        print("No records found for the specified criteria.")
        return

    # 7. Transform to Excel
    columns = [
        "epic_id", "epic_desc", "created_at", "test_id", 
        "test_desc", "test_steps", "expected_results", 
        "test_status", "blocked_by"
    ]
    df = pd.DataFrame(raw_data, columns=columns)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='EpicSummary')
        
        ws = writer.sheets['EpicSummary']
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrapText=True, vertical='top')

    print(f"\nSUCCESS: {len(df)} records exported to: {output_path}")

if __name__ == "__main__":
    main()