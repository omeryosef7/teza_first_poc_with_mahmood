# Stage 4.7 — Condition Summary (Percent Format)

**n = 12 prompts per condition (greedy decoding)**

| Condition | n_comp | ASR% [95% CI] | Mean SR | Med SR | Mean Think Tok | Med Think Tok | Censored |
|-----------|--------|--------------|---------|--------|---------------|--------------|---------|
| A (Full puzzle (thinking on)) | 12 | **83.3%** [55.2–95.3] | 0.823 | 1.000 | 11458 | 13592 | 0 (0%) |
| D (No puzzle (thinking on)) | 11 | **45.5%** [21.3–72.0] | 0.406 | 0.000 | 2924 | 2574 | 1 (8%) |
| F (Benign wrapper (thinking on)) | 11 | **27.3%** [9.7–56.6] | 0.240 | 0.000 | 824 | 821 | 1 (8%) |
| E (Full puzzle (thinking off)) | 9 | **44.4%** [18.9–73.3] | 0.333 | 0.000 | 0 | 0 | 3 (25%) |

## Paired Contrasts

| Contrast | Paired n | ΔASR (pp) | Mean ΔSR | Med ΔSR | Mean ΔThink | n+/n−/tie | sign-test p |
|----------|---------|-----------|---------|--------|-----------|---------|-----------|
| A-D | 12 | **+41.7** | 0.417 | 0.062 | 8534 | 5/0/7 | 0.0625 |
| A-E | 12 | **+50.0** | 0.490 | 0.438 | 11458 | 6/0/6 | 0.0312 |
| A-F | 12 | **+58.3** | 0.583 | 0.938 | 10634 | 7/0/5 | 0.0156 |
| D-F | 12 | **+16.7** | 0.167 | 0.000 | 2100 | 3/1/8 | 0.6250 |