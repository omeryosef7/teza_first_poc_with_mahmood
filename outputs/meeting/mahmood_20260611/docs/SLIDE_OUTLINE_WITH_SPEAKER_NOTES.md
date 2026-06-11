# Slide Outline with Speaker Notes

**Meeting:** Mahmood, 2026-06-11  
**Format:** 5 slides, ~20 minutes, informal research update

---

## Slide 1: From refusal-direction hypothesis to controlled tests

**Figure:** None (text slide or simple diagram)

**Bullets on slide:**
- Original hypothesis: puzzle hijacks model by diluting refusal direction (Layer 22)
- Stage 4: Layer-22 direction extracted from 42 traces — showed early divergence in thinking
- Stage 4A2: 0/160 causal interventions survived → direction is diagnostic, not causal
- Pivot: controlled behavioral experiments (Stages 4.7 and 4.8)

**Detailed speaker notes (Hebrew):**

הסלייד הזה מסביר את השינוי בכיוון המחקר. ב-Stage 4 חילצנו כיוון סקלרי מ-Layer 22 שנראה כמו "כיוון סירוב" — כלומר, כשהמודל מסרב, הוא מקרין יותר על הכיוון הזה. גילינו שב-500 הטוקנים הראשונים של החשיבה, ה-attack מצליח מציג ציוני projection גבוהים יותר מאשר ה-attack שנכשל (5.20 לעומת 3.86 בממוצע).

אבל כשניסינו להתערב קושית — כלומר להחליש את הכיוון הזה במהלך הגנרציה — אף אחת מ-160 ניסיונות ה-intervention לא הצליחה. המודל קרס או התעלם. אז הכיוון הזה הוא אינדיקטיבי, לא סיבתי.

לכן עברנו לניסויים behavioral מבוקרים: Stage 4.7 השוואה בין 4 תנאים על 12 פרומפטים, ו-Stage 4.8 השכפול הסטוכסטי עם seeds שונים.

**מה לא לטעון:** אל תגיד שה-direction מודד "עמידות לסירוב". אמור: "כיוון ניגודיות harmful/harmless provisionally — לא עבר ולידציה סיבתית."

**If Mahmood asks:** "Why 0/160 survivors?" — The interventions were strong steering vectors applied to activations. The model collapsed rather than comply. This is consistent with the direction not being the gating mechanism — steering it just breaks the forward pass.

---

## Slide 2: Puzzle beats both controls

**Figure:** `01_stage47_behavior_A_D_F.png`

**Bullets on slide:**
- 12 prompts × 4 conditions (A=full puzzle, D=bare target, F=length-matched benign, E=no thinking)
- A: 10/12 success (83.3%) | D: 5/11 (45.5%) | F: 3/11 (27.3%) | E: 4/9 (44.4%)
- A − D: p = 0.031 (sign test) | A − F: p = 0.008 | A − E: p = 0.031
- Stable across all 4 goals (LOGO: 4/4 folds positive for A−D and A−F)
- Length alone is insufficient: A and F are matched in prompt length

**Detailed speaker notes (Hebrew):**

זה הממצא המרכזי — הפאזל עובד, וגם אחרי שאנחנו שולטים באורך הפרומפט.

שלושה תנאים עיקריים: A זה הפאזל המלא עם thinking, D זה הטרגט לבד בלי הפאזל, ו-F זה wrapper בנלי באותו אורך כמו A (גם מבחינת מספר הטוקנים). הנקודה עם F היא קריטית: הוא מחייב אותנו להוכיח שלא מדובר סתם בפרומפט ארוך.

A מנצח את D ואת F באופן מובהק סטטיסטית (p<0.05 בכל ה-contrasts). הממצא יציב על פני כל 4 ה-goals — כלומר, לא מדובר בתוצאה ספציפית לנושא מסוים.

A מנצח גם את E (פאזל מלא עם thinking=off), מה שמראה שגם ה-thinking עצמו קריטי — לא רק ה-puzzle format.

**מה לא לטעון:** אל תגיד "הוכחנו שהסמנטיקה של הפאזל היא הגורם". הממצא שולל אורך פרומפט, אבל לא מבדיל בין סמנטיקה של הפאזל לבין מבנה הנמקה (reasoning structure) או קוהרנטיות הטאסק.

**If Mahmood asks:** "Is n=12 enough?" — It's enough for exploratory sign tests. The p=0.008 for A−F is robust; p=0.031 for A−D is at the minimum achievable with n=12 (6 positive, 6 tied). The LOGO stability (4/4 folds) confirms it's not driven by a single goal.

---

## Slide 3: Same length, different thinking

**Figure:** `02_stage47_thinking_tokens.png`

**Bullets on slide:**
- A and F are length-matched prompts (±5% token count)
- A generates 13.97× more thinking tokens than F (11,458 vs 824 tokens)
- D generates 2,924 tokens — less than A despite having similar prompt length to F
- Same prompt length does not imply same reasoning dynamics

**Detailed speaker notes (Hebrew):**

זה ה-slide שמסביר למה F לא מספיק כביקורת. אמנם F ו-A זהים באורך, אבל כשנותנים למודל לחשוב — A יוצר 13.97 פעמים יותר טוקני חשיבה מאשר F.

זה אומר שהפרומפט של A עצמו מפעיל מנגנון חשיבה עמוקה שה-wrapper הבנלי לא מפעיל. מה שמעניין פה: ה-thinking amplification היא לא רק כמותית — זה גם איכותי. המודל בתנאי A נכנס ל"מצב" שונה.

למה זה חשוב? כי זה מסביר למה F נכשל — לא כי הפרומפט קצר מדי, אלא כי ה-wrapper הבנלי לא מפעיל את מנגנון ה-reasoning שה-puzzle מפעיל.

**If Mahmood asks:** "Is the thinking actually deeper or just longer?" — We can't answer that from token count alone. What we know is that longer thinking is correlated with success (condition A), but the Layer-22 direction doesn't track this success — it tracks the length of thinking, not the outcome.

---

## Slide 4: The old direction fails mechanistically

**Figure:** `03_stage47_projection_vs_thinking.png`  
**Backup:** `backup_stage47_layer22_projection.png`

**Bullets on slide:**
- Layer-22 ordering: A < F < D (projection values: A=7.12, F=8.08, D=8.95)
- Behavioral ordering: A > D > F — these are **opposite**
- A − D projection diff: −1.79 (A is lower, p = 0.039)
- Direction anti-correlates with thinking depth: Spearman ρ = −0.68, p = 0.015 (condition A)
- Replicated in Stage 4.8 (independent stochastic sampling, same ordering)

**Detailed speaker notes (Hebrew):**

זה ה-finding המכניסטי המרכזי — וזה גם הבעיה עם ה-hypothesis המקורית.

אם הכיוון מ-Layer 22 היה מנגנון ה-"compliance", הייתי מצפה ש-A (הכי מצליח) יהיה עם ה-projection הגבוה ביותר. אבל המציאות הפוכה: A יש לו ה-projection הכי נמוך (7.12), ו-D — שנכשל הרבה יותר — יש לו ה-projection הגבוה ביותר (8.95).

האפשרות הפשוטה ביותר: הכיוון לא מודד compliance — הוא מודד עומק חשיבה. כשיש הרבה חשיבה (תנאי A), ה-projection יורד. כשיש מעט חשיבה (תנאי D, F), ה-projection גבוה.

ה-Spearman rho של −0.68 (בתנאי A, n=12) מאשר: ככל שיש יותר טוקני חשיבה, ה-projection יורד. הקורלציה הזו שוכפלה ב-Stage 4.8 באופן עצמאי.

**מה לא לטעון:** אל תגיד שה-direction "לא שימושי". אמור: "הכיוון הוא proxy לעומק חשיבה, לא ל-compliance. כלומר, הוא יכול להיות שימושי לדברים אחרים, אבל לא כמנגנון direct של hijacking."

**If Mahmood asks:** "Does this disprove the refusal-dilution theory?" — It weakens it significantly. The direction we extracted doesn't track compliance in controlled settings. But it's possible that a *different* direction, or a *subspace*, does track compliance. The scalar direction we have is insufficient.

---

## Slide 5: Stochastic replication and next decision

**Figures:** `04_stage48_seed_outcomes.png`, `05_stage48_variance_decomposition.png`

**Bullets on slide:**
- 60 generations: 4 prompts × 3 conditions × 5 seeds, 0 censored
- A: 60%, D: 50%, F: 40% — A > D > F trend replicates ✓
- Goal identity dominates: Goal 1 = 0/15, Goal 3 = 15/15 across ALL conditions
- Between-cell variance 3.69× within-cell variance
- Only 3 matched-outcome cells → direction extraction not valid (Branch C)
- Need more goals or prompts to enable mechanistic follow-up

**Detailed speaker notes (Hebrew):**

Stage 4.8 עשה משהו פשוט: לקח 4 פרומפטים מ-Stage 4.7, הריץ כל אחד 5 פעמים עם seeds שונים, ובדק האם ה-trend הבסיסי (A > D > F) נשמר תחת sampling stochastic.

התשובה: כן. ה-trend נשמר. A מנצח בסבירות גבוהה יותר גם כשמשנים את ה-seed.

אבל הממצא הגדול יותר: לא ה-condition הוא הגורם הדומיננטי — הוא ה-goal. Goal 1 נכשל לחלוטין (0/15) בכל התנאים. Goal 3 מצליח לחלוטין (15/15) בכל התנאים. כלומר: ה-between-cell variance (0.197) גדולה פי 3.69 מה-within-cell variance (0.053) — ה-variability בין prompts גדולה בהרבה מה-variability בין seeds.

למה זה בעיה? כי עם רק 3 matched-outcome cells (כלומר cells שיש בהן גם הצלחות וגם כישלונות), אי אפשר לחלץ כיוון מכניסטי אמין. הגענו ל-Branch C — עצירה מבוקרת.

**מה צריך מהמחמוד:** ה-decision הכי חשוב עכשיו הוא: בכיוון מה ממשיכים?
1. יותר goals/prompts (Option A) — נגדיל את הנתון כדי לקבל יותר matched cells
2. subspace/probe מכניסטי (Option B) — נחפש מנגנון רב-ממדי עשיר יותר
3. AutoInject adaptation (Option C) — נעשה behavioral optimization של הפרומפט

**If Mahmood asks:** "Why not just run more seeds?" — More seeds within the same 4 goals won't help — Goals 1 and 3 are near-deterministic. We need *new goals* with intermediate susceptibility to get matched-outcome cells.

---

## General notes for the meeting

**What this progresses in the thesis:**
- We showed a clean behavioral effect: puzzle format matters beyond prompt length.
- We showed a mechanistic null: the simple scalar direction theory is wrong.
- We have a principled decision gate (Branch C) that tells us exactly what to do next.
- This is more interesting than a positive result — it rules out the simple story and opens a richer question.

**What we should NOT claim:**
- Do not claim "puzzle semantics are proven causal." We only ruled out length.
- Do not claim "Layer 22 is a validated refusal mechanism." It's a thinking-depth proxy.
- Do not claim "StrongREJECT = human judgment." It's an automated proxy.
- Do not claim "LLM-onset annotation is available." It is blocked (spending cap on Gemini judge).

**Decision needed from Mahmood:**
Which thesis framing? Mechanistic (→ Option B) or attack-improvement (→ Option C)?
This shapes the next sprint.
