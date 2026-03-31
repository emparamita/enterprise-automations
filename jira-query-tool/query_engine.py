def get_paged_issues(jira, query, block_size):
    """Generic pagination for any JQL."""
    start_at = 0
    while True:
        issues = jira.search_issues(query, startAt=start_at, maxResults=block_size)
        if not issues: break
        for issue in issues:
            yield issue
        if len(issues) < block_size: break
        start_at += block_size

def extract_issue_data(issue, fields_to_extract):
    """Dynamically extracts fields based on the .env list."""
    data = {}
    for field in fields_to_extract:
        # Handle 'key' which is a top-level attribute, not a field
        if field == "key":
            data[field] = issue.key
        else:
            # Safely get field value (handles nested objects like status/priority)
            val = getattr(issue.fields, field, None)
            if hasattr(val, 'name'):
                data[field] = val.name
            elif hasattr(val, 'displayName'):
                data[field] = val.displayName
            else:
                data[field] = str(val) if val is not None else ""
    return data