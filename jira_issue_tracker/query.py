import requests
import urllib3

# Suppress SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_paged_issues(jira, jql, block_size):
    """Standard Jira Pagination."""
    start_at = 0
    while True:
        issues = jira.search_issues(jql, startAt=start_at, maxResults=block_size)
        if not issues: break
        for issue in issues:
            yield issue
        if len(issues) < block_size: break
        start_at += block_size

def fetch_zephyr_details(issue_obj, config):
    """
    Fetches steps from ZAPI using numeric Issue ID.
    Maps 'stepBeanCollection' to child_steps and expected_results.
    """
    unique_id = issue_obj.id 
    headers = {"Authorization": f"Bearer {config.TOKEN}"}
    
    steps_list = []
    results_list = []
    status_str = "Unexecuted"

    # 1. Fetch Steps
    step_url = f"{config.SERVER}/rest/zapi/latest/teststep/{unique_id}"
    try:
        res = requests.get(step_url, headers=headers, verify=False, timeout=10)
        if res.status_code == 200:
            data = res.json()
            steps_data = data.get('stepBeanCollection', [])
            for i, s in enumerate(steps_data):
                steps_list.append(f"{i+1}. {s.get('step', '')}")
                results_list.append(f"{i+1}. {s.get('result', '')}")
    except Exception:
        pass

    # 2. Fetch Latest Execution for Blockers/Status
    exec_url = f"{config.SERVER}/rest/zapi/latest/execution?issueId={unique_id}"
    blockers = []
    try:
        res = requests.get(exec_url, headers=headers, verify=False, timeout=10)
        if res.status_code == 200:
            executions = res.json().get('executions', [])
            if executions:
                status_str = executions[0].get('statusName', 'Unknown')
                # Note: If Zephyr stores blockers in the execution, extract here.
                # Otherwise, standard issueLinks are used in the stream logic.
    except Exception:
        pass

    return "\n".join(steps_list), "\n".join(results_list), status_str

def stream_hierarchy_data(jira, config):
    """Yields rows using the original requested column structure."""
    parent_jql = f'project = "{config.PROJECT}" AND issuetype = "{config.PARENT_TYPE}"'
    if config.START_DATE: parent_jql += f' AND created >= "{config.START_DATE}"'
    if config.END_DATE: parent_jql += f' AND created <= "{config.END_DATE}"'
    
    for parent in get_paged_issues(jira, parent_jql, config.API_BLOCK_SIZE):
        child_jql = (f'project = "{config.PROJECT}" AND issuetype = "{config.CHILD_TYPE}" '
                     f'AND "{config.LINK_FIELD}" = {parent.key}')
        
        for child in get_paged_issues(jira, child_jql, config.API_BLOCK_SIZE):
            # 1. Basic Metadata
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

            # 2. Zephyr Enrichment
            if child.fields.issuetype.name == 'Test':
                z_steps, z_results, z_status = fetch_zephyr_details(child, config)
                row["child_steps"] = z_steps
                row["expected_results"] = z_results
                # Overwrite status with Zephyr execution status if available
                if z_status != "Unexecuted":
                    row["child_status"] = z_status

            # 3. Standard Blocker Extraction (from Jira Links)
            blocker_list = []
            if hasattr(child.fields, 'issuelinks'):
                for link in child.fields.issuelinks:
                    if hasattr(link, 'type') and link.type.name == 'Blocks':
                        if hasattr(link, 'inwardIssue'):
                            bug = link.inwardIssue
                            blocker_list.append(f"{bug.key}={bug.fields.status.name}")
            
            if blocker_list:
                row["blocked_by"] = "\n".join(blocker_list)

            yield row