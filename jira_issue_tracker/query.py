def fetch_test_cases(jira, project_key, start_date, end_date):
    """Executes JQL and parses results into a list of dictionaries."""
    jql = (f'project = "{project_key}" AND issuetype = "Test" '
           f'AND created >= "{start_date}" AND created <= "{end_date}" '
           f'ORDER BY created ASC')
    
    issues = jira.search_issues(jql, maxResults=500)
    extracted_data = []

    for issue in issues:
        # Extracting Steps (adjust customfield ID based on your IPython test)
        steps_data = getattr(issue.fields, 'customfield_12345', [])
        steps = [f"{i+1}. {s.get('step', '')}" for i, s in enumerate(steps_data)]
        results = [f"{i+1}. {s.get('result', '')}" for i, s in enumerate(steps_data)]

        # Extracting "Blocked By" Bugs
        blockers = []
        if hasattr(issue.fields, 'issuelinks'):
            for link in issue.fields.issuelinks:
                if hasattr(link, 'type') and link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                    bug = link.inwardIssue
                    blockers.append(f"{bug.key} ({bug.fields.status.name})")

        extracted_data.append({
            "Key": issue.key,
            "Summary": issue.fields.summary,
            "Status": issue.fields.status.name,
            "Created": issue.fields.created[:10],
            "Steps": "\n".join(steps),
            "Expected Results": "\n".join(results),
            "Blocking Bugs": "\n".join(blockers) if blockers else "None"
        })
    
    return extracted_data