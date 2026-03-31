import requests
import logging
import urllib3

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_paged_issues(jira, jql, block_size):
    start_at = 0
    logger.debug(f"Executing JQL: {jql}")
    while True:
        try:
            issues = jira.search_issues(jql, startAt=start_at, maxResults=block_size)
            if not issues:
                break
            for issue in issues:
                yield issue
            if len(issues) < block_size:
                break
            start_at += block_size
        except Exception as e:
            logger.error(f"Pagination Error: {e}")
            break

def fetch_zephyr_details(issue_obj, config):
    """Fetches steps from ZAPI using numeric Issue ID."""
    unique_id = issue_obj.id 
    headers = {"Authorization": f"Bearer {config.TOKEN}"}
    steps_list, results_list = [], []
    status_str = "Unexecuted"

    # Step Fetching
    step_url = f"{config.SERVER}/rest/zapi/latest/teststep/{unique_id}"
    try:
        res = requests.get(step_url, headers=headers, verify=False, timeout=10)
        if res.status_code == 200:
            data = res.json()
            steps_data = data.get('stepBeanCollection', [])
            for i, s in enumerate(steps_data):
                steps_list.append(f"{i+1}. {s.get('step', '')}")
                results_list.append(f"{i+1}. {s.get('result', '')}")
    except Exception as e:
        logger.error(f"ZAPI Error for {issue_obj.key}: {e}")

    # Execution Fetching
    exec_url = f"{config.SERVER}/rest/zapi/latest/execution?issueId={unique_id}"
    try:
        res = requests.get(exec_url, headers=headers, verify=False, timeout=10)
        if res.status_code == 200:
            executions = res.json().get('executions', [])
            if executions:
                status_str = executions[0].get('statusName', 'Unknown')
    except Exception:
        pass

    return "\n".join(steps_list), "\n".join(results_list), status_str

def stream_hierarchy_data(jira, config):
    """Yields rows with date filtering and ZAPI enrichment."""
    # 1. Build Parent JQL with Date Logic
    parent_jql = f'project = "{config.PROJECT}" AND issuetype = "{config.PARENT_TYPE}"'
    
    if config.START_DATE:
        parent_jql += f' AND created >= "{config.START_DATE}"'
    if config.END_DATE:
        parent_jql += f' AND created <= "{config.END_DATE}"'
    
    logger.info(f"Streaming Parents with JQL: {parent_jql}")
    
    for parent in get_paged_issues(jira, parent_jql, config.API_BLOCK_SIZE):
        logger.info(f"Processing Parent: {parent.key}")
        
        # 2. Build Child JQL (Using 'parent' instead of 'Epic Link' as suspected)
        # Change 'parent' back to 'Epic Link' in .env if your instance is older
        child_jql = (f'project = "{config.PROJECT}" AND issuetype = "{config.CHILD_TYPE}" '
                     f'AND "{config.LINK_FIELD}" = {parent.key}')
        
        for child in get_paged_issues(jira, child_jql, config.API_BLOCK_SIZE):
            row = {
                "parent_id": parent.key,
                "parent_desc": parent.fields.summary,
                "created_at": parent.fields.created[:10],
                "child_id": child.key,
                "child_desc": child.fields.summary,
                "child_steps": "N/A",
                "expected_results": "N/A",
                "child_status": child.fields.status.name,
                "blocked_by": "None"
            }

            if child.fields.issuetype.name == 'Test':
                z_steps, z_results, z_status = fetch_zephyr_details(child, config)
                row["child_steps"] = z_steps
                row["expected_results"] = z_results
                if z_status != "Unexecuted":
                    row["child_status"] = z_status

            # Standard Blocker Link check
            if hasattr(child.fields, 'issuelinks'):
                blockers = []
                for link in child.fields.issuelinks:
                    if hasattr(link, 'type') and link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                        b = link.inwardIssue
                        blockers.append(f"{b.key}={b.fields.status.name}")
                if blockers:
                    row["blocked_by"] = "\n".join(blockers)

            yield row