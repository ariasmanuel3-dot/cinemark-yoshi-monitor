import json
import pathlib

PRODUCT = "BALDE YOSHI SUPER MARIO GALXY"

RESULTS = [
    {
        "store_id": "mall_mirador",
        "store_name": "Mall Mirador",
        "url": "https://www.cinemark.cl/confiteria?tag=2302&cine=cinemark_mallplaza_mirador_bio_bio",
        "product": PRODUCT,
        "status": "sold_out",
        "message": "TEST: forcing sold_out.",
        "container_class": "product-sold",
        "container_text": "TEST ONLY - Mall Mirador forced sold_out",
        "product_text": PRODUCT,
    },
    {
        "store_id": "mall_plaza_trebol",
        "store_name": "Mall Plaza Trébol",
        "url": "https://www.cinemark.cl/confiteria?tag=548&cine=cinemark_mallplaza_trebol",
        "product": PRODUCT,
        "status": "available",
        "message": "TEST: forcing available.",
        "container_class": "test-container",
        "container_text": "TEST ONLY - Mall Plaza Trébol forced available",
        "product_text": PRODUCT,
    },
    {
        "store_id": "cinemark_coronel",
        "store_name": "Cinemark Coronel",
        "url": "https://www.cinemark.cl/confiteria?tag=2306&cine=cinemark_arauco_coronel",
        "product": PRODUCT,
        "status": "sold_out",
        "message": "TEST: forcing sold_out.",
        "container_class": "product-sold",
        "container_text": "TEST ONLY - Cinemark Coronel forced sold_out",
        "product_text": PRODUCT,
    },
]


def write_text(path: pathlib.Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def main() -> None:
    debug_dir = pathlib.Path("debug")
    debug_dir.mkdir(exist_ok=True)

    for result in RESULTS:
        store_id = result["store_id"]
        write_text(debug_dir / f"{store_id}_container_class.txt", result["container_class"])
        write_text(debug_dir / f"{store_id}_container_text.txt", result["container_text"])
        write_text(debug_dir / f"{store_id}_product_text.txt", result["product_text"])

    write_text(debug_dir / "results.json", json.dumps(RESULTS, ensure_ascii=False, indent=2))
    print(json.dumps(RESULTS, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
