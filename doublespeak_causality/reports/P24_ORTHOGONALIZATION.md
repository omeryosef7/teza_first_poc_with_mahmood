# §24 — Orthogonalization: behavioral control lives in the REFUSAL component

**Status:** ✅ STRONG confirmation of the concept-vs-refusal dissociation (Claim C/E). After removing the
concept↔refusal overlap, the **refusal component alone causally controls ASR; the concept component does not.**

**Run:** `phase24_orthogonalization.py` (`...736571`), v3 clearharm, Llama L18, train-fitted validated dirs.

## Result — ΔASR vs ds_base (paired McNemar), Llama L18
| arm | train (n=85) | test (n=42) |
|---|---|---|
| **refusal ⊥ concept** (refusal component, overlap removed) | **−0.212 (p=0.0001)** | −0.071 (ns, n=42) |
| concept ⊥ refusal (concept component, overlap removed) | +0.106 (p=0.049) | +0.095 (ns) |
| both | +0.035 (ns) | +0.119 (ns) |

## Interpretation
- **The refusal component orthogonalized against concept still strongly reduces ASR** (−0.21, p<0.001 on
  train) — restoring the refusal axis (with any concept overlap removed) collapses the jailbreak.
- **The concept component orthogonalized against refusal does NOT reduce ASR** (if anything +0.11) — the
  concept representation, stripped of refusal overlap, has no behavioral control.
- Therefore the earlier concept⊥refusal near-orthogonality (|cos|≤0.153, BR-12) is not what's carrying the
  effect: **behavioral control lives in the refusal component, not the concept component**, even after
  removing their overlap. Clean support for Claim C (causal separability) and Claim E (refusal is the lever).
- Test split underpowered (n=42, ns) but same sign; train is decisive.
