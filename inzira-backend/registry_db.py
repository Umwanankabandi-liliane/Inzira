"""
SQLite registry of verified Rwanda websites that host opportunities.
This is the long-term map Inzira searches — discovery scripts grow it over time.
"""

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hosts_label(categories: List[str]) -> str:
    labels = {
        "scholarship": "scholarships",
        "job": "jobs",
        "internship": "internships",
        "training": "training",
        "competition": "competitions",
        "program": "programs",
        "free_course": "free courses",
    }
    parts = [labels.get(c, c.replace("_", " ")) for c in categories]
    return ", ".join(parts)


def website_snippet(name: str, categories: List[str]) -> str:
    hosts = hosts_label(categories)
    return f"Website hosting {hosts} that Rwandans can browse and apply for on the official site."


SEARCH_STOPWORDS = frozenset({
    "the", "and", "for", "in", "to", "of", "a", "an", "rwanda", "youth", "all",
    "opportunity", "opportunities", "website", "websites", "apply", "open", "hosting",
    "that", "can", "browse", "official", "site", "with", "from", "your", "our",
    "kigali", "country", "national", "nationwide", "east", "africa", "african",
})

GEO_STOPWORDS = frozenset({
    "rwanda", "kigali", "country", "national", "nationwide", "east", "africa", "african",
})

CATEGORY_CHIP_WORDS = frozenset({
    "job", "jobs", "scholarship", "scholarships", "internship", "internships",
    "training", "trainings", "program", "programs", "programme", "programmes", "competition",
    "competitions", "course", "courses", "intern", "career", "careers",
    "amahugurwa", "akazi", "uburenganzira", "imyitozo", "gahunda", "amarushanwa",
})

KIN_CATEGORY_WORDS = {
    "akazi": "job",
    "amahugurwa": "training",
    "uburenganzira": "scholarship",
    "imyitozo": "internship",
    "gahunda": "program",
    "amarushanwa": "competition",
}

GENERIC_PORTAL_TITLE_RE = re.compile(
    r"^(Open job vacancies|Scholarships? & grants?|Internship openings?|"
    r"Training programs?|Competitions? & challenges?|Youth programs?|"
    r"Free courses?|Opportunities) at ",
    re.I,
)

PORTAL_SNIPPET_PREFIX = "[portal] "
EXTRACTED_SNIPPET_PREFIX = "[listing] "

DOMAIN_CATEGORY_HINTS = {
    "job": ("job", "career", "hire", "vacancy", "employment"),
    "scholarship": ("scholar", "hec", "edu", "bursary", "grant"),
    "internship": ("intern", "trainee"),
    "training": ("wda", "train", "tvet", "skills"),
    "program": ("program", "gov.rw", "fellowship"),
    "competition": ("competition", "challenge", "hack"),
    "free_course": ("course", "mooc", "learn"),
}


def is_portal_summary_listing(item: dict) -> bool:
    title = (item.get("title") or "").strip()
    if GENERIC_PORTAL_TITLE_RE.match(title):
        return True
    try:
        from opportunity_extractor import is_junk_listing_title
        if is_junk_listing_title(title):
            return True
    except Exception:
        pass
    snippet = (item.get("snippet") or "").strip()
    return snippet.startswith(PORTAL_SNIPPET_PREFIX)


def filter_real_opportunities(
    items: List[dict],
    *,
    strict_category: Optional[str] = None,
    allow_portal_summaries: bool = False,
) -> List[dict]:
    """Return scraped listings only; drop generic portal placeholder cards."""
    if not items:
        return []

    merged: List[dict] = []
    if allow_portal_summaries:
        merged = list(items)
    else:
        by_domain: Dict[str, List[dict]] = {}
        for item in items:
            domain = (item.get("source_domain") or item.get("domain") or "").lower()
            by_domain.setdefault(domain, []).append(item)

        for group in by_domain.values():
            real = [g for g in group if not is_portal_summary_listing(g)]
            merged.extend(real)

    try:
        from opportunity_extractor import (
            align_category_with_title,
            is_junk_listing_title,
            polish_listing_title,
        )
        cleaned: List[dict] = []
        for item in merged:
            title = polish_listing_title(item.get("title") or "")
            if is_junk_listing_title(title):
                continue
            item = dict(item)
            item["title"] = title
            try:
                from listing_curation import is_ur_admission, normalize_ur_admission_fields
                if is_ur_admission(item):
                    item = normalize_ur_admission_fields(item)
                else:
                    item["category"] = align_category_with_title(
                        title, item.get("category") or "program", item.get("snippet") or "",
                    )
            except Exception:
                item["category"] = align_category_with_title(
                    title, item.get("category") or "program", item.get("snippet") or "",
                )
            item["categories"] = [item["category"]]
            cleaned.append(item)
        merged = cleaned
    except Exception:
        pass

    if strict_category:
        cat = strict_category.lower().strip()
        merged = [o for o in merged if (o.get("category") or "").lower() == cat]

    try:
        from listing_quality import filter_publishable
        merged = filter_publishable(merged)
    except Exception:
        pass

    return merged


def query_tokens(query_text: str) -> List[str]:
    tokens = []
    for raw in re.split(r"\W+", (query_text or "").lower()):
        if len(raw) < 3 or raw in SEARCH_STOPWORDS or raw in CATEGORY_CHIP_WORDS:
            continue
        if raw in GEO_STOPWORDS:
            continue
        tokens.append(raw)
    return tokens


def _deadline_rank_bonus(deadline: str) -> float:
    if not (deadline or "").strip():
        return 0.0
    bonus = 8.0
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", deadline)
    if not m:
        return bonus
    try:
        from datetime import date
        dl = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        today = date.today()
        days = (dl - today).days
        if days < 0:
            return -6.0
        if days <= 14:
            return bonus + 14.0
        if days <= 45:
            return bonus + 8.0
    except ValueError:
        pass
    return bonus


def _specialist_score(row: sqlite3.Row, category: Optional[str], tokens: List[str]) -> float:
    cats = json.loads(row["categories"])
    score = float(row["trust_score"] or 0)
    domain = (row["domain"] or "").lower()
    blob = f"{row['name']} {domain} {row['snippet'] or ''} {' '.join(cats)}".lower()

    for i, tok in enumerate(tokens):
        if tok in blob:
            score += 14 + max(0, 4 - i)

    if category:
        if category not in cats:
            return -9999.0
        n = len(cats)
        if n == 1:
            score += 18
        elif n == 2:
            score += 10
        elif n == 3:
            score += 4
        elif n >= 5:
            score -= 18
        for hint in DOMAIN_CATEGORY_HINTS.get(category, ()):
            if hint in domain:
                score += 10

    return score


def _opportunity_score(row: sqlite3.Row, category: Optional[str], tokens: List[str]) -> float:
    score = float(row["trust_score"] or 0)
    cat = (row["category"] or "").lower()
    blob = f"{row['title']} {row['organization']} {row['snippet'] or ''} {cat} {row['source_domain']}".lower()

    for i, tok in enumerate(tokens):
        if tok in blob:
            score += 14 + max(0, 4 - i)

    score += _deadline_rank_bonus(row["deadline"] or "")

    if category:
        if cat != category:
            return -9999.0
        score += 16
        domain = (row["source_domain"] or "").lower()
        if domain.endswith(".gov.rw"):
            score += 22
        elif domain.endswith(".rw") or domain.endswith(".ac.rw"):
            score += 14
        for hint in DOMAIN_CATEGORY_HINTS.get(category, ()):
            if hint in domain:
                score += 8

    return score


def _effective_listing_trust(
    portal_trust: float,
    *,
    title: str,
    snippet: str,
    deadline: str,
    district: str,
) -> float:
    """
    Listing-level trust — not the same as portal trust.
    Avoids every card showing 100% when only the parent site was verified.
    """
    base = portal_trust if portal_trust > 1 else portal_trust * 100
    score = base * 0.55 + 25
    if (deadline or "").strip():
        score += 18
    if (district or "").strip():
        score += 12
    if snippet and len(snippet) > 40:
        score += 8
    if len(title) >= 20:
        score += 5
    return round(min(96.0, max(58.0, score)), 1)


def _tld_bucket(domain: str) -> str:
    if domain.endswith(".gov.rw"):
        return ".gov.rw"
    if domain.endswith(".ac.rw"):
        return ".ac.rw"
    if domain.endswith(".rw"):
        return ".rw"
    if domain.endswith(".org"):
        return ".org"
    if domain.endswith(".com"):
        return ".com"
    parts = domain.rsplit(".", 1)
    return f".{parts[-1]}" if len(parts) > 1 else "other"


def _days_ago_iso(days: int) -> str:
    from datetime import timedelta
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    return dt.isoformat()


class Registry:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS websites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    categories TEXT NOT NULL,
                    trust_score REAL DEFAULT 0,
                    has_open_applications INTEGER DEFAULT 0,
                    verified INTEGER DEFAULT 0,
                    snippet TEXT DEFAULT '',
                    organization TEXT DEFAULT '',
                    deadline TEXT DEFAULT '',
                    eligibility TEXT DEFAULT '',
                    location TEXT DEFAULT 'Rwanda',
                    apply_link TEXT DEFAULT '',
                    source TEXT DEFAULT 'seed',
                    last_checked TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS pending_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    domain TEXT NOT NULL,
                    suggested_category TEXT,
                    discovered_via TEXT DEFAULT '',
                    discovered_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_websites_verified
                    ON websites(verified, has_open_applications);

                CREATE TABLE IF NOT EXISTS registry_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS discovery_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    discovered_at TEXT NOT NULL,
                    method TEXT NOT NULL,
                    category TEXT,
                    detail TEXT DEFAULT '',
                    is_new_domain INTEGER DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_discovery_domain
                    ON discovery_log(domain);
                CREATE INDEX IF NOT EXISTS idx_discovery_at
                    ON discovery_log(discovered_at);
                CREATE INDEX IF NOT EXISTS idx_websites_created
                    ON websites(created_at);

                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    organization TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    district TEXT DEFAULT '',
                    deadline TEXT DEFAULT '',
                    snippet TEXT DEFAULT '',
                    apply_url TEXT NOT NULL,
                    source_url TEXT DEFAULT '',
                    source_domain TEXT NOT NULL,
                    scope TEXT DEFAULT '',
                    trust_score REAL DEFAULT 0,
                    verified INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    UNIQUE(title, apply_url, source_domain)
                );

                CREATE INDEX IF NOT EXISTS idx_opportunities_verified
                    ON opportunities(verified, category);
                CREATE INDEX IF NOT EXISTS idx_opportunities_domain
                    ON opportunities(source_domain);
                CREATE INDEX IF NOT EXISTS idx_opportunities_district
                    ON opportunities(district);

                CREATE TABLE IF NOT EXISTS search_harvest_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    category TEXT DEFAULT '',
                    district TEXT DEFAULT '',
                    enqueued_at TEXT NOT NULL,
                    processed_at TEXT DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_search_harvest_pending
                    ON search_harvest_queue(processed_at, enqueued_at);
            """)
            # Lightweight migration for older DBs
            try:
                conn.execute("ALTER TABLE opportunities ADD COLUMN scope TEXT DEFAULT ''")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE opportunities ADD COLUMN subtype TEXT DEFAULT ''")
            except Exception:
                pass

    def get_meta(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM registry_meta WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO registry_meta (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))

    def domain_exists(self, domain: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM websites WHERE domain = ? UNION SELECT 1 FROM pending_urls WHERE domain = ? LIMIT 1",
                (domain, domain),
            ).fetchone()
        return row is not None

    def register_discovery(
        self,
        domain: str,
        url: str,
        category: Optional[str],
        method: str,
        detail: str = "",
    ) -> bool:
        """Log discovery event. Returns True if this domain was never seen before."""
        is_new = not self.domain_exists(domain)
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO discovery_log
                (domain, discovered_at, method, category, detail, is_new_domain)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (domain, _utc_now(), method, category, detail, 1 if is_new else 0))
        return is_new

    def list_crawl_seeds(self, limit: int = 25) -> List[sqlite3.Row]:
        """Verified portals + high-trust sites to crawl for outbound links."""
        with self._connect() as conn:
            return conn.execute("""
                SELECT domain, name, url FROM websites
                WHERE verified = 1
                ORDER BY trust_score DESC
                LIMIT ?
            """, (limit,)).fetchall()

    def list_all_verified(self, limit: int = 500) -> List[dict]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM websites
                WHERE verified = 1 AND has_open_applications = 1
                ORDER BY trust_score DESC, created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
        return [self.row_to_api_result(r) for r in rows]

    def list_verified_rows(self, limit: int = 500) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("""
                SELECT * FROM websites
                WHERE verified = 1 AND has_open_applications = 1
                ORDER BY trust_score DESC, created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()

    def count_opportunities(self, verified_only: bool = True) -> int:
        clause = "WHERE verified = 1" if verified_only else ""
        with self._connect() as conn:
            return conn.execute(f"SELECT COUNT(*) FROM opportunities {clause}").fetchone()[0]

    def count_verified_websites(self) -> int:
        with self._connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM websites WHERE verified = 1"
            ).fetchone()[0]

    def count_districts_with_listings(self) -> int:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT COUNT(DISTINCT TRIM(district)) FROM opportunities
                WHERE verified = 1 AND TRIM(COALESCE(district, '')) != ''
                """
            ).fetchone()[0]

    def district_listing_coverage(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT TRIM(district) AS district, COUNT(*) AS listings
                FROM opportunities
                WHERE verified = 1 AND TRIM(COALESCE(district, '')) != ''
                GROUP BY TRIM(district)
                ORDER BY listings DESC
                """
            ).fetchall()
        return [{"district": r["district"], "listings": r["listings"]} for r in rows]

    def count_verified_websites_between(self, start_iso: str, end_iso: str) -> int:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT COUNT(*) FROM websites
                WHERE verified = 1 AND created_at >= ? AND created_at < ?
                """,
                (start_iso, end_iso),
            ).fetchone()[0]

    def purge_unpublishable_listings(self) -> int:
        """Remove expired, foreign-only, junk, and auto-curated reject rows."""
        from opportunity_extractor import align_category_with_title, polish_listing_title
        from listing_curation import should_auto_purge, is_ur_admission

        removed = 0
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, title, category, snippet, location, organization, deadline, "
                "apply_url, source_url, source_domain, subtype FROM opportunities"
            ).fetchall()
            for row in rows:
                item = {
                    "title": polish_listing_title(row["title"] or ""),
                    "category": row["category"] or "program",
                    "snippet": row["snippet"] or "",
                    "location": row["location"] or "",
                    "organization": row["organization"] or "",
                    "deadline": row["deadline"] or "",
                    "apply_url": row["apply_url"] or "",
                    "source_url": row["source_url"] or "",
                    "source_domain": row["source_domain"] or "",
                    "subtype": row["subtype"] or "",
                }
                if is_ur_admission(item):
                    conn.execute(
                        "UPDATE opportunities SET subtype = 'admission', category = 'program' WHERE id = ?",
                        (row["id"],),
                    )
                    continue
                reason = should_auto_purge(item)
                if reason:
                    conn.execute("DELETE FROM opportunities WHERE id = ?", (row["id"],))
                    removed += 1
                    continue
                from listing_quality import is_publishable_listing
                item["category"] = align_category_with_title(
                    item["title"], item["category"], item["snippet"],
                )
                if not is_publishable_listing(item):
                    conn.execute("DELETE FROM opportunities WHERE id = ?", (row["id"],))
                    removed += 1
        return removed

    def purge_past_deadlines(self) -> int:
        """Remove listings whose stored deadline is today or earlier."""
        try:
            from inzira_features import deadline_guardian
        except Exception:
            return 0
        removed = 0
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, deadline FROM opportunities WHERE COALESCE(deadline, '') != ''"
            ).fetchall()
            for row in rows:
                st = deadline_guardian(row["deadline"] or "")
                days = st.get("days_left")
                if st.get("status") == "expired" or (days is not None and days <= 0):
                    conn.execute("DELETE FROM opportunities WHERE id = ?", (row["id"],))
                    removed += 1
        return removed

    def delete_opportunities_for_domain(self, source_domain: str) -> None:
        if not source_domain:
            return
        with self._connect() as conn:
            conn.execute("DELETE FROM opportunities WHERE source_domain = ?", (source_domain,))

    def deactivate_domain(self, domain: str) -> tuple[int, int]:
        """Mark website unverified and delete all its opportunity rows."""
        dom = (domain or "").strip().lower().replace("www.", "")
        if not dom:
            return 0, 0
        with self._connect() as conn:
            cur = conn.execute(
                """
                UPDATE websites
                SET verified = 0, has_open_applications = 0, last_checked = ?
                WHERE REPLACE(LOWER(domain), 'www.', '') LIKE ?
                """,
                (_utc_now(), f"%{dom}%"),
            )
            sites = cur.rowcount
            cur2 = conn.execute(
                "DELETE FROM opportunities WHERE REPLACE(LOWER(source_domain), 'www.', '') LIKE ?",
                (f"%{dom}%",),
            )
            opps = cur2.rowcount
        return sites, opps

    def upsert_live_listings(self, items: List[dict]) -> int:
        """Insert or update individual listings from fast live search (no domain wipe)."""
        if not items:
            return 0
        try:
            from listing_quality import dedupe_listings
            items = dedupe_listings(items)
        except Exception:
            pass
        now = _utc_now()
        saved = 0
        with self._connect() as conn:
            for item in items:
                if is_portal_summary_listing(item):
                    continue
                title = (item.get("title") or "").strip()
                from listing_curation import coalesce_apply_urls
                apply_url, source_url = coalesce_apply_urls(item)
                from rwanda_sources import domain_of as _domain_of
                source_domain = (item.get("source_domain") or _domain_of(apply_url) or "").strip()
                if not title or not apply_url or not source_domain:
                    continue
                from opportunity_extractor import align_category_with_title
                item_cat = align_category_with_title(
                    title, item.get("category") or "program", item.get("snippet") or "",
                )
                conn.execute("""
                    INSERT INTO opportunities (
                        title, category, organization, location, district, deadline,
                        snippet, apply_url, source_url, source_domain, trust_score,
                        verified, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ON CONFLICT(title, apply_url, source_domain) DO UPDATE SET
                        category = excluded.category,
                        organization = excluded.organization,
                        location = excluded.location,
                        district = excluded.district,
                        deadline = excluded.deadline,
                        snippet = excluded.snippet,
                        source_url = excluded.source_url,
                        trust_score = excluded.trust_score,
                        verified = 1
                """, (
                    title,
                    item_cat,
                    item.get("organization") or "",
                    item.get("location") or "",
                    item.get("district") or "",
                    item.get("deadline") or "",
                    item.get("snippet") or "",
                    apply_url,
                    source_url,
                    source_domain,
                    float(item.get("trust_score") or 0),
                    now,
                ))
                saved += 1
        return saved

    def list_opportunities_for_revalidation(self, limit: int = 400) -> List[dict]:
        """Active verified listings for live URL re-check."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, apply_url, source_url, deadline, category
                FROM opportunities
                WHERE verified = 1
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (max(1, int(limit)),),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_opportunity_by_id(self, opp_id: int) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM opportunities WHERE id = ?", (int(opp_id),))
            return cur.rowcount > 0

    def count_opportunities_for_domain(self, source_domain: str) -> int:
        if not source_domain:
            return 0
        with self._connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE source_domain = ?",
                (source_domain,),
            ).fetchone()[0]

    def list_apply_urls_for_domain(self, source_domain: str) -> List[str]:
        if not source_domain:
            return []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT apply_url FROM opportunities WHERE source_domain = ?",
                (source_domain,),
            ).fetchall()
        return [r["apply_url"] for r in rows if r["apply_url"]]

    def _normalize_apply_url(self, url: str) -> str:
        from site_crawler import normalize_url
        return normalize_url((url or "").strip())

    def _purge_expired_for_domain(self, conn, source_domain: str) -> int:
        try:
            from inzira_features import deadline_guardian
        except Exception:
            return 0
        removed = 0
        rows = conn.execute(
            "SELECT id, deadline FROM opportunities WHERE source_domain = ?",
            (source_domain,),
        ).fetchall()
        for row in rows:
            st = deadline_guardian(row["deadline"] or "")
            if st.get("status") == "expired":
                conn.execute("DELETE FROM opportunities WHERE id = ?", (row["id"],))
                removed += 1
        return removed

    def replace_opportunities_for_domain(
        self,
        source_domain: str,
        items: List[dict],
        *,
        seen_apply_urls: Optional[List[str]] = None,
    ) -> int:
        """
        Upsert harvest results and mark seen detail URLs.
        Removes only listings missing from this crawl (gone from site) or expired deadlines.
        Hash-skipped (unchanged) pages keep their existing rows.
        """
        if not source_domain:
            return 0
        try:
            from listing_quality import dedupe_listings
            items = dedupe_listings(items)
        except Exception:
            pass
        try:
            from record_normalizer import normalize_registry_item
        except Exception:
            normalize_registry_item = None
        now = _utc_now()
        seen_norm = {
            self._normalize_apply_url(u)
            for u in (seen_apply_urls or [])
            if u
        }
        with self._connect() as conn:
            saved = 0
            for item in items:
                if is_portal_summary_listing(item):
                    continue
                if normalize_registry_item:
                    item = normalize_registry_item(item, domain=source_domain)
                title = (item.get("title") or "").strip()
                from listing_curation import coalesce_apply_urls
                apply_url, source_url = coalesce_apply_urls(item)
                if not title or not apply_url:
                    continue
                from opportunity_extractor import align_category_with_title, is_procurement_listing
                snippet = (item.get("snippet") or "").strip()
                if is_procurement_listing(title, snippet):
                    continue
                try:
                    from rwanda_relevance import listing_scope
                    scope = listing_scope({**item, "source_domain": source_domain, "apply_url": apply_url})
                except Exception:
                    scope = ""
                item_cat = align_category_with_title(
                    title, item.get("category") or "program", item.get("snippet") or "",
                )
                conn.execute("""
                    INSERT INTO opportunities (
                        title, category, organization, location, district, deadline,
                        snippet, apply_url, source_url, source_domain, scope, trust_score,
                        verified, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                    ON CONFLICT(title, apply_url, source_domain) DO UPDATE SET
                        category = excluded.category,
                        organization = excluded.organization,
                        location = excluded.location,
                        district = excluded.district,
                        deadline = excluded.deadline,
                        snippet = excluded.snippet,
                        source_url = excluded.source_url,
                        scope = excluded.scope,
                        trust_score = excluded.trust_score,
                        verified = 1
                """, (
                    title,
                    item_cat,
                    item.get("organization") or "",
                    item.get("location") or "",
                    item.get("district") or "",
                    item.get("deadline") or "",
                    item.get("snippet") or "",
                    apply_url,
                    source_url,
                    source_domain,
                    scope,
                    float(item.get("trust_score") or 0),
                    now,
                ))
                saved += 1

            if seen_norm:
                rows = conn.execute(
                    "SELECT id, apply_url FROM opportunities WHERE source_domain = ?",
                    (source_domain,),
                ).fetchall()
                for row in rows:
                    norm = self._normalize_apply_url(row["apply_url"] or "")
                    if norm and norm not in seen_norm:
                        conn.execute("DELETE FROM opportunities WHERE id = ?", (row["id"],))

            self._purge_expired_for_domain(conn, source_domain)

        return self.count_opportunities_for_domain(source_domain)

    def opportunity_row_to_api(self, row: sqlite3.Row) -> dict:
        created = row["created_at"] or ""
        is_new = created >= _days_ago_iso(7) if created else False
        domain = row["source_domain"] or ""
        from opportunity_extractor import (
            EXTRACTED_SNIPPET_PREFIX,
            align_category_with_title,
            clean_organization,
            polish_listing_title,
        )
        title = polish_listing_title(row["title"] or "")
        snippet = (row["snippet"] or "").strip()
        if snippet.startswith(EXTRACTED_SNIPPET_PREFIX):
            snippet = snippet[len(EXTRACTED_SNIPPET_PREFIX):]
        cat = align_category_with_title(
            title, row["category"] or "program", snippet,
        )
        org = clean_organization(
            row["organization"] or "",
            row["source_domain"] or "",
            title,
        )
        location = (row["location"] or "").strip()
        district = (row["district"] or "").strip()
        if not location and district:
            location = f"{district}, Rwanda"
        trust = _effective_listing_trust(
            float(row["trust_score"] or 0),
            title=title,
            snippet=snippet,
            deadline=row["deadline"] or "",
            district=district,
        )
        from listing_curation import (
            is_ur_admission,
            normalize_ur_admission_fields,
            resolve_apply_link,
        )
        base = normalize_ur_admission_fields({
            "id": row["id"],
            "title": title,
            "category": cat,
            "snippet": snippet,
            "organization": org,
            "deadline": row["deadline"] or "",
            "location": location,
            "district": district,
            "scope": (row["scope"] or "").strip(),
            "apply_url": row["apply_url"] or "",
            "source_url": row["source_url"] or "",
            "source_domain": domain,
            "subtype": (row["subtype"] if "subtype" in row.keys() else "") or "",
        })
        cat = base.get("category") or cat
        apply_url, apply_label = resolve_apply_link(base)
        needs_manual_search = apply_label in ("search_on_site",)
        return {
            "id": row["id"],
            "url": apply_url,
            "title": title,
            "category": cat,
            "categories": [cat],
            "trust_score": trust,
            "organization": org,
            "deadline": row["deadline"] or "",
            "eligibility": "",
            "location": location,
            "district": district,
            "scope": (row["scope"] or "").strip(),
            "apply_link": apply_url,
            "apply_label": apply_label,
            "needs_manual_search": needs_manual_search,
            "snippet": snippet,
            "last_verified": "",
            "domain": domain,
            "source_domain": domain,
            "source_url": row["source_url"] or "",
            "tld": _tld_bucket(domain),
            "first_seen": created,
            "is_new": is_new,
            "source": "registry",
            "subtype": base.get("subtype") or "",
            "is_admission": is_ur_admission(base) or base.get("subtype") == "admission",
        }

    def list_all_opportunities(
        self,
        limit: int = 200,
        category: Optional[str] = None,
        district: Optional[str] = None,
        query_text: str = "",
        verified_only: bool = True,
    ) -> List[dict]:
        rows = self._search_opportunity_rows(
            category=category,
            query_text=query_text,
            district=district,
            limit=limit,
            verified_only=verified_only,
        )
        return filter_real_opportunities(
            [self.opportunity_row_to_api(r) for r in rows],
            strict_category=category,
        )

    def search_opportunities(
        self,
        category: Optional[str],
        query_text: str = "",
        limit: int = 20,
        district: Optional[str] = None,
        verified_only: bool = True,
    ) -> List[dict]:
        tokens = query_tokens(query_text)
        if category and not tokens and not district:
            fetch_limit = max(limit * 3, 120)
        else:
            fetch_limit = max(limit * 4, 60) if category or tokens or district else limit * 2
        rows = self._search_opportunity_rows(
            category=category,
            query_text=query_text,
            district=district,
            limit=fetch_limit,
            verified_only=verified_only,
            tokens=tokens,
        )
        if category or tokens:
            rows = sorted(
                rows,
                key=lambda r: _opportunity_score(r, category, tokens),
                reverse=True,
            )
        api_rows = [self.opportunity_row_to_api(r) for r in rows[:limit]]
        return filter_real_opportunities(api_rows, strict_category=category)

    def _search_opportunity_rows(
        self,
        category: Optional[str],
        query_text: str,
        district: Optional[str],
        limit: int,
        verified_only: bool,
        tokens: Optional[List[str]] = None,
    ) -> List[sqlite3.Row]:
        tokens = tokens if tokens is not None else query_tokens(query_text)
        site_only = re.match(r"^site:([\w.-]+)\s*$", (query_text or "").strip(), re.I)
        # When filtering by category, fetch extra rows — title alignment may reclassify many items.
        fetch_limit = limit * 6 if category else limit
        clauses = []
        params: list = []

        if verified_only:
            clauses.append("verified = 1")

        if category:
            clauses.append("category = ?")
            params.append(category)

        if district:
            d = district.strip().lower()
            # Only listings where we actually detected this district in the listing text.
            clauses.append("LOWER(district) = ?")
            params.append(d)

        if site_only:
            dom = site_only.group(1).lower().replace("www.", "")
            clauses.append("REPLACE(LOWER(source_domain), 'www.', '') LIKE ?")
            params.append(f"%{dom}%")
        elif tokens:
            token_parts = []
            for tok in tokens:
                token_parts.append(
                    "(LOWER(title) LIKE ? OR LOWER(organization) LIKE ? OR LOWER(snippet) LIKE ? "
                    "OR LOWER(source_domain) LIKE ? OR LOWER(category) LIKE ?)"
                )
                like = f"%{tok}%"
                params.extend([like, like, like, like, like])
            clauses.append("(" + " OR ".join(token_parts) + ")")
        elif query_text.strip():
            q = f"%{query_text.strip().lower()}%"
            clauses.append(
                "(LOWER(title) LIKE ? OR LOWER(organization) LIKE ? OR LOWER(snippet) LIKE ? OR LOWER(category) LIKE ?)"
            )
            params.extend([q, q, q, q])

        where = " AND ".join(clauses) if clauses else "1=1"
        sql = f"""
            SELECT * FROM opportunities
            WHERE {where}
            ORDER BY trust_score DESC, created_at DESC, title ASC
            LIMIT ?
        """
        params.append(fetch_limit)
        with self._connect() as conn:
            return conn.execute(sql, params).fetchall()

    def list_new_websites(self, days: int = 7, verified_only: bool = True) -> List[dict]:
        since = _days_ago_iso(days)
        clauses = ["created_at >= ?"]
        params: list = [since]
        if verified_only:
            clauses.append("verified = 1 AND has_open_applications = 1")
        where = " AND ".join(clauses)
        with self._connect() as conn:
            rows = conn.execute(f"""
                SELECT * FROM websites WHERE {where}
                ORDER BY created_at DESC
            """, params).fetchall()
        return [self.row_to_api_result(r) for r in rows]

    def discovery_report(self, new_days: int = 7) -> Dict[str, Any]:
        since = _days_ago_iso(new_days)
        with self._connect() as conn:
            verified_rows = conn.execute("""
                SELECT domain FROM websites
                WHERE verified = 1 AND has_open_applications = 1
            """).fetchall()
            by_tld: Dict[str, int] = {}
            for row in verified_rows:
                bucket = _tld_bucket(row["domain"])
                by_tld[bucket] = by_tld.get(bucket, 0) + 1

            new_verified = conn.execute("""
                SELECT COUNT(*) FROM websites
                WHERE verified = 1 AND has_open_applications = 1 AND created_at >= ?
            """, (since,)).fetchone()[0]

            new_logged = conn.execute("""
                SELECT COUNT(DISTINCT domain) FROM discovery_log
                WHERE is_new_domain = 1 AND discovered_at >= ?
            """, (since,)).fetchone()[0]

            recent_discoveries = conn.execute("""
                SELECT domain, discovered_at, method, category, detail, is_new_domain
                FROM discovery_log
                WHERE discovered_at >= ?
                ORDER BY discovered_at DESC
                LIMIT 50
            """, (since,)).fetchall()

        stats = self.stats()
        return {
            **stats,
            "new_verified_last_days": new_verified,
            "new_domains_detected_last_days": new_logged,
            "new_days_window": new_days,
            "verified_by_tld": by_tld,
            "recent_discovery_events": [
                {
                    "domain": r["domain"],
                    "discovered_at": r["discovered_at"],
                    "method": r["method"],
                    "category": r["category"],
                    "detail": r["detail"],
                    "is_new_domain": bool(r["is_new_domain"]),
                    "tld": _tld_bucket(r["domain"]),
                }
                for r in recent_discoveries
            ],
        }

    def browse_category(self, category: str, limit: int = 25) -> List[dict]:
        """All AI-verified websites for a category — ranked by category fit."""
        return self.search(category=category, query_text="", limit=limit, verified_only=True)

    def upsert_website(
        self,
        domain: str,
        name: str,
        url: str,
        categories: List[str],
        trust_score: float = 0,
        has_open: bool = False,
        verified: bool = False,
        snippet: str = "",
        organization: str = "",
        deadline: str = "",
        eligibility: str = "",
        location: str = "Rwanda",
        apply_link: str = "",
        source: str = "seed",
    ) -> None:
        now = _utc_now()
        cats = sorted(set(categories))
        cats_json = json.dumps(cats)
        if not snippet.strip():
            snippet = website_snippet(name, cats)
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT categories FROM websites WHERE domain = ?", (domain,)
            ).fetchone()
            if existing:
                old = json.loads(existing["categories"])
                cats = sorted(set(old + cats))
                cats_json = json.dumps(cats)
                if snippet.startswith("Website hosting"):
                    snippet = website_snippet(name, cats)
            conn.execute("""
                INSERT INTO websites (
                    domain, name, url, categories, trust_score,
                    has_open_applications, verified, snippet, organization,
                    deadline, eligibility, location, apply_link, source,
                    last_checked, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    name = excluded.name,
                    url = excluded.url,
                    categories = excluded.categories,
                    trust_score = excluded.trust_score,
                    has_open_applications = excluded.has_open_applications,
                    verified = excluded.verified,
                    snippet = excluded.snippet,
                    organization = excluded.organization,
                    deadline = excluded.deadline,
                    eligibility = excluded.eligibility,
                    location = excluded.location,
                    apply_link = excluded.apply_link,
                    source = excluded.source,
                    last_checked = excluded.last_checked
            """, (
                domain, name, url, cats_json, trust_score,
                1 if has_open else 0, 1 if verified else 0,
                snippet, organization, deadline, eligibility,
                location, apply_link or url, source, now, now,
            ))

    def upsert_from_api_result(self, result: dict, source: str = "live") -> None:
        from rwanda_sources import domain_of
        domain = domain_of(result.get("url", ""))
        if not domain:
            return
        cat = result.get("category", "program")
        self.upsert_website(
            domain=domain,
            name=result.get("title") or domain,
            url=result.get("url", ""),
            categories=[cat] if isinstance(cat, str) else cat,
            trust_score=float(result.get("trust_score", 0)),
            has_open=True,
            verified=True,
            snippet=result.get("snippet", ""),
            organization=result.get("organization", ""),
            deadline=result.get("deadline", ""),
            eligibility=result.get("eligibility", ""),
            location=result.get("location", ""),
            apply_link=result.get("apply_link", result.get("url", "")),
            source=source,
        )

    def add_pending(self, url: str, domain: str,
                    suggested_category: Optional[str] = None,
                    discovered_via: str = "") -> bool:
        try:
            with self._connect() as conn:
                cur = conn.execute("""
                    INSERT OR IGNORE INTO pending_urls
                    (url, domain, suggested_category, discovered_via, discovered_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (url, domain, suggested_category, discovered_via, _utc_now()))
            return cur.rowcount > 0
        except sqlite3.Error:
            return False

    def enqueue_search_harvest(
        self,
        query: str,
        category: Optional[str] = None,
        district: Optional[str] = None,
    ) -> None:
        q = (query or "").strip()
        if not q:
            return
        cat = (category or "").strip()
        dist = (district or "").strip()
        with self._connect() as conn:
            recent = conn.execute("""
                SELECT 1 FROM search_harvest_queue
                WHERE query = ? AND category = ? AND district = ?
                  AND processed_at = '' AND enqueued_at >= datetime('now', '-2 days')
                LIMIT 1
            """, (q, cat, dist)).fetchone()
            if recent:
                return
            conn.execute("""
                INSERT INTO search_harvest_queue (query, category, district, enqueued_at)
                VALUES (?, ?, ?, ?)
            """, (q, cat, dist, _utc_now()))

    def list_search_harvest_queue(self, limit: int = 30) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute("""
                SELECT * FROM search_harvest_queue
                WHERE processed_at = '' OR processed_at IS NULL
                ORDER BY enqueued_at ASC
                LIMIT ?
            """, (limit,)).fetchall()

    def mark_search_harvest_processed(self, row_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE search_harvest_queue SET processed_at = ? WHERE id = ?",
                (_utc_now(), row_id),
            )

    def list_pending(self, limit: int = 100) -> List[sqlite3.Row]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM pending_urls ORDER BY id ASC LIMIT ?", (limit,)
            ).fetchall()
        return rows

    def remove_pending(self, url: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM pending_urls WHERE url = ?", (url,))

    def list_all_websites(self) -> List[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM websites ORDER BY trust_score DESC"
            ).fetchall()

    def list_for_verification(self) -> List[sqlite3.Row]:
        """All registry sites + pending URLs (as pseudo-rows)."""
        with self._connect() as conn:
            return conn.execute("""
                SELECT domain, name, url, categories, source FROM websites
                UNION
                SELECT domain, domain AS name, url, suggested_category AS categories, 'pending' AS source
                FROM pending_urls
            """).fetchall()

    def search(
        self,
        category: Optional[str],
        query_text: str = "",
        limit: int = 20,
        verified_only: bool = True,
    ) -> List[dict]:
        tokens = query_tokens(query_text)
        fetch_limit = max(limit * 4, 60) if category or tokens else limit * 2
        rows = self._search_rows(category, query_text, tokens, fetch_limit, verified_only)
        # Token filter too strict — fall back to category browse and rank by relevance
        if not rows and tokens:
            rows = self._search_rows(category, "", [], fetch_limit, verified_only)
        if category or tokens:
            rows = sorted(
                rows,
                key=lambda r: _specialist_score(r, category, tokens),
                reverse=True,
            )
        results = [self.row_to_api_result(r, category) for r in rows]
        return results[:limit]

    def _search_rows(
        self,
        category: Optional[str],
        query_text: str,
        tokens: List[str],
        limit: int,
        verified_only: bool,
    ) -> List[sqlite3.Row]:
        clauses = []
        params: list = []

        if verified_only:
            clauses.append("verified = 1 AND has_open_applications = 1")

        if category:
            clauses.append("categories LIKE ?")
            params.append(f'%"{category}"%')

        if tokens:
            token_parts = []
            for tok in tokens:
                token_parts.append(
                    "(LOWER(name) LIKE ? OR LOWER(domain) LIKE ? OR LOWER(snippet) LIKE ? OR LOWER(categories) LIKE ?)"
                )
                like = f"%{tok}%"
                params.extend([like, like, like, like])
            clauses.append("(" + " OR ".join(token_parts) + ")")
        elif query_text.strip():
            q = f"%{query_text.strip().lower()}%"
            clauses.append(
                "(LOWER(name) LIKE ? OR LOWER(domain) LIKE ? OR LOWER(snippet) LIKE ?)"
            )
            params.extend([q, q, q])

        where = " AND ".join(clauses) if clauses else "1=1"
        sql = f"""
            SELECT * FROM websites
            WHERE {where}
            ORDER BY trust_score DESC, created_at DESC, name ASC
            LIMIT ?
        """
        params.append(limit)
        with self._connect() as conn:
            return conn.execute(sql, params).fetchall()

    def row_to_api_result(self, row: sqlite3.Row, preferred_category: Optional[str] = None) -> dict:
        cats = json.loads(row["categories"])
        category = preferred_category if preferred_category in cats else (cats[0] if cats else "program")
        name = row["name"]
        snippet = row["snippet"] or website_snippet(name, cats)
        created = row["created_at"] or ""
        is_new = created >= _days_ago_iso(7) if created else False
        domain = row["domain"]
        return {
            "url":          row["url"],
            "title":        name,
            "category":     category,
            "categories":   cats,
            "trust_score":  row["trust_score"],
            "organization": row["organization"] or name,
            "deadline":     "",
            "eligibility":  "",
            "location":     row["location"] or "",
            "apply_link":   row["apply_link"] or row["url"],
            "snippet":      snippet,
            "last_verified": row["last_checked"] or "",
            "domain":       domain,
            "tld":          _tld_bucket(domain),
            "first_seen":   created,
            "is_new":       is_new,
            "source":       row["source"] or "",
        }

    def stats(self) -> Dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM websites").fetchone()[0]
            verified = conn.execute(
                "SELECT COUNT(*) FROM websites WHERE verified = 1 AND has_open_applications = 1"
            ).fetchone()[0]
            opp_total = conn.execute(
                "SELECT COUNT(*) FROM opportunities WHERE verified = 1"
            ).fetchone()[0]
            verified_websites = conn.execute(
                "SELECT COUNT(*) FROM websites WHERE verified = 1"
            ).fetchone()[0]
            districts_tagged = conn.execute(
                """
                SELECT COUNT(DISTINCT TRIM(district)) FROM opportunities
                WHERE verified = 1 AND TRIM(COALESCE(district, '')) != ''
                """
            ).fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM pending_urls").fetchone()[0]
            by_cat = {}
            opp_by_cat = {}
            for cat in INZIRA_CATEGORIES:
                n = conn.execute(
                    "SELECT COUNT(*) FROM websites WHERE verified = 1 AND categories LIKE ?",
                    (f'%"{cat}"%',),
                ).fetchone()[0]
                by_cat[cat] = n
                opp_by_cat[cat] = conn.execute(
                    "SELECT COUNT(*) FROM opportunities WHERE verified = 1 AND category = ?",
                    (cat,),
                ).fetchone()[0]
            scope_rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(TRIM(scope), ''), 'blank') AS scope, COUNT(*) AS n
                FROM opportunities WHERE verified = 1
                GROUP BY 1
                """
            ).fetchall()
            by_scope = {r[0]: r[1] for r in scope_rows}
        return {
            "total_websites": total,
            "verified_open": verified,
            "verified_websites": verified_websites,
            "verified_opportunities": opp_total,
            "districts_with_listings": districts_tagged,
            "pending_urls": pending,
            "by_category": by_cat,
            "opportunities_by_category": opp_by_cat,
            "opportunities_by_scope": by_scope,
            "last_refresh_at": self.get_meta("last_refresh_at"),
            "last_discovery_at": self.get_meta("last_discovery_at"),
            "last_discovery_new_domains": self.get_meta("last_discovery_new_domains"),
            "last_opportunity_sync_at": self.get_meta("last_opportunity_sync_at"),
            "last_scheduled_harvest_at": self.get_meta("last_scheduled_harvest_at"),
        }


INZIRA_CATEGORIES = [
    "scholarship", "job", "internship", "training",
    "competition", "program", "free_course",
]
