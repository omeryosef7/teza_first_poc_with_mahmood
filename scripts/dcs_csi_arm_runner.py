"""W3 -- run many score_behavior arms in ONE process, paying the model load ONCE.

WHY. Design 7.1 measures the load at ~866 s/arm, 55.3% of an allocation. Over the 48 primary arms
that is ~11.5 GPU-hours spent re-reading the same weights -- MORE THAN THE ARMS' OWN COMPUTE
(8.55 h, S-193). W3 is not an optimisation, it is most of the cost.

⛔ IT DOES NOT EDIT score_behavior.py, AND THAT IS THE WHOLE DESIGN CONSTRAINT.
PR-CSI-003's VOID condition prohibits modifying that file. So W3 does not add an inject-a-model
parameter to it. It MEMOISES `ds_common.load_model` from the outside and calls `score_behavior.main()`
once per arm with a rewritten `sys.argv`. `score_behavior` reaches the loader as `dc.load_model`,
where `dc` is the ds_common MODULE object (score_behavior.py:2716 `dc, pc = ds(), pair()`), so
replacing the module attribute is seen at call time and nothing in the file changes.

THE THREE WAYS IN-PROCESS LOOPING CAN SILENTLY CORRUPT A FAMILY, AND WHAT IS DONE ABOUT EACH:

1. A LEAKED HOOK. Arm N registers a forward hook and fails to remove it; arm N+1 then runs under an
   intervention nobody asked for and NOTHING IN ITS ARTIFACT RECORDS THIS. `pair_common` registers
   hooks in 28 places. So every module's hook dicts are counted before and after each arm, and any
   residue is a REFUSAL -- the family stops rather than producing a contaminated arm.

2. THE WRONG MODEL RETURNED BY THE CACHE. If arm N+1 asks for a different dtype, attention backend,
   revision or model id, a naive memo hands back arm N's model and the arm records the parameters it
   REQUESTED while running on something else. The memo is therefore KEYED ON EVERY LOAD PARAMETER:
   a differing request MISSES and loads fresh. Correct by construction rather than by assertion.

3. RNG CARRY-OVER. Checked, and it is a non-issue: `main()` calls `seed_everything(args.seed)` at
   score_behavior.py:2714, before any work, so each arm re-seeds exactly as a fresh process would.

ONE RECORDED CONSEQUENCE, NOT A DEFECT. `common.SEED_LOG` is per-PROCESS, and `RunDir.finish`
writes both `applied` (the whole log) and `since` (this run's slice). In-process, `applied` grows
across arms -- still literally "what this process applied". `since` remains the per-arm field and is
the one a per-arm verifier must read. Every run dir W3 produces records `in_process_runner: true`
so a reader knows which convention applies.
"""
import argparse, json, os, sys, time

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

import torch                                    # noqa: E402
import ds_common as dc                          # noqa: E402


def hook_census(model):
    """(n_hooks, [where]) over every submodule. A leak is invisible in an artifact, so it is counted."""
    n, where = 0, []
    for name, mod in model.named_modules():
        for attr in ("_forward_hooks", "_forward_pre_hooks", "_backward_hooks",
                     "_backward_pre_hooks"):
            d = getattr(mod, attr, None)
            if d:
                n += len(d)
                where.append("%s.%s x%d" % (name or "<root>", attr, len(d)))
    return n, where


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--argv-file", required=True,
                    help="one full score_behavior command per line (from dcs_csi_pr010_argv.py)")
    ap.add_argument("--expect-n", type=int, default=0,
                    help="row count that defines a COMPLETE arm; enables skip-if-done")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stop-on-fail", action="store_true",
                    help="stop the family at the first failing arm instead of continuing")
    a = ap.parse_args()

    lines = [l.strip() for l in open(a.argv_file) if l.strip() and not l.startswith("#")]

    # ⛔ SKIP ARMS THAT ARE ALREADY COMPLETE, AND THIS IS A CORRECTNESS REQUIREMENT, NOT A SAVING.
    # A preempted allocation keeps every arm that finished -- each writes its own run dir. Re-running
    # such an arm creates a SECOND run dir under the SAME TAG, and `strict_run_dir` then refuses the
    # whole family for having more than one candidate (S-104/S-127). So a resubmission must not
    # re-run what already landed. A tag that resolves to exactly one COMPLETE run is skipped; a tag
    # that resolves to several is REFUSED here rather than at read time.
    if a.expect_n:
        import importlib.util as _il
        _sp = _il.spec_from_file_location("rederive", os.path.join(REPO, "scripts",
                                                                   "dcs_csi_rederive_patch.py"))
        _rd = _il.module_from_spec(_sp); _sp.loader.exec_module(_rd)
        keep, skipped_done = [], []
        for line in lines:
            av = line.split()
            tag = av[av.index("--tag") + 1] if "--tag" in av else None
            if tag is None:
                keep.append(line); continue
            try:
                _rd.strict_run_dir(tag, a.expect_n, row_file="results.jsonl")
                skipped_done.append(tag)          # exactly one complete run exists
            except SystemExit as e:
                msg = str(e)
                if "more than one" in msg or "resolved to" in msg:
                    sys.exit("REFUSING: tag %r already resolves to MORE THAN ONE complete run; "
                             "re-running would deepen the duplicate. Resolve it first. (%s)"
                             % (tag, msg[:160]))
                keep.append(line)
            except Exception:
                keep.append(line)
        if skipped_done:
            print("[w3] SKIPPING %d arm(s) already complete: %s"
                  % (len(skipped_done), ", ".join(t.split("_")[-1] for t in skipped_done)), flush=True)
        lines = keep

    print("[w3] SIZE arms to run = %d" % len(lines), flush=True)
    if not lines:
        print("[w3] every requested arm is already complete -- nothing to run")
        return 0

    # ---- the memo, keyed on EVERY load parameter -------------------------------------------
    real_load = dc.load_model
    cache, loads = {}, []

    def memo_load_model(model_id=dc.PRIMARY_MODEL, dtype=torch.bfloat16, device_map="auto",
                        revision=None, attn_implementation="sdpa", quantize=None):
        key = (str(model_id), str(dtype), str(device_map), str(revision),
               str(attn_implementation), str(quantize))
        if key not in cache:
            t0 = time.time()
            cache[key] = real_load(model_id=model_id, dtype=dtype, device_map=device_map,
                                   revision=revision, attn_implementation=attn_implementation,
                                   quantize=quantize)
            loads.append({"key": list(key), "seconds": round(time.time() - t0, 3)})
            print("[w3] MODEL LOAD #%d (%.1f s) key=%s" % (len(loads), loads[-1]["seconds"], key),
                  flush=True)
        return cache[key]

    dc.load_model = memo_load_model
    import score_behavior as sb                  # noqa: E402  (after the patch, before any arm)

    results, argv0 = [], list(sys.argv)
    for i, line in enumerate(lines):
        argv = line.split()
        if argv and argv[0] == "python":
            argv = argv[1:]
        arm = argv[argv.index("--arm") + 1] if "--arm" in argv else "arm%d" % i
        # hooks BEFORE -- a leak from the previous arm must stop this one, not ride along
        pre_n, pre_w = (hook_census(next(iter(cache.values())).model) if cache else (0, []))
        if pre_n:
            sys.exit("REFUSING before arm %s: %d hook(s) survive from the previous arm -- the next "
                     "arm would run under an intervention nobody requested and its artifact would "
                     "record nothing. %s" % (arm, pre_n, pre_w[:6]))
        t0 = time.time()
        sys.argv = argv
        status, rc = "ok", None
        try:
            rc = sb.main()
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 1
            status = "refused" if rc else "ok"
        except Exception as e:                    # noqa: BLE001
            status, rc = "raised: %r" % (e,), 1
        finally:
            sys.argv = argv0
        wall = round(time.time() - t0, 3)
        post_n, post_w = (hook_census(next(iter(cache.values())).model) if cache else (0, []))
        rec = {"i": i, "arm": arm, "status": status, "rc": rc, "wall_seconds": wall,
               "hooks_after": post_n, "hooks_where": post_w[:6]}
        results.append(rec)
        print("[w3] %2d/%d %-12s %-8s rc=%s %8.1f s  hooks_after=%d"
              % (i + 1, len(lines), arm, status, rc, wall, post_n), flush=True)
        if post_n:
            print("[w3] REFUSING: arm %s leaked %d hook(s): %s" % (arm, post_n, post_w[:6]),
                  file=sys.stderr, flush=True)
            break
        if status != "ok" and a.stop_on_fail:
            print("[w3] stopping: --stop-on-fail and arm %s did not succeed" % arm, file=sys.stderr)
            break

    ok = sum(1 for r in results if r["status"] == "ok")
    out = {
        "schema": "dcs_csi_arm_runner/1",
        "argv_file": a.argv_file, "n_arms_requested": len(lines), "n_arms_run": len(results),
        "n_ok": ok, "n_model_loads": len(loads), "loads": loads,
        "in_process_runner": True,
        "arms": results,
        "SEED_LOG_NOTE": ("RunDir 'applied' is per-PROCESS and grows across arms here; 'since' is "
                          "the per-arm slice and is the field a per-arm verifier must read"),
        "hook_leak_detected": any(r["hooks_after"] for r in results),
    }
    d = os.path.dirname(os.path.abspath(a.out)) or "."
    tmp = os.path.join(d, ".tmp_w3.json")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2); fh.write("\n"); fh.flush(); os.fsync(fh.fileno())
    json.load(open(tmp)); os.replace(tmp, a.out)
    print("[w3] wrote %s (%d bytes)" % (a.out, os.path.getsize(a.out)))
    print("[w3] arms ok %d/%d | MODEL LOADS %d (one per distinct load key)"
          % (ok, len(lines), len(loads)))
    if len(loads) > 1:
        print("[w3] NOTE: more than one load means the arms did NOT all request the same model "
              "configuration; that is the memo working, not failing.")
    return 0 if (ok == len(lines) and not out["hook_leak_detected"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
