import requests
import logging
import urllib3

logger = logging.getLogger(__name__)

def fetch_zephyr_data(issue_id, issue_key, config):
    """Extracts Test Steps and Execution Status via ZAPI."""
    headers = {"Authorization": f"Bearer {config.TOKEN}"}
    steps, results, status = [], [], "Unexecuted"
    
    try:
        # Fetch Steps
        res = requests.get(f"{config.SERVER}/rest/zapi/latest/teststep/{issue_id}", 
                           headers=headers, verify=False, timeout=10)
        if res.status_code == 200:
            data = res.json().get('stepBeanCollection', [])
            steps = [f"{i+1}. {s.get('step','')}" for i, s in enumerate(data)]
            results = [f"{i+1}. {s.get('result','')}" for i, s in enumerate(data)]
        
        # Fetch Execution
        res_exec = requests.get(f"{config.SERVER}/rest/zapi/latest/execution?issueId={issue_id}", 
                                headers=headers, verify=False, timeout=10)
        if res_exec.status_code == 200:
            execs = res_exec.json().get('executions', [])
            if execs:
                status = execs[0].get('statusName', 'Unknown')
    except Exception as e:
        logger.error(f"ZAPI Error for {issue_key}: {e}")
        
    return "\n".join(steps), "\n".join(results), status

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
    """Main logic to extract entities, linked tests, and blockers."""
    jql = f'project = "{config.PROJECT}" AND issuetype = "{config.ENTITY_TYPE}"'
    if config.START_DATE: jql += f' AND created >= "{config.START_DATE}"'
    if config.END_DATE: jql += f' AND created <= "{config.END_DATE}"'
    
    logger.info(f"Executing Master JQL: {jql}")
    
    entities, tests, blockers = [], [], []
    
    for issue in get_paged_issues(jira, jql, config.API_BLOCK_SIZE):
        logger.info(f"Processing: {issue.key}")
        
        item_data = {
            "issue_id": issue.id,
            "issue_key": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "inwards": [],
            "outwards": []
        }
        
        if hasattr(issue.fields, 'issuelinks'):
            for link in issue.fields.issuelinks:
                # Process OUTWARD Links
                if hasattr(link, 'outwardIssue'):
                    out = link.outwardIssue
                    out_data = {"id": out.id, "key": out.key, "name": out.fields.issuetype.name, "status": out.fields.status.name}
                    item_data["outwards"].append(out_data)
                    
                    if out.fields.issuetype.name == 'Test':
                        s, r, st = fetch_zephyr_data(out.id, out.key, config)
                        tests.append({"parent_key": issue.key, "test_key": out.key, "summary": out.fields.summary, "steps": s, "results": r, "execution_status": st})
                    
                    if link.type.name == 'Blocks':
                        blockers.append({"source_key": issue.key, "target_key": out.key, "type": "Outward-Blocks", "status": out.fields.status.name})

                # Process INWARD Links
                if hasattr(link, 'inwardIssue'):
                    inv = link.inwardIssue
                    inv_data = {"id": inv.id, "key": inv.key, "name": inv.fields.issuetype.name, "status": inv.fields.status.name}
                    item_data["inwards"].append(inv_data)
                    
                    if inv.fields.issuetype.name == 'Test':
                        s, r, st = fetch_zephyr_data(inv.id, inv.key, config)
                        tests.append({"parent_key": issue.key, "test_key": inv.key, "summary": inv.fields.summary, "steps": s, "results": r, "execution_status": st})

                    if link.type.name == 'Blocks':
                        blockers.append({"source_key": inv.key, "target_key": issue.key, "type": "Inward-Blocks", "status": inv.fields.status.name})

        entities.append(item_data)
        
    return entities, tests, blockers