from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from io import StringIO
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
import cloudscraper

from forex_news_guard.core.config import Settings
from forex_news_guard.domain.models import ForexEvent, ImpactLevel


class ForexFactoryError(RuntimeError):
    """Base exception for Forex Factory integration issues."""


class ForexFactoryBlockedError(ForexFactoryError):
    """Raised when Forex Factory blocks direct access."""


class ForexFactoryParseError(ForexFactoryError):
    """Raised when the upstream response format cannot be parsed."""


@dataclass(slots=True)
class ForexFactoryClient:
    calendar_url: str
    news_url: str
    user_agent: str
    timeout_seconds: float
    cookie_header: str | None = None

    @classmethod
    def from_settings(cls, settings: Settings) -> "ForexFactoryClient":
        return cls(
            calendar_url=settings.forex_factory_calendar_url,
            news_url=settings.forex_factory_news_url,
            user_agent=settings.forex_factory_user_agent,
            timeout_seconds=settings.forex_factory_timeout_seconds,
            cookie_header=settings.forex_factory_cookie,
        )

    def fetch_calendar_events(self, reference_time: datetime) -> list[ForexEvent]:
        html = self._get_text(self.calendar_url)
        return parse_calendar_html(
            html=html,
            base_url=self.calendar_url,
            reference_time=reference_time,
        )

    def fetch_breaking_news_events(self, reference_time: datetime) -> list[ForexEvent]:
        html = self._get_text(self.news_url)
        return parse_breaking_news_html(
            html=html,
            base_url=self.news_url,
            reference_time=reference_time,
        )

    def _get_text(self, url: str) -> str:
        headers = {}
        if self.cookie_header:
            headers["Cookie"] = self.cookie_header
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "desktop": True}
        )
        response = scraper.get(url, headers=headers, timeout=self.timeout_seconds)
        body = response.text
        if response.status_code in {403, 429} or _looks_like_cloudflare_challenge(body):
            raise ForexFactoryBlockedError(
                "Forex Factory bloqueo la solicitud directa. "
                "En este entorno ni siquiera el cliente HTTP compatible con Cloudflare pudo pasar. "
                "Configura FOREX_GUARD_FOREX_FACTORY_COOKIE con una sesion valida del navegador."
            )
        if response.status_code >= 400:
            raise ForexFactoryError(f"Forex Factory respondio con estado {response.status_code} para {url}.")
        return body


def parse_calendar_html(html: str, base_url: str, reference_time: datetime) -> list[ForexEvent]:
    script_events = _extract_calendar_events_from_component_state(html, base_url, reference_time)
    if script_events:
        return script_events

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.calendar__row, tr.calendar_row, tr[data-eventid]")
    if not rows:
        raise ForexFactoryParseError("No se encontraron filas de calendario en el HTML de Forex Factory.")

    events: list[ForexEvent] = []
    current_date_label: str | None = None

    for row in rows:
        date_label = _extract_text(row.select_one("td.calendar__date, td.date"))
        if date_label:
            current_date_label = date_label
        event_id = row.get("data-event-id") or row.get("data-eventid") or _extract_text(row.select_one("[data-eventid]"))
        time_text = _extract_text(row.select_one("td.calendar__time, td.time"))
        currency = _extract_text(row.select_one("td.calendar__currency, td.currency"))
        title = _extract_text(
            row.select_one(
                "td.calendar__event .calendar__event-title, td.calendar__event, td.event .calendar__event-title, td.event"
            )
        )
        impact_cell = row.select_one("td.calendar__impact, td.impact")
        impact = _parse_impact(impact_cell)

        if not event_id or not currency or not title or impact is None:
            continue

        scheduled_at = _parse_calendar_datetime(current_date_label, time_text, reference_time)
        if scheduled_at is None:
            continue

        detail_link = row.select_one("td.calendar__detail a, td.detail a, a.calendar_detail")
        event_url = urljoin(base_url, detail_link.get("href")) if detail_link and detail_link.get("href") else None
        events.append(
            ForexEvent(
                id=f"ff-calendar-{event_id}",
                title=title,
                currency=currency,
                impact=impact,
                scheduled_at=scheduled_at,
                actual=_extract_text(row.select_one("td.calendar__actual, td.actual")),
                forecast=_extract_text(row.select_one("td.calendar__forecast, td.forecast")),
                previous=_extract_text(row.select_one("td.calendar__previous, td.previous")),
                actual_better_worse=None,
                url=event_url,
            )
        )

    return events


def _extract_calendar_events_from_component_state(
    html: str,
    base_url: str,
    reference_time: datetime,
) -> list[ForexEvent]:
    marker_match = re.search(r"window\.calendarComponentStates\[\d+\]\s*=\s*\{", html)
    if not marker_match:
        return []

    days_match = re.search(r"[\"']?days[\"']?\s*:\s*\[", html[marker_match.end() :], flags=re.DOTALL)
    if not days_match:
        return []

    array_start = marker_match.end() + days_match.start()
    bracket_start = html.find("[", array_start)
    if bracket_start == -1:
        return []

    depth = 0
    bracket_end = -1
    for index in range(bracket_start, len(html)):
        char = html[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                bracket_end = index
                break
    if bracket_end == -1:
        return []

    payload_text = html[bracket_start : bracket_end + 1]
    try:
        days = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise ForexFactoryParseError("No se pudo decodificar el arreglo serializado de dias del calendario.") from exc

    events: list[ForexEvent] = []
    for day in days:
        for record in day.get("events", []):
            impact = _parse_impact_text(_first_non_empty(record, "impactName", "impactTitle", "impactClass"))
            title = _first_non_empty(record, "name", "title", "prefixedName")
            currency = _first_non_empty(record, "currency")
            event_id = _first_non_empty(record, "id")
            if not title or not currency or not event_id or impact is None:
                continue

            dateline = record.get("dateline")
            scheduled_at = None
            if dateline not in (None, ""):
                try:
                    scheduled_at = datetime.fromtimestamp(int(dateline), tz=reference_time.tzinfo)
                except (TypeError, ValueError, OSError):
                    scheduled_at = None
            if scheduled_at is None:
                scheduled_at = _parse_calendar_datetime(
                    _first_non_empty(record, "date"),
                    _first_non_empty(record, "timeLabel", "time"),
                    reference_time,
                )
            if scheduled_at is None:
                continue

            events.append(
                ForexEvent(
                    id=f"ff-calendar-{event_id}",
                    title=title,
                    currency=currency,
                    impact=impact,
                    scheduled_at=scheduled_at,
                    actual=_first_non_empty(record, "actual"),
                    forecast=_first_non_empty(record, "forecast"),
                    previous=_first_non_empty(record, "previous", "revision"),
                    actual_better_worse=_coerce_int(record.get("actualBetterWorse")),
                    url=urljoin(base_url, _first_non_empty(record, "url", "soloUrl") or ""),
                )
            )
    return events


def parse_breaking_news_html(html: str, base_url: str, reference_time: datetime) -> list[ForexEvent]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = soup.select("article, li, div")
    if not candidates:
        raise ForexFactoryParseError("No se encontraron nodos de noticias en el HTML de Forex Factory.")

    events: list[ForexEvent] = []
    seen_ids: set[str] = set()

    for candidate in candidates:
        impact = _parse_impact(candidate)
        if impact != ImpactLevel.HIGH:
            continue

        title_node = candidate.select_one("h1 a, h2 a, h3 a, a[href*='/news/']")
        title = _extract_text(title_node)
        href = title_node.get("href") if title_node else None
        if not title or not href:
            continue

        story_id_match = re.search(r"/news/(\d+)", href)
        story_id = story_id_match.group(1) if story_id_match else href
        if story_id in seen_ids:
            continue
        seen_ids.add(story_id)

        published_at = _parse_relative_timestamp(candidate.get_text(" ", strip=True), reference_time)
        events.append(
            ForexEvent(
                id=f"ff-breaking-{story_id}",
                title=title,
                currency="NEWS",
                impact=impact,
                published_at=published_at or reference_time,
                url=urljoin(base_url, href),
                is_breaking=True,
            )
        )

    return events


def parse_calendar_json(payload: str, reference_time: datetime) -> list[ForexEvent]:
    data = json.loads(payload)
    if isinstance(data, dict):
        records = data.get("events") or data.get("calendar") or data.get("data") or []
    else:
        records = data
    if not isinstance(records, list):
        raise ForexFactoryParseError("El JSON del calendario no contiene una lista de eventos.")
    return _normalize_records(records, reference_time)


def parse_calendar_csv(payload: str, reference_time: datetime) -> list[ForexEvent]:
    reader = csv.DictReader(StringIO(payload))
    return _normalize_records(list(reader), reference_time)


def _normalize_records(records: list[dict[str, Any]], reference_time: datetime) -> list[ForexEvent]:
    events: list[ForexEvent] = []
    for index, record in enumerate(records):
        impact = _parse_impact_text(
            _first_non_empty(
                record,
                "impact",
                "impact_title",
                "impact_level",
                "impactLevel",
                "volatility",
            )
        )
        title = _first_non_empty(record, "title", "event", "name")
        currency = _first_non_empty(record, "currency", "curr", "symbol")
        event_id = _first_non_empty(record, "id", "event_id", "eventId") or str(index)
        scheduled_at = _parse_datetime_from_record(record, reference_time)
        if not title or not currency or impact is None or scheduled_at is None:
            continue
        events.append(
            ForexEvent(
                id=f"ff-calendar-{event_id}",
                title=title,
                currency=currency,
                impact=impact,
                scheduled_at=scheduled_at,
                actual=_first_non_empty(record, "actual"),
                forecast=_first_non_empty(record, "forecast"),
                previous=_first_non_empty(record, "previous", "revision"),
                actual_better_worse=_coerce_int(record.get("actualBetterWorse")),
                url=_first_non_empty(record, "url", "link"),
            )
        )
    return events


def _parse_datetime_from_record(record: dict[str, Any], reference_time: datetime) -> datetime | None:
    timestamp = _first_non_empty(record, "timestamp", "datetime", "date_utc")
    if timestamp:
        return _coerce_datetime(timestamp, reference_time)
    date_text = _first_non_empty(record, "date", "day")
    time_text = _first_non_empty(record, "time")
    return _parse_calendar_datetime(date_text, time_text, reference_time)


def _parse_calendar_datetime(
    date_label: str | None,
    time_text: str | None,
    reference_time: datetime,
) -> datetime | None:
    if not date_label or not time_text:
        return None
    cleaned_time = " ".join(time_text.split())
    if cleaned_time.lower() in {"all day", "day 1", "day 2", "day 3", "tentative"}:
        return None

    date_text = date_label.strip()
    parsed_date: datetime | None = None
    for fmt in ("%a %b %d %Y", "%a %b %d", "%b %d %Y", "%b %d"):
        try:
            parsed = datetime.strptime(
                f"{date_text} {reference_time.year}" if fmt in {"%a %b %d", "%b %d"} else date_text,
                f"{fmt} %Y" if fmt in {"%a %b %d", "%b %d"} else fmt,
            )
            parsed_date = parsed.replace(tzinfo=reference_time.tzinfo)
            break
        except ValueError:
            continue
    if parsed_date is None:
        return None

    for fmt in ("%I:%M%p", "%I:%M %p", "%H:%M"):
        try:
            parsed_time = datetime.strptime(cleaned_time.upper(), fmt)
            return parsed_date.replace(hour=parsed_time.hour, minute=parsed_time.minute)
        except ValueError:
            continue
    return None


def _parse_relative_timestamp(text: str, reference_time: datetime) -> datetime | None:
    match = re.search(r"(\d+)\s+min\s+ago", text, flags=re.IGNORECASE)
    if match:
        return reference_time - timedelta(minutes=int(match.group(1)))
    match = re.search(r"(\d+)\s+hr\s+ago", text, flags=re.IGNORECASE)
    if match:
        return reference_time - timedelta(hours=int(match.group(1)))
    match = re.search(r"([A-Z][a-z]{2}\s+[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})", text)
    if match:
        return _coerce_datetime(match.group(1), reference_time)
    return None


def _coerce_datetime(value: str, reference_time: datetime) -> datetime | None:
    for parser in (
        lambda raw: datetime.fromisoformat(raw.replace("Z", "+00:00")),
        parsedate_to_datetime,
    ):
        try:
            parsed = parser(value)
            return parsed.astimezone(reference_time.tzinfo) if parsed.tzinfo else parsed.replace(tzinfo=reference_time.tzinfo)
        except Exception:
            continue
    for fmt in ("%a %b %d %Y %I:%M%p", "%a %b %d %Y %I:%M %p", "%b %d %Y %I:%M%p", "%Y-%m-%d %H:%M:%S"):
        try:
            parsed = datetime.strptime(value, fmt)
            return parsed.replace(tzinfo=reference_time.tzinfo)
        except ValueError:
            continue
    return None


def _parse_impact(node: Tag | None) -> ImpactLevel | None:
    if node is None:
        return None
    title_text = " ".join(
        filter(
            None,
            [
                node.get("title"),
                node.get("aria-label"),
                " ".join(node.get("class", [])),
                node.get_text(" ", strip=True),
            ],
        )
    )
    for child in node.select("[title], [aria-label], span, i"):
        title_text += " " + " ".join(
            filter(
                None,
                [
                    child.get("title"),
                    child.get("aria-label"),
                    " ".join(child.get("class", [])),
                    child.get_text(" ", strip=True),
                ],
            )
        )
    return _parse_impact_text(title_text)


def _parse_impact_text(value: str | None) -> ImpactLevel | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if any(token in normalized for token in ("high", "red", "impact-red", "icon--ff-impact-red", "3")):
        return ImpactLevel.HIGH
    if any(token in normalized for token in ("medium", "orange", "impact-orange", "icon--ff-impact-orange", "2")):
        return ImpactLevel.MEDIUM
    if any(token in normalized for token in ("low", "yellow", "impact-yellow", "icon--ff-impact-yellow", "1")):
        return ImpactLevel.LOW
    return None


def _extract_text(node: Tag | None) -> str:
    return node.get_text(" ", strip=True) if node else ""


def _first_non_empty(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _looks_like_cloudflare_challenge(body: str) -> bool:
    lowered = body.lower()
    return "just a moment" in lowered and "challenges.cloudflare.com" in lowered


def _coerce_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
