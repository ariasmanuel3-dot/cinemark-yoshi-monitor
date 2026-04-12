import json
import pathlib

MISSING_THRESHOLD = 12

STATE_PATH = pathlib.Path("state/last_state.json")
RESULTS_PATH = pathlib.Path("debug/results.json")
SUMMARY_PATH = pathlib.Path("state/transition_summary.json")


def load_json(path: pathlib.Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: pathlib.Path, data) -> None:
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    previous = load_json(STATE_PATH, {"stores": {}})
    results = load_json(RESULTS_PATH, [])

    prev_stores = previous.get("stores", {})
    new_state = {"stores": {}}
    changed_stores = []

    for result in results:
        store_id = result["store_id"]
        store_name = result["store_name"]

        prev = prev_stores.get(
            store_id,
            {"name": store_name, "url": result["url"], "last_seen_state": "unknown", "missing_streak": 0},
        )

        prev_seen = prev.get("last_seen_state", "unknown")
        prev_missing = int(prev.get("missing_streak", 0))
        raw_status = result.get("status", "error")

        missing_streak = prev_missing
        current_state = prev_seen
        alert_event = None

        if raw_status == "missing":
            missing_streak = prev_missing + 1
            if missing_streak >= MISSING_THRESHOLD:
                current_state = "missing_confirmed"
                if prev_seen != "missing_confirmed":
                    alert_event = "missing_confirmed"
            else:
                current_state = "missing_pending"

        elif raw_status == "available":
            missing_streak = 0
            current_state = "available"
            if prev_seen != "available":
                alert_event = "available"

        elif raw_status == "sold_out":
            missing_streak = 0
            current_state = "sold_out"
            if prev_seen == "available":
                alert_event = "sold_out"

        elif raw_status == "error":
            current_state = prev_seen
            missing_streak = prev_missing

        persistent_state = prev_seen
        if current_state in {"available", "sold_out", "missing_confirmed"}:
            persistent_state = current_state

        new_state["stores"][store_id] = {
            "name": store_name,
            "url": result["url"],
            "last_seen_state": persistent_state,
            "missing_streak": missing_streak,
        }

        if alert_event is not None:
            changed_stores.append(
                {
                    "store_id": store_id,
                    "store_name": store_name,
                    "url": result["url"],
                    "event": alert_event,
                    "previous_state": prev_seen,
                    "current_state": current_state,
                    "missing_streak": missing_streak,
                    "raw_status": raw_status,
                    "message": result.get("message", ""),
                }
            )

    summary = {
        "changed_stores": changed_stores,
        "results": results,
    }

    save_json(STATE_PATH, new_state)
    save_json(SUMMARY_PATH, summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
