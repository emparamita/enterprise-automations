# Universal Jira Hierarchical Extractor

An enterprise-grade automation tool designed to extract parent-child relationships from Jira (e.g., Enhancements to Tests, Epics to Stories) and export them into formatted reports.

## Features
* **Dual Export Modes:** Switch between formatted **Excel** (for reporting) and high-speed **CSV** (for massive historical data).
* **Memory-Efficient:** Uses Python generators to handle thousands of rows without crashing local machines.
* **Fully Configurable:** No code changes required to switch projects, issue types, or date ranges.
* **Network Optimized:** Designed to work within restricted customer networks (handles SSL verification and corporate proxies).

---

## Setup Instructions

### 1. Environment Setup (Conda)
Ensure you are using the dedicated Conda environment to avoid library conflicts:

```bash
# Create and activate environment
conda create -n jira_automation python=3.10 -y
conda activate jira_automation

# Install dependencies
conda install -c conda-forge jira pandas openpyxl python-dotenv -y
```

### 2. Configuration (.env)
Create a `.env` file in the root directory. This file is **private** and contains your credentials and extraction criteria.

```text
# CONNECTION
JIRA_SERVER=[https://jira.comp](https://jira.comp).<company>.com
JIRA_TOKEN=your_personal_access_token

# EXTRACTION CRITERIA
PROJECT_KEY=PROJ
PARENT_TYPE=Enhancement
CHILD_TYPE=Test
LINK_FIELD=Epic Link

# DATE RANGE (Leave empty for 'All Time')
START_DATE=2026-01-01
END_DATE=

# PERFORMANCE & FORMAT
EXPORT_FORMAT=EXCEL  # Options: EXCEL or CSV
API_BLOCK_SIZE=50
STEPS_CUSTOM_FIELD=customfield_12345
```

---

## Usage Guide for Customers

### Which Export Format should I choose?


| Format | Best For... | Features |
| :--- | :--- | :--- |
| **EXCEL** | Weekly Status Reports | Pre-formatted, text-wrapped, and ready for presentation. |
| **CSV** | Historical Audits | Extremely fast. Use this if you are extracting >10,000 rows to prevent memory lag. |

### Running the App
1.  Update the `START_DATE` and `END_DATE` in `.env`.
2.  Open your terminal/shell and run:
    ```bash
    python main.py
    ```
3.  Find your report in the `/exports` folder. The filename will follow the pattern:
    `jira_exports_YYYYMMDD_YYYYMMDD.xlsx` (or `.csv`)

---

## Project Structure
* `main.py`: The orchestrator. Handles file naming, directory creation, and the export engine toggle.
* `query.py`: The logic engine. Uses pagination to ensure no data is missed from Jira.
* `config.py`: The security layer. Safely loads environment variables.
* `exports/`: (Auto-generated) Stores all your generated reports.

---

## Security Note
This app is configured with `verify=False` to bypass internal SSL certificate issues common in customer networks. Ensure your **Personal Access Token (PAT)** is kept secure and never shared.
```

---

### Final Project Structure
Your folder should now look like this:
```text
jira_project/
├── .env
├── .gitignore
├── config.py
├── query.py
├── main.py
├── README.md
└── exports/ (auto-generated)
```