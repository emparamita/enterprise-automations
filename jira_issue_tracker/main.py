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
        logger.warning("No data collected.")
        return

    is_test_mode = (JiraConfig.ENTITY_TYPE.lower() == 'test')
    main_tab_name = JiraConfig.ENTITY_TYPE.capitalize()

    # Define Column Order for Test Data
    test_cols = [
        "parent_id", "issue_key", "summary", "status", "created", 
        "child_steps", "last_executed_by", "last_execution_timestamp", "last_execution_status"
    ]

    if JiraConfig.EXPORT_FORMAT == "EXCEL":
        output_path = export_dir / f"{main_tab_name}_Report_{timestamp}.xlsx"
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            
            # Tab 1: Primary Entity
            df_main = pd.DataFrame(entities)
            if is_test_mode:
                df_main = df_main[test_cols]
            df_main.to_excel(writer, sheet_name=main_tab_name, index=False)
            
            # Tab 2: Linked Tests (for non-test entities)
            if not is_test_mode and linked_tests:
                df_linked = pd.DataFrame(linked_tests)
                df_linked = df_linked[test_cols]
                df_linked.to_excel(writer, sheet_name='Linked_Tests', index=False)
            
            # Tab 3: Blockers
            if blockers:
                pd.DataFrame(blockers).to_excel(writer, sheet_name='Blockers', index=False)
        
        logger.info(f"Export Success: {output_path}")
    else:
        # CSV Handling logic...
        pd.DataFrame(entities).to_csv(export_dir / f"{main_tab_name}_{timestamp}.csv", index=False)
        logger.info("CSV files created.")

if __name__ == "__main__":
    main()