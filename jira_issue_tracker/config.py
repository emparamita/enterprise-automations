import os
import urllib3
from jira import JIRA
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Suppress SSL warnings for internal network usage
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JiraConfig:
    """Secure configuration loader for Jira."""
    SERVER = os.getenv("JIRA_SERVER")
    TOKEN = os.getenv("JIRA_TOKEN")
    PROJECT = os.getenv("PROJECT_KEY")

    @classmethod
    def get_client(cls):
        """Initializes and returns a secure JIRA client instance."""
        if not cls.TOKEN:
            raise ValueError("JIRA_TOKEN not found! Check your .env file.")
            
        try:
            return JIRA(
                server=cls.SERVER,
                token_auth=cls.TOKEN,
                options={'verify': False}
            )
        except Exception as e:
            print(f"Failed to connect to Jira at {cls.SERVER}: {e}")
            return None