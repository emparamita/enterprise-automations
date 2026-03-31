import os
import urllib3
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JiraConfig:
    SERVER = os.getenv("JIRA_SERVER")
    TOKEN = os.getenv("JIRA_TOKEN")
    QUERY = os.getenv("JIRA_QUERY")
    
    # Convert comma-separated string to a list
    FIELDS = [f.strip() for f in os.getenv("EXTRACT_FIELDS", "key,summary").split(",")]
    
    BLOCK_SIZE = int(os.getenv("API_BLOCK_SIZE", 50))

    @classmethod
    def get_client(cls):
        return JIRA(server=cls.SERVER, token_auth=cls.TOKEN, options={'verify': False})