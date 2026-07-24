# ============================================================
# INZIRA — FASTAPI BACKEND
# main.py
# ============================================================

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, date
from dataclasses import dataclass
import torch
import pickle
import spacy
import numpy as np
import requests
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INZIRA_DATA_DIR = os.getenv("INZIRA_DATA_DIR", BASE_DIR)

# Windows consoles often default to cp1252; avoid 500s when logging Unicode.
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from bs4 import BeautifulSoup
from transformers import (
    BertTokenizer, BertForSequenceClassification, BertModel,
    RobertaTokenizer, RobertaForSequenceClassification
)
from sklearn.preprocessing import LabelEncoder
from groq import Groq
from ddgs import DDGS
from rwanda_sources import get_sources_for_category, domain_of, SKIP_DOMAINS, RWANDA_SOURCES
from registry_db import Registry, query_tokens
from analytics_db import AnalyticsStore
from match_engine import (
    profile_completeness,
    rank_opportunities,
    district_radar,
    ai_insights,
    RWANDA_DISTRICTS,
    _norm_interests,
    _norm_list,
    INTEREST_ALIASES,
)
from mifotra_auth import (
    allowed_domains,
    create_session,
    is_staff_email,
    staff_auth_required,
    validate_session,
    verify_staff_login,
)

from config import cors_origins, is_production, server_port
from db import ENGINE, db_session
from models import Base, PushSubscription, SavedSite, User, YouthProfile
from alert_service import scan_user_saved_sites
from push_service import vapid_configured, vapid_public_key
from scheduler import start_alert_scheduler, start_harvest_scheduler
from firebase_auth import delete_firebase_user, extract_identity, verify_id_token
from inzira_features import (
    apply_readiness,
    district_gap_map,
    eligibility_verdict,
    enrich_opportunity,
    explain_trust,
    impact_stats,
    pathway_steps,
)

REGISTRY_PATH = os.path.join(INZIRA_DATA_DIR, "registry.db")
registry = Registry(REGISTRY_PATH)
registry.init_db()
analytics = AnalyticsStore(REGISTRY_PATH)
analytics.init_db()
print(f"Registry loaded: {REGISTRY_PATH}")
print(f"Data directory: {INZIRA_DATA_DIR}")

# Create Postgres tables if migrations haven't run yet.
# In production you should run Alembic, but this makes first run safe.
try:
    Base.metadata.create_all(bind=ENGINE)
    from sqlalchemy import inspect, text
    from config import database_url as _db_url

    if _db_url().startswith("sqlite"):
        insp = inspect(ENGINE)
        if insp.has_table("saved_sites"):
            cols = {c["name"] for c in insp.get_columns("saved_sites")}
            with ENGINE.begin() as conn:
                if "notify_enabled" not in cols:
                    conn.execute(text(
                        "ALTER TABLE saved_sites ADD COLUMN notify_enabled BOOLEAN DEFAULT 0 NOT NULL"
                    ))
                if "last_deadline" not in cols:
                    conn.execute(text(
                        "ALTER TABLE saved_sites ADD COLUMN last_deadline VARCHAR(128)"
                    ))
                if "last_deadline_check" not in cols:
                    conn.execute(text(
                        "ALTER TABLE saved_sites ADD COLUMN last_deadline_check TIMESTAMP"
                    ))
                if "last_alert_at" not in cols:
                    conn.execute(text(
                        "ALTER TABLE saved_sites ADD COLUMN last_alert_at TIMESTAMP"
                    ))
                if "last_alert_reason" not in cols:
                    conn.execute(text(
                        "ALTER TABLE saved_sites ADD COLUMN last_alert_reason VARCHAR(32)"
                    ))
except Exception as e:
    print(f"Database schema bootstrap skipped: {e}")

app = FastAPI(title="Inzira API", version="2.0.0")

_cors = cors_origins()
if is_production() and not _cors:
    print("WARNING: CORS_ORIGINS must be set in production (comma-separated HTTPS domains).")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors or ["https://invalid-cors-config.local"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── PATHS ────────────────────────────────────────────────────
WEB_DIR        = os.path.join(BASE_DIR, "web")
WEB_ASSETS_DIR = os.path.join(WEB_DIR, "assets")
DOWNLOADS_DIR  = os.path.join(WEB_DIR, "downloads")
LOCAL_APK_PATH = os.path.join(DOWNLOADS_DIR, "inzira.apk")
NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
}
def _model_dir(name: str) -> str:
    """Resolve a local model folder; fail clearly if the deploy bundle is missing."""
    p = (Path(INZIRA_DATA_DIR) / "models" / name).resolve()
    if not (p / "config.json").is_file():
        raise FileNotFoundError(
            f"ML model not found at {p} (missing config.json). "
            "Ensure INZIRA_ASSETS_BUNDLE_URL is set and restart the Space."
        )
    return str(p)


BERT_PATH      = _model_dir("bert_classifier")
ROBERTA_PATH   = _model_dir("roberta_classifier")
SPACY_PATH     = str((Path(INZIRA_DATA_DIR) / "models" / "spacy_ner").resolve())
RF_PATH        = os.path.join(INZIRA_DATA_DIR, "models", "trust_scorer", "random_forest.pkl")
LABEL_ENC_PATH = os.path.join(INZIRA_DATA_DIR, "models", "roberta_classifier", "label_encoder.pkl")

# ── LOAD MODELS ──────────────────────────────────────────────
print("Loading models...")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
print(f"BERT_PATH exists: {os.path.isdir(BERT_PATH)}")

bert_tokenizer  = BertTokenizer.from_pretrained(BERT_PATH, local_files_only=True, token=False)
bert_classifier = BertForSequenceClassification.from_pretrained(BERT_PATH, local_files_only=True, use_safetensors=True, token=False)
bert_classifier = bert_classifier.to(device)
bert_classifier.eval()
print("BERT classifier loaded")

bert_base_model = BertModel.from_pretrained(BERT_PATH, local_files_only=True, use_safetensors=True, token=False)
bert_base_model = bert_base_model.to(device)
bert_base_model.eval()
print("BERT base model loaded")

roberta_tokenizer  = RobertaTokenizer.from_pretrained(ROBERTA_PATH, local_files_only=True, token=False)
roberta_classifier = RobertaForSequenceClassification.from_pretrained(ROBERTA_PATH, local_files_only=True, use_safetensors=True, token=False)
roberta_classifier = roberta_classifier.to(device)
roberta_classifier.eval()
print("RoBERTa classifier loaded")

with open(LABEL_ENC_PATH, "rb") as f:
    label_encoder = pickle.load(f)
print("Label encoder loaded")

nlp_ner = spacy.load(SPACY_PATH)
print("spaCy NER loaded")

with open(RF_PATH, "rb") as f:
    rf_model = pickle.load(f)
print("Random Forest trust scorer loaded")

print("All models loaded successfully")

# ── CACHE ────────────────────────────────────────────────────
search_cache = {}
search_jobs: dict = {}

# ── Basic rate limiting (in-memory) ───────────────────────────
# This is a simple safety net. For production, prefer a shared store (Redis) or an API gateway.
RATE_LIMIT_WINDOW_S = 60
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX_PER_MIN", "120"))
_rate_hits = {}

# ── REQUEST MODELS ───────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str = ""
    category: Optional[str] = None
    max_results: Optional[int] = 20
    district: Optional[str] = None

class AIAssistantRequest(BaseModel):
    message: str
    language: Optional[str] = "english"


class MifotraStaffRequest(BaseModel):
    email: str
    password: str = ""


class YouthProfileRequest(BaseModel):
    name: Optional[str] = None
    district: Optional[str] = None
    age: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None


class EligibilityRequest(BaseModel):
    opportunity: dict
    profile: Optional[YouthProfileRequest] = None


def _enrich_results_list(
    results: List[dict],
    profile: Optional[dict] = None,
    *,
    list_view: bool = True,
) -> List[dict]:
    pdata = profile or {}
    from listing_dedup import dedupe_listings
    deduped = dedupe_listings(results)
    enriched = [enrich_opportunity(r, pdata, list_view=list_view) for r in deduped]
    try:
        from listing_quality import filter_publishable
        enriched = filter_publishable(enriched)
    except Exception:
        pass
    return enriched


class SavedSiteRequest(BaseModel):
    url: str
    title: Optional[str] = None
    category: Optional[str] = None
    notify_enabled: Optional[bool] = None


class NotifyToggleRequest(BaseModel):
    enabled: bool = True


class WebPushKeys(BaseModel):
    p256dh: str
    auth: str


class WebPushSubscribeRequest(BaseModel):
    endpoint: str
    keys: WebPushKeys


class FcmTokenRequest(BaseModel):
    token: str


class PushUnsubscribeRequest(BaseModel):
    endpoint: Optional[str] = None
    token: Optional[str] = None


USER_ROLE_YOUTH = "youth"
USER_ROLE_ADMIN = "admin"


@dataclass
class AuthUser:
    id: int
    firebase_uid: str
    email: Optional[str]
    phone_e164: Optional[str]
    display_name: Optional[str]
    role: str


def _admin_emails() -> set[str]:
    raw = os.getenv("INZIRA_ADMIN_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


def _resolve_user_role(email: Optional[str], phone: Optional[str] = None) -> str:
    if email and email.lower() in _admin_emails():
        return USER_ROLE_ADMIN
    return USER_ROLE_YOUTH


def _bearer_token(request: Request) -> Optional[str]:
    h = request.headers.get("authorization") or ""
    if not h.lower().startswith("bearer "):
        return None
    return h.split(" ", 1)[1].strip() or None


def get_current_user(request: Request) -> AuthUser:
    token = _bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        decoded = verify_id_token(token)
        uid, email, phone = extract_identity(decoded)
    except Exception as e:
        print(f"Auth token verify failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    with db_session() as db:
        user = db.query(User).filter(User.firebase_uid == uid).one_or_none()
        role = _resolve_user_role(email, phone)
        if not user:
            user = User(
                firebase_uid=uid,
                email=email,
                phone_e164=phone,
                role=role,
            )
            db.add(user)
            db.flush()
            db.add(YouthProfile(user_id=user.id))
            db.flush()
        else:
            if email and user.email != email:
                user.email = email
            if phone and user.phone_e164 != phone:
                user.phone_e164 = phone
            user.role = role
        return AuthUser(
            id=user.id,
            firebase_uid=user.firebase_uid,
            email=user.email,
            phone_e164=user.phone_e164,
            display_name=user.display_name,
            role=user.role or USER_ROLE_YOUTH,
        )


def require_admin(request: Request) -> AuthUser:
    user = get_current_user(request)
    if user.role != USER_ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _profile_dict(p: Optional[YouthProfile]) -> dict:
    if not p:
        return {
            "district": None,
            "age": None,
            "education": None,
            "skills": [],
            "interests": [],
        }
    skills = [x.strip() for x in (p.skills or "").split(",") if x.strip()]
    interests = [x.strip() for x in (p.interests or "").split(",") if x.strip()]
    return {
        "district": p.district,
        "age": p.age,
        "education": p.education,
        "skills": skills,
        "interests": interests,
    }


def require_mifotra_session(token: Optional[str]) -> None:
    if not validate_session(token):
        raise HTTPException(
            status_code=401,
            detail="MIFOTRA staff login required. Use your official @mifotra.gov.rw email.",
        )

# ── SEARCH PHILOSOPHY ────────────────────────────────────────
# Return real Rwanda WEBSITES hosting apply-able opportunities today —
# like an expert curator, not random Google links.
MIN_TRUST_SCORE     = 62
CURATED_TRUST_SCORE = 92
DEFAULT_MAX_RESULTS = 25
MAX_SEARCH_RESULTS = 100
MIN_REGISTRY_BEFORE_LIVE = 10
MAX_LIVE_DISCOVERY = 6

OPEN_SIGNALS = [
    "apply now", "apply online", "application open", "open application",
    "call for applications", "call for proposals", "register now", "register here",
    "submit your application", "deadline", "closing date", "now hiring",
    "vacancy", "vacancies", "recruitment", "internship", "scholarship",
    "programme", "program", "fellowship", "training opportunity",
    "eligible candidates", "how to apply", "apply here",
    "2025", "2026",
]

CLOSED_SIGNALS = [
    "applications closed", "application closed", "no longer accepting",
    "expired", "has ended", "was closed", "archived",
]

EXPIRED_YEARS = ["2018", "2019", "2020", "2021", "2022", "2023"]

# ── CATEGORY MAP ─────────────────────────────────────────────
CATEGORY_MAP = {
    "scholarship": ["scholarship", "scholarships", "bursary", "grant", "funding"],
    "internship":  ["internship", "internships", "intern"],
    "job":         ["job", "jobs", "career", "careers", "employment", "vacancy", "vacancies", "hiring"],
    "training":    ["training", "trainings", "workshop", "bootcamp", "tvet", "skills"],
    "competition": ["competition", "competitions", "challenge", "hackathon", "contest"],
    "program":     ["program", "programs", "programme", "programmes", "fellowship", "fellowships"],
    "free_course": ["free course", "free courses", "mooc", "online course", "online learning"],
}

# ── HELPER FUNCTIONS ─────────────────────────────────────────
def fetch_page_text(url: str) -> str:
    try:
        headers  = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=8)
        soup     = BeautifulSoup(response.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        text = " ".join(text.split()[:400])
        return text
    except Exception:
        return ""


_DEADLINE_SCAN_CACHE: dict[str, tuple[float, str]] = {}
_DEADLINE_CACHE_SEC = 300
_DEADLINE_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_deadline_date(text: str) -> Optional[date]:
    if not text:
        return None
    raw = text.strip()
    low = raw.lower()
    if any(x in low for x in ("rolling", "ongoing", "open until filled", "no deadline", "tbd")):
        return None
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", raw)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        for day, month in ((a, b), (b, a)):
            try:
                if 1 <= month <= 12 and 1 <= day <= 31:
                    return date(y, month, day)
            except ValueError:
                continue
    m = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})",
        low,
    )
    if m:
        month = _DEADLINE_MONTHS.get(m.group(1))
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(2)))
            except ValueError:
                pass
    m = re.search(
        r"(\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})",
        low,
    )
    if m:
        month = _DEADLINE_MONTHS.get(m.group(2))
        if month:
            try:
                return date(int(m.group(3)), month, int(m.group(1)))
            except ValueError:
                pass
    return None


def scan_site_deadline(url: str) -> str:
    dom = domain_of(url)
    now = datetime.utcnow().timestamp()
    if dom and dom in _DEADLINE_SCAN_CACHE:
        ts, cached = _DEADLINE_SCAN_CACHE[dom]
        if now - ts < _DEADLINE_CACHE_SEC:
            return cached
    text = fetch_page_text(url)
    deadline = ""
    if text:
        try:
            deadline = extract_entities(text).get("deadline", "") or ""
        except Exception:
            deadline = ""
        if not deadline:
            m = re.search(
                r"(?:deadline|closing date|apply by|due date)[:\s]+([^.;\n]{4,40})",
                text,
                re.IGNORECASE,
            )
            if m:
                deadline = m.group(1).strip()
    if dom:
        _DEADLINE_SCAN_CACHE[dom] = (now, deadline)
    return deadline


def _saved_site_dict(row: SavedSite) -> dict:
    return {
        "url": row.url,
        "domain": row.domain,
        "title": row.title,
        "category": row.category,
        "notify_enabled": bool(row.notify_enabled),
        "last_deadline": row.last_deadline or "",
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def get_bert_embedding(text: str) -> np.ndarray:
    encoding = bert_tokenizer(
        text,
        max_length=256,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    input_ids      = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)
    with torch.no_grad():
        outputs   = bert_base_model(input_ids=input_ids, attention_mask=attention_mask)
        embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
    return embedding[0]


def classify_binary(text: str) -> tuple:
    encoding = bert_tokenizer(
        text,
        max_length=256,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    input_ids      = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)
    with torch.no_grad():
        outputs    = bert_classifier(input_ids=input_ids, attention_mask=attention_mask)
        probs      = torch.softmax(outputs.logits, dim=1)
        label      = torch.argmax(probs, dim=1).item()
        confidence = probs[0][label].item()
    return label, confidence


def classify_category(text: str) -> tuple:
    encoding = roberta_tokenizer(
        text,
        max_length=256,
        padding="max_length",
        truncation=True,
        return_tensors="pt"
    )
    input_ids      = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)
    with torch.no_grad():
        outputs    = roberta_classifier(input_ids=input_ids, attention_mask=attention_mask)
        probs      = torch.softmax(outputs.logits, dim=1)
        label_idx  = torch.argmax(probs, dim=1).item()
        confidence = probs[0][label_idx].item()
    category = label_encoder.inverse_transform([label_idx])[0]
    return category, confidence


def extract_entities(text: str) -> dict:
    doc      = nlp_ner(text[:500])
    entities = {
        "organization": "",
        "deadline":     "",
        "eligibility":  "",
        "location":     "",
        "apply_link":   ""
    }
    for ent in doc.ents:
        if ent.label_ == "ORG" and not entities["organization"]:
            entities["organization"] = ent.text
        elif ent.label_ == "DEADLINE" and not entities["deadline"]:
            entities["deadline"] = ent.text
        elif ent.label_ == "ELIGIBILITY" and not entities["eligibility"]:
            entities["eligibility"] = ent.text
        elif ent.label_ == "LOCATION" and not entities["location"]:
            entities["location"] = ent.text
        elif ent.label_ == "APPLY_LINK" and not entities["apply_link"]:
            entities["apply_link"] = ent.text
    return entities


def compute_trust_score(text: str, url: str) -> float:
    embedding   = get_bert_embedding(text)
    proba       = rf_model.predict_proba([embedding])[0]
    trust_score = proba[1] * 100
    return round(trust_score, 2)


def should_skip_url(url: str) -> bool:
    d = domain_of(url)
    return not d or any(skip in d for skip in SKIP_DOMAINS)


def has_open_application_signals(text: str) -> bool:
    t = text.lower()
    if any(s in t for s in CLOSED_SIGNALS):
        return False
    has_open = any(s in t for s in OPEN_SIGNALS)
    if not has_open:
        return False
    # Reject pages dominated by old years unless a current year is present
    has_old = any(y in t for y in EXPIRED_YEARS)
    has_current = "2025" in t or "2026" in t or "open" in t or "apply" in t
    if has_old and not has_current:
        return False
    return True


def is_rwanda_relevant(text: str, url: str) -> bool:
    t = text.lower()
    d = domain_of(url)
    if d.endswith(".rw") or d.endswith(".gov.rw"):
        return True
    if "rwanda" in d or "kigali" in d:
        return True
    if "rwanda" in t or "kigali" in t:
        return True
    # Africa-focused portals found via Rwanda-scoped search
    if any(x in t for x in ("east africa", "african youth", "africa opportunities")):
        return True
    return False


def category_keywords_match(text: str, category: Optional[str]) -> bool:
    if not category:
        return True
    keywords = CATEGORY_MAP.get(category, [])
    t = text.lower()
    return any(kw in t for kw in keywords)


def build_result(url: str, title: str, snippet: str, category: str,
                 trust_score: float, page_text: str, organization: str = "") -> dict:
    try:
        entities = extract_entities(page_text)
    except Exception:
        entities = {"organization": "", "deadline": "", "eligibility": "",
                    "location": "Rwanda", "apply_link": ""}
    apply_link = (entities.get("apply_link") or "").strip()
    if not apply_link.startswith(("http://", "https://")) or " " in apply_link:
        apply_link = ""
    page_url = (url or "").strip()
    return {
        "url":          page_url,
        "title":        title,
        "category":     category,
        "trust_score":  round(trust_score, 2),
        "organization": organization or entities.get("organization", ""),
        "deadline":     entities.get("deadline", ""),
        "eligibility":  entities.get("eligibility", ""),
        "location":     entities.get("location", "") or "Rwanda",
        "apply_link":   apply_link or page_url,
        "snippet":      snippet[:300] if snippet else "",
    }


def verify_with_ai(page_text: str, matched_category: Optional[str]) -> Optional[tuple]:
    """Returns (category, trust_score) if page passes strict checks, else None."""
    if len(page_text) < 80:
        return None
    if not has_open_application_signals(page_text):
        return None

    bert_label, _ = classify_binary(page_text)
    if bert_label == 0:
        return None

    category, _ = classify_category(page_text)
    if category == "not_opportunity":
        return None

    if matched_category and category != matched_category:
        # Allow closely related categories only for broad queries
        related = {matched_category, "program", "training"}
        if category not in related:
            return None

    trust_score = compute_trust_score(page_text, "")
    if trust_score < MIN_TRUST_SCORE:
        return None

    return category, trust_score


def scan_curated_sources(matched_category: Optional[str]) -> List[dict]:
    """Check known Rwanda opportunity websites — the core of Inzira search."""
    verified = []
    sources  = get_sources_for_category(matched_category)

    for source in sources:
        best = None
        for path in source.get("paths", ["/"]):
            base = source["url"].rstrip("/")
            page_url = base if path == "/" else base + path
            page_text = fetch_page_text(page_url)
            if not page_text:
                continue

            if not is_rwanda_relevant(f"{source['name']} {page_text}", page_url):
                continue
            if not has_open_application_signals(page_text):
                continue

            if matched_category and matched_category not in source["categories"]:
                if not category_keywords_match(page_text, matched_category):
                    continue

            cat = matched_category or infer_category_from_text(page_text, "program")
            trust = CURATED_TRUST_SCORE
            ai = verify_with_ai(page_text, matched_category)
            if not ai:
                continue
            cat, ai_trust = ai
            trust = max(CURATED_TRUST_SCORE, ai_trust)

            snippet = page_text[:280] + "..."
            candidate = build_result(
                url=page_url,
                title=source["name"],
                snippet=snippet,
                category=cat,
                trust_score=trust,
                page_text=page_text,
                organization=source["name"],
            )
            if best is None or candidate["trust_score"] > best["trust_score"]:
                best = candidate

        if best:
            verified.append(best)
            print(f"  OK Curated: {source['name']}")

    return verified


def search_trusted_web(query: str, matched_category: Optional[str],
                       max_results: int = 15) -> List[dict]:
    """Targeted search on trusted Rwanda domains only."""
    sources = get_sources_for_category(matched_category)
    domains = list({s["domain"] for s in sources})[:12]
    verified = []
    seen_domains = set()

    cat_term = matched_category.replace("_", " ") if matched_category else query

    with DDGS() as ddgs:
        for domain in domains:
            rwanda_query = f"site:{domain} {cat_term} apply open Rwanda 2025 2026"
            try:
                for r in list(ddgs.text(rwanda_query, max_results=5)):
                    url = r.get("href", "")
                    if not url or should_skip_url(url):
                        continue
                    d = domain_of(url)
                    if d in seen_domains:
                        continue

                    title   = r.get("title", "")
                    snippet = r.get("body", "")
                    page_text = fetch_page_text(url) or snippet
                    combined  = f"{title} {page_text}"

                    if not is_rwanda_relevant(combined, url):
                        continue
                    if not has_open_application_signals(combined):
                        continue

                    ai = verify_with_ai(page_text, matched_category)
                    if not ai:
                        continue

                    category, trust = ai
                    seen_domains.add(d)
                    verified.append(build_result(
                        url, title or d, snippet, category, trust, page_text
                    ))
                    if len(verified) >= max_results:
                        return verified
            except Exception as e:
                print(f"  Trusted search error ({domain}): {e}")

    return verified


def search_web_broad(query: str, matched_category: Optional[str],
                     max_results: int = 10) -> List[dict]:
    """Last resort — broad web, but still strict verification."""
    verified = []
    seen_domains = set()
    queries = [
        f"{query} Rwanda apply now open applications 2025 2026 site:.rw",
        f"{query} Rwanda youth opportunities apply",
    ]

    with DDGS() as ddgs:
        for rwanda_query in queries:
            try:
                for r in list(ddgs.text(rwanda_query, max_results=8)):
                    url = r.get("href", "")
                    if not url or should_skip_url(url):
                        continue
                    d = domain_of(url)
                    if d in seen_domains:
                        continue

                    title   = r.get("title", "")
                    snippet = r.get("body", "")
                    page_text = fetch_page_text(url) or snippet

                    if not is_rwanda_relevant(page_text, url):
                        continue
                    if not has_open_application_signals(f"{title} {page_text}"):
                        continue

                    ai = verify_with_ai(page_text, matched_category)
                    if not ai:
                        continue

                    category, trust = ai
                    seen_domains.add(d)
                    verified.append(build_result(
                        url, title, snippet, category, trust, page_text
                    ))
                    if len(verified) >= max_results:
                        return verified
            except Exception as e:
                print(f"  Broad search error: {e}")

    return verified


def dedupe_by_website(results: List[dict]) -> List[dict]:
    """One card per website — the listing page with highest trust."""
    by_domain: dict = {}
    for r in results:
        d = domain_of(r["url"])
        if not d:
            continue
        if d not in by_domain or r["trust_score"] > by_domain[d]["trust_score"]:
            by_domain[d] = r
    return sorted(by_domain.values(), key=lambda x: x["trust_score"], reverse=True)


def infer_category_from_text(text: str, fallback: str = "program") -> str:
    text_lower = text.lower()
    for cat, keywords in CATEGORY_MAP.items():
        if any(kw in text_lower for kw in keywords):
            return cat
    return fallback


# Chip / category-only queries from the app — browse full category, no text filter
CATEGORY_CHIP_MAP = {
    "jobs": "job",
    "job": "job",
    "scholarships": "scholarship",
    "scholarship": "scholarship",
    "internships": "internship",
    "internship": "internship",
    "training programs": "training",
    "training": "training",
    "programs": "program",
    "program": "program",
    "competitions": "competition",
    "competition": "competition",
    "free online courses": "free_course",
    "free courses": "free_course",
    "free course": "free_course",
}


def normalize_search_category(category: Optional[str]) -> Optional[str]:
    """Map API/UI aliases (e.g. internships) to registry category ids."""
    if not category:
        return None
    c = category.lower().strip()
    if c in CATEGORY_MAP:
        return c
    if c in CATEGORY_CHIP_MAP:
        return CATEGORY_CHIP_MAP[c]
    return None


def get_matched_category(query: str):
    query_lower = query.lower().strip()
    if query_lower in CATEGORY_CHIP_MAP:
        return CATEGORY_CHIP_MAP[query_lower]
    for cat, keywords in CATEGORY_MAP.items():
        if any(kw in query_lower for kw in keywords):
            return cat
    return None


def is_category_only_query(query: str, category: Optional[str]) -> bool:
    if not category:
        return False
    q = query.lower().strip()
    if q in CATEGORY_CHIP_MAP and CATEGORY_CHIP_MAP[q] == category:
        return True
    keywords = CATEGORY_MAP.get(category, [])
    return any(q == kw or q == kw + "s" for kw in keywords)


def extract_search_terms(query: str, category: Optional[str]) -> str:
    """Keep meaningful words after stripping category chip vocabulary."""
    tokens = query_tokens(query)
    if not tokens:
        return ""
    extra_stop = set()
    if category:
        for kw in CATEGORY_MAP.get(category, []):
            extra_stop.update(kw.split())
    filtered = [t for t in tokens if t not in extra_stop]
    return " ".join(filtered)


def resolve_search(category: Optional[str], query: str):
    """Category browse (explicit/inferred filter) or free-text registry search."""
    q = (query or "").strip()
    explicit_cat = normalize_search_category(category)

    # Results-page category chip or API category param — strict category filter.
    if explicit_cat:
        if not q or is_category_only_query(q, explicit_cat):
            return explicit_cat, ""
        terms = extract_search_terms(q, explicit_cat)
        return explicit_cat, terms or ""

    if not q:
        return None, ""

    # Single-word chip labels (e.g. "jobs") → strict category browse.
    if q.lower() in CATEGORY_CHIP_MAP and " " not in q:
        return CATEGORY_CHIP_MAP[q.lower()], ""

    # Multi-word category queries (e.g. "Internships Rwanda") → strict category filter.
    inferred = get_matched_category(q)
    if inferred:
        if is_category_only_query(q, inferred):
            return inferred, ""
        terms = extract_search_terms(q, inferred)
        return inferred, terms or ""

    return None, q


def persist_result_to_registry(result: dict, source: str = "live_search") -> None:
    url = result.get("url") or ""
    domain = domain_of(url)
    if not domain:
        return
    cat = result.get("category") or "program"
    cats = result.get("categories")
    if not isinstance(cats, list):
        cats = [cat]
    registry.upsert_website(
        domain=domain,
        name=result.get("title") or domain,
        url=url,
        categories=cats,
        trust_score=float(result.get("trust_score") or 75),
        has_open=True,
        verified=True,
        snippet=result.get("snippet") or "",
        organization=result.get("organization") or result.get("title") or domain,
        deadline=result.get("deadline") or "",
        eligibility=result.get("eligibility") or "",
        location=result.get("location") or "Rwanda",
        apply_link=result.get("apply_link") or url,
        source=source,
    )
    try:
        from opportunity_sync import sync_opportunities_for_website
        sync_opportunities_for_website(
            registry,
            {
                "domain": domain,
                "name": result.get("title") or domain,
                "url": url,
                "categories": cats,
                "trust_score": float(result.get("trust_score") or 75),
                "verified": 1,
                "has_open_applications": 1,
                "snippet": result.get("snippet") or "",
                "organization": result.get("organization") or result.get("title") or domain,
                "apply_link": result.get("apply_link") or url,
                "location": result.get("location") or "Rwanda",
            },
        )
    except Exception as exc:
        print(f"  Opportunity sync skipped for {domain}: {exc}")


def dedupe_opportunities(results: List[dict]) -> List[dict]:
    from listing_dedup import dedupe_listings
    return dedupe_listings(results)


def hybrid_search_response(
    category: Optional[str],
    query: str,
    max_results: int,
    district: Optional[str] = None,
) -> dict:
    norm_category = normalize_search_category(category)
    cat, text_filter = resolve_search(norm_category, query)
    print(f"  Resolved: category={cat!r} terms={text_filter!r} district={district!r}")

    registry_results = registry.search_opportunities(
        category=cat,
        query_text=text_filter,
        limit=max_results,
        district=district,
        verified_only=True,
    )
    seen_urls = {(r.get("apply_link") or r.get("url") or "").lower().rstrip("/") for r in registry_results}
    seen_domains = {domain_of(r.get("source_domain") or r.get("domain") or r.get("url") or "") for r in registry_results}
    seen_domains.discard("")
    supplemental: List[dict] = []
    sources_used = ["registry"]

    # Live/curated supplements only when the registry has zero matches — keeps search fast.
    has_specific_terms = len(query_tokens(text_filter or query)) >= 1
    if has_specific_terms and len(registry_results) == 0 and not cat:
        try:
            from website_discovery import discover_and_verify_websites
            live_query = text_filter or query or (cat or "opportunities")
            print(f"  Live discovery (registry had {len(registry_results)} hits)...")
            live = discover_and_verify_websites(
                live_query,
                cat,
                max_results=MAX_LIVE_DISCOVERY,
                skip_domains=seen_domains,
            )
            for item in live:
                d = domain_of(item.get("url", ""))
                if d and d not in seen_domains:
                    seen_domains.add(d)
                    supplemental.append(item)
                    persist_result_to_registry(item, source="live_search")
            if supplemental:
                sources_used.append("live_discovery")
                print(f"  +{len(supplemental)} newly verified websites")
                registry_results = registry.search_opportunities(
                    category=cat,
                    query_text=text_filter,
                    limit=max(max_results * 2, 40),
                    district=district,
                    verified_only=True,
                )
        except Exception as e:
            print(f"  Live discovery skipped: {e}")

    # Still sparse — scan curated Rwanda sources (known portals)
    combined_count = len(registry_results)
    if combined_count == 0 and not cat:
        try:
            curated = scan_curated_sources(cat)
            added = 0
            for item in curated:
                d = domain_of(item.get("url", ""))
                if d and d not in seen_domains:
                    seen_domains.add(d)
                    supplemental.append(item)
                    persist_result_to_registry(item, source="curated_scan")
                    added += 1
            if added:
                sources_used.append("curated")
                print(f"  +{added} curated Rwanda websites")
                registry_results = registry.search_opportunities(
                    category=cat,
                    query_text=text_filter,
                    limit=max(max_results * 2, 40),
                    district=district,
                    verified_only=True,
                )
        except Exception as e:
            print(f"  Curated scan skipped: {e}")

    combined = dedupe_opportunities(registry_results)
    if cat or text_filter:
        combined = _rerank_results(combined, cat, query_tokens(text_filter or query))
    if district:
        combined = _prioritize_district(combined, district)
    from registry_db import filter_real_opportunities
    combined = filter_real_opportunities(combined, strict_category=cat)
    combined = combined[:max_results]

    district_note = None
    if district and not combined:
        district_note = (
            f"No verified listings mention {district} yet. "
            "Showing national Rwanda programs is disabled until we find district-specific matches."
        )

    stats = registry.stats()
    return {
        "query": query,
        "category": cat,
        "search_terms": text_filter,
        "district": district,
        "district_note": district_note,
        "total_found": len(combined),
        "verified": len(combined),
        "results": _enrich_results_list(combined),
        "registry_size": stats.get("verified_opportunities", 0) or stats.get("verified_open", 0),
        "last_refresh_at": stats.get("last_refresh_at") or "",
        "source": "+".join(sources_used),
    }


def _rerank_results(results: List[dict], category: Optional[str], tokens: List[str]) -> List[dict]:
    """Re-score API results for display order (category fit + query tokens)."""
    def score(r: dict) -> float:
        s = float(r.get("trust_score") or 0)
        cats = r.get("categories") or [r.get("category", "")]
        domain = domain_of(r.get("url", "")).lower()
        blob = f"{r.get('title', '')} {domain} {r.get('snippet', '')} {' '.join(cats)}".lower()
        for i, tok in enumerate(tokens):
            if tok in blob:
                s += 14 + max(0, 4 - i)
        if category and category in cats:
            n = len(cats)
            if n == 1:
                s += 18
            elif n == 2:
                s += 10
            elif n >= 5:
                s -= 18
            for hint in ("job", "scholar", "hec", "intern", "wda", "train"):
                if hint in domain:
                    s += 6
        return s

    return sorted(results, key=score, reverse=True)


def _prioritize_district(results: List[dict], district: str) -> List[dict]:
    """Keep only listings with an explicit district tag matching the filter."""
    if not district:
        return results
    d = district.strip().lower()
    return [
        r for r in results
        if (r.get("district") or "").strip().lower() == d
    ]


def registry_search_response(category: Optional[str], query: str, max_results: int) -> dict:
    """Backward-compatible alias."""
    return hybrid_search_response(category, query, max_results)


# ── ROUTES ───────────────────────────────────────────────────
if os.path.isdir(WEB_ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=WEB_ASSETS_DIR), name="web_assets")
if os.path.isdir(DOWNLOADS_DIR):
    app.mount("/downloads", StaticFiles(directory=DOWNLOADS_DIR), name="web_downloads")


@app.middleware("http")
async def no_cache_app_assets(request, call_next):
    # rate limit (best-effort)
    try:
        import time
        ip = request.client.host if request.client else "unknown"
        key = f"{ip}:{request.url.path}"
        now = time.time()
        hits = _rate_hits.get(key, [])
        hits = [t for t in hits if now - t < RATE_LIMIT_WINDOW_S]
        hits.append(now)
        _rate_hits[key] = hits
        if len(hits) > RATE_LIMIT_MAX and request.url.path in ("/search", "/assistant", "/youth/matches", "/me/saved"):
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
    except Exception:
        pass

    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.endswith((".js", ".css", ".html")) or path.startswith("/assets/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
    return response


@app.get("/")
def root():
    index = os.path.join(WEB_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index, headers=NO_CACHE_HEADERS)
    return {"message": "Inzira API is running", "version": "2.0.0", "mode": "production-registry"}


@app.get("/manifest.json")
def web_manifest():
    path = os.path.join(WEB_DIR, "manifest.json")
    if os.path.isfile(path):
        return FileResponse(path, media_type="application/manifest+json")
    raise HTTPException(status_code=404)


@app.get("/sw.js")
def service_worker():
    path = os.path.join(WEB_DIR, "sw.js")
    if os.path.isfile(path):
        return FileResponse(path, media_type="application/javascript", headers=NO_CACHE_HEADERS)
    raise HTTPException(status_code=404)


@app.get("/web")
def web_interface():
    index = os.path.join(WEB_DIR, "index.html")
    if os.path.isfile(index):
        return FileResponse(index, headers=NO_CACHE_HEADERS)
    return FileResponse(os.path.join(WEB_DIR, "legacy", "inzira_web.html"), headers=NO_CACHE_HEADERS)


def _resolve_apk_url(request: Request) -> Optional[str]:
    explicit = os.getenv("INZIRA_APK_URL", "").strip()
    if explicit:
        return explicit
    if os.path.isfile(LOCAL_APK_PATH):
        base = str(request.base_url).rstrip("/")
        return f"{base}/downloads/inzira.apk"
    return None


@app.get("/app/config")
def app_config(request: Request):
    apk_url = _resolve_apk_url(request)
    return {
        "apk_url": apk_url,
        "apk_available": bool(apk_url),
        "mifotra_staff_login": staff_auth_required(),
    }


@app.get("/health")
def health():
    out = {
        "status": "healthy",
        "env": "production" if is_production() else "development",
        "models_loaded": True,
        "database": False,
        "firebase_auth": False,
        "firebase_admin": False,
        "mifotra_auth": staff_auth_required(),
    }
    try:
        with db_session() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        out["database"] = True
    except Exception:
        out["status"] = "degraded"
    try:
        from firebase_auth import _admin_configured, firebase_project_id
        firebase_project_id()
        out["firebase_auth"] = True
        if _admin_configured():
            from firebase_auth import _init_firebase
            _init_firebase()
            out["firebase_admin"] = True
        out["web_push"] = vapid_configured()
    except Exception:
        out["status"] = "degraded"
    return out


@app.on_event("startup")
def _startup_alert_scheduler():
    start_alert_scheduler(entity_extractor=extract_entities)
    start_harvest_scheduler(
        is_stale_fn=_opportunity_harvest_stale,
        is_running_fn=lambda: registry.get_meta("harvest_in_progress", "") == "1",
        run_harvest_fn=_run_opportunity_harvest_background,
    )
    _schedule_opportunity_harvest()


def _opportunity_harvest_stale(hours: int = 24) -> bool:
    """True when listings were never synced or last sync is older than `hours`."""
    last = registry.get_meta("last_opportunity_sync_at", "")
    if not last:
        return True
    try:
        from datetime import datetime, timezone, timedelta
        ts = datetime.fromisoformat(last.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - ts > timedelta(hours=hours)
    except Exception:
        return True


def _run_opportunity_harvest_background(reason: str = "scheduled") -> None:
    import threading

    def _job():
        try:
            from opportunity_sync import sync_all_verified
            from registry_db import _utc_now
            registry.set_meta("harvest_in_progress", "1")
            registry.set_meta("harvest_started_at", _utc_now())
            print(f"Opportunity harvest ({reason}) — crawling verified portals...")
            n = sync_all_verified(registry, log=print)
            print(f"Opportunity harvest done — {n} listings stored.")
            try:
                from listing_revalidation import revalidate_active_listings
                revalidate_active_listings(registry, log=print)
            except Exception as rev_exc:
                print(f"Live re-validation skipped: {rev_exc}")
            purged = registry.purge_unpublishable_listings()
            if purged:
                print(f"Purged {purged} expired/foreign/junk listings.")
        except Exception as exc:
            print(f"Opportunity harvest failed: {exc}")
        finally:
            registry.set_meta("harvest_in_progress", "0")

    threading.Thread(target=_job, daemon=True).start()


def _schedule_opportunity_harvest() -> None:
    try:
        purged = registry.purge_unpublishable_listings()
        if purged:
            print(f"Startup: purged {purged} bad opportunity listings.")
        stats = registry.stats()
        verified = stats.get("verified_open", 0)
        if verified <= 0:
            return
        opp_count = registry.count_opportunities()
        if opp_count == 0:
            _run_opportunity_harvest_background("bootstrap")
        elif _opportunity_harvest_stale(hours=24):
            _run_opportunity_harvest_background("stale_refresh")
    except Exception as exc:
        print(f"Opportunity harvest schedule skipped: {exc}")


@app.get("/registry/stats")
def registry_stats():
    return registry.stats()


@app.get("/me")
def me(request: Request):
    user = get_current_user(request)
    with db_session() as db:
        prof = db.query(YouthProfile).filter(YouthProfile.user_id == user.id).one_or_none()
        saved_n = db.query(SavedSite).filter(SavedSite.user_id == user.id).count()
        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone_e164,
            "name": user.display_name,
            "role": user.role or USER_ROLE_YOUTH,
            "profile": _profile_dict(prof),
            "saved_count": saved_n,
        }


@app.put("/me/profile")
def update_profile(profile: YouthProfileRequest, request: Request):
    user = get_current_user(request)
    pdata = profile.model_dump()
    skills = pdata.get("skills") or []
    interests = pdata.get("interests") or []
    with db_session() as db:
        db_user = db.query(User).filter(User.id == user.id).one()
        if pdata.get("name") is not None:
            db_user.display_name = (pdata.get("name") or "").strip() or None
        prof = db.query(YouthProfile).filter(YouthProfile.user_id == user.id).one_or_none()
        if not prof:
            prof = YouthProfile(user_id=user.id)
            db.add(prof)
            db.flush()
        if pdata.get("district") is not None:
            prof.district = pdata.get("district")
        if pdata.get("age") is not None:
            prof.age = pdata.get("age")
        if pdata.get("education") is not None:
            prof.education = pdata.get("education")
        if profile.skills is not None:
            prof.skills = ", ".join([s.strip() for s in skills if isinstance(s, str) and s.strip()])
        if profile.interests is not None:
            prof.interests = ", ".join([s.strip() for s in interests if isinstance(s, str) and s.strip()])
        db.flush()
        return {"ok": True, "profile": _profile_dict(prof), "name": db_user.display_name}


@app.delete("/me")
def delete_account(request: Request):
    user = get_current_user(request)
    uid = user.firebase_uid
    with db_session() as db:
        db.query(User).filter(User.id == user.id).delete()
    firebase_deleted = True
    try:
        delete_firebase_user(uid)
    except Exception:
        firebase_deleted = False
    return {"ok": True, "firebase_deleted": firebase_deleted}


@app.get("/me/saved")
def list_saved(request: Request):
    user = get_current_user(request)
    with db_session() as db:
        rows = (
            db.query(SavedSite)
            .filter(SavedSite.user_id == user.id)
            .order_by(SavedSite.created_at.desc())
            .limit(500)
            .all()
        )
        return {
            "total": len(rows),
            "items": [_saved_site_dict(r) for r in rows],
        }


@app.post("/me/saved")
def save_site(body: SavedSiteRequest, request: Request):
    user = get_current_user(request)
    url = (body.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    dom = domain_of(url)
    if not dom:
        raise HTTPException(status_code=400, detail="Invalid url")
    with db_session() as db:
        existing = (
            db.query(SavedSite)
            .filter(SavedSite.user_id == user.id, SavedSite.domain == dom)
            .one_or_none()
        )
        if existing:
            existing.url = url
            if body.title is not None:
                existing.title = body.title
            if body.category is not None:
                existing.category = body.category
            if body.notify_enabled is not None:
                existing.notify_enabled = body.notify_enabled
            db.flush()
            return {"ok": True, "saved": True, "domain": dom, "notify_enabled": existing.notify_enabled}

        row = SavedSite(
            user_id=user.id,
            url=url,
            domain=dom,
            title=body.title,
            category=body.category,
            notify_enabled=bool(body.notify_enabled),
        )
        db.add(row)
        db.flush()
        return {"ok": True, "saved": True, "domain": dom}


@app.delete("/me/saved/{domain}")
def unsave_site(domain: str, request: Request):
    user = get_current_user(request)
    dom = (domain or "").strip().lower()
    if not dom:
        raise HTTPException(status_code=400, detail="domain is required")
    with db_session() as db:
        n = (
            db.query(SavedSite)
            .filter(SavedSite.user_id == user.id, SavedSite.domain == dom)
            .delete()
        )
        return {"ok": True, "removed": n}


@app.put("/me/saved/{domain}/notify")
def toggle_saved_notify(domain: str, body: NotifyToggleRequest, request: Request):
    user = get_current_user(request)
    dom = (domain or "").strip().lower()
    if not dom:
        raise HTTPException(status_code=400, detail="domain is required")
    with db_session() as db:
        row = (
            db.query(SavedSite)
            .filter(SavedSite.user_id == user.id, SavedSite.domain == dom)
            .one_or_none()
        )
        if not row:
            raise HTTPException(status_code=404, detail="Site not saved")
        row.notify_enabled = bool(body.enabled)
        db.flush()
        return {"ok": True, "domain": dom, "notify_enabled": row.notify_enabled}


@app.get("/me/alerts/check")
def check_deadline_alerts(request: Request, limit: int = 6):
    """Scan notify-enabled saved sites for new or soon deadlines."""
    user = get_current_user(request)
    limit = min(max(limit, 1), 10)
    return scan_user_saved_sites(
        user.id,
        limit=limit,
        entity_extractor=extract_entities,
        send_push=False,
    )


@app.get("/push/vapid-public-key")
def push_vapid_key():
    return {"publicKey": vapid_public_key(), "configured": vapid_configured()}


@app.post("/me/push/subscribe")
def push_subscribe_web(body: WebPushSubscribeRequest, request: Request):
    user = get_current_user(request)
    endpoint = (body.endpoint or "").strip()
    if not endpoint:
        raise HTTPException(status_code=400, detail="endpoint is required")
    with db_session() as db:
        row = (
            db.query(PushSubscription)
            .filter(PushSubscription.user_id == user.id, PushSubscription.endpoint == endpoint)
            .one_or_none()
        )
        if not row:
            row = PushSubscription(
                user_id=user.id,
                channel="web",
                endpoint=endpoint,
            )
            db.add(row)
        row.channel = "web"
        row.p256dh = body.keys.p256dh
        row.auth_secret = body.keys.auth
        row.active = True
        row.updated_at = datetime.utcnow()
        db.flush()
        return {"ok": True, "channel": "web"}


@app.post("/me/push/fcm")
def push_subscribe_fcm(body: FcmTokenRequest, request: Request):
    user = get_current_user(request)
    token = (body.token or "").strip()
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    with db_session() as db:
        row = (
            db.query(PushSubscription)
            .filter(PushSubscription.user_id == user.id, PushSubscription.endpoint == token)
            .one_or_none()
        )
        if not row:
            row = PushSubscription(
                user_id=user.id,
                channel="fcm",
                endpoint=token,
            )
            db.add(row)
        row.channel = "fcm"
        row.active = True
        row.updated_at = datetime.utcnow()
        db.flush()
        return {"ok": True, "channel": "fcm"}


@app.delete("/me/push/unsubscribe")
def push_unsubscribe(body: PushUnsubscribeRequest, request: Request):
    user = get_current_user(request)
    target = (body.endpoint or body.token or "").strip()
    if not target:
        raise HTTPException(status_code=400, detail="endpoint or token is required")
    with db_session() as db:
        n = (
            db.query(PushSubscription)
            .filter(PushSubscription.user_id == user.id, PushSubscription.endpoint == target)
            .delete()
        )
        return {"ok": True, "removed": n}


@app.get("/admin/stats")
def admin_stats(request: Request):
    require_admin(request)
    with db_session() as db:
        return {
            "users": db.query(User).count(),
            "profiles": db.query(YouthProfile).count(),
            "saved_sites": db.query(SavedSite).count(),
            "admins": db.query(User).filter(User.role == USER_ROLE_ADMIN).count(),
        }


@app.get("/admin/users")
def admin_users(request: Request, limit: int = 50):
    require_admin(request)
    limit = min(max(limit, 1), 200)
    with db_session() as db:
        rows = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
        return {
            "total": len(rows),
            "items": [
                {
                    "id": u.id,
                    "email": u.email,
                    "phone": u.phone_e164,
                    "name": u.display_name,
                    "role": u.role or USER_ROLE_YOUTH,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in rows
            ],
        }


@app.post("/youth/matches")
def youth_matches(
    profile: YouthProfileRequest,
    limit: int = 30,
    category: Optional[str] = None,
    request: Request = None,
):
    """Rank verified opportunities for a youth profile."""
    limit = min(max(limit, 1), 50)
    pdata = profile.model_dump()
    category_filter = (category or "").strip().lower() or None
    if category_filter:
        category_filter = INTEREST_ALIASES.get(category_filter, category_filter)

    # If user is authenticated and payload is partial, fall back to stored profile.
    token = _bearer_token(request) if request else None
    if token:
        try:
            user = get_current_user(request)
            with db_session() as db:
                prof = db.query(YouthProfile).filter(YouthProfile.user_id == user.id).one_or_none()
            stored = _profile_dict(prof)
            for key in ("district", "age", "education"):
                if pdata.get(key) in (None, "", []):
                    pdata[key] = stored.get(key)
            if pdata.get("skills") is None:
                pdata["skills"] = stored.get("skills") or []
            if pdata.get("interests") is None:
                pdata["interests"] = stored.get("interests") or []
        except Exception:
            pass

    user_district = (pdata.get("district") or "").strip()
    if category_filter:
        pool = registry.list_all_opportunities(
            limit=300,
            category=category_filter,
            district=user_district or None,
        )
        if not pool and user_district:
            pool = registry.list_all_opportunities(limit=300, category=category_filter)
    elif user_district:
        pool = registry.list_all_opportunities(limit=200, district=user_district)
        if not pool:
            pool = []
    else:
        pool = registry.list_all_opportunities(limit=300)

    # Always enforce field-of-interest (skills) when present — no soft district-only fallback.
    matches = rank_opportunities(
        pdata,
        pool,
        limit=limit,
        category_filter=category_filter,
        strict_skills=True,
    )
    matches = _enrich_results_list(matches, pdata, list_view=True)
    opportunities = registry.list_all_opportunities(limit=300)
    radar = district_radar(opportunities, RWANDA_DISTRICTS)
    national_pool = []
    if user_district:
        national_raw = registry.list_all_opportunities(limit=60, district=None)
        national_raw = [o for o in national_raw if not (o.get("district") or "").strip()]
        national_pool = _enrich_results_list(national_raw[:12], pdata, list_view=True)
    return {
        "profile_completeness": profile_completeness(pdata),
        "matches": matches,
        "national_opportunities": national_pool,
        "district_filter": user_district or None,
        "category_filter": category_filter,
        "insights": ai_insights(matches, radar),
        "total_opportunities": len(opportunities),
    }


@app.get("/youth/radar")
def youth_radar():
    """District-level opportunity density for the radar map."""
    opportunities = registry.list_all_opportunities(limit=500)
    districts = district_radar(opportunities, RWANDA_DISTRICTS)
    demand = analytics.district_demand_all(days=30)
    gaps = district_gap_map(opportunities, demand, RWANDA_DISTRICTS)
    gap_by_name = {g["district"]: g for g in gaps}
    for d in districts:
        g = gap_by_name.get(d["district"], {})
        d["gap_level"] = g.get("gap_level", "balanced")
        d["demand"] = g.get("demand", 0)
        d["gap_score"] = g.get("gap_score", 0)
    return {
        "total": len(opportunities),
        "districts": districts,
        "gap_map": gaps,
    }


@app.get("/youth/gap-map")
def youth_gap_map(days: int = 30):
    opportunities = registry.list_all_opportunities(limit=500)
    demand = analytics.district_demand_all(days=min(max(days, 7), 90))
    gaps = district_gap_map(opportunities, demand, RWANDA_DISTRICTS)
    return {"days": days, "districts": gaps}


@app.get("/youth/impact")
def youth_impact():
    stats = registry.stats()
    opp_n = registry.count_opportunities()
    summary = analytics.summary(days=30)
    user_n = 0
    saved_n = 0
    try:
        with db_session() as db:
            from sqlalchemy import func
            user_n = db.query(func.count(User.id)).scalar() or 0
            saved_n = db.query(func.count(SavedSite.id)).scalar() or 0
    except Exception:
        pass
    return impact_stats(stats, opp_n, summary, user_n, saved_n)


@app.get("/youth/pathways")
def youth_pathways():
    return {"steps": pathway_steps()}


@app.post("/youth/eligibility")
def youth_eligibility(body: EligibilityRequest):
    pdata = body.profile.model_dump() if body.profile else {}
    return eligibility_verdict(pdata, body.opportunity or {})


@app.get("/youth/trust-explain")
def youth_trust_explain(url: str = "", title: str = ""):
    opp = {"url": url, "title": title, "trust_score": 75}
    return {"reasons": explain_trust(opp)}


@app.get("/registry/opportunities")
def registry_opportunities(
    limit: int = 200,
    category: Optional[str] = None,
    district: Optional[str] = None,
    q: str = "",
):
    """Individual job/scholarship/program listings extracted from verified portals."""
    limit = min(limit, 500)
    cat = category if category in CATEGORY_MAP else None
    if district:
        district_raw = registry.list_all_opportunities(
            limit=limit,
            category=cat,
            district=district,
            query_text=q,
            verified_only=True,
        )
        national_raw = registry.list_all_opportunities(
            limit=min(limit, 80),
            category=cat,
            district=None,
            query_text=q,
            verified_only=True,
        )
        national_raw = [o for o in national_raw if not (o.get("district") or "").strip()]
        district_items = _enrich_results_list(district_raw, list_view=True)
        national_items = _enrich_results_list(national_raw, list_view=True)
        return {
            "total": len(district_items) + len(national_items),
            "opportunities": district_items,
            "district_opportunities": district_items,
            "national_opportunities": national_items,
            "district_filter": district,
            "source": "registry",
        }

    items = registry.list_all_opportunities(
        limit=limit,
        category=cat,
        district=None,
        query_text=q,
        verified_only=True,
    )
    enriched = _enrich_results_list(items, list_view=True)
    return {
        "total": len(enriched),
        "opportunities": enriched,
        "district_opportunities": [o for o in enriched if (o.get("district") or "").strip()],
        "national_opportunities": [o for o in enriched if not (o.get("district") or "").strip()],
        "district_filter": None,
        "source": "registry",
    }


@app.get("/registry/websites")
def registry_websites(limit: int = 200):
    """Full list of AI-verified opportunity websites (all TLDs)."""
    limit = min(limit, 500)
    sites = registry.list_all_verified(limit=limit)
    return {
        "total": len(sites),
        "websites": sites,
        "source": "registry",
    }


@app.get("/registry/new")
def registry_new_websites(days: int = 7):
    """Websites first detected in the last N days — for MIFOTRA monitoring."""
    days = min(max(days, 1), 90)
    sites = registry.list_new_websites(days=days, verified_only=True)
    return {
        "days": days,
        "total_new": len(sites),
        "websites": sites,
    }


@app.get("/registry/report")
def registry_discovery_report(days: int = 7):
    """
    MIFOTRA discovery report: all verified sites, new detections, breakdown by .com/.org/.rw.
    """
    days = min(max(days, 1), 90)
    report = registry.discovery_report(new_days=days)
    report["all_verified_websites"] = registry.list_all_verified(limit=500)
    report["new_verified_websites"] = registry.list_new_websites(days=days, verified_only=True)
    return report


@app.get("/mifotra/staff-config")
def mifotra_staff_config():
    domains = allowed_domains()
    return {
        "email_required": staff_auth_required(),
        "allowed_domains": [f"@{d}" for d in domains],
        "hint": "@mifotra.gov.rw" if "mifotra.gov.rw" in domains else (
            f"@{domains[0]}" if domains else "any email (dev mode)"
        ),
    }


@app.post("/mifotra/verify-staff")
def mifotra_verify_staff(request: MifotraStaffRequest):
    email = (request.email or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid staff email required")
    if not verify_staff_login(email, request.password):
        allowed = ", ".join(f"@{d}" for d in allowed_domains()) or "@mifotra.gov.rw"
        raise HTTPException(
            status_code=401,
            detail=f"Invalid staff credentials. Use {allowed} and the institution password from MIFOTRA IT.",
        )
    token, expires_in = create_session()
    return {"ok": True, "token": token, "expires_in": expires_in, "email": email}


@app.get("/mifotra/dashboard")
def mifotra_dashboard(
    days: int = 30,
    x_mifotra_token: Optional[str] = Header(None, alias="X-Mifotra-Token"),
):
    """
    MIFOTRA unified dashboard: website registry + youth search analytics.
    Requires staff email session (X-Mifotra-Token header).
    """
    require_mifotra_session(x_mifotra_token)
    days = min(max(days, 1), 365)
    reg_report = registry.discovery_report(new_days=days)
    return {
        "days": days,
        "registry": {
            "verified_total": reg_report.get("verified_open", 0),
            "new_verified": reg_report.get("new_verified_last_days", 0),
            "new_domains_detected": reg_report.get("new_domains_detected_last_days", 0),
            "pending_verification": reg_report.get("pending_urls", 0),
            "verified_by_tld": reg_report.get("verified_by_tld", {}),
            "by_category": reg_report.get("by_category", {}),
            "last_refresh_at": reg_report.get("last_refresh_at"),
            "new_websites": registry.list_new_websites(days=min(days, 30), verified_only=True),
            "all_websites": registry.list_all_verified(limit=200),
        },
        "opportunities": {
            "listings_total": registry.count_opportunities(),
            "last_sync_at": registry.get_meta("last_opportunity_sync_at"),
            "last_sync_count": registry.get_meta("last_opportunity_sync_count"),
            "harvest_mode": registry.get_meta("last_opportunity_harvest_mode", ""),
        },
        "youth_analytics": analytics.dashboard(days),
    }


@app.post("/mifotra/harvest-opportunities")
def mifotra_harvest_opportunities(
    x_mifotra_token: Optional[str] = Header(None, alias="X-Mifotra-Token"),
):
    """MIFOTRA staff: start background re-crawl of all verified portals."""
    require_mifotra_session(x_mifotra_token)
    if registry.get_meta("harvest_in_progress") == "1":
        return {
            "ok": True,
            "started": False,
            "message": "Harvest already running",
            "last_sync_at": registry.get_meta("last_opportunity_sync_at"),
        }
    _run_opportunity_harvest_background("mifotra_manual")
    return {
        "ok": True,
        "started": True,
        "message": "Harvest started in background (10-20 min)",
        "last_sync_at": registry.get_meta("last_opportunity_sync_at"),
    }


@app.get("/registry/harvest-status")
def registry_harvest_status():
    stats = registry.stats()
    return {
        "verified_portals": stats.get("verified_open", 0),
        "opportunity_listings": stats.get("verified_opportunities", registry.count_opportunities()),
        "last_opportunity_sync_at": registry.get_meta("last_opportunity_sync_at"),
        "last_opportunity_sync_count": registry.get_meta("last_opportunity_sync_count"),
        "harvest_mode": registry.get_meta("last_opportunity_harvest_mode", ""),
        "harvest_in_progress": registry.get_meta("harvest_in_progress") == "1",
        "harvest_started_at": registry.get_meta("harvest_started_at", ""),
    }


@app.get("/browse/{category}")
def browse_category(category: str, limit: int = 25):
    """Instant list of verified websites for one category (Jobs, Scholarships, …)."""
    if category not in CATEGORY_MAP:
        raise HTTPException(status_code=400, detail=f"Unknown category. Use: {list(CATEGORY_MAP.keys())}")
    limit = min(limit, DEFAULT_MAX_RESULTS)
    results = registry.browse_category(category, limit=limit)
    stats = registry.stats()
    return {
        "category": category,
        "total_found": len(results),
        "results": results,
        "registry_size": stats.get("verified_open", 0),
        "last_refresh_at": stats.get("last_refresh_at") or "",
        "source": "registry",
    }


def _execute_search(request: SearchRequest) -> dict:
    """Run hybrid search and log analytics (shared by sync and async search paths)."""
    norm_category = normalize_search_category(request.category)
    max_results = min(request.max_results or DEFAULT_MAX_RESULTS, MAX_SEARCH_RESULTS)
    cat, text_filter = resolve_search(norm_category, request.query)
    cache_key = f"{cat or ''}|{text_filter}|{request.query.lower().strip()}|{(request.district or '').lower()}"

    print(f"\n-- Search: query='{request.query}' category={cat} terms='{text_filter}' district={request.district!r} --")
    response = hybrid_search_response(
        norm_category,
        request.query,
        max_results,
        district=request.district,
    )

    analytics.log_search(
        query=request.query,
        category=cat,
        district=request.district,
        results_count=response["total_found"],
    )

    print(f"-> {response['total_found']} verified opportunities ({response.get('source', '')})\n")

    search_cache[cache_key] = response
    return response


def _registry_only_search_response(
    category: Optional[str],
    query: str,
    max_results: int,
    district: Optional[str] = None,
) -> dict:
    """Fast registry-only slice for progressive search UI."""
    norm_category = normalize_search_category(category)
    cat, text_filter = resolve_search(norm_category, query)
    registry_results = registry.search_opportunities(
        category=cat,
        query_text=text_filter,
        limit=max_results,
        district=district,
        verified_only=True,
    )
    combined = dedupe_opportunities(registry_results)
    if cat or text_filter:
        combined = _rerank_results(combined, cat, query_tokens(text_filter or query))
    if district:
        combined = _prioritize_district(combined, district)
    from registry_db import filter_real_opportunities
    combined = filter_real_opportunities(combined, strict_category=cat)
    combined = combined[:max_results]
    stats = registry.stats()
    return {
        "query": query,
        "category": cat,
        "search_terms": text_filter,
        "district": district,
        "total_found": len(combined),
        "registry_count": len(combined),
        "verified": len(combined),
        "results": _enrich_results_list(combined),
        "registry_size": stats.get("verified_opportunities", 0) or stats.get("verified_open", 0),
        "last_refresh_at": stats.get("last_refresh_at") or "",
        "source": "registry",
    }


def _run_search_job(job_id: str, request: SearchRequest) -> None:
    import threading

    job = search_jobs.get(job_id)
    if not job:
        return
    max_results = min(request.max_results or DEFAULT_MAX_RESULTS, MAX_SEARCH_RESULTS)
    try:
        job["progress"] = 18
        job["message"] = "Searching verified registry..."
        partial = _registry_only_search_response(
            request.category,
            request.query,
            max_results,
            district=request.district,
        )
        job["partial_ready"] = True
        job["partial_result"] = partial
        job["progress"] = 45
        job["message"] = f"Found {partial['total_found']} in registry — checking live sources..."

        result = _execute_search(request)
        job["result"] = result
        job["progress"] = 100
        job["message"] = "Done"
        job["done"] = True
    except Exception as exc:
        print(f"Search job {job_id} failed: {exc}")
        job["error"] = str(exc)
        job["done"] = True
    finally:
        # Drop stale jobs after an hour to avoid unbounded memory use.
        def _expire():
            import time
            time.sleep(3600)
            search_jobs.pop(job_id, None)
        threading.Thread(target=_expire, daemon=True).start()


@app.post("/search/start")
def search_start(request: SearchRequest):
    import threading
    import uuid

    job_id = str(uuid.uuid4())
    search_jobs[job_id] = {
        "job_id": job_id,
        "done": False,
        "error": None,
        "partial_ready": False,
        "partial_result": None,
        "result": None,
        "progress": 8,
        "message": "Starting search...",
    }
    threading.Thread(target=_run_search_job, args=(job_id, request), daemon=True).start()
    return {"job_id": job_id}


@app.get("/search/job/{job_id}")
def search_job_status(job_id: str):
    job = search_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not Found")
    return job


@app.post("/search")
def search(request: SearchRequest):
    try:
        return _execute_search(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _assistant_site_lines(results: List[dict], is_rw: bool = False) -> str:
    if not results:
        return (
            "(Nta mbuga zemewe muri registry — koresha build_registry.py refresh.)"
            if is_rw else
            "(No verified websites in registry yet — run build_registry.py refresh.)"
        )
    cat_rw = {
        "scholarship": "uburenganzira",
        "job": "akazi",
        "internship": "imyitozo",
        "training": "amahugurwa",
        "program": "gahunda",
        "free_course": "amasomo yubuntu",
    }
    lines = []
    for i, r in enumerate(results[:12], 1):
        trust = r.get("trust_score", "")
        if isinstance(trust, (int, float)):
            trust = f"{trust:.2f}" if trust <= 1 else f"{trust:.0f}"
        cat = r.get("category", "program")
        cat_label = cat_rw.get(str(cat).lower(), cat) if is_rw else cat
        type_label = "Ubwoko" if is_rw else "Type"
        trust_label = "Icyizere" if is_rw else "Trust"
        about_label = "Ibyerekeye" if is_rw else "About"
        lines.append(
            f"{i}. {r.get('title', r.get('domain', 'Site'))}\n"
            f"   URL: {r.get('url', '')}\n"
            f"   {type_label}: {cat_label} | {trust_label}: {trust}\n"
            f"   {about_label}: {(r.get('snippet') or '')[:200]}"
        )
    return "\n".join(lines)


def assistant_registry_context(user_message: str) -> tuple:
    """Pull verified websites relevant to what the user asked."""
    cat, terms = resolve_search(None, user_message)
    query_text = terms or user_message
    results = registry.search(category=cat, query_text=query_text, limit=12, verified_only=True)
    if not results and cat:
        results = registry.search(category=cat, query_text="", limit=12, verified_only=True)
    if not results:
        results = registry.search(category=None, query_text=query_text, limit=12, verified_only=True)
    if cat or query_tokens(query_text):
        results = _rerank_results(results, cat, query_tokens(query_text))
    return cat, results


def assistant_fallback_reply(message: str, language: str, results: List[dict]) -> str:
    """Return a grounded answer from the verified registry."""
    is_rw = language and language.lower() == "kinyarwanda"
    if not results:
        return (
            "Nta mbuga zemewe zabonetse. Koresha gushakisha cyangwa tegereza ko registry refresh yakoze."
            if is_rw else
            "I could not find verified websites for that yet. Try Search, or run registry refresh on the server."
        )
    intro = (
        f"Nashyize ikibazo cyawe muri registry yemewe ya Inzira nsanga izi mbuga {len(results)} zegereye icyo ushaka:"
        if is_rw else
        f"I matched your question against Inzira's verified registry and found these {len(results)} closest results:"
    )
    body = []
    for r in results[:8]:
        title = r.get("title", r.get("domain", "Website"))
        url = r.get("url", "")
        cat = r.get("category", "opportunity")
        cat_rw = {
            "scholarship": "uburenganzira", "job": "akazi", "internship": "imyitozo",
            "training": "amahugurwa", "program": "gahunda", "free_course": "amasomo yubuntu",
        }
        if is_rw:
            cat = cat_rw.get(str(cat).lower(), cat)
        body.append(f"- {title} ({cat})\n  {url}")
    tail = (
        "Sura urubuga rwemewe kugirango usabe."
        if is_rw else
        "Visit the official website to apply. Use Search in the app for more."
    )
    return intro + "\n\n" + "\n\n".join(body) + "\n\n" + tail


@app.post("/assistant")
def assistant(request: AIAssistantRequest):
    try:
        user_message = (request.message or "").strip()
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")

        cat, registry_results = assistant_registry_context(user_message)
        is_rw = request.language and request.language.lower() == "kinyarwanda"
        print(f"\n-- Assistant: '{user_message[:60]}' category={cat} sites={len(registry_results)} --")
        reply = assistant_fallback_reply(user_message, request.language or "english", registry_results)
        return {
            "response": reply,
            "language": request.language,
            "source": "registry",
            "sites_used": len(registry_results),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"  Assistant error: {e}")
        try:
            _, registry_results = assistant_registry_context(request.message or "")
            return {
                "response": assistant_fallback_reply(
                    request.message or "", request.language or "english", registry_results
                ),
                "language": request.language,
                "source": "registry_fallback",
                "sites_used": len(registry_results),
            }
        except Exception:
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = server_port(8000)
    print(f"Starting Inzira on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)