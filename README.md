# CV Anonymisation Pipeline

Automated pipeline that turns a consultant's CV into **two outputs**:

1. an **anonymised CV (PDF)** for the client: no name, contact details, age, employers, schools or hobbies;
2. an **internal register (Google Sheet)** with the real data, linked to the PDF by a consultant code (`CONS-XXXXXX`).

Built during the GRETA *Dev IA* training (November 2026). **n8n** is the engine, **Streamlit** is the front end.

> ⚠️ Use **fake CVs only**. Never send real candidate data to a free AI service.

---

## Architecture

```
Streamlit (Python)  ──POST /webhook/cv-upload──►  n8n  ──►  Groq (LLM)
   │  password gate                                │  ├─►  Gotenberg (HTML/Word → PDF)
   │                                               │  ├─►  Google Sheets (register)
   └──GET /webhook/consultants────────────────────►│  └─►  ./sorties (PDF files)
                                                   │
Client link ──GET /webhook/cv-anonyme?code=…──────►┘  (serves the anonymised PDF)
```

### Pipeline steps

| # | Step | Done by |
|---|------|---------|
| 1 | Receive the CV (PDF or Word) | n8n Webhook |
| 2 | Word → PDF conversion if needed | Gotenberg (LibreOffice) |
| 3 | Text extraction, stop if the PDF is scanned or empty | n8n |
| 4 | **AI ①**: text → structured JSON | Groq (`openai/gpt-oss-120b`) |
| 5 | Reduced payload without any identifying field | Code node |
| 6 | **AI ②**: neutral summary and rewritten missions | Groq |
| 7 | Consultant code, sectors instead of employers, school types | Code node |
| 8 | **RGPD leak check**: detect, redact, verify (no AI) | Code node |
| 9 | HTML template → PDF | Gotenberg (Chromium) |
| 10 | Save the PDF and append a row to the register | n8n + Google Sheets |

**Design principle:** the AI only does what needs language (summary, rewriting). Everything that must be reliable (codes, sector mapping, leak check) is deterministic code.

---

## Features

- Upload a CV from a web interface and get a consultant code, a link and the number of RGPD alerts caught.
- View the anonymised CVs.
- Search the consultant database (real data, behind a password).
- Webhooks protected by an API key (Header Auth).
- Clean error handling: a scanned CV returns a clear message (HTTP 422) instead of a server error.

---

## Tech stack

- **n8n** (self-hosted, Docker): workflow engine
- **Gotenberg**: document-to-PDF service
- **Groq**: free LLM API
- **Google Sheets**: consultant register
- **Streamlit** + `requests` + `pandas`: front end

---

## Repository structure

```
.
├── docker-compose.yml          # n8n + Gotenberg
├── workflows/                  # exported n8n workflows (no secrets)
│   ├── cv-anonymisation-api.json
│   ├── cv-download.json
│   └── consultants-list.json
├── streamlit-app/
│   ├── main.py                 # UI only
│   ├── auth.py                 # password gate
│   ├── n8n_client.py           # all HTTP calls to n8n
│   ├── config.py               # settings from .env
│   ├── requirements.txt
│   └── .env.example
├── sorties/                    # generated PDFs (git-ignored)
└── README.md
```

---

## Getting started

### 1. Start n8n and Gotenberg

```bash
docker compose up -d
```

Open <http://localhost:5678> and create the owner account.

### 2. Configure n8n

1. **Credentials**
   - *Groq*: your API key from [console.groq.com](https://console.groq.com)
   - *Google Sheets OAuth2*: create an OAuth client in Google Cloud Console (enable the Sheets and Drive APIs, add yourself as a test user)
   - *Header Auth* named `Streamlit API key`: header `X-API-Key`, value from `openssl rand -hex 24`
2. **Google Sheet** named `Registre CV` with these headers in row 1:
   `Code consultant · Date de traitement · Prénom · Nom · E-mail · Téléphone · Adresse · Liens (LinkedIn, GitHub…) · Poste · Années d'expérience · Compétences · Lien CV anonymisé · Fichier source · Alertes RGPD rattrapées`
3. **Import** the three workflows from `workflows/`, reselect the credentials, then **publish** each one.

### 3. Run the Streamlit app

```bash
cd streamlit-app
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # then edit the values
streamlit run main.py
```

`.env`:

```
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your-key-here
APP_PASSWORD=choose-a-password
```

### 4. Test the API without Streamlit

```bash
curl -X POST http://localhost:5678/webhook/cv-upload \
  -H "X-API-Key: YOUR_KEY" -F "CV=@fake_cv.pdf"

curl http://localhost:5678/webhook/consultants -H "X-API-Key: YOUR_KEY"
```

---

## Privacy and security

- The client CV must contain **no identifying data**. The leak check compares the final HTML with the real name, e-mail, phone, city, address, links, employers and schools. Leaks are redacted and counted; anything that survives blocks the PDF.
- The Streamlit app is behind a password, and the database tab shows real data.
- Webhooks `cv-upload` and `consultants` require an API key. The download link is protected only by its unguessable code.
- `.env`, `sorties/` and any CV files are in `.gitignore`. Exported workflows contain credential **references**, not keys.
- The register is stored in Google Drive for this training. A real deployment should keep it inside the company's own infrastructure.

---

## Known limitations

- The leak check matches **exact strings** after normalising case and accents; nicknames or misspelled employers can slip through, and free-text hobbies are not checked.
- Scanned PDFs are rejected (no OCR).
- Years of experience come from the AI; the rule (do internships count?) should be computed in code.
- `localhost` links only work on the machine running n8n.
- Google OAuth in *Testing* mode expires after 7 days.

## Possible improvements

- Compute years of experience deterministically from the dates.
- Add OCR for scanned CVs.
- Alerts (e-mail or chat) when a CV is rejected or a leak is caught.
- Automated tests for the leak check, ideally rewritten as a small Python module.
- Deploy behind a public HTTPS address with proper authentication.

---

## Author

Built as a training project. Feedback is welcome.
