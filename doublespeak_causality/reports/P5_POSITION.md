# §5 — Demonstration-Position Decomposition (which part suppresses refusal?)

**Status:** PARTIAL / nuanced. No single demo manipulation cleanly dissociates concept-remap from
refusal-suppression; the suppression is driven broadly by demo structure/count, not one separable component.

**Run:** `phase5_position.py` (`...736658`), v3 clearharm test, 9 matched demo-text variants. Per variant:
decision-token refusal projection restore-frac, ASR, p_concept.

## Result — dissociation table (want ΔASR<0 while p_concept stays high)
| variant | ΔASR vs full-DS | proj_restore_frac | p_concept |
|---|---|---|---|
| codeword_randomized | −0.072 | −0.216 | 0.875 (high) |
| benign_format | −0.072 | −0.096 | 0.968 (high) |
| mapping_altered | 0.000 | −0.236 | 0.904 |
| single_demo | +0.024 | **−0.597** (most refusal restored) | 0.468 (concept drops) |
| shuffled | +0.048 | −0.087 | 0.964 |
| reduced_count | +0.048 | −0.162 | 0.942 |

## Interpretation
- **`single_demo` restores refusal the most (−0.60) but also drops concept-remap (0.47)** — reducing the
  demonstrations weakens BOTH the concept remap and the refusal suppression together (not a clean dissociation).
- **`codeword_randomized` / `benign_format` slightly reduce ASR (−0.07) while keeping concept-remap high
  (0.87–0.97)** — a weak partial dissociation (concept preserved, ASR down), but refusal restoration is modest.
- No manipulation both preserves concept AND fully restores refusal → the refusal-suppression is not localized
  to one demo component; it is a broad function of the demonstration structure/count. ΔASR effects are small
  (≤0.07) at test n=42 (likely ns) — treat as directional; a train+dev run would power it.
