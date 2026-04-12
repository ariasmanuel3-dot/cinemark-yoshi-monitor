import json
import pathlib
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

PRODUCT = "BALDE YOSHI SUPER MARIO GALXY"

STORES = [
    {
        "id": "mall_mirador",
        "name": "Mall Mirador",
        "url": "https://www.cinemark.cl/confiteria?tag=2302&cine=cinemark_mallplaza_mirador_bio_bio",
    },
    {
        "id": "mall_plaza_trebol",
        "name": "Mall Plaza Trébol",
        "url": "https://www.cinemark.cl/confiteria?tag=548&cine=cinemark_mallplaza_trebol",
    },
    {
        "id": "cinemark_coronel",
        "name": "Cinemark Coronel",
        "url": "https://www.cinemark.cl/confiteria?tag=2306&cine=cinemark_arauco_coronel",
    },
]


def write_text(path: pathlib.Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    debug_dir = pathlib.Path("debug")
    debug_dir.mkdir(exist_ok=True)

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for store in STORES:
            page = browser.new_page()

            result = {
                "store_id": store["id"],
                "store_name": store["name"],
                "url": store["url"],
                "product": PRODUCT,
                "status": "error",
                "message": "",
                "container_class": "",
                "container_text": "",
                "product_text": "",
            }

            try:
                page.goto(store["url"], wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(8000)

                page.screenshot(
                    path=str(debug_dir / f'{store["id"]}_page.png'),
                    full_page=True,
                )

                product = page.get_by_text(PRODUCT, exact=False).first

                try:
                    product.wait_for(timeout=10000)
                except PlaywrightTimeoutError:
                    result["status"] = "missing"
                    result["message"] = "The product name could not be found on the page."
                    results.append(result)
                    page.close()
                    continue

                container = product.locator("xpath=ancestor::li[1]")
                container.wait_for(timeout=10000)

                product_text = product.inner_text().strip()
                container_class = container.get_attribute("class") or ""
                container_text = container.inner_text().strip()

                result["product_text"] = product_text
                result["container_class"] = container_class
                result["container_text"] = container_text

                write_text(debug_dir / f'{store["id"]}_product_text.txt', product_text)
                write_text(debug_dir / f'{store["id"]}_container_class.txt', container_class)
                write_text(debug_dir / f'{store["id"]}_container_text.txt', container_text)

                container.screenshot(
                    path=str(debug_dir / f'{store["id"]}_container.png')
                )

                if PRODUCT not in container_text:
                    result["status"] = "error"
                    result["message"] = (
                        "Found an LI container, but it does not contain the expected product name."
                    )
                elif "product-sold" in container_class:
                    result["status"] = "sold_out"
                    result["message"] = "Still sold out."
                else:
                    result["status"] = "available"
                    result["message"] = "Possible restock detected."

            except Exception as e:
                result["status"] = "error"
                result["message"] = f"Unexpected error: {e}"

            results.append(result)
            page.close()

        browser.close()

    write_text(debug_dir / "results.json", json.dumps(results, ensure_ascii=False, indent=2))
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
