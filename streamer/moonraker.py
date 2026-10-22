import json
import logging
import urllib.request

log = logging.getLogger("streamer.moonraker")


def _call(base, method, path, body=None):
    req = urllib.request.Request(base.rstrip("/") + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r).get("result", {})


def register(base, webcams):
    """Add or update each camera in Moonraker's webcam list. True once all are in."""
    try:
        existing = {w.get("name"): w for w in _call(base, "GET", "/server/webcams/list").get("webcams", [])}
        for name, service, stream, snapshot, fps in webcams:
            item = {"name": name, "service": service, "stream_url": stream, "snapshot_url": snapshot,
                    "target_fps": fps, "enabled": True, "location": "printer"}
            if existing.get(name, {}).get("uid"):
                item["uid"] = existing[name]["uid"]
            _call(base, "POST", "/server/webcams/item", item)
            log.info("registered %s with Moonraker", name)
        return True
    except OSError as ex:
        log.warning("couldn't reach Moonraker at %s (%s), will try again", base, ex)
        return False
