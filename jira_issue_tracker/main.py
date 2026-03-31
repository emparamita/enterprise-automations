import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from config import JiraConfig
from query import stream_hierarchy_data
from openpyxl.styles import Alignment

def main():
    # Initialize Logger
    JiraConfig.setup_logging()
    logger = logging.getLogger("main")
    
    logger.info("Initializing Jira connection...")
    jira = JiraConfig.get_client()
    if not jira:
        return

    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    ext = "csv" if JiraConfig.EXPORT_FORMAT == "CSV" else "xlsx"
    output_path = export_dir / f"jira_tracker_{timestamp}.{ext}"

    fieldnames = [
        "parent_id", "parent_desc", "created_at", "child_id", 
        "child_desc", "child_steps", "expected_results", 
        "child_status", "blocked_by"
    ]

    logger.info("Starting data extraction loop...")
    data_list = []
    
    try:
        for row in stream_hierarchy_data(jira, JiraConfig):
            data_list.append(row)
            if len(data_list) % 10 == 0:
                logger.info(f"Progress: {len(data_list)} issues processed.")
    except Exception as e:
        logger.critical(f"Critical error during stream: {e}")
        return
    
    if not data_list:
        logger.warning("Extraction completed but no records were found.")
        return

    logger.info(f"Generating {JiraConfig.EXPORT_FORMAT} file...")
    df = pd.DataFrame(data_list, columns=fieldnames)

    if JiraConfig.EXPORT_FORMAT == "CSV":
        df.to_csv(output_path, index=False, encoding='utf-8')
    else:
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
                ws = writer.sheets['Report']
                for r in ws.iter_rows(min_row=2):
                    for cell in r:
                        cell.alignment = Alignment(wrapText=True, vertical='top')
        except Exception as e:
            logger.error(f"Failed to write Excel file: {e}")
            return

    logger.info(f"Process Successful. Total records: {len(df)}")
    logger.info(f"Output saved to: {output_path}")

if __name__ == "__main__":
    main()