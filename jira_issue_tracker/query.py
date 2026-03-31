import pandas as pd
from datetime import datetime
from pathlib import Path
from config import JiraConfig
from query import stream_hierarchy_data
from openpyxl.styles import Alignment

def main():
    jira = JiraConfig.get_client()
    if not jira:
        return

    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    ext = "csv" if JiraConfig.EXPORT_FORMAT == "CSV" else "xlsx"
    output_path = export_dir / f"jira_tracker_{timestamp}.{ext}"

    fieldnames = [
        "parent_id", 
        "parent_desc", 
        "created_at", 
        "child_id", 
        "child_desc", 
        "child_steps", 
        "expected_results", 
        "child_status", 
        "blocked_by"
    ]

    print("Starting Extraction...")
    
    data_list = []
    
    # Collect data from the generator defined in query.py
    for row in stream_hierarchy_data(jira, JiraConfig):
        data_list.append(row)
        if len(data_list) % 5 == 0:
            print(f"Extracted {len(data_list)} rows...")
    
    # Check if data_list is empty to prevent IndexErrors in ExcelWriter
    if not data_list:
        print("No data was found for the given criteria.")
        print("Verify PROJECT_KEY, PARENT_TYPE, and CHILD_TYPE in the .env file.")
        return

    df = pd.DataFrame(data_list, columns=fieldnames)

    if JiraConfig.EXPORT_FORMAT == "CSV":
        df.to_csv(output_path, index=False, encoding='utf-8')
    else:
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
                ws = writer.sheets['Report']
                
                # Apply text wrapping and alignment to all cells
                for r in ws.iter_rows(min_row=2):
                    for cell in r:
                        cell.alignment = Alignment(wrapText=True, vertical='top')
        except Exception as e:
            print(f"Excel Error: {e}")
            return

    print(f"Export Complete: {len(df)} rows saved to {output_path}")

if __name__ == "__main__":
    main()
