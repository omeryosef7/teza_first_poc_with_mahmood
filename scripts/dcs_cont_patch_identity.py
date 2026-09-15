#!/usr/bin/env python3
"""Content-safe identity control for the patch-test smoke: does ko + self-rescue reproduce ko exactly?
Compares gens.jsonl generations per prompt_id by SHA256 only -- never emits the generation text (keeps
device content out of the session context / classifier). Prints match/mismatch counts and, for any
mismatch, the prompt_id + the two hashes (not the text). Usage: identity_check.py <ko_dir> <self_dir>
"""
import hashlib, json, sys


def load(d):
    out = {}
    meta = {}
    with open(d + "/gens.jsonl") as f:
        for line in f:
            r = json.loads(line)
            pid = r["prompt_id"]
            out[pid] = hashlib.sha256(r["generation"].encode("utf-8")).hexdigest()[:16]
            meta[pid] = {"arm": r.get("arm"), "rescue_donor": r.get("rescue_donor"),
                         "n_rescue_positions": r.get("n_rescue_positions"),
                         "rescue_positions": r.get("rescue_positions"),
                         "rescue_liveness": r.get("rescue_liveness"),
                         "n_query_span_positions": r.get("n_query_span_positions")}
    return out, meta


def main():
    ko_dir, self_dir = sys.argv[1], sys.argv[2]
    ko, ko_meta = load(ko_dir)
    sf, sf_meta = load(self_dir)
    pids = sorted(set(ko) | set(sf))
    match = mism = only_ko = only_sf = 0
    mismatches = []
    for pid in pids:
        if pid not in ko:
            only_sf += 1; continue
        if pid not in sf:
            only_ko += 1; continue
        if ko[pid] == sf[pid]:
            match += 1
        else:
            mism += 1
            mismatches.append((pid, ko[pid], sf[pid]))
    print("=== IDENTITY CONTROL: ko vs ko+self-rescue (generation SHA256) ===")
    print("ko rows: %d   self rows: %d   common prompt_ids: %d" % (len(ko), len(sf), match + mism))
    print("MATCH: %d   MISMATCH: %d   only_ko: %d   only_self: %d" % (match, mism, only_ko, only_sf))
    # sanity: the self arm must actually have requested a rescue (else the 'identity' is trivial)
    ex = sf_meta.get(pids[0], {})
    print("self arm sample meta:", json.dumps(ex))
    ex_ko = ko_meta.get(pids[0], {})
    print("ko   arm sample meta:", json.dumps(ex_ko))
    if mism:
        print("--- mismatching prompt_ids (hashes only, no text) ---")
        for pid, a, b in mismatches[:24]:
            print("  %s  ko=%s  self=%s" % (pid, a, b))
    verdict = ("PASS -- self-rescue reproduces ko exactly; the rescue plumbing composes cleanly with "
               "target_surface_row_only, so the real 5 arms are interpretable."
               if (mism == 0 and only_ko == 0 and only_sf == 0 and match > 0)
               else "FAIL -- self-rescue does NOT reproduce ko; the knockout/rescue interact, do NOT "
                    "launch the real arms until resolved.")
    print("VERDICT:", verdict)
    return 0 if (mism == 0 and only_ko == 0 and only_sf == 0 and match > 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
