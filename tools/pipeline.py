#!/usr/bin/env python3
"""
Full pipeline: mine -> consolidate -> fetch -> verify.

Run after upstream moves, or when you want to absorb new forks. Every stage is
idempotent, so this is safe to schedule. Without GH_TOKEN it stops at the first
network stage instead of degrading into an unauthenticated rate-limited run.

  python tools/pipeline.py                 # everything, report only
  python tools/pipeline.py --apply         # write into the tree and manifest/
  python tools/pipeline.py --tier 2        # also merge the C sources into src/
  python tools/pipeline.py --from 0        # deep-probe the first N candidates
                                         # (default all; 688 needs a PAT)

Exit code is 0 only when `verify_tree.py` reports VERIFY: PASS, which makes
this usable as a CI check.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run(argv, env=None, check=True):
    e = dict(os.environ)
    if env:
        e.update(env)
    print("+", " ".join(argv), flush=True)
    p = subprocess.run(argv, cwd=ROOT, env=e)
    if check and p.returncode != 0:
        raise SystemExit(f"FAILED ({p.returncode}): {' '.join(argv)}")
    return p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write into the tree and manifest/ (default: report only)")
    ap.add_argument("--tier", type=int, choices=(0, 1, 2), default=1,
                    help="highest tier to fetch; 1 = tcl/ only (default)")
    ap.add_argument("--deep-budget", type=int, default=200,
                    help="how many candidates to deep-probe")
    ap.add_argument("--wide-budget", type=int, default=700,
                    help="how many candidates to wide-probe")
    args = ap.parse_args()

    env = {"PYTHONIOENCODING": "utf-8"}
    if not os.environ.get("GH_TOKEN"):
        print("GH_TOKEN is not set.", file=sys.stderr)
        print("The token is read only from the environment and is never written "
              "to disk. Without it the pipeline stops here.", file=sys.stderr)
        return 2
    if not args.apply:
        print("Report-only run: nothing in the tree or under manifest/ is "
              "rewritten. Re-run with --apply.\n", file=sys.stderr)

    # 1. mine upstream's full recursive inventory and diff every candidate
    #    against it. INDEX is loaded before any diff, so the new-vs-relocated
    #    split is exact rather than guessed from basenames.
    run(["bash", "run_mine.sh"],
        env=dict(env, DIFF_BUDGET=str(args.deep_budget),
                 WIDE_BUDGET=str(args.wide_budget)))
    # 2. drop self/upstream and recompute the confirmed-new set
    run([sys.executable, "refine_survey.py"], env=env)
    # 3. cross-repo dedup + upstream-duplicate removal.
    #    This is the single source of truth; pruning happens while writing the
    #    manifest, so the manifest can never disagree with what lands on disk.
    run([sys.executable, "consolidate.py"], env=env)

    if args.tier >= 1:
        # 4. merge the tier-1 tcl files into tcl/ and verify them
        run([sys.executable, "fetch_third_party.py", "--tier", "1"], env=env)
        if args.apply:
            run([sys.executable, "resolve_deps.py", "--apply"], env=env)
            run([sys.executable, "pin_commits.py"], env=env)
    if args.tier >= 2:
        run([sys.executable, "fetch_third_party.py", "--tier", "2"], env=env)
        if args.apply:
            run([sys.executable, "pin_commits.py"], env=env)

    if not args.apply:
        return 0

    # 5. regenerate the reports from the updated manifests
    run([sys.executable, "gen_report.py"], env=env)
    run([sys.executable, "gen_licenses.py"], env=env)
    run([sys.executable, "build_provenance.py"], env=env)

    # 6. offline gate; must pass before anything is committed
    run([sys.executable, "verify_tree.py"], env=env)
    print("\nVERIFY: PASS - safe to commit", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())