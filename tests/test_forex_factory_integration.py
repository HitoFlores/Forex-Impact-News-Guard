from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from forex_news_guard.domain.models import ImpactLevel
from forex_news_guard.integrations.forex_factory import (
    ForexFactoryBlockedError,
    parse_breaking_news_html,
    parse_calendar_html,
)
from forex_news_guard.services.forex_factory_monitor import preview_live_alerts


def test_parse_calendar_html_supports_legacy_rows() -> None:
    html = """
    <table>
      <tr class="calendar_row" data-eventid="63273">
        <td class="date">Tue May 26</td>
        <td class="time">8:30am</td>
        <td class="currency">USD</td>
        <td class="impact"><span title="High Impact Expected" class="high"></span></td>
        <td class="event"><span>Core Durable Goods Orders m/m</span></td>
        <td class="detail"><a class="calendar_detail" href="/calendar?event=63273"></a></td>
      </tr>
    </table>
    """
    reference_time = datetime(2026, 5, 26, 7, 0, tzinfo=ZoneInfo("America/Chihuahua"))

    events = parse_calendar_html(html, "https://www.forexfactory.com/calendar", reference_time)

    assert len(events) == 1
    assert events[0].impact == ImpactLevel.HIGH
    assert events[0].currency == "USD"
    assert events[0].title == "Core Durable Goods Orders m/m"


def test_parse_calendar_html_supports_modern_rows() -> None:
    html = """
    <table>
      <tr class="calendar__row" data-eventid="99111">
        <td class="calendar__date">Fri May 29</td>
        <td class="calendar__time">9:45am</td>
        <td class="calendar__currency">USD</td>
        <td class="calendar__impact"><span title="High Impact Expected" class="icon--ff-impact-red"></span></td>
        <td class="calendar__event">Chicago PMI</td>
        <td class="calendar__detail"><a href="/calendar?event=99111"></a></td>
      </tr>
    </table>
    """
    reference_time = datetime(2026, 5, 29, 7, 0, tzinfo=ZoneInfo("America/Chihuahua"))

    events = parse_calendar_html(html, "https://www.forexfactory.com/calendar", reference_time)

    assert len(events) == 1
    assert events[0].id == "ff-calendar-99111"
    assert events[0].scheduled_at == datetime(2026, 5, 29, 9, 45, tzinfo=ZoneInfo("America/Chihuahua"))


def test_parse_calendar_html_supports_component_state_payload() -> None:
    html = """
    <script>
    if (typeof window.calendarComponentStates === 'undefined') { window.calendarComponentStates = {} }
    window.calendarComponentStates[1] = {
      "days": [
        {
          "date": "Tue <span>May 26</span>",
          "dateline": 1779778800,
          "events": [
            {
              "id": 152594,
              "name": "CPI m/m",
              "dateline": 1779845400,
              "currency": "AUD",
              "impactName": "high",
              "impactClass": "icon--ff-impact-red",
              "impactTitle": "High Impact Expected",
              "timeLabel": "6:30pm",
              "url": "/calendar?day=may26.2026#detail=152594"
            }
          ]
        }
      ]
    }
    window.calendarInit = true;
    </script>
    """
    reference_time = datetime(2026, 5, 26, 12, 0, tzinfo=ZoneInfo("America/Chihuahua"))

    events = parse_calendar_html(html, "https://www.forexfactory.com/calendar", reference_time)

    assert len(events) == 1
    assert events[0].impact == ImpactLevel.HIGH
    assert events[0].currency == "AUD"
    assert events[0].title == "CPI m/m"


def test_parse_breaking_news_html_filters_high_impact_items() -> None:
    html = """
    <section>
      <article class="flexposts__story flexposts__story--high">
        <span title="High Impact" class="icon--ff-impact-red"></span>
        <h3><a href="/news/1351635-wh-official-trump-likely-to-fire-fed-chair">Emergency central bank headline</a></h3>
        <div>From @financialjuice | 30 min ago</div>
      </article>
      <article class="flexposts__story flexposts__story--medium">
        <span title="Medium Impact" class="icon--ff-impact-orange"></span>
        <h3><a href="/news/1351636-medium-story">Medium impact story</a></h3>
        <div>From @source | 5 min ago</div>
      </article>
    </section>
    """
    reference_time = datetime(2026, 5, 26, 15, 0, tzinfo=ZoneInfo("America/Chihuahua"))

    events = parse_breaking_news_html(html, "https://www.forexfactory.com/news", reference_time)

    assert len(events) == 1
    assert events[0].is_breaking is True
    assert events[0].impact == ImpactLevel.HIGH
    assert events[0].published_at == datetime(2026, 5, 26, 14, 30, tzinfo=ZoneInfo("America/Chihuahua"))


def test_live_preview_merges_calendar_and_breaking_news() -> None:
    timezone = ZoneInfo("America/Chihuahua")
    reference_time = datetime(2026, 5, 26, 15, 0, tzinfo=timezone)

    class FakeClient:
        def fetch_calendar_events(self, reference_time: datetime):  # noqa: ANN202
            return parse_calendar_html(
                """
                <tr class="calendar__row" data-eventid="99111">
                  <td class="calendar__date">Tue May 26</td>
                  <td class="calendar__time">4:00pm</td>
                  <td class="calendar__currency">USD</td>
                  <td class="calendar__impact"><span title="High Impact Expected" class="icon--ff-impact-red"></span></td>
                  <td class="calendar__event">FOMC Minutes</td>
                </tr>
                """,
                "https://www.forexfactory.com/calendar",
                reference_time,
            )

        def fetch_breaking_news_events(self, reference_time: datetime):  # noqa: ANN202
            return parse_breaking_news_html(
                """
                <article class="flexposts__story flexposts__story--high">
                  <span title="High Impact" class="icon--ff-impact-red"></span>
                  <h3><a href="/news/1351635-live-headline">Emergency headline</a></h3>
                  <div>From @financialjuice | 5 min ago</div>
                </article>
                """,
                "https://www.forexfactory.com/news",
                reference_time,
            )

    result = preview_live_alerts(policy={"lead_minutes": 15}, reference_time=reference_time, client=FakeClient())

    assert len(result.planned_alerts) == 2
    assert result.planned_alerts[0].alert_kind.value == "breaking"
    assert result.planned_alerts[1].alert_kind.value == "calendar"


def test_live_preview_reports_blocked_source() -> None:
    class BlockedClient:
        def fetch_calendar_events(self, reference_time: datetime):  # noqa: ANN202
            raise ForexFactoryBlockedError("blocked")

    with pytest.raises(ForexFactoryBlockedError):
        preview_live_alerts(policy={"lead_minutes": 15}, client=BlockedClient())
