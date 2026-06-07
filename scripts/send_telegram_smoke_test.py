from __future__ import annotations

import json
import os
from pathlib import Path

from forex_news_guard.services.telegram_smoke_test import send_telegram_smoke_test


def main() -> None:
    response = send_telegram_smoke_test()
    payload = response.model_dump(mode="json")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines = [
        "# Telegram smoke test",
        "",
        f"Mensajes enviados: {len(response.sent_messages)}",
        "",
    ]
    lines.extend(f"- {title}" for title in response.sent_messages)
    Path(summary_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
