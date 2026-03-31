import os
import urllib3
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JiraConfig:
    SERVER = os.getenv("JIRA_SERVER")
    TOKEN = os.getenv("JIRA_TOKEN")
    PROJECT = os.getenv("PROJECT_KEY")
    PARENT_TYPE = os.getenv("PARENT_TYPE")
    CHILD_TYPE = os.getenv("CHILD_TYPE")
    LINK_FIELD = os.getenv("LINK_FIELD", "Epic Link")
    START_DATE = os.getenv("START_DATE")
    END_DATE = os.getenv("END_DATE")
    STEPS_FIELD = os.getenv("STEPS_CUSTOM_FIELD")
    
    # Performance & Format
    API_BLOCK_SIZE = int(os.getenv("API_BLOCK_SIZE", 50))
    EXPORT_FORMAT = os.getenv("EXPORT_FORMAT", "EXCEL").upper()

    @classmethod
    def get_client(cls):
        return JIRA(server=cls.SERVER, token_auth=cls.TOKEN, options={'verify': False})