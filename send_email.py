import json
import mimetypes
import os
import pathlib
import smtplib
import ssl
import sys
from email.message import EmailMessage


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


def main() -> None:
    debug_dir = pathlib.Path("debug")
    result_path = debug_dir / "result.json"

    if not result_path.exists():
        raise RuntimeError("debug/result.json does not exist.")

    result = json.loads(result_path.read_text(encoding="utf-8"))

    alert_event = os.getenv("ALERT_EVENT", "").strip()
    previous_status = os.getenv("PREVIOUS_STATUS", "").strip()
    current_status = os.getenv("CURRENT_STATUS", "").strip()

    if alert_event not in {"available", "sold_out"}:
        print("No email sent because there is no alertable transition.")
        return

    smtp_host = require_env("SMTP_HOST")
    smtp_port = int(require_env("SMTP_PORT"))
    smtp_user = require_env("SMTP_USER")
    smtp_password = require_env("SMTP_PASSWORD")
    alert_to = require_env("ALERT_TO")
    recipients = [email.strip() for email in alert_to.split(",") if email.strip()]
    alert_from = os.getenv("ALERT_FROM") or smtp_user

    product = result.get("product", "Product")
    url = result.get("url", "")
    container_class = result.get("container_class", "")
    container_text = result.get("container_text", "")
    message_text = result.get("message", "")

    if alert_event == "available":
        subject = f"[Stock Alert] {product} is now available"
        intro = "The monitor detected a transition to AVAILABLE."
    else:
        subject = f"[Stock Alert] {product} sold out again"
        intro = "The monitor detected a transition back to SOLD OUT."

    body = f"""{intro}

Product: {product}
URL: {url}

Previous status: {previous_status}
Current status: {current_status}

Monitor message: {message_text}
Container class: {container_class}

Visible text captured from the product card:
{container_text}
"""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = alert_from
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    attach_file(message, debug_dir / "container.png")
    attach_file(message, debug_dir / "container_text.txt")
    attach_file(message, debug_dir / "result.json")

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(message, to_addrs=recipients)

    print(f"Alert email sent for transition: {previous_status} -> {current_status}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Email error: {e}")
        sys.exit(1)
