"""RAH3 Phase-0: capture-site structural inspection. TOKENIZER ONLY -- no forward pass, no GPU,
no intervention, effect-blind by construction. Reproduces rah_preflight_transport.py's donor
resolution exactly (rfind + token_index_covering) and reports what sits at each offset."""
import json, os, sys
sys.path.insert(0, "src/boombness")
sys.path.insert(0, "doublespeak_causality")
import ds_common as dc
from transformers import AutoTokenizer


def token_index_covering(offsets, lo, hi):
    hits = [k for k, (a, b) in enumerate(offsets) if b > lo and a < hi and b > a]
    if not hits:
        raise ValueError("no token overlaps [%d,%d)" % (lo, hi))
    return hits[-1]


BANKS = {
    "cb": ("data/boombness_prompts/boombness_prompt_bank.jsonl", 8),
    "lp": ("data/boombness_prompts/boombness_prompt_bank_rbd_lantern_poison.jsonl", 8),
}
MODELS = {"p": "meta-llama/Llama-3.1-8B-Instruct", "q": "Qwen/Qwen3-14B"}
CANDS = {"cb": ["bomb", "carrot", "knife", "ticket"], "lp": ["poison", "lantern", "missile", "candle"]}
OFFSETS = [0, 1, 2, 3, 4, 5, -1]

out = {}
for mk, mid in MODELS.items():
    tok = AutoTokenizer.from_pretrained(mid)
    for bk, (bank, nex) in BANKS.items():
        rows = [json.loads(l) for l in open(bank)]
        cand = [r for r in rows if r["condition"] == "direct_harmful"
                and r["query_kind"] == "behavioral" and r["n_examples"] == nex]
        donors = sorted(cand, key=lambda r: r["prompt_id"])[:8]
        key = "%s_%s" % (mk, bk)
        recs = []
        for d in donors:
            templated = dc.apply_template(tok, d["full_prompt"], enable_thinking=None)
            enc = tok(templated, add_special_tokens=False, return_offsets_mapping=True)
            offs, ids = enc["offset_mapping"], enc["input_ids"]
            surf = d["target_surface"]
            pos_c = templated.lower().rfind(surf.lower())
            p = token_index_covering(offs, pos_c, pos_c + len(surf))
            r = {"prompt_id": d["prompt_id"], "seq_len": len(ids), "p0": p,
                 "n_conc": d["n_concept_occurrences"], "n_code": d["n_codeword_occurrences"]}
            for N in OFFSETS:
                idx = (len(ids) - 1) if N == -1 else (p + N)
                piece = tok.decode([ids[idx]])
                r["off%s" % N] = {"idx": idx, "piece": piece,
                                  "in_bounds": 0 <= idx < len(ids),
                                  "overlaps_concept": piece.strip().casefold() in d["concept"].casefold() and bool(piece.strip()),
                                  "overlaps_codeword": piece.strip().casefold() in d["codeword"].casefold() and bool(piece.strip()),
                                  "is_candidate": piece.strip().casefold() in [c.casefold() for c in CANDS[bk]]}
            r["tail"] = [tok.decode([i]) for i in ids[p:p + 8]]
            recs.append(r)
        out[key] = {"model": mid, "bank": bank, "n_donors": len(recs), "rows": recs}
        print("== %s (%s / %s) n=%d" % (key, mk, bk, len(recs)))
        for N in OFFSETS:
            pieces = sorted({r["off%s" % N]["piece"] for r in recs})
            bad = sum(1 for r in recs if r["off%s" % N]["overlaps_concept"]
                      or r["off%s" % N]["overlaps_codeword"] or r["off%s" % N]["is_candidate"])
            print("   offset %-3s consistent=%-5s pieces=%r  DISQUALIFIED_ROWS=%d"
                  % (N, len(pieces) == 1, pieces[:6], bad))
        print("   tail from concept:", recs[0]["tail"])
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


_atomic_json_dump(out, sys.argv[1], indent=1)
print("\n-> %s" % sys.argv[1])
