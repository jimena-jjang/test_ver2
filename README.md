# Product Management System (Ver.2)

This project is an evolved version of the Product Management System, built with Streamlit and Google Sheets.

## 터미널 실행 명령어
- streamlit run app.py

## Features
- **Roadmap View**: Gantt chart visualization with complex sorting (User -> Squad -> Order).
- **Analysis Report**: Workload analysis, Start date prediction, Swap scenarios, Issue tracking.
- **Data Ops**: Direct data editing and snapshot saving to Google Sheets.
- **Automated Testing**: Pytest integration for core logic.

## Project Structure
```
test_ver2/
├── app.py                # Main Streamlit Application
├── logic.py              # Core Business Logic (Sorting, Prediction, etc.)
├── gsheet_handler.py     # Google Sheets connection & Snapshot logic
├── views/                # UI Components
│   ├── roadmap.py
│   ├── analysis.py
│   └── data_ops.py
├── tests/                # Unit Tests
│   └── test_logic.py
├── requirements.txt      # Dependencies
├── vercel.json           # Vercel Deployment Config
└── .github/              # CI/CD Workflows
```

## Setup & Run Locally

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Sheets Configuration**
   - Create a `.streamlit/secrets.toml` file or set environment variables.
   - Required format in `secrets.toml`:
     ```toml
     [gcp_service_account]
     type = "service_account"
     project_id = "..."
     private_key_id = "..."
     private_key = "..."
     client_email = "..."
     client_id = "..."
     auth_uri = "..."
     token_uri = "..."
     auth_provider_x509_cert_url = "..."
     client_x509_cert_url = "..."
     
     G_SHEET_ID = "your-google-sheet-id"
     ```

3. **Run Application**
   ```bash
   streamlit run app.py
   ```

## Testing
Run unit tests to verify logic:
```bash
python -m pytest tests/test_logic.py
```

## Deployment (Vercel)
1. Push this repository to GitHub.
2. Link the repository to a new project in Vercel.
3. Configure **Environment Variables** in Vercel settings (copy contents from `secrets.toml`).


