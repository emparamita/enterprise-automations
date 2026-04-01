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
    
    entities, linked_tests, blockers = process_entities(jira, JiraConfig)

    if not entities:
        logger.warning("No data found.")
        return

    df_main = pd.DataFrame(entities)
    df_linked_tests = pd.DataFrame(linked_tests)
    df_blockers = pd.DataFrame(blockers)

    # Determine tab names and logic
    main_tab_name = JiraConfig.ENTITY_TYPE.capitalize()
    is_test_mode = (JiraConfig.ENTITY_TYPE.lower() == 'test')

    if JiraConfig.EXPORT_FORMAT == "EXCEL":
        output_path = export_dir / f"{main_tab_name}_Report_{timestamp}.xlsx"
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Tab 1: The Primary Entity (e.g., Test or Enhancement)
            df_main.to_excel(writer, sheet_name=main_tab_name, index=False)
            
            # Tab 2: Linked Tests (Only if Entity is NOT Test and tests were found)
            if not is_test_mode and not df_linked_tests.empty:
                df_linked_tests.to_excel(writer, sheet_name='Linked_Tests', index=False)
            
            # Tab 3: Blockers (If any found)
            if not df_blockers.empty:
                df_blockers.to_excel(writer, sheet_name='Blockers', index=False)
        
        logger.info(f"Excel report created: {output_path}")
    else:
        # CSV Export Logic
        df_main.to_csv(export_dir / f"{main_tab_name}_{timestamp}.csv", index=False)
        if not is_test_mode and not df_linked_tests.empty:
            df_linked_tests.to_csv(export_dir / f"linked_tests_{timestamp}.csv", index=False)
        if not df_blockers.empty:
            df_blockers.to_csv(export_dir / f"blockers_{timestamp}.csv", index=False)
        logger.info("Individual CSV files generated.")

if __name__ == "__main__":
    main()