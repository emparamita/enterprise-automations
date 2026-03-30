import os
import pandas as pd
from pathlib import Path
from config import JiraConfig
from query import fetch_test_cases
from openpyxl.styles import Alignment

def main():
    # 1. Initialize Connection
    jira = JiraConfig.get_client()
    if not jira:
        return

    # 2. Retrieve Inputs
    project = JiraConfig.PROJECT
    start = JiraConfig.START_DATE
    end = JiraConfig.END_DATE

    if not all([project, start, end]):
        print("Error: Missing PROJECT_KEY, START_DATE, or END_DATE in .env file.")
        return

    # 3. Setup Export Directory
    # This creates an 'exports' folder in the current project directory
    export_dir = Path("exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    # 4. Fetch Data
    print(f"Targeting Project: {project} | Range: {start} to {end}")
    raw_data = fetch_test_cases(jira, project, start, end)
    
    if not raw_data:
        print("No records found for the specified criteria.")
        return

    # 5. Transform to Excel
    df = pd.DataFrame(raw_data)
    
    # Format filename: Jira_Report_PROJ_2026-01-01.xlsx
    safe_date = start.split()[0] 
    filename = f"Jira_Report_{project}_{safe_date}.xlsx"
    
    # Define the full path inside the exports folder
    output_path = export_dir / filename
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='TestCases')
        
        # Apply 'Wrap Text' and 'Top Alignment'
        ws = writer.sheets['TestCases']
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrapText=True, vertical='top')

    print(f"\nSUCCESS: {len(df)} test cases exported to: {output_path}")

if __name__ == "__main__":
    main()