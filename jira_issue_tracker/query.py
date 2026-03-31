import requests
import urllib3
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_zephyr_details(issue_obj, config):
    unique_id = issue_obj.id 
    headers = {"Authorization": f"Bearer {config.TOKEN}"}
    
    steps_list, results_list = [], []
    status_str = "Unexecuted"

    # Set a strict 5-second timeout so the script doesn't hang forever
    timeout_val = 5 

    # 1. Fetch Steps
    step_url = f"{config.SERVER}/rest/zapi/latest/teststep/{unique_id}"
    try:
        # Added timeout=timeout_val
        res = requests.get(step_url, headers=headers, verify=False, timeout=timeout_val)
        if res.status_code == 200:
            data = res.json()
            steps_data = data.get('stepBeanCollection', [])
            for i, s in enumerate(steps_data):
                steps_list.append(f"{i+1}. {s.get('step', '')}")
                results_list.append(f"{i+1}. {s.get('result', '')}")
    except Exception as e:
        print(f"      ⚠️ Step Timeout/Error for {issue_obj.key}: {e}")

    # 2. Fetch Execution
    exec_url = f"{config.SERVER}/rest/zapi/latest/execution?issueId={unique_id}"
    try:
        res = requests.get(exec_url, headers=headers, verify=False, timeout=timeout_val)
        if res.status_code == 200:
            executions = res.json().get('executions', [])
            if executions:
                status_str = executions[0].get('statusName', 'Unknown')
    except Exception as e:
        print(f"      ⚠️ Exec Timeout/Error for {issue_obj.key}: {e}")

    return "\n".join(steps_list), "\n".join(results_list), status_str

def stream_hierarchy_data(jira, config):
    parent_jql = f'project = "{config.PROJECT}" AND issuetype = "{config.PARENT_TYPE}"'
    
    print(f"🔍 Searching Parents: {parent_jql}")
    parents = list(get_paged_issues(jira, parent_jql, config.API_BLOCK_SIZE))
    print(f"📊 Found {len(parents)} Parent issues.")

    for parent in parents:
        print(f"  📂 Processing Parent: {parent.key}")
        child_jql = (f'project = "{config.PROJECT}" AND issuetype = "{config.CHILD_TYPE}" '
                     f'AND "{config.LINK_FIELD}" = {parent.key}')
        
        # We wrap this in a list to ensure it's not an empty generator hang
        children = list(get_paged_issues(jira, child_jql, config.API_BLOCK_SIZE))
        
        for child in children:
            print(f"    📄 Fetching Child: {child.key} (ID: {child.id})", end='\r')
            sys.stdout.flush() # Force print to screen immediately
            
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

            # Blocker logic stays the same...
            yield row
