import configparser
from dataclasses import dataclass, field
from pathlib import Path

TIERS = ("light", "basic", "full")
_tier_file = Path(__file__).with_name("TIER")
BUILT_TIER = _tier_file.read_text().strip() if _tier_file.exists() else None


@dataclass
class Cam:
    name: str
    device: str = "auto"
    port: int = 8080
    resolution: str = "1280x720"
    fps: int = 15
    flags: str = ""


@dataclass
class Config:
    tier: str = "basic"
    moonraker: str = "http://127.0.0.1:7125"
    host: str = "auto"
    log_level: str = "info"
    cams: list = field(default_factory=list)


def load(path):
    cp = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
    if not cp.read(path):
        raise SystemExit(f"config not found: {path}")
    s = cp["streamer"] if cp.has_section("streamer") else {}
    cfg = Config(
        tier=s.get("tier", BUILT_TIER or "basic").strip().lower(),
        moonraker=s.get("moonraker", "http://127.0.0.1:7125").strip(),
        host=s.get("host", "auto").strip(),
        log_level=s.get("log_level", "info").strip().lower(),
    )
    if cfg.tier not in TIERS:
        raise SystemExit(f"tier must be one of {', '.join(TIERS)}, not {cfg.tier!r}")
    if BUILT_TIER in TIERS and TIERS.index(cfg.tier) > TIERS.index(BUILT_TIER):
        raise SystemExit(f"this is the {BUILT_TIER} package; the {cfg.tier} tier needs the {cfg.tier} package")
    for sec in cp.sections():
        if not sec.lower().startswith("cam"):
            continue
        c, i = cp[sec], len(cfg.cams)
        cfg.cams.append(Cam(
            name=c.get("name", f"cam{i + 1}").strip(),
            device=c.get("device", "auto").strip(),
            port=c.getint("port", 8080 + i),
            resolution=c.get("resolution", "1280x720").strip(),
            fps=c.getint("fps", 15),
            flags=c.get("flags", "").strip(),
        ))
    return cfg
