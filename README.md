# Inzira

Inzira is a web app that helps young people in Rwanda find scholarships, jobs, internships,training, competitions,free coursesand programs in one place.

## Quick links

| Item | Link |
|------|------|
| Live web app | [Open Inzira](https://huggingface.co/spaces/Liliane078/inzira) |
| Demo video | [Open the demo video](https://drive.google.com/file/d/1C-WmXusrbjR5wTogNIy9cJBx-s8HcUUO/view?usp=sharing) |
| Android APK | https://liliane078-inzira.hf.space/downloads/inzira.apk |

## What the app does

- Shows opportunities by district so users can find results close to home.
- Ranks listings with trust scores so users can avoid unreliable pages.
- Lets users search by category, save useful pages, and track deadlines.
- Includes personalized matches and a chat assistant for quick questions.
- Gives MIFOTRA a separate dashboard for analytics and planning.

## Project structure

| Path | Purpose |
|------|---------|
| [inzira-backend](inzira-backend) | Main web app, API, and backend logic |
| [Inzira-app](Inzira-app) | Android app |
| [inzira_dataset](inzira_dataset) | Scraping and training data |
| [notebooks](notebooks) | Model experiments and training notebooks |
| [screenshots](screenshots) | Submission screenshots |

## Run locally

### Prerequisites

- Python 3.10+
- Git
- Optional: Android Studio if you want to build the mobile app

### 1. Clone the repository

```powershell
git clone https://github.com/Umwanankabandi-liliane/Inzira.git
cd Inzira
```

### 2. Set up the backend

```powershell
cd inzira-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment values

Copy `.env.example` to `.env` and add the values for Firebase, Groq, and the MIFOTRA staff password.

### 4. Start the app

```powershell
python main.py
```

Open the app at `http://localhost:8000`.

## Screenshots

The submission screenshots are in [screenshots](screenshots).


