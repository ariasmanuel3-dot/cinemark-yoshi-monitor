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

    if result.get("status") != "available":
        print("No email sent because the product is not marked available.")
        return

    smtp_host = require_env("SMTP_HOST")
    smtp_port = int(require_env("SMTP_PORT"))
    smtp_user = require_env("SMTP_USER")
    smtp_password = require_env("SMTP_PASSWORD")
    alert_to = require_env("ALERT_TO")
    alert_from = os.getenv("ALERT_FROM") or smtp_user

    subject = f"[Stock Alert] {result.get('product', 'Product')} may be available"

    body = f"""The monitor thinks the product may be available.

Product: {result.get("product", "")}
URL: {result.get("url", "")}
Status: {result.get("status", "")}
Message: {result.get("message", "")}
Container class: {result.get("container_class", "")}

Visible text captured from the product card:
{result.get("container_text", "")}
"""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = alert_from
    message["To"] = alert_to
    message.set_content(body)

    attach_file(message, debug_dir / "container.png")
    attach_file(message, debug_dir / "container_text.txt")
    attach_file(message, debug_dir / "result.json")

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    print("Alert email sent.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Email error: {e}")
        sys.exit(1)
