# Folio: CV and Cover Letter Studio

A small Flask app that drafts an ATS-friendly CV or a role-focused cover letter from profile details. Drafts use the OpenAI API and are returned to the browser; this demo does not store profile data.

## Run locally

1. Activate the project's virtual environment, or create one and install the dependencies:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your own OpenAI API key. Keep `.env` private; it is excluded by `.gitignore`.

   ```powershell
   Copy-Item .env.example .env
   ```

   Set `OPENAI_MODEL` in `.env` to a model available to your account if the default is unavailable.

3. Start the app and open `http://127.0.0.1:5000`:

   ```powershell
   python app.py
   ```

Without an API key, the interface still loads, but generation returns a setup message. API usage may incur provider charges. Never commit or share your API key.

PDF export uses jsPDF from jsDelivr, so the browser needs an internet connection when loading the page. Drafts are formatted and exported in the browser; they are not uploaded for PDF conversion.

## Verify

Run the local tests without calling the external AI service:

```powershell
python -m unittest discover -v
```

## Current scope

- Profile form with example data
- AI-generated plain-text CV and cover letter
- Draft copy, text download, and paginated PDF export
- No accounts, persistence, or production deployment configuration
