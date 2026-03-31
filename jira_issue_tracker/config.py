import os
import logging
import urllib3
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Suppress SSL warnings for internal corporate Jira instances
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JiraConfig:
    # --- Connection Settings ---
    SERVER = os.getenv("JIRA_SERVER")
    TOKEN = os.getenv("JIRA_TOKEN")
    
    # --- Hierarchy & Query Criteria ---
    PROJECT = os.getenv("PROJECT_KEY")
    PARENT_TYPE = os.getenv("PARENT_TYPE")
    CHILD_TYPE = os.getenv("CHILD_TYPE")
    LINK_FIELD = os.getenv("LINK_FIELD", "Epic Link")
    
    # --- Date Filtering (The Restored Features) ---
    START_DATE = os.getenv("START_DATE")
    END_DATE = os.getenv("END_DATE")
    
    # --- Logging Configuration ---
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", "True").lower() == "true"
    LOG_FILE = os.getenv("LOG_FILE_NAME", "jira_extractor.log")
    
    # --- Performance & Export Settings ---
    EXPORT_FORMAT = os.getenv("EXPORT_FORMAT", "EXCEL").upper()
    API_BLOCK_SIZE = int(os.getenv("API_BLOCK_SIZE", 50))

    @classmethod
    def setup_logging(cls):
        """
        Configures the logging system based on .env settings.
        Provides a standard format: Timestamp - Module - Level - Message
        """
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        handlers = [logging.StreamHandler()]
        
        if cls.LOG_TO_FILE:
            handlers.append(logging.FileHandler(cls.LOG_FILE))
            
        logging.basicConfig(
            level=getattr(logging, cls.LOG_LEVEL, logging.INFO),
            format=log_format,
            handlers=handlers
        )
        
        # Suppress noisy logs from third-party libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("jira").setLevel(logging.WARNING)

    @classmethod
    def get_client(cls):
        """
        Returns an authenticated Jira client instance.
        """
        try:
            return JIRA(
                server=cls.SERVER, 
                token_auth=cls.TOKEN, 
                options={'verify': False}
            )
        except Exception as e:
            logging.error(f"Critical: Could not connect to Jira server. Error: {e}")
            return None