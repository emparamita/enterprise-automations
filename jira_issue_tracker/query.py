import requests
import logging
import urllib3

logger = logging.getLogger(__name__)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_zephyr_data(issue_id, issue_key, config):
    """
    Extracts Test Steps and the most recent execution details.
    Traverses the status lookup map for the displayName.
    """
    headers = {"Authorization": f"Bearer {config.TOKEN}"}
    steps, results = [], []
    
    # Execution default values
    exec_status = "Unexecuted"
    executed_by = "N/A"
    executed_on = "N/A"
    
    try:
        # 1. Fetch Test Steps
        res_steps = requests.get(f"{config.SERVER}/rest/zapi/latest/teststep/{issue_id}", 
                                 headers=headers, verify=False, timeout=10)
        if res_steps.status_code == 200:
            data = res_steps.json().get('stepBeanCollection', [])
            steps = [f"{i+1}. {s.get('step','')}" for i, s in enumerate(data)]
            results = [f"{i+1}. {s.get('result','')}" for i, s in enumerate(data)]
        
        # 2. Fetch Executions Array and Status Map
        res_exec = requests.get(f"{config.SERVER}/rest/zapi/latest/execution?issueId={issue_id}", 
                                headers=headers, verify=False, timeout=10)
        
        if res_exec.status_code == 200:
            payload = res_exec.json()
            status_lookup = payload.get('status', {}) # The Map: {"1": {"name": "Pass"}}
            executions = payload.get('executions', []) # The Array
            
            if isinstance(executions, list) and len(executions) > 0:
                # Zephyr returns the most recent execution at index 0
                latest = executions[0]
                
                # Get Status Display Name via Lookup
                status_id = str(latest.get('executionStatusId', '-1'))
                status_obj = status_lookup.get(status_id)
                if status_obj:
                    exec_status = status_obj.get('name', 'Unknown')
                
                # Get User and Timestamp
                executed_by = latest.get('executedByDisplay', latest.get('executedBy', 'Unknown'))
                executed_on = latest.get('executedOn', 'N/A')
                
    except Exception as e:
        logger.error(f"ZAPI Error for {issue_key}: {e}")
        
    return "\n".join(steps), "\n".join(results), exec_status, executed_by, executed_on

def get_paged_issues(jira, jql, block_size):
    start_at = 0
    while True:
        issues = jira.search_issues(jql, startAt=start_at, maxResults=block_size)
        if not issues: break
        for issue in issues:
            yield issue
        if len(issues) < block_size: break
        start_at += block_size

def process_entities(jira, config):
    """Processes Entities with support for Test-specific execution fields."""
    jql = f'project = "{config.PROJECT}" AND issuetype = "{config.ENTITY_TYPE}"'
    if config.START_DATE: jql += f' AND created >= "{config.START_DATE}"'
    if config.END_DATE: jql += f' AND created <= "{config.END_DATE}"'
    
    logger.info(f"Executing JQL: {jql}")
    
    main_entities, linked_tests, blockers = [], [], []
    is_direct_test = (config.ENTITY_TYPE.lower() == 'test')

    for issue in get_paged_issues(jira, jql, config.API_BLOCK_SIZE):
        logger.info(f"Processing: {issue.key}")
        
        # Find Parent for traceability (if applicable)
        parent_key = "N/A"
        if hasattr(issue.fields, 'issuelinks'):
            for link in issue.fields.issuelinks:
                linked = getattr(link, 'outwardIssue', getattr(link, 'inwardIssue', None))
                if linked and linked.fields.issuetype.name != 'Test':
                    parent_key = linked.key
                    break

        if is_direct_test:
            s, r, stat, by, on = fetch_zephyr_data(issue.id, issue.key, config)
            row = {
                "parent_id": parent_key,
                "issue_key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "created": issue.fields.created[:10],
                "child_steps": s,
                "last_executed_by": by,
                "last_execution_timestamp": on,
                "last_execution_status": stat
            }
            main_entities.append(row)
            
            # Direct Blockers
            if hasattr(issue.fields, 'issuelinks'):
                for link in issue.fields.issuelinks:
                    if link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                        bug = link.inwardIssue
                        blockers.append({
                            "test_key": issue.key,
                            "bug_key": bug.key,
                            "bug_status": bug.fields.status.name
                        })
        else:
            # Standard Entity Logic (Enhancement, etc.)
            main_entities.append({
                "issue_id": issue.id,
                "issue_key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
                "created": issue.fields.created[:10]
            })
            
            # Linked Tests for non-Test entity types
            if hasattr(issue.fields, 'issuelinks'):
                for link in issue.fields.issuelinks:
                    linked = getattr(link, 'outwardIssue', getattr(link, 'inwardIssue', None))
                    if linked and linked.fields.issuetype.name == 'Test':
                        s, r, stat, by, on = fetch_zephyr_data(linked.id, linked.key, config)
                        linked_tests.append({
                            "parent_id": issue.key,
                            "test_key": linked.key,
                            "summary": linked.fields.summary,
                            "child_steps": s,
                            "last_executed_by": by,
                            "last_execution_timestamp": on,
                            "last_execution_status": stat
                        })
                    
                    if link.type.name == 'Blocks':
                        blockers.append({
                            "source": issue.key,
                            "target": linked.key,
                            "status": linked.fields.status.name
                        })

    return main_entities, linked_tests, blockers