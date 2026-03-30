
# Jira Test Case Extractor

A Python-based automation tool to extract Test Cases and related Blocking Bugs from Jira into a formatted Excel report.

## Setup Instructions

### 1. Environment Creation
Ensure you have **Conda** installed. Run the following commands to set up the isolated environment:

```bash
# Create the environment
conda create -n jira_automation python=3.10 -y

# Activate the environment
conda activate jira_automation

# Install dependencies
conda install -c conda-forge jira pandas openpyxl python-dotenv -y
```

### 2. Configuration (.env)
The project uses a `.env` file to manage sensitive credentials securely. This file is ignored by Git.

1. Create a new file named `.env` in the root directory.
2. Copy the following template and populate it with your details:

```text
JIRA_SERVER=[https://jira.comp](https://jira.comp).<company_name>.com
JIRA_TOKEN=your_personal_access_token_here
PROJECT_KEY=PROJ
```

> **Note:** To generate a PAT, go to your Jira Profile > Personal Access Tokens.

### 3. Usage
Once the environment is active and the `.env` file is populated, run the extractor:

```bash
python main.py
```

The formatted Excel report will be generated in the root folder as `Jira_Extract_YYYY-MM-DD.xlsx`.

## 🛠 Project Structure
* `main.py`: Entry point for the extraction process.
* `query.py`: Contains JQL logic and data parsing.
* `config.py`: Securely loads credentials and initializes the Jira client.
* `.env`: (Private) Stores your server URL and Access Token.
```

---

### Pro-Tip: The `.env.example` File
As we discussed, to make the "Populate .env" step even easier for others, you should create a file named `.env.example` and commit it to your repository. 

**Run this command in your terminal to create it quickly:**
```bash
echo "JIRA_SERVER=https://jira.yourcompany.com\nJIRA_TOKEN=PASTE_TOKEN_HERE\nPROJECT_KEY=PROJ" > .env.example
```

This way, a new user can just run `cp .env.example .env` and then fill in their details.
