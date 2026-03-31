import csv
from datetime import datetime
from pathlib import Path
from config import JiraConfig
from query_engine import get_paged_issues, extract_issue_data

def main():
    jira = JiraConfig.get_client()
    if not jira: return

    # Setup Export Folder
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = export_dir / f"query_results_{timestamp}.csv"

    print(f"Executing JQL: {JiraConfig.QUERY}")
    
    count = 0
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=JiraConfig.FIELDS)
        writer.writeheader()

        # Stream directly from Jira to CSV
        for issue in get_paged_issues(jira, JiraConfig.QUERY, JiraConfig.BLOCK_SIZE):
            row = extract_issue_data(issue, JiraConfig.FIELDS)
            writer.writerow(row)
            count += 1
            if count % 50 == 0:
                print(f"  Extracted {count} issues...")

    if count > 0:
        print(f"\nSUCCESS: {count} issues written to {output_path}")
    else:
        print("\nNo issues matched the query.")

if __name__ == "__main__":
    main()