import json
import mimetypes
import os
import pathlib
import smtplib
import ssl
import sys
from email.message import EmailMessage

SUMMARY_PATH = pathlib.Path("state/transition_summary.json")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def attach_file(message: EmailMessage, path: pathlib.Path) -> None:
    if not path.exists():
        return

    content_type, encoding = mimetypes.guess_type(path.name)
    if content_type is None or encoding is not None:
        content_type = "application/octet-stream"

    maintype, subtype = content_type.split("/", 1)

    with path.open("rb") as f:
        message.add_attachment(
            f.read(),
            maintype=maintype,
            subtype=subtype,
            filename=path.name,
        )


def line_for_change(change: dict) -> str:
    store = change["store_name"]
    event = change["event"]

    if event == "available":
        return f"- {store}: now available."
    if event == "sold_out":
        return (
            f"- {store}: The product sold out again. "
            "However, if it becomes available, you'll be notified."
        )
    if event == "missing_confirmed":
        return (
            f"- {store}: The product no longer appears on the page. "
            "However, if it becomes available again, you'll be notified."
        )
    return f"- {store}: state changed."


def subject_for_changes(changed: list[dict]) -> str:
    product = "BALDE YOSHI SUPER MARIO GALXY"

    if len(changed) == 1:
        change = changed[0]
        store = change["store_name"]
        event = change["event"]

        if event == "available":
            return f"[Stock Alert] {product} is now available — {store}"
        if event == "sold_out":
            return f"[Stock Alert] {product} sold out again — {store}"
        if event == "missing_confirmed":
            return f"[Stock Alert] {product} no longer appears — {store}"

    return f"[Stock Alert] {product} status changed in {len(changed)} stores"


def main() -> None:
    if not SUMMARY_PATH.exists():
        raise RuntimeError("state/transition_summary.json does not exist.")

    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    changed = summary.get("changed_stores", [])

    if not changed:
        print("No email sent because no stores changed.")
        return

    smtp_host = require_env("SMTP_HOST")
    smtp_port = int(require_env("SMTP_PORT"))
    smtp_user = require_env("SMTP_USER")
    smtp_password = require_env("SMTP_PASSWORD")
    alert_to = require_env("ALERT_TO")
    recipients = [email.strip() for email in alert_to.split(",") if email.strip()]
    alert_from = os.getenv("ALERT_FROM") or smtp_user

    subject = subject_for_changes(changed)

    lines = [
        "Hi, Isidora:",
        "",
        "I checked the three Cinemark store pages and these were the changes:",
        "",
    ]

    for change in changed:
        lines.append(line_for_change(change))
        lines.append(f"  URL: {change['url']}")
        lines.append("")

    lines.append("I attached the relevant screenshots for quick verification.")

    body = "\n".join(lines)

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = alert_from
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    attach_file(message, SUMMARY_PATH)
    attach_file(message, pathlib.Path("debug/results.json"))
    attach_file(message, pathlib.Path("state/last_state.json"))

    for change in changed:
        store_id = change["store_id"]
        attach_file(message, pathlib.Path(f"debug/{store_id}_page.png"))
        attach_file(message, pathlib.Path(f"debug/{store_id}_container.png"))
        attach_file(message, pathlib.Path(f"debug/{store_id}_container_text.txt"))
        attach_file(message, pathlib.Path(f"debug/{store_id}_container_class.txt"))

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(message, to_addrs=recipients)

    print(f"Alert email sent for {len(changed)} changed store(s).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Email error: {e}")
        sys.exit(1)
