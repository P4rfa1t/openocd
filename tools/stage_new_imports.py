#!/usr/bin/env python3
"""Stage the 14 newly approved third-party files for review.

Downloads the exact bytes from the pinned source commits into a staging
directory (NOT the tree) so the integration can be reviewed before anything
lands in the git tree.

Usage: python tools/stage_new_imports.py
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(errors="backslashreplace")

API = "https://api.github.com"
CRED = os.path.expanduser("~/.dsh/.ghcred")
TOKEN = os.environ.get("GH_TOKEN", "")
if not TOKEN and os.path.exists(CRED):
    with open(CRED, encoding="utf-8") as f:
        TOKEN = f.read().strip()
STAGE = os.path.join("raw", "stage-new-imports")

# repo, branch, pinned commit, [(in-tree path, source path)]
GROUPS = {
    "espressif-esp-gpio": (
        "espressif/openocd-esp32", "master",
        "a585825d4d0bbd5b8aff83e01816d2f2c04ffd84",
        [
            ("src/jtag/drivers/esp_gpio.c", "src/jtag/drivers/esp_gpio.c"),
            ("src/jtag/drivers/esp_gpio.h", "src/jtag/drivers/esp_gpio.h"),
            ("tcl/interface/esp_gpio_jtag.cfg", "tcl/interface/esp_gpio_jtag.cfg"),
            ("tcl/interface/esp_gpio_swd.cfg", "tcl/interface/esp_gpio_swd.cfg"),
        ],
    ),
    "wch-wlink-riscv": (
        "Seneral/riscv-openocd-wch", "wch-linke-sdi",
        "bde507c1e98514162bdbe4275662027a46b98e55",
        [
            ("src/jtag/drivers/wlinke.c", "src/jtag/drivers/wlinke.c"),
            ("src/target/wch_riscv.c", "src/target/wch_riscv.c"),
            ("src/target/wch_riscv.h", "src/target/wch_riscv.h"),
            ("src/target/wch_riscv-013.c", "src/target/wch_riscv-013.c"),
        ],
    ),
    "anlogic-al-link": (
        "AnlogicInfo/al_openocd", "master",
        "3580f4327d61a5a8d78462c8caa96ee8e28ca4d4",
        [
            ("src/jtag/drivers/al_link.c", "src/jtag/drivers/al_link.c"),
            ("src/jtag/drivers/al_link_cyusb.c", "src/jtag/drivers/al_link_cyusb.c"),
            ("src/jtag/drivers/al_link_cyusb.h", "src/jtag/drivers/al_link_cyusb.h"),
            ("src/server/rbb_server.c", "src/server/rbb_server.c"),
            ("src/server/rbb_server.h", "src/server/rbb_server.h"),
            ("tcl/interface/al_link.cfg", "tcl/interface/al_link.cfg"),
        ],
    ),
}


def api(path):
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "openocd-consolidator/0.3")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch(repo, commit, path):
    d = api("/repos/%s/contents/%s?ref=%s"
            % (repo, urllib.parse.quote(path), commit))
    if d.get("type") != "file":
        return None
    return base64.b64decode(d["content"])


def main():
    out = {}
    for name, (repo, branch, commit, files) in GROUPS.items():
        for dest, src in files:
            blob = fetch(repo, commit, src)
            if blob is None:
                print("FAIL", dest, "<-", repo)
                continue
            p = os.path.join(STAGE, dest)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(blob)
            out[dest] = {
                "group": name,
                "source_repo": repo,
                "source_branch": branch,
                "source_commit": commit,
                "source_path": src,
                "bytes": len(blob),
                "sha256": hashlib.sha256(blob).hexdigest(),
            }
            print("staged %-45s %7d bytes  %s" % (dest, len(blob), name))
    meta = os.path.join(STAGE, "stage.json")
    os.makedirs(STAGE, exist_ok=True)
    with open(meta, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=2, ensure_ascii=False, sort_keys=True)
    print("\n%d files staged -> %s" % (len(out), STAGE))


if __name__ == "__main__":
    main()
