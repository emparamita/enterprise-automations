import os
import logging
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
    
    # Logging Config
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    LOG_FILE = os.getenv("LOG_FILE_NAME", "jira_extractor.log")
    
    # Performance & Export
    EXPORT_FORMAT = os.getenv("EXPORT_FORMAT", "EXCEL").upper()
    API_BLOCK_SIZE = int(os.getenv("API_BLOCK_SIZE", 50))

    @classmethod
    def setup_logging(cls):
        """Initializes logging based on .env settings."""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        handlers = [logging.StreamHandler()]
        
        if cls.LOG_TO_FILE:
            handlers.append(logging.FileHandler(cls.LOG_FILE))
            
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL, logging.INFO),
            format=log_format,
            handlers=handlers
        )

    @classmethod
    def get_client(cls):
        try:
            return JIRA(server=cls.SERVER, token_auth=cls.TOKEN, options={'verify': False})
        except Exception as e:
            logging.error(f"Failed to connect to Jira: {e}")
            return None