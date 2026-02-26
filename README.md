# 🏦 Credit Suvidha Portal

A secure fintech application built for credit assessment, loan workflows, and financial accessibility.

## 🚀 Overview
**Credit Suvidha Portal** is a comprehensive fintech solution designed to streamline the loan application process and manage credit workflows securely. By integrating conversational AI via WhatsApp and web-based dashboards, the platform makes financial services more accessible while automating lead generation and user data processing.

## ✨ Features
* **WhatsApp Bot Integration (`whatsapp_bot.py`):** Automates interactions with users, allowing them to apply for credit, check status, or submit data directly via WhatsApp.
* **Lead Generation & Management:** Automatically captures and processes daily leads (`daily_leads/`) to keep the sales pipeline active and organized.
* **Financial Data Tracking:** Handles and analyzes master profit sheets and business metrics seamlessly.
* **Web Dashboard (`templates/`):** A frontend interface built with HTML to manage workflows, assess credit, and view application statuses.
* **Lightning-Fast Dependency Management:** Managed using `uv` and `pyproject.toml` for a rapid, reliable Python development environment.

## 🛠️ Tech Stack
* **Backend:** Python (FastAPI/Flask/Django depending on your main setup)
* **Frontend:** HTML & Jinja2 Templates
* **Package Management:** `uv` (`pyproject.toml`, `uv.lock`)
* **Integrations:** WhatsApp API (for conversational workflows)

## 📁 Project Structure
```text
credit-suvidha-portal/
├── User_Data_Bot/             # Core logic for extracting and managing user data via bot
├── daily_leads/               # Output directory/logic for daily credit leads
├── templates/                 # HTML templates for the web portal
├── main.py                    # Main application entry point
├── whatsapp_bot.py            # WhatsApp API integration and chatbot logic
├── MASTER_PROFIT_SHEET.xlsx   # Financial tracking and reporting sheet
├── pyproject.toml             # Python project metadata and dependencies
└── uv.lock                    # Locked dependencies for deterministic builds

```
💻 Local Setup Instructions
1. Clone the repository:

Bash
git clone [https://github.com/manan-dev-ai/credit-suvidha-portal.git](https://github.com/manan-dev-ai/credit-suvidha-portal.git)
cd credit-suvidha-portal

2. Install dependencies:
This project uses uv for fast dependency management. If you don't have it installed, run pip install uv first.

Bash
uv sync
(Alternatively, you can install via pip install -r requirements.txt if you export your dependencies).

3. Set up Environment Variables:
Create a .env file in the root directory and add your necessary API keys (e.g., WhatsApp API tokens, Database URIs).

4. Run the Application:
To start the main web server:

Bash
python main.py
To run the WhatsApp bot service independently (if separated):

Bash
python whatsapp_bot.py
🛡️ Security & Privacy
This application handles sensitive financial and user data. Please ensure that all API keys, webhook secrets, and .env files are added to your .gitignore and never committed to the public repository.

🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
