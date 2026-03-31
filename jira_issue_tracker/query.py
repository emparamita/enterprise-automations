def fetch_hierarchy_data(jira, config):
    """Generic hierarchical extractor using dynamic link fields."""
    
    # 1. Build Parent JQL
    parent_jql = f'project = "{config.PROJECT}" AND issuetype = "{config.PARENT_TYPE}"'
    if config.START_DATE:
        parent_jql += f' AND created >= "{config.START_DATE}"'
    if config.END_DATE:
        parent_jql += f' AND created <= "{config.END_DATE}"'
    parent_jql += ' ORDER BY created ASC'
    
    print(f"Searching for {config.PARENT_TYPE}s...")
    parents = jira.search_issues(parent_jql, maxResults=100)
    
    all_rows = []

    for parent in parents:
        # 2. Search for Children using the GENERIC LINK FIELD (e.g., "Epic Link" = PROJ-1)
        child_jql = (f'project = "{config.PROJECT}" AND issuetype = "{config.CHILD_TYPE}" '
                     f'AND "{config.LINK_FIELD}" = {parent.key}')
        
        children = jira.search_issues(child_jql)

        for child in children:
            # Extract Steps & Expected Results
            steps_data = getattr(child.fields, config.STEPS_FIELD, [])
            steps = [f"{i+1}. {s.get('step', '')}" for i, s in enumerate(steps_data)]
            results = [f"{i+1}. {s.get('result', '')}" for i, s in enumerate(steps_data)]

            # Extract Blockers (ID=Status)
            blockers = []
            if hasattr(child.fields, 'issuelinks'):
                for link in child.fields.issuelinks:
                    if hasattr(link, 'type') and link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                        bug = link.inwardIssue
                        blockers.append(f"{bug.key}={bug.fields.status.name}")

            # Universal Data Mapping
            all_rows.append({
                "parent_id": parent.key,
                "parent_desc": parent.fields.summary,
                "created_at": parent.fields.created[:10],
                "child_id": child.key,
                "child_desc": child.fields.summary,
                "child_steps": "\n".join(steps) if steps else "N/A",
                "expected_results": "\n".join(results) if results else "N/A",
                "child_status": child.fields.status.name,
                "blocked_by": "\n".join(blockers) if blockers else "None"
            })
    
    return all_rows