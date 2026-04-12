import json
import pathlib
import sys
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = "https://www.cinemark.cl/confiteria?tag=548"
PRODUCT = "BALDE YOSHI SUPER MARIO GALXY"


def write_text(path: pathlib.Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    debug_dir = pathlib.Path("debug")
    debug_dir.mkdir(exist_ok=True)

    result = {
        "url": URL,
        "product": PRODUCT,
        "status": "error",
        "message": "",
        "container_class": "",
        "container_text": "",
        "product_text": "",
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(8000)

            product = page.get_by_text(PRODUCT, exact=False).first
            product.wait_for(timeout=10000)

            container = product.locator("xpath=ancestor::li[1]")
            container.wait_for(timeout=10000)

            product_text = product.inner_text().strip()
            container_class = container.get_attribute("class") or ""
            container_text = container.inner_text().strip()

            write_text(debug_dir / "product_text.txt", product_text)
            write_text(debug_dir / "container_class.txt", container_class)
            write_text(debug_dir / "container_text.txt", container_text)

            container.screenshot(path=str(debug_dir / "container.png"))
            page.screenshot(path=str(debug_dir / "page.png"), full_page=True)

            result["product_text"] = product_text
            result["container_class"] = container_class
            result["container_text"] = container_text

            if PRODUCT not in container_text:
                result["status"] = "error"
                result["message"] = "Found an LI container, but it does not contain the expected product name."
            elif "product-sold" in container_class:
                result["status"] = "sold_out"
                result["message"] = "Still sold out."
            else:
                result["status"] = "available"
                result["message"] = "Possible restock detected."

            browser.close()

    except PlaywrightTimeoutError:
        result["status"] = "error"
        result["message"] = "Timed out while locating the product or its LI container."
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Unexpected error: {e}"

    write_text(debug_dir / "status.txt", result["status"])
    write_text(
        debug_dir / "result.json",
        json.dumps(result, ensure_ascii=False, indent=2),
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if result["status"] == "error":
        sys.exit(2)


if __name__ == "__main__":
    main()
