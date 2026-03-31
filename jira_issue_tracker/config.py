import os
import urllib3
from jira import JIRA
from dotenv import load_dotenv

load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JiraConfig:
    """Secure configuration loader for Generic Jira Extraction."""
    SERVER = os.getenv("JIRA_SERVER")
    TOKEN = os.getenv("JIRA_TOKEN")
    
    # Generic Inputs
    PROJECT = os.getenv("PROJECT_KEY")
    PARENT_TYPE = os.getenv("PARENT_TYPE")
    CHILD_TYPE = os.getenv("CHILD_TYPE")
    LINK_FIELD = os.getenv("LINK_FIELD", "Epic Link")
    
    # Date Range
    START_DATE = os.getenv("START_DATE")
    END_DATE = os.getenv("END_DATE")

    # Field IDs
    STEPS_FIELD = os.getenv("STEPS_CUSTOM_FIELD")

    @classmethod
    def get_client(cls):
        if not cls.TOKEN or not cls.SERVER:
            raise ValueError("Credentials missing in .env file.")
        try:
            return JIRA(
                server=cls.SERVER,
                token_auth=cls.TOKEN,
                options={'verify': False}
            )
        except Exception as e:
            print(f"Connection Error: {e}")
            return None