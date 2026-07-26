# CoT Span Structure Analysis

Descriptive structural analysis of CoT span annotations, split by attack outcome (`is_success` True vs False). All figures are numeric / structural: component presence, normalized token position, span length, instance counts, and coverage-miss rates. No harmful content, no causal or PASS claims.

## Qwen_Qwen3-14B

- n(success)=13, n(fail)=31

| component | presence(succ) | presence(fail) | norm_tok_start(succ) | norm_tok_start(fail) | norm_tok_end(succ) | norm_tok_end(fail) | tok_len(succ) | tok_len(fail) | count(succ) | count(fail) | miss(succ) | miss(fail) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| harmful_instruction | 0.000 | 0.161 |  | 0.965 |  | 0.973 |  | 11.8 | 0.00 | 0.16 | 1.000 | 0.839 |
| benign_puzzle_scaffold | 1.000 | 1.000 | 0.122 | 0.002 | 0.893 | 0.891 | 676.0 | 1163.7 | 1.00 | 1.00 | 0.000 | 0.000 |
| injected_reasoning | 0.000 | 0.677 |  | 0.319 |  | 0.325 |  | 8.1 | 0.00 | 0.68 | 1.000 | 0.323 |
| final_answer_cue | 1.000 | 1.000 | 0.892 | 0.891 | 0.994 | 0.996 | 84.3 | 135.9 | 1.00 | 1.00 | 0.000 | 0.000 |
| system_prompt | 0.000 | 0.000 |  |  |  |  |  |  | 0.00 | 0.00 | 1.000 | 1.000 |
| chat_template_tokens | 1.000 | 1.000 | 0.663 | 0.664 | 0.665 | 0.665 | 1.0 | 1.0 | 3.00 | 3.00 | 0.000 | 0.000 |
| assistant_generation_marker | 1.000 | 1.000 | 0.996 | 0.998 | 1.000 | 1.000 | 3.0 | 3.0 | 1.00 | 1.00 | 0.000 | 0.000 |

## microsoft_Phi-4-mini-reasoning

- n(success)=13, n(fail)=59

| component | presence(succ) | presence(fail) | norm_tok_start(succ) | norm_tok_start(fail) | norm_tok_end(succ) | norm_tok_end(fail) | tok_len(succ) | tok_len(fail) | count(succ) | count(fail) | miss(succ) | miss(fail) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| harmful_instruction | 0.000 | 0.068 |  | 0.932 |  | 0.938 |  | 10.0 | 0.00 | 0.07 | 1.000 | 0.932 |
| benign_puzzle_scaffold | 1.000 | 1.000 | 0.021 | 0.016 | 0.891 | 0.882 | 877.2 | 1075.0 | 1.00 | 1.00 | 0.000 | 0.000 |
| injected_reasoning | 0.000 | 0.610 |  | 0.335 |  | 0.340 |  | 6.1 | 0.00 | 0.61 | 1.000 | 0.390 |
| final_answer_cue | 0.846 | 0.983 | 0.871 | 0.880 | 0.998 | 0.998 | 129.0 | 154.0 | 0.85 | 0.98 | 0.154 | 0.017 |
| system_prompt | 0.000 | 0.000 |  |  |  |  |  |  | 0.00 | 0.00 | 1.000 | 1.000 |
| chat_template_tokens | 1.000 | 1.000 | 0.406 | 0.404 | 0.407 | 0.405 | 1.0 | 1.0 | 5.00 | 5.00 | 0.000 | 0.000 |
| assistant_generation_marker | 1.000 | 1.000 | 0.999 | 0.999 | 1.000 | 1.000 | 1.0 | 1.0 | 1.00 | 1.00 | 0.000 | 0.000 |

## Implications for the attention-measurement design

### Qwen_Qwen3-14B
- **injected_reasoning**: present in 0.000 of successes vs 0.677 of failures; in successes it sits at normalized token-start ~n/a (mean span length  tokens, 0.00 instances/record). -> Prioritize measuring attention mass DIRECTED AT the injected_reasoning token spans near this position.
- **final_answer_cue**: present in 1.000 of successes vs 1.000 of failures; in successes it sits at normalized token-start ~0.89 (mean span length 84.3 tokens, 1.00 instances/record). -> Prioritize measuring attention mass DIRECTED AT the final_answer_cue token spans near this position.

### microsoft_Phi-4-mini-reasoning
- **injected_reasoning**: present in 0.000 of successes vs 0.610 of failures; in successes it sits at normalized token-start ~n/a (mean span length  tokens, 0.00 instances/record). -> Prioritize measuring attention mass DIRECTED AT the injected_reasoning token spans near this position.
- **final_answer_cue**: present in 0.846 of successes vs 0.983 of failures; in successes it sits at normalized token-start ~0.87 (mean span length 129.0 tokens, 0.85 instances/record). -> Prioritize measuring attention mass DIRECTED AT the final_answer_cue token spans near this position.

General note: components with a large success-vs-failure gap in presence rate and a stable normalized position are the highest-value targets for the attention-mass probe; components with high coverage-miss rates are less reliably localizable and should be de-prioritized or re-annotated first.

