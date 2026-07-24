"""
Youth search analytics for MIFOTRA — categories, zero-result queries, districts.
"""

import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _days_ago_iso(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


class AnalyticsStore:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS search_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    searched_at TEXT NOT NULL,
                    query TEXT DEFAULT '',
                    category TEXT,
                    district TEXT DEFAULT 'Unknown',
                    results_count INTEGER DEFAULT 0,
                    zero_results INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_search_at ON search_events(searched_at);
                CREATE INDEX IF NOT EXISTS idx_search_district ON search_events(district);
                CREATE INDEX IF NOT EXISTS idx_search_category ON search_events(category);
            """)

    def log_search(
        self,
        query: str,
        category: Optional[str],
        district: Optional[str],
        results_count: int,
    ) -> None:
        district = (district or "Unknown").strip() or "Unknown"
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO search_events
                (searched_at, query, category, district, results_count, zero_results)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                _utc_now(),
                (query or "").strip(),
                category,
                district,
                results_count,
                1 if results_count == 0 else 0,
            ))

    def top_categories(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        since = _days_ago_iso(days)
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT COALESCE(category, 'general') AS category, COUNT(*) AS searches
                FROM search_events
                WHERE searched_at >= ?
                GROUP BY COALESCE(category, 'general')
                ORDER BY searches DESC
                LIMIT ?
            """, (since, limit)).fetchall()
        return [{"category": r["category"], "searches": r["searches"]} for r in rows]

    def zero_result_searches(self, days: int = 30, limit: int = 25) -> List[Dict[str, Any]]:
        since = _days_ago_iso(days)
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT query, category, district, COUNT(*) AS times_searched,
                       MAX(searched_at) AS last_searched
                FROM search_events
                WHERE searched_at >= ? AND zero_results = 1
                GROUP BY LOWER(TRIM(query)), COALESCE(category, ''), district
                ORDER BY times_searched DESC, last_searched DESC
                LIMIT ?
            """, (since, limit)).fetchall()
        return [
            {
                "query": r["query"],
                "category": r["category"],
                "district": r["district"],
                "times_searched": r["times_searched"],
                "last_searched": r["last_searched"],
            }
            for r in rows
        ]

    def top_districts(self, days: int = 30, limit: int = 15) -> List[Dict[str, Any]]:
        since = _days_ago_iso(days)
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT district, COUNT(*) AS searches,
                       SUM(zero_results) AS zero_result_searches
                FROM search_events
                WHERE searched_at >= ?
                GROUP BY district
                ORDER BY searches DESC
                LIMIT ?
            """, (since, limit)).fetchall()
        return [
            {
                "district": r["district"],
                "searches": r["searches"],
                "zero_result_searches": r["zero_result_searches"],
            }
            for r in rows
        ]

    def summary(self, days: int = 30) -> Dict[str, Any]:
        since = _days_ago_iso(days)
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM search_events WHERE searched_at >= ?", (since,)
            ).fetchone()[0]
            zero = conn.execute(
                "SELECT COUNT(*) FROM search_events WHERE searched_at >= ? AND zero_results = 1",
                (since,),
            ).fetchone()[0]
            districts = conn.execute(
                "SELECT COUNT(DISTINCT district) FROM search_events WHERE searched_at >= ?",
                (since,),
            ).fetchone()[0]
        return {
            "days": days,
            "total_searches": total,
            "zero_result_searches": zero,
            "unique_districts": districts,
            "zero_result_rate_pct": round(100.0 * zero / total, 1) if total else 0.0,
        }

    def period_compare(self, days: int) -> Dict[str, Any]:
        """Compare search volume in the last `days` vs the prior `days` window."""
        current_since = _days_ago_iso(days)
        previous_since = _days_ago_iso(days * 2)
        with self._connect() as conn:
            current = conn.execute(
                "SELECT COUNT(*) FROM search_events WHERE searched_at >= ?",
                (current_since,),
            ).fetchone()[0]
            previous = conn.execute(
                """
                SELECT COUNT(*) FROM search_events
                WHERE searched_at >= ? AND searched_at < ?
                """,
                (previous_since, current_since),
            ).fetchone()[0]
        change_pct = None
        if previous > 0:
            change_pct = round(100.0 * (current - previous) / previous, 1)
        return {
            "days": days,
            "current": int(current),
            "previous": int(previous),
            "change_pct": change_pct,
        }

    def top_search_queries(self, days: int = 30, limit: int = 8) -> List[Dict[str, Any]]:
        since = _days_ago_iso(days)
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM search_events WHERE searched_at >= ?", (since,)
            ).fetchone()[0]
            rows = conn.execute(
                """
                SELECT TRIM(query) AS query, COUNT(*) AS searches
                FROM search_events
                WHERE searched_at >= ? AND TRIM(COALESCE(query, '')) != ''
                GROUP BY TRIM(LOWER(query))
                ORDER BY searches DESC
                LIMIT ?
                """,
                (since, limit),
            ).fetchall()
        out = []
        for r in rows:
            searches = int(r["searches"])
            pct = round(100.0 * searches / total, 1) if total else 0.0
            out.append({
                "query": r["query"],
                "searches": searches,
                "share_pct": pct,
            })
        return out

    def district_demand_all(self, days: int = 30) -> Dict[str, int]:
        since = _days_ago_iso(days)
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT district, COUNT(*) AS searches
                FROM search_events
                WHERE searched_at >= ?
                GROUP BY district
            """, (since,)).fetchall()
        out = {r["district"]: r["searches"] for r in rows}
        return out

    def dashboard(self, days: int = 30) -> Dict[str, Any]:
        return {
            "summary": self.summary(days),
            "top_categories": self.top_categories(days),
            "top_search_queries": self.top_search_queries(days),
            "zero_result_queries": self.zero_result_searches(days),
            "top_districts": self.top_districts(days),
            "comparisons": {
                "searches_month": self.period_compare(30),
                "searches_week": self.period_compare(7),
            },
        }
