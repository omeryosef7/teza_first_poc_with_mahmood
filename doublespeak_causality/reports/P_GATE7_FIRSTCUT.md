# §14–18 Gate-7 — Attack-Objective First-Cut (does a refusal-derived GCG objective beat token-only?)

**Status:** first-cut **NEGATIVE for specificity (Claim F not supported at first-cut).** A mechanism-derived
(refusal-suppression) GCG objective does **not** beat a norm-matched **random-direction** control at matched
compute → no evidence the *mechanism* specifically improves adversarial optimization. DIRECTIONAL only —
needs multi-seed / full-step confirmation before it is definitive.

**Runs:** optimization `slurm_scripts/run_gcg_p9_firstcut_optimize.slurm` (job 732918) → 4 arms in
`outputs/stage_gcg_full/phase9_gcg_mac_matrix_arm{04,07_L18,07_L22,07_rand_L18}_seed42`; held-out eval
(job 736438, `26_eval_p9_gcg_heldout_asr.py`) → `p9_heldout_asr_summary.json` per arm. §16 optimizer
unit-tests PASS (objective enters selection, weight=0 == baseline); `--no-filter-cand`, `--suffix-placement
user`. Objective was active during optimization (arm07 rd_loss drove +0.02 → −0.06).

## Result — held-out StrongREJECT ASR (test n=42; suffix optimized on the 20-item train, compute-matched)
| arm | objective | ASR | refusal rate |
|---|---|---|---|
| arm04 | vanilla GCG (task-only) | 0.262 | 0.714 |
| arm07-L18 | refusal-suppression @ **validated L18** | 0.405 | 0.524 |
| arm07-L22 | refusal-suppression @ frozen/unvalidated L22 | 0.500 | 0.262 |
| arm07-rand-L18 | **norm-matched random** direction @ L18 (control) | **0.476** | 0.429 |

## Interpretation
1. **Adding a decision-state suppression term to candidate selection raises ASR** (all three repr arms
   0.40–0.50 vs vanilla 0.26). The objective genuinely changes the search.
2. **But it is NOT refusal-mechanism-specific:** the norm-matched **random** control (0.476) **beats** the
   validated-L18 refusal objective (0.405), and the *unvalidated* L22 direction is highest (0.500). If the
   refusal mechanism were the lever, the validated refusal objective should beat random — it does not.
3. This converts the paper's causal dissociation into an optimization result and is **coherent with §23
   fragility**: any sufficient perturbation of the high-norm decision state breaks refusal, so a random
   direction serves as well as (better than) the specific refusal axis for *attack* purposes. The refusal
   mechanism is behaviorally causal (Gate B) yet does **not** yield a specifically better attack objective.
4. **Claim F ("a refusal-derived objective improves adversarial optimization"): first-cut NOT SUPPORTED.**
   A well-controlled negative — the random control is what makes it interpretable.

## Caveats (this is a first-cut, not the definitive Gate-7)
- **Underpowered / single condition:** n=42 test, **one seed (42)**, **50 steps** (reduced from the planned
  200), **20-item** train pool. No CIs, no McNemar, no multi-seed variance. Treat the ordering as directional.
- **Mechanistic validity not yet measured (§17):** rd_loss decreased during optimization (objective moved),
  but whether the optimized suffix actually *lowers the held-out refusal projection* was not measured here.
- **Concept objective (arm B) + combined (E) + Jacobian (G) not run** — the decisive concept comparison and
  the combined objective remain for the full matrix.
- Split integrity is respected: suffix optimized on train, evaluated on frozen test.

## Verdict & next
- **Gate E / Claim F — first-cut NEGATIVE (non-specific).** Report as a controlled negative.
- To make it definitive: multiple seeds, 200 steps, larger prompt pool, add the concept (B) and combined (E)
  arms, and add the §17 mechanistic-validity check (does optimizing refusal lower the held-out projection?).
