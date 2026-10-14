# VERIFY — "basketball" occurrence-gate failures vs the INCUMBENT basket artifacts

**Verifier:** F3 (2026-10-14). **Code:** ad-hoc read-only checks + `research/heretic_csi/verify/codeword_collision_scan.py`.
**JSON:** `reports/heretic_csi/VERIFY_basketball_occurrence.json`, `reports/heretic_csi/VERIFY_codeword_collision_scan.json`.

**Input (F7):** 30/22272 basket-bank rows fail `extract_boombness.resolve_occurrences` (text count 5 vs token count 6,
because " basketball" tokenizes with the ` basket` id). **All 30 are in domain `school_campus`.**

1. **Behavioral extraction corpus** (`cont1_behavioral_basket_bomb_20260910_113902_3966018`, the axis-fit source):
   population 3720 rows → 3714 written. The 6 missing rows are exactly the 6 failing behavioral rows (3 cell A + 3 cell C,
   school_campus) → **SKIPPED by the pre-flight refusal, not mis-positioned.** The 7 surviving school_campus C rows have
   n_occurrences 5, 1 subtoken, `codeword_last`. Moreover the axis fit **excludes school_campus entirely**
   (`hcsi_ranksweep_basket.pt` meta `excluded_domains` = restaurant_kitchen, school_campus, subway_station; 670 rows / 67 dom).
2. **Rescue runs** (S-049 basket r1 TRAIN 966084 + VAL 968532; r16 965928/968533; K4 r4/r8 969085/969086; r4 VAL 1022699;
   BASE/KO/KO_FULL/candidate arms): **0 offending ids in any population; 0 school_campus rows at all.** school_campus is a
   preregistered whole-population exclusion (DCS-C-075 / DCS-R-108) and the 3 offending rescue ids are listed explicitly in
   `runargs/dcs_cont/exclude_basket_bomb_sow_{train,validation}.txt` (and the K4 file).
3. **Sensitivity recompute:** not needed — dropping them is a no-op. **No verdict changes** (S-049, S-050 K4, S-072 r4 VAL).
4. **Button bank:** F7's gate finds 0 failures; my independent text scan finds no superstring words (no buttonhole /
   buttoned / buttons; only JSON-escape artifacts). Basket's only real superstring is "basketball", consistent with F7.

**Implication for P6/new banks:** the gate is the right guard; any new codeword bank must pass `resolve_occurrences` and
collision domains must be excluded mechanically before population freezing (cushion: 24 fails, 2 rescue-pop in TEST;
bottle: 30 fails, 3 rescue-pop TRAIN — per F7).
