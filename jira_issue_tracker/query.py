def fetch_epic_hierarchy(jira, project_key, start_date, end_date):
    """
    1. Extracts Epics within a date range.
    2. Finds all Tests linked to those Epics.
    3. Parses test steps, status, and blockers.
    """
    # Step 1: Extract all Epics in the date range
    # Base JQL
    epic_jql = f'project = "{project_key}" AND issuetype = "Epic"'
    
    # Add date filters only if they exist
    if start_date:
        epic_jql += f' AND created >= "{start_date}"'
    if end_date:
        epic_jql += f' AND created <= "{end_date}"'
        
    epic_jql += ' ORDER BY created ASC'
    
    print(f"Searching for Epics: {epic_jql}")
    epics = jira.search_issues(epic_jql)
    
    all_rows = []

    for epic in epics:
        epic_id = epic.key
        epic_desc = epic.fields.summary
        epic_created = epic.fields.created[:10]

        # Step 2: Get all Tests belonging to THIS Epic
        # For Data Center, use 'Epic Link'. For Cloud, 'parent' is often used.
        test_jql = f'project = "{project_key}" AND issuetype = "Test" AND "Epic Link" = {epic_id}'
        tests = jira.search_issues(test_jql)

        if not tests:
            # Optional: Add the Epic even if it has no tests
            continue

        for test in tests:
            # a. Extract Test Steps & Expected Results
            steps_field = getattr(test.fields, 'customfield_12345', []) # Replace with your ID
            steps = [f"{i+1}. {s.get('step', '')}" for i, s in enumerate(steps_field)]
            results = [f"{i+1}. {s.get('result', '')}" for i, s in enumerate(steps_field)]

            # b. Extract Status
            test_status = test.fields.status.name

            # c. Extract Blocks ($.blockId + '=' + $.blockedStatus)
            blocked_by_list = []
            if hasattr(test.fields, 'issuelinks'):
                for link in test.fields.issuelinks:
                    if hasattr(link, 'type') and link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                        bug = link.inwardIssue
                        # Logic: ID=Status
                        blocked_by_list.append(f"{bug.key}={bug.fields.status.name}")

            # 3. Prepare row for XLSX
            all_rows.append({
                "epic_id": epic_id,
                "epic_desc": epic_desc,
                "created_at": epic_created,
                "test_id": test.key,
                "test_desc": test.fields.summary,
                "test_steps": "\n".join(steps),
                "expected_results": "\n".join(results),
                "test_status": test_status,
                "blocked_by": "\n".join(blocked_by_list) if blocked_by_list else "None"
            })
    
    return all_rows