from config import JiraConfig
from query import fetch_test_cases
import pandas as pd
from openpyxl.styles import Alignment

def main():
    # 1. Access the secure client
    jira = JiraConfig.get_client()
    if not jira:
        return

    # 2. Define Date Range (Could also move to .env if static)
    START = "2026-01-01"
    END = "2026-01-01 23:59"

    print(f"Connection Verified. Fetching tests from {JiraConfig.PROJECT}...")
    
    # 3. Execution Logic
    raw_data = fetch_test_cases(jira, JiraConfig.PROJECT, START, END)
    
    if raw_data:
        df = pd.DataFrame(raw_data)
        output = f"Jira_Extract_{START}.xlsx"
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
            # Alignment logic here...
        print(f"Success! File saved as {output}")

if __name__ == "__main__":
    main()