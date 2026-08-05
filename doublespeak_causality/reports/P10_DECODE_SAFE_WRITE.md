# P10 — The concept-write null SURVIVES a decode-safe re-test

**Status: ✅ COMPLETE** (job 718938, n=86 clearharm, 44 train / 42 test, 1 h 23 m).
**Verdict: the L8–11 concept write is behaviorally inert during generation, not merely during prefill.**

---

## 1. Why this run was necessary

The previous sprint concluded the concept circuit is "behaviorally inert" from an ablation applied
**throughout harmful generation**. It was not. `pc.ComponentOutSwap`'s position guard
(`keep = [k for k,p in enumerate(pos) if 0 <= p < seq]`, pair_common.py:407) drops every position when
`seq == 1`, which is every KV-cached decode step. **The ablation therefore fired during prefill only, and
the generation phase was never tested.** (Verified separately: the guard's *other* failure mode — writing
the prompt-position-0 row onto every generated token — could not have applied here, because under the Llama
chat template token 0 is always `<|begin_of_text|>`, so a codeword index is never 0. The old decode phase
was a clean no-op, not a corrupted one.)

This run tests both phasings **in one experiment**, on the same items, so the difference is measurable
rather than inferred.

## 2. Design

| arm | what it does |
|---|---|
| `baseline` | no intervention |
| `write_abl_prefill` | the historical arm — zero `mlp_out` at L8–11 on the ~12 demo-codeword positions, prefill only |
| `rand_pos_abl_prefill` | count-matched random non-codeword positions, prefill only |
| **`write_abl_decodesafe`** | prefill as above **plus** zeroing L8–11 on **every generated token** |
| **`rand_pos_abl_decodesafe`** | the same, with count-matched random positions |

The decode-safe arms use `PhasedMLPZero`, verified **bit-identical to `ComponentOutSwap(zeros)` on prefill**
so the comparison is apples-to-apples and differs *only* in timestep coverage.

**⚠️ The confound this design exists to handle.** The decode half is necessarily broad — generated positions
are not known in advance, so it cannot be codeword-selective the way the prefill half is. A raw
baseline-vs-decodesafe delta therefore confounds *"the write is needed"* with *"zeroing 4 MLP layers on
every generated token damages generation."* **The count-matched random control runs in both phasings and
carries the identical decode-side damage**, so `write − rand` isolates position specificity with damage held
constant. **Read that number, not the raw delta.**

## 3. Results — every arm null, and the two splits disagree in sign

ASR, paired exact McNemar, bootstrap CI, Holm across the 4 ablation arms:

| split | arm | ΔASR | 95 % CI | McNemar p | Holm | empty |
|---|---|---|---|---|---|---|
| train (44) | `write_abl_prefill` | −0.0227 | [−0.114, +0.068] | 1.000 | 1.0 | 0.0 |
| | `rand_pos_abl_prefill` | 0.0000 | [−0.114, +0.114] | 1.000 | 1.0 | 0.0 |
| | **`write_abl_decodesafe`** | **+0.0682** | [−0.068, +0.205] | 0.508 | 1.0 | 0.0 |
| | `rand_pos_abl_decodesafe` | +0.0455 | [−0.068, +0.159] | 0.688 | 1.0 | 0.0 |
| test (42) | `write_abl_prefill` | +0.0952 | [−0.048, +0.238] | 0.344 | 1.0 | 0.0 |
| | `rand_pos_abl_prefill` | +0.0238 | [−0.095, +0.143] | 1.000 | 1.0 | 0.0 |
| | **`write_abl_decodesafe`** | **−0.0714** | [−0.238, +0.095] | 0.581 | 1.0 | 0.0 |
| | `rand_pos_abl_decodesafe` | 0.0000 | [−0.119, +0.119] | 1.000 | 1.0 | 0.0 |

**Every CI includes 0. Every McNemar p ≥ 0.34. Every Holm-corrected p = 1.0. `empty_rate` = 0.0 in all 10
cells**, so no result is decoder breakage. 86 rows, 0 skipped.

**The specificity-controlled numbers** (`write − rand`, decode damage held constant):
**train +0.0227, test −0.0715** — *opposite signs*, both within the ~2 pp judge noise floor's
neighbourhood. The prefill arms also disagree in sign (−0.023 / +0.095). Sign-flipping across a
pre-registered split is the signature of noise, not of a small real effect.

**The confound was real and worth controlling.** On train, the random-position decode arm *alone* moves ASR
by **+0.0455** — roughly **two thirds** of the apparent +0.0682 "necessity". Had we read the raw delta we
would have reported an effect that is mostly generic decode damage.

## 4. Conclusion

**The concept-circuit behavioral null survives.** Ablating the L8–11 write across *both* prefill and every
generated token leaves attack success statistically unchanged, against a count-matched control that absorbs
the decode-side damage.

This **closes the §0.9 defect** rather than overturning the finding: the original null was accidentally
untested for the generation phase, and now that it *is* tested, the answer is the same. The
representation ≠ behavior dissociation is therefore stronger than before — it rests on a measurement that
actually did what it claimed.

## 5. Honest limitations

- **This is a null at n = 86**, subject to the same power ceiling as its predecessor: at the empirically
  measured flip-noise level, detecting ΔASR ≈ 0.07 at 80 % power needs **n ≈ 275** (P10.0 §power). The
  claim is *"no effect detectable at this n"*, **not** *"no effect"*.
- The two splits disagreeing in sign is consistent with a true zero, but with n = 42–44 per split it is also
  consistent with a small effect swamped by noise.
- The judge contributes an irreducible **~2 pp** label-flip floor on byte-identical text, so |ΔASR| below
  ~2 pp is uninterpretable regardless of n.
- Only the **clearharm v1** cohort was run. The v3 benches (n = 170 + 154) exist and a re-run there would be
  the natural power upgrade.
- `--allpos-arm` (zeroing L8–11 at *every* position, a strictly broader upper bound) was **not** enabled;
  it is available and honestly labelled if a bound is ever wanted.

## 6. Reproduce

```
sbatch --time=08:00:00 --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSN=0 \
  doublespeak_causality/slurm/run_behav_write.sh
python scripts/phase_behav_carry_analyze.py outputs/behav_write_clearharm_L8_9_10_11_ds_20260805_232238_718938
```
Run dir: `behav_write_clearharm_L8_9_10_11_ds_20260805_232238_718938` (git `bc653407`).
Legacy arm names are preserved via `legacy_arm_name_map` (`write_abl` → `write_abl_prefill`).
