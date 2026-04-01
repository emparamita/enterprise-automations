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
    """Logic to branch between direct Test extraction and Parent-linked extraction."""
    jql = f'project = "{config.PROJECT}" AND issuetype = "{config.ENTITY_TYPE}"'
    if config.START_DATE: jql += f' AND created >= "{config.START_DATE}"'
    if config.END_DATE: jql += f' AND created <= "{config.END_DATE}"'
    
    logger.info(f"Executing JQL: {jql}")
    
    main_entities, linked_tests, blockers = [], [], []
    is_direct_test = (config.ENTITY_TYPE.lower() == 'test')

    for issue in get_paged_issues(jira, jql, config.API_BLOCK_SIZE):
        logger.info(f"Processing: {issue.key}")
        
        # Base entity data
        item_data = {
            "issue_id": issue.id,
            "issue_key": issue.key,
            "summary": issue.fields.summary,
            "status": issue.fields.status.name,
            "created": issue.fields.created[:10]
        }

        # --- BRANCH 1: DIRECT TEST EXTRACTION ---
        if is_direct_test:
            s, r, st = fetch_zephyr_data(issue.id, issue.key, config)
            item_data.update({"steps": s, "results": r, "execution_status": st})
            main_entities.append(item_data)
            
            # Check for blockers directly linked to this test
            if hasattr(issue.fields, 'issuelinks'):
                for link in issue.fields.issuelinks:
                    if link.type.name == 'Blocks' and hasattr(link, 'inwardIssue'):
                        bug = link.inwardIssue
                        blockers.append({
                            "blocked_test": issue.key,
                            "bug_key": bug.key,
                            "bug_summary": bug.fields.summary,
                            "bug_status": bug.fields.status.name
                        })

        # --- BRANCH 2: PARENT ENTITY EXTRACTION (Enhancement, etc.) ---
        else:
            main_entities.append(item_data)
            if hasattr(issue.fields, 'issuelinks'):
                for link in issue.fields.issuelinks:
                    linked = getattr(link, 'outwardIssue', getattr(link, 'inwardIssue', None))
                    if not linked: continue
                    
                    # Extract linked Tests
                    if linked.fields.issuetype.name == 'Test':
                        s, r, st = fetch_zephyr_data(linked.id, linked.key, config)
                        linked_tests.append({
                            "parent_key": issue.key,
                            "test_key": linked.key,
                            "summary": linked.fields.summary,
                            "steps": s, 
                            "results": r, 
                            "execution_status": st
                        })
                    
                    # Extract linked Blockers
                    if link.type.name == 'Blocks':
                        source = issue.key if hasattr(link, 'outwardIssue') else linked.key
                        target = linked.key if hasattr(link, 'outwardIssue') else issue.key
                        blockers.append({
                            "source": source,
                            "target": target,
                            "status": linked.fields.status.name,
                            "summary": linked.fields.summary
                        })

    return main_entities, linked_tests, blockers