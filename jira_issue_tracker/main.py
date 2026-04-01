import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from config import JiraConfig
from query import process_entities

def main():
    JiraConfig.setup_logging()
    logger = logging.getLogger("main")
    
    jira = JiraConfig.get_client()
    if not jira: return

    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    logger.info(f"Starting Extraction for {JiraConfig.ENTITY_TYPE}...")
    entities, tests, blockers = process_entities(jira, JiraConfig)

    if not entities:
        logger.warning("No data found for the specified criteria.")
        return

    # Prepare DataFrames
    df_entities = pd.DataFrame(entities)
    df_tests = pd.DataFrame(tests)
    df_blockers = pd.DataFrame(blockers)

    if JiraConfig.EXPORT_FORMAT == "EXCEL":
        output_path = export_dir / f"Master_Report_{timestamp}.xlsx"
        logger.info(f"Assembling Excel tabs at {output_path}")
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df_entities.to_excel(writer, sheet_name='Main_Entities', index=False)
            if not df_tests.empty:
                df_tests.to_excel(writer, sheet_name='Linked_Tests', index=False)
            if not df_blockers.empty:
                df_blockers.to_excel(writer, sheet_name='Blockers', index=False)
    else:
        # Generate individual CSVs
        df_entities.to_csv(export_dir / f"entities_{timestamp}.csv", index=False)
        if not df_tests.empty:
            df_tests.to_csv(export_dir / f"tests_{timestamp}.csv", index=False)
        if not df_blockers.empty:
            df_blockers.to_csv(export_dir / f"blockers_{timestamp}.csv", index=False)
        logger.info("CSV extraction complete.")

    logger.info("Job finished successfully.")

if __name__ == "__main__":
    main()