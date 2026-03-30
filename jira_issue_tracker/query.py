def fetch_test_cases(jira, project_key, start_date, end_date):
    """Executes JQL based on .env inputs and parses results."""
    
    # Tuned JQL using the provided dates
    jql = (f'project = "{project_key}" AND issuetype = "Test" '
           f'AND created >= "{start_date}" AND created <= "{end_date}" '
           f'ORDER BY created ASC')
    
    print(f"Executing Query: {jql}")
    
    # Increase maxResults if you expect more than 100 tests
    issues = jira.search_issues(jql, maxResults=500)
    extracted_data = []

    for issue in issues:
        # 1. Extraction of Test Steps (Adjust customfield_ID if needed)
        steps_field = getattr(issue.fields, 'customfield_12345', [])
        steps = [f"{i+1}. {s.get('step', '')}" for i, s in enumerate(steps_field)]
        results = [f"{i+1}. {s.get('result', '')}" for i, s in enumerate(steps_field)]

        # 2. Traceability: "Is Blocked By"
        blockers = []
        if hasattr(issue.fields, 'issuelinks'):
            for link in issue.fields.issuelinks:
                if hasattr(link, 'type') and link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                    bug = link.inwardIssue
                    if bug.fields.issuetype.name == "Bug":
                        blockers.append(f"{bug.key} ({bug.fields.status.name})")

        # 3. Row Construction
        extracted_data.append({
            "Key": issue.key,
            "Summary": issue.fields.summary,
            "Execution Status": issue.fields.status.name,
            "Created Date": issue.fields.created[:10],
            "Test Steps": "\n".join(steps) if steps else "N/A",
            "Expected Results": "\n".join(results) if results else "N/A",
            "Blocking Bugs": "\n".join(blockers) if blockers else "None"
        })
    
    return extracted_data