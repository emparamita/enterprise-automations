def get_paged_issues(jira, jql, block_size):
    start_at = 0
    while True:
        issues = jira.search_issues(jql, startAt=start_at, maxResults=block_size)
        if not issues: break
        for issue in issues:
            yield issue
        if len(issues) < block_size: break
        start_at += block_size

def stream_hierarchy_data(jira, config):
    parent_jql = f'project = "{config.PROJECT}" AND issuetype = "{config.PARENT_TYPE}"'
    if config.START_DATE: parent_jql += f' AND created >= "{config.START_DATE}"'
    if config.END_DATE: parent_jql += f' AND created <= "{config.END_DATE}"'
    
    for parent in get_paged_issues(jira, parent_jql, config.API_BLOCK_SIZE):
        child_jql = (f'project = "{config.PROJECT}" AND issuetype = "{config.CHILD_TYPE}" '
                     f'AND "{config.LINK_FIELD}" = {parent.key}')
        
        for child in get_paged_issues(jira, child_jql, config.API_BLOCK_SIZE):
            steps_data = getattr(child.fields, config.STEPS_FIELD, [])
            steps = [f"{i+1}. {s.get('step', '')}" for i, s in enumerate(steps_data)]
            res = [f"{i+1}. {s.get('result', '')}" for i, s in enumerate(steps_data)]

            blockers = []
            if hasattr(child.fields, 'issuelinks'):
                for link in child.fields.issuelinks:
                    if hasattr(link, 'type') and link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                        b = link.inwardIssue
                        blockers.append(f"{b.key}={b.fields.status.name}")

            yield {
                "parent_id": parent.key,
                "parent_desc": parent.fields.summary,
                "created_at": parent.fields.created[:10],
                "child_id": child.key,
                "child_desc": child.fields.summary,
                "child_steps": "\n".join(steps),
                "expected_results": "\n".join(res),
                "child_status": child.fields.status.name,
                "blocked_by": "\n".join(blockers) if blockers else "None"
            }