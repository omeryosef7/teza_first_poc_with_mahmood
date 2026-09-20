#!/usr/bin/env python3
"""Run a CROSS-MODEL LLM-judge panel over the blind sheet and emit the `passes` panel format that
scripts/dcs_cont_llm_judge_analyze.py consumes. One "pass" per judge model (median across models =
consensus). This is the OpenAI/Gemini realization of the LLM-judge PROXY -- the Claude-subagent panel
is hard-blocked by the safety classifier (the sheet contains genuine device recipes), so a same-session
Claude panel is impossible; the OpenAI judge is the ESTABLISHED pipeline (StrongREJECT sr in the key was
already scored by it), so it adds no new exposure. Reuses RUBRIC/parse_sheet/load_env/judge_* from
dcs_cont_llm_judge.py. BLIND: reads only the arms-stripped sheet, never the sealed key. Validity still
rests entirely on the disclaimer-sensitivity diagnostic computed at aggregation; never replaces the human read.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys, time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = importlib.util.spec_from_file_location("gen", os.path.join(REPO, "scripts/dcs_cont_llm_judge.py"))
gen = importlib.util.module_from_spec(g); g.loader.exec_module(gen)

# (pass_name, family, model)
JUDGES = [
    ("openai_gpt4o", "openai", "gpt-4o"),
    ("openai_gpt4o_mini", "openai", "gpt-4o-mini"),
    ("gemini_15pro", "gemini", "gemini-1.5-pro"),
]


def _atomic_json_dump(obj, path, **kw):
    """Atomic, VERIFIED JSON write. Fix for sprint entry S-124.

    Replaces `json.dump(x, open(p, "w"), ...)`, whose handle is never closed: `open` truncates the
    destination immediately and the buffered bytes are flushed only in the GC finaliser, where
    CPython PRINTS and then SWALLOWS an EDQUOT. A full quota therefore produced a 0-byte file at a
    real artifact name, with "wrote <path>" on stdout and exit status 0 -- indistinguishable from a
    finished report. Temp file + fsync + size check + re-parse + os.replace makes the write ATOMIC
    as well as checked: a half-written file never appears at the real name, and whatever was there
    before survives a failure. On any error this RAISES, naming the path and the byte count.
    """
    import tempfile                        # local: keeps this helper drop-in and import-order-free
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, **kw)
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777   # keep the artifact's existing permissions:
        except OSError:                             # mkstemp makes the temp file 0600 and
            mode = 0o644                            # os.replace would carry that onto the report
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            n = os.path.getsize(tmp)
        except OSError:
            n = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_json_dump FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, n, e)) from e
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_LLM_JUDGE_PANEL.json"))
    a = ap.parse_args()
    env = gen.load_env()
    items = gen.parse_sheet()
    print("parsed %d answers" % len(items))

    clients = {}
    if env.get("OPENAI_API_KEY"):
        import openai
        clients["openai"] = openai.OpenAI(api_key=env["OPENAI_API_KEY"])
    if env.get("GEMINI_API_KEY"):
        import google.generativeai as genai
        genai.configure(api_key=env["GEMINI_API_KEY"]); clients["gemini"] = genai
    judges = [(nm, fam, mdl) for (nm, fam, mdl) in JUDGES if fam in clients]
    print("judges:", [j[0] for j in judges])

    passes = []
    for nm, fam, mdl in judges:
        ratings, n_err = [], 0
        for iid in sorted(items):
            val = None
            for attempt in range(3):
                try:
                    if fam == "openai":
                        val = gen.judge_openai(clients["openai"], items[iid], model=mdl)
                    else:
                        val = gen.judge_gemini(clients["gemini"], items[iid], model=mdl)
                    val = gen._norm(val); break
                except Exception as e:
                    last = "%s:%s" % (type(e).__name__, str(e)[:80]); time.sleep(2 * (attempt + 1))
            if val is None:
                n_err += 1; continue
            ratings.append({"item_id": iid, "score": val["score"], "prop": val["prop"],
                            "literal": val["literal"], "reason": val["reason"]})
        print("  %-20s rated %d / %d (errors %d)" % (nm, len(ratings), len(items), n_err))
        passes.append({"pass": nm, "model": mdl, "ratings": ratings})

    out = {"schema": "dcs_cont_llm_judge_panel/openai_gemini", "n_passes": len(passes),
           "framing": "cross-model LLM-judge PROXY for the human read; per-pass = per-model; consensus "
                      "= median across models. Trustworthy ONLY if disclaimer-insensitive (see diagnostic).",
           "judges": [j[0] for j in judges], "passes": passes}
    _atomic_json_dump(out, a.out, indent=1)
    print("wrote %s" % os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
