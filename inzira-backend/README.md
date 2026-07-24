---
title: Inzira
emoji: 🌍
colorFrom: blue
colorTo: yellow
sdk: docker
app_port: 8000
pinned: false
license: mit
---

# Inzira — AI-Verified Youth Opportunity Platform (Rwanda)

Live web app + API for Rwandan youth: scholarships, jobs, trust scores, district map, AI assistant.

**Health:** `/health` · **App:** `/`

## Deploy secrets (Settings → Variables and secrets)

| Secret | Required |
|--------|----------|
| `INZIRA_ENV` | `production` |
| `GROQ_API_KEY` | Yes |
| `INZIRA_ASSETS_BUNDLE_URL` | Google Drive zip link |
| `INZIRA_MIFOTRA_STAFF_PASSWORD` | Yes |
| `INZIRA_VAPID_PUBLIC_KEY` | Yes |
| `INZIRA_VAPID_PRIVATE_KEY` | Yes |
| `INZIRA_FIREBASE_PROJECT_ID` | `inzira-52474` |
| `CORS_ORIGINS` | `https://YOUR-USERNAME-inzira.hf.space` |

Add your HF domain to Firebase → Authentication → Authorized domains.
