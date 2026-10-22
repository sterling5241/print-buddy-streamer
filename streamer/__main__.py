import argparse
import logging
import os
import sys

from . import config, detect, manager


def main():
    ap = argparse.ArgumentParser(prog="streamer", description="Print Buddy Streamer")
    ap.add_argument("-c", "--config", default="streamer.conf")
    ap.add_argument("--list", action="store_true", help="show the cameras found and exit")
    a = ap.parse_args()
    if a.list:
        print("\n".join(detect.describe()))
        return 0
    cfg = config.load(a.config)
    logging.basicConfig(level=getattr(logging, cfg.log_level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return manager.Supervisor(cfg, os.path.dirname(os.path.abspath(a.config))).run()


if __name__ == "__main__":
    sys.exit(main())
