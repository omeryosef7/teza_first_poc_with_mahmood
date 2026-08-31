"""rah_preflight_transport.py -- `RAH-PR-004` GO/NO-GO pre-flight for the Track-A transport assay.

WHY THIS EXISTS. The Track-A design (`RAH-PR-001` §10.1) rests on a cross-prompt activation
patchscope. `RAH-DR-001` established that the repository's forced-choice patchscope
(`doublespeak_causality/46_forced_choice_patchscope.py`) has been run **exactly once**, and its own
positive control **failed by ~712x**:

    doublespeak_causality/outputs/next3_fc_patchscope_bomb.json
      positive_control.pos_ctrl_max = 1.404e-04     (gate: > 0.1)
      per_layer_p_concept flat 3.2e-05 .. 1.4e-04 across ALL 33 rows
      evaluated = false
      surface_baseline.p_codeword = 0.9529   <-- option mass is NOT the problem

So the instrument Track A depends on has never demonstrated that it can transport a concept AT ALL.
This script answers one question, before any assay code is written:

    Is there ANY (receiver form, receiver layer R) at which a CLEAN, concept-bearing donor
    activation forces a receiver to name that concept?

If no configuration passes, Track A stops and the sprint reports a sourced negative
(`RAH-PR-004`'s registered stop rule). A null from a readout that fails its own positive control is
uninterpretable -- this repository has already retracted a result on exactly that ground
(`DOUBLESPEAK_MASTER_LOG.md`).

THE LEAD BEING TESTED. The one patchscope configuration that HAS passed a positive control here
(`07_patchscope_readout.py`, P(virus)=0.722) patches at the final prompt token and reads the logits
**at that same position** -- zero attention hops. `46` patches ~40 tokens upstream of its read
position with only 4 blocks remaining. Receiver GEOMETRY, not donor layer, is the axis this sweeps.

DEFECTS FROM `RAH-DR-001` FIXED HERE BY CONSTRUCTION (so the pre-flight cannot fail for a reason
that is really a bug):
  * FATAL-3  own tokenisation, `add_special_tokens=False`, on the already-templated string;
             `capture_target_reps`/`forward_hidden_states` are NOT used (they pass
             add_special_tokens=True over a templated prompt -> double BOS on Llama, every donor
             position shifted +1).
  * FATAL-4  ONE layer convention: donor block index `L` means `hidden_states[L+1]`, the coordinate
             `LayerPatch(layer_idx=L)` writes. `L` is restricted to [0, n_layers-2] because
             `hidden_states[n_layers]` is the POST-FINAL-NORM state, a different coordinate.
  * FATAL-7  labels scored with `signals.readout_ids(...)["primary_id"]` -- ONE id per label, and
             the helper raises on a multi-token leading-space form. Pairwise disjointness asserted.
  * FATAL-8  `enable_thinking=False` passed explicitly for Qwen3, and the rendered receiver is
             asserted to contain a closed `<think></think>` before any forward.
  * S-11     an explicit `Answer:` prefix on the forced-choice receivers.
  * S-12     `attn_implementation="eager"` forced for every forward, recorded per row.
  * S-10     probe resolved by CHARACTER OFFSET into the quoted slot, then asserted.

Scalars only are persisted. No prompt text, no completions.

Usage (GPU):
  python src/boombness/rah_preflight_transport.py \
      --bank data/boombness_prompts/boombness_prompt_bank_rbd_lantern_poison.jsonl \
      --model Qwen/Qwen3-14B --enable-thinking false --n-donors 4 --tag rahpf_qlp
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# `common` is this package's sanctioned sys.path bootstrap: it puts `doublespeak_causality/` on the
# path so `import ds_common` resolves. Importing it for that side effect is the house pattern
# (`score_behavior.py:39-41`), not an accident.
import common  # noqa: E402,F401

SCHEMA = "RAH_PREFLIGHT_TRANSPORT/1"

#: The gate `46_forced_choice_patchscope.patchscope_gate` applies, restated rather than imported so
#: this script's verdict does not depend on the module whose only run failed.
POSITIVE_CONTROL_THRESH = 0.1

#: `07_patchscope_readout.INSPECTION_PROMPT` -- the ONLY configuration in this repository that has
#: ever passed a patchscope positive control. Reproduced verbatim; do not "improve" it.
ID_PROMPT = "hello hello\nworld world\ncat cat\nX"


def provenance(_run=None):
    """`RAH2-DR-002` D11. Every job id, commit and `dirty=0` in the RAH2 log is **prose** — the
    artifact schema carried none of it, so a reader could not check any of it without the SLURM
    logs, which are not part of the record. This emits the block so provenance is **attested**.

    Every field degrades to a string rather than raising: a provenance block must never be the
    reason a completed sweep fails to persist. `git_commit` is None only if git itself is absent.
    """
    runner = _run if _run is not None else subprocess.run

    def _git(*a):
        """Returns (ok, text). `_run` is injectable ONLY so the tri-state can be tested against a
        FAILING git without breaking git on the machine -- see `RAH2-C-030`, where a source-string
        guard for this missed a rewrite of the same defect. `RAH2-C-030`: the first version returned None on both failure AND
        empty output, so `bool(None)` made `git_dirty` report a CLEAN TREE whenever git could not
        run at all -- a missing binary, a timeout on this NFS repo, or a dubious-ownership refusal
        in this shared tree all produced an artifact asserting the code was unmodified."""
        try:
            r = runner(("git",) + a, cwd=HERE, capture_output=True, text=True, timeout=20)
        except BaseException:                     # noqa: BLE001 -- never block the write, ever
            return False, None
        if r.returncode != 0:
            return False, None
        return True, r.stdout.strip()

    ok_head, head = _git("rev-parse", "HEAD")
    ok_status, status = _git("status", "--porcelain")
    return {
        "git_ok": bool(ok_head and ok_status),
        "git_commit": head if ok_head else None,
        # tri-state ON PURPOSE: None means "could not tell", which is NOT "clean".
        "git_dirty": (bool(status) if ok_status else None),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "slurm_nodelist": os.environ.get("SLURM_JOB_NODELIST"),
        "hostname": os.environ.get("HOSTNAME") or os.environ.get("SLURMD_NODENAME"),
        "argv": sys.argv[1:],
        "started_utc": None,          # filled by main(). `RAH2-C-030`: this is the COMPUTE node's
        "finished_utc": None,         # clock (main() runs in the job), which skewed ~3 min from the
                                      # login node this phase -- so these date a run, they do not
                                      # order it against `squeue` output taken on the login node.
        "python": sys.version.split()[0],
    }


def _git_branch():
    """Branch name for the provenance block, or None. Never raises -- provenance must not be the
    reason a completed sweep fails to persist."""
    try:
        r = subprocess.run(("git", "rev-parse", "--abbrev-ref", "HEAD"), cwd=HERE,
                           capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except BaseException:                          # noqa: BLE001
        return None


def _diff_sha256():
    """SHA256 of the full working diff, so a dirty-tree run is still citable (§5.4)."""
    import hashlib
    try:
        r = subprocess.run(("git", "diff", "HEAD"), cwd=HERE, capture_output=True, timeout=60)
        return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None
    except BaseException:                          # noqa: BLE001
        return None


def receiver_forms(concept, codeword, other_concept, other_codeword, probe):
    """The receiver geometries under test, ordered by ATTENTION HOPS between patch and read.

    `read_at` is 'patch' (read the logits at the patched position -- zero hops, 07's geometry) or
    'final' (read at the last position -- 46's geometry).

    `body` is the USER message. `suffix` is appended AFTER chat templating, i.e. on the ASSISTANT
    side -- `RAH-C-006` / review F3. `score_behavior.next_token_readout:85` implements the validated
    form as `tokenizer(templated + answer_prefix, add_special_tokens=False)` and its comment records
    why (as_is 1.4e-2 -> forced 0.979): with the prefix inside the user turn, templating appends the
    assistant header and the read position lands on the trailing newline, not on the answer slot.
    An empty suffix means the form reads at the patched position and needs no prefix.
    """
    labels = '"{a}", "{b}", "{c}" or "{d}"'.format(a=concept, b=codeword,
                                                   c=other_concept, d=other_codeword)
    return [
        # zero hops, RAW string, no chat template -- 07 exactly. `templated=False` also selects
        # add_special_tokens=True at the call site, because 07 tokenizes this prompt WITH BOS
        # (review F1); dropping BOS would mean the one configuration that has ever passed a
        # positive control here was not actually reproduced.
        {"name": "id07_raw", "templated": False, "read_at": "patch",
         "body": ID_PROMPT, "suffix": "", "patch_at": "last"},
        # zero hops, chat-templated (does the template alone break it?)
        {"name": "id07_tmpl", "templated": True, "read_at": "patch",
         "body": ID_PROMPT, "suffix": "", "patch_at": "last"},
        # few hops: probe LAST in the user turn, options before it, ASSISTANT-side answer prefix
        {"name": "fc_probe_last", "templated": True, "read_at": "final",
         "body": ('Labels: {L}. Choose one label only and answer with just that label. '
                  'Which label describes the word "{p}"?').format(L=labels, p=probe),
         "suffix": "Answer:", "patch_at": "probe"},
        # 46's geometry: probe FIRST, ~40 tokens upstream of the read position. The known failure,
        # kept as the comparison point so this run reproduces the archive rather than asserting it.
        {"name": "fc46", "templated": True, "read_at": "final",
         "body": ('Consider the word "{p}" on its own. Choose one label only and answer with just '
                  'that label. Does the word "{p}" refer to {L}?').format(p=probe, L=labels),
         "suffix": "Answer:", "patch_at": "probe"},
    ]


def render_receiver(dc, tok, form, think):
    """Build the receiver string exactly as the repo's validated readout does.

    Templated forms: apply_template(body) + suffix, tokenized add_special_tokens=False (the template
    already carries BOS). Untemplated forms: the raw body, tokenized WITH specials, matching 07.
    """
    if form["templated"]:
        return dc.apply_template(tok, form["body"], enable_thinking=think) + form["suffix"], False
    return form["body"], True


def assert_thinking_actually_off(dc, tok, body, think):
    """`RAH-C-006` / review S1: test the EFFECT, not the presence of a tag.

    `ds_common.apply_template` SWALLOWS TypeError/ValueError when a tokenizer rejects
    `enable_thinking` and silently falls back to a plain call -- so a rendered string containing no
    `<think>` at all is indistinguishable from "thinking is off", and the old guard (open tag present
    AND close tag absent) could never fire in either real state. Compare the two renderings instead.
    """
    if think is not False:
        return {"checked": False, "reason": "enable_thinking not requested False"}
    t_off = dc.apply_template(tok, body, enable_thinking=False)
    t_def = dc.apply_template(tok, body, enable_thinking=None)
    if t_off == t_def:
        raise SystemExit("enable_thinking=False had NO EFFECT on the rendered template -- the "
                         "tokenizer silently ignored the kwarg (ds_common.apply_template swallows "
                         "it). Refusing to run: on Qwen3 the read position would be <think>.")
    if "</think>" not in t_off:
        raise SystemExit("enable_thinking=False changed the template but did not close <think>")
    return {"checked": True, "differs_from_default": True, "think_block_closed": True}


def nuisance_receiver_forms(concept, codeword, other_concept, other_codeword, probe):
    """The FROZEN form plus a wording paraphrase of it -- the nuisance axis, kept OUT of the grid.

    `RAH-C-008`. This deliberately does NOT live in `receiver_forms`. That function's output defined
    the Stage-A grid (4 forms x 5 receiver layers = 20 configurations) over which `RAH-R-010` made
    the frozen selection, and `scripts/rah_select_config.py` re-runs that selection as an audit.
    Adding a fifth form there would silently change what a re-run produces and break the audit of a
    frozen artifact -- so the paraphrase is a separate inventory with a separate caller.

    WHY A PARAPHRASE AT ALL (`RAH-DR-002` F5). The receiver is one deterministic greedy forward, so
    its "repeatability" is float jitter of order 1e-6. An equivalence margin derived from that would
    be far below the rule-of-three floor 3/n and would make `EQUIVALENT` UNREACHABLE for every
    possible dataset. The margin must come from variation the design considers IRRELEVANT -- option
    ORDER and receiver WORDING -- measured on BASE donors only, so it cannot see the effect.
    """
    base = [f for f in receiver_forms(concept, codeword, other_concept, other_codeword, probe)
            if f["name"] == "fc_probe_last"]
    labels = '"{a}", "{b}", "{c}" or "{d}"'.format(a=concept, b=codeword,
                                                   c=other_concept, d=other_codeword)
    return base + [{
        "name": "fc_probe_last_v2", "templated": True, "read_at": "final",
        "body": ('Which of these labels best describes the word "{p}"? '
                 'The options are {L}. Reply with the single label only.').format(L=labels, p=probe),
        "suffix": "Answer:", "patch_at": "probe"}]


def readout_ladder_forms(concept, codeword, other_concept, other_codeword, probe):
    """`RAH2-PR-001`'s five-form ladder across the NAMING x CONSTRAINT space.

    NOT added to `receiver_forms()`. That function's output defines the FROZEN Stage-A grid
    (`RAH-R-010`) which `scripts/rah_select_config.py` re-runs as an audit; adding a form there would
    silently change what the audit reproduces. `RAH-C-008` is that exact mistake, caught once already.

    The two extremes are carried forward UNCHANGED so the three new forms are measured against them
    on the same rows:

        fc_probe_last   names all four candidates, strong slot constraint   (high mass, confounded)
        id07_tmpl       names none, NO slot constraint (free continuation)  (clean, unreportable)

    The three new forms name NO candidate while constraining the answer slot. The constraint lives on
    the ASSISTANT side, appended after the chat template exactly as `score_behavior.py:85` does --
    a stem inside the user turn would leave the read position on the post-header newline, which is
    the `RAH-DR-002` F3 defect.
    """
    keep = {"fc_probe_last", "id07_tmpl"}
    base = [f for f in receiver_forms(concept, codeword, other_concept, other_codeword, probe)
            if f["name"] in keep]
    new_forms = [
        # constrains the next token to a CATEGORY NOUN, names nothing
        {"name": "cat_cue", "templated": True, "read_at": "final", "patch_at": "probe",
         "body": 'What kind of thing is the word "{p}"?'.format(p=probe),
         "suffix": "It refers to a kind of"},
        # constrains the next token to a SYNONYM, names nothing
        {"name": "synonym", "templated": True, "read_at": "final", "patch_at": "probe",
         "body": 'Give a one-word synonym for the word "{p}".'.format(p=probe),
         "suffix": "A synonym is"},
        # constrains to ONE WORD with the repo's validated answer prefix, names nothing
        {"name": "defn_oneword", "templated": True, "read_at": "final", "patch_at": "probe",
         "body": 'Define the word "{p}" in exactly one word.'.format(p=probe),
         "suffix": "Answer:"},
    ]
    return base + new_forms


def fewshot_receiver_forms(concept, codeword, other_concept, other_codeword, probe):
    """`RAH2-PR-002`'s few-shot forms, plus the two reference extremes.

    `RAH2-R-001` found mass comes from either PRINTING the candidates or asking the model to ECHO the
    patched token -- both point the answer slot at something already present. Neither points it at a
    FUNCTION of the patched token. These forms do: the slot is constrained by a mapping demonstrated
    in context on UNRELATED word pairs, so nothing about the candidates is printed.

    The exemplars are deliberately far from every candidate vocabulary -- no weapon, container or
    hazard term -- so the demonstration cannot prime the answer. `EXEMPLAR_WORDS` is exported so a
    caller can assert no exemplar shares a first token with a candidate.
    """
    # `RAH2-PR-003` adds `id07_raw`: the few-shot forms are UNTEMPLATED while both original
    # references are TEMPLATED, so a mass difference confounded framing with the chat
    # template. `id07_raw` is the echo frame WITHOUT the template -- it holds framing fixed
    # and varies only what `fewshot_*` also varies, making the comparison attributable.
    keep = {"fc_probe_last", "id07_tmpl", "id07_raw"}
    base = [f for f in receiver_forms(concept, codeword, other_concept, other_codeword, probe)
            if f["name"] in keep]
    return base + [
        {"name": "fewshot_cat", "templated": False, "read_at": "final", "patch_at": "probe",
         "body": ('apple -> fruit\nhammer -> tool\nsparrow -> bird\n"{p}" ->').format(p=probe),
         "suffix": ""},
        {"name": "fewshot_syn", "templated": False, "read_at": "final", "patch_at": "probe",
         "body": ('big -> large\nswift -> fast\nbegin -> start\n"{p}" ->').format(p=probe),
         "suffix": ""},
    ]


def exemplar_candidate_collisions(tok, labels):
    """`RAH2-PR-002`'s structural anti-priming check: no few-shot exemplar may share a first token
    with any candidate, or the demonstration could prime the answer vocabulary.

    Deliberately uses the RAW first token of " word" rather than `signals.readout_ids`: exemplars
    appear in the PROMPT, never as a scored readout, so the single-token requirement that
    `readout_ids` enforces does not apply to them ("sparrow" is 2 tokens on Llama). What matters is
    only whether the first token collides.
    """
    first = lambda w: tok(" " + w, add_special_tokens=False)["input_ids"][0]
    cand = {first(w) for w in labels}
    return sorted({w for w in EXEMPLAR_WORDS if first(w) in cand})


#: every content word appearing in a few-shot exemplar; none may collide with a candidate.
EXEMPLAR_WORDS = ["apple", "fruit", "hammer", "tool", "sparrow", "bird",
                  "big", "large", "swift", "fast", "begin", "start"]


def names_any_candidate(text, labels):
    """Structural exposure test: does the rendered receiver contain any candidate string?

    This is the binary axis of `RAH2-PR-001`. It is checked on the RENDERED text, not on the
    template, because a form could name a candidate only after substitution.
    """
    low = text.casefold()
    return sorted([w for w in labels if w.casefold() in low])


def find_quoted_probe_span(text, probe):
    """Character offsets of the FIRST `"probe"` occurrence, quotes excluded.

    Offset-based on purpose (`RAH-DR-001` S-10): a token-id run matcher has no notion of the
    carrier string and will happily resolve `word` into the template's own 'the word'.
    """
    needle = '"%s"' % probe
    i = text.find(needle)
    if i < 0:
        raise ValueError("probe %r not present in quotes" % probe)
    return i + 1, i + 1 + len(probe)


def token_index_covering(offsets, lo, hi):
    """LAST token index whose character span OVERLAPS [lo, hi). Own tokenisation, per prompt.

    OVERLAP, not containment -- `RAH-C-005`. A BPE tokenizer emits the leading space as part of the
    word token: for `poison` at chars [870, 876) Llama produces ONE token `' poison'` spanning
    [869, 876). A containment test (`a >= lo and b <= hi`) matches nothing and the capture site is
    lost. The first preflight crashed here rather than resolving to a neighbouring token, which is
    the good failure mode -- but only by luck of this segmentation. Overlap is the correct rule, and
    the caller additionally asserts the chosen token decodes into the target word.
    """
    hits = [k for k, (a, b) in enumerate(offsets) if b > lo and a < hi and b > a]
    if not hits:
        raise ValueError("no token overlaps char span [%d,%d)" % (lo, hi))
    return hits[-1]


def assert_token_is_part_of(tokenizer, ids, idx, word, what):
    """The resolved token must decode to a piece of `word`. Catches a mis-resolved capture site."""
    piece = tokenizer.decode([ids[idx]]).strip().casefold()
    if not piece or piece not in word.casefold():
        raise SystemExit("%s: token %d decodes to %r, which is not a piece of %r"
                         % (what, idx, piece, word))
    return piece


def _char_spans(text, needle):
    """Every [lo, hi) character span of `needle` in `text`, case-insensitively. Used to prove a
    chosen capture token does NOT overlap the concept or codeword surface ANYWHERE in the prompt --
    not merely at the occurrence the anchor happened to select."""
    low, n, out, i = text.casefold(), len(needle), [], 0
    nl = needle.casefold()
    while True:
        i = low.find(nl, i)
        if i < 0:
            return out
        out.append((i, i + n))
        i += 1


def resolve_donor_capture(tok, ids, offsets, templated, concept_surface, codeword_surface,
                          label_ids, capture_mode, capture_offset, what):
    """`RAH3-PR-001` §2.3. Resolve the donor capture site and return its FULL invariant record.

    Pure: takes an already-tokenised prompt and returns scalars, so every invariant is testable and
    independently re-derivable WITHOUT a GPU or a model. This is the whole point -- the RAH2
    positive controls could not be audited for the copy confound because the capture site was
    resolved inline inside a forward-pass loop and only `piece` survived into the artifact.

    ``capture_mode='surface'`` (the DEFAULT) reproduces the historical path EXACTLY: last occurrence
    of the concept surface, last overlapping token, and the assertion that the token decodes to a
    piece of that surface. ``RAH3-C-000`` would be filed if this path ever changed, because every
    prior artifact in ``outputs/boombness/rah_preflight/`` was produced by it.

    ``capture_mode='offset'`` is `RAH3-PR-001`'s NON-COPY control. It anchors identically, then
    moves ``capture_offset`` tokens and HARD-FAILS -- ``SystemExit``, never a default -- if the
    resulting token overlaps the concept surface, overlaps the codeword surface, or IS a candidate
    label. Those three are exactly the ways a "transport" result could be a copy result.
    """
    if capture_mode not in ("surface", "offset"):
        raise SystemExit("%s: unknown capture_mode %r" % (what, capture_mode))
    if capture_mode == "surface" and capture_offset != 0:
        raise SystemExit("%s: capture_mode=surface forbids a non-zero offset (%d); use "
                         "--capture-mode offset to move the capture site" % (what, capture_offset))
    if capture_mode == "offset" and capture_offset == 0:
        raise SystemExit("%s: capture_mode=offset with offset 0 is the surface path in disguise; "
                         "it would silently produce a COPY test labelled as a non-copy control"
                         % what)

    pos_c = templated.lower().rfind(concept_surface.lower())
    if pos_c < 0:
        raise SystemExit("%s: target_surface %r absent from templated donor" % (what, concept_surface))
    anchor = token_index_covering(offsets, pos_c, pos_c + len(concept_surface))
    assert_token_is_part_of(tok, ids, anchor, concept_surface, "%s anchor" % what)

    idx = anchor + capture_offset
    if not (0 <= idx < len(ids)):
        raise SystemExit("%s: capture index %d (anchor %d + offset %d) outside [0,%d)"
                         % (what, idx, anchor, capture_offset, len(ids)))
    piece = tok.decode([ids[idx]])
    bare = piece.strip().casefold()

    # Overlap is decided on CHARACTER SPANS against EVERY occurrence, then again lexically. The
    # span test catches a token that shares characters with the surface; the lexical test catches a
    # token whose text IS the surface even if the tokeniser's offsets are unreliable. Both, because
    # either alone has a hole.
    a, b = offsets[idx]
    span_hit = lambda w: any(b > lo and a < hi for lo, hi in _char_spans(templated, w)) if w else False
    ov_concept = bool(span_hit(concept_surface)
                      or (bare and bare in concept_surface.casefold()))
    ov_codeword = bool(span_hit(codeword_surface)
                       or (bare and codeword_surface and bare in codeword_surface.casefold()))
    # A candidate label by TOKEN ID, not by string: the id is what the readout scores, so an id
    # match is the precise "the capture supplies the answer" condition.
    cand_by_id = sorted([w for w, i in label_ids.items() if i == ids[idx]])
    cand_by_str = sorted([w for w in label_ids if bare and bare == w.casefold()])
    is_cand = bool(cand_by_id or cand_by_str)

    rec = {
        "capture_mode": capture_mode, "capture_offset": capture_offset,
        "concept_surface_char_pos": pos_c, "concept_tok_idx": anchor,
        "codeword_tok_idx": _codeword_tok_idx(offsets, templated, codeword_surface),
        "donor_tok_idx": idx, "donor_piece": piece,
        "donor_char_span": [a, b],
        "tok_distance_from_concept": idx - anchor,
        "overlaps_concept_surface": ov_concept,
        "overlaps_codeword_surface": ov_codeword,
        "is_candidate_label": is_cand,
        "candidate_matches": sorted(set(cand_by_id) | set(cand_by_str)),
        "seq_len": len(ids),
    }
    if rec["tok_distance_from_concept"] != capture_offset:
        raise SystemExit("%s: resolved distance %d != requested offset %d"
                         % (what, rec["tok_distance_from_concept"], capture_offset))

    if capture_mode == "surface":
        # historical behaviour: the token MUST be part of the concept surface
        if not ov_concept:
            raise SystemExit("%s: surface capture resolved OFF the concept surface (piece %r)"
                             % (what, piece))
        return rec

    # ---- the non-copy path. No `.get(..., default)`. Raise. ------------------------------------
    if not bare:
        raise SystemExit("%s: capture token %d decodes to whitespace %r -- not a valid capture site"
                         % (what, idx, piece))
    if ov_concept:
        raise SystemExit("%s: NON-COPY VIOLATION -- capture token %d (%r) overlaps the CONCEPT "
                         "surface %r. This is a copy test." % (what, idx, piece, concept_surface))
    if ov_codeword:
        raise SystemExit("%s: NON-COPY VIOLATION -- capture token %d (%r) overlaps the CODEWORD "
                         "surface %r. This is a copy test." % (what, idx, piece, codeword_surface))
    if is_cand:
        raise SystemExit("%s: NON-COPY VIOLATION -- capture token %d (%r) IS a candidate label %r. "
                         "The capture supplies the answer."
                         % (what, idx, piece, rec["candidate_matches"]))
    return rec


def _codeword_tok_idx(offsets, templated, codeword_surface):
    """LAST token overlapping the LAST codeword occurrence, or None when the codeword is absent --
    `direct_harmful` prompts need not contain it, and that is not an error."""
    if not codeword_surface:
        return None
    p = templated.lower().rfind(codeword_surface.lower())
    if p < 0:
        return None
    try:
        return token_index_covering(offsets, p, p + len(codeword_surface))
    except ValueError:
        return None


def assert_capture_consistent(records, what="donor capture"):
    """`RAH3-PR-001` §2.3, cross-row. The registered trailer is pair-independent, so a non-copy
    capture must land on the SAME token piece on every donor. A row-varying piece means the offset
    does not denote one structural position -- §9's "offset produces inconsistent semantics
    across rows" -- and the run must refuse rather than average over two different sites."""
    if not records:
        raise SystemExit("%s: no donor rows to check" % what)
    pieces = sorted({r["donor_piece"] for r in records})
    dists = sorted({r["tok_distance_from_concept"] for r in records})
    if len(pieces) != 1 or len(dists) != 1:
        raise SystemExit("%s: INCONSISTENT capture across %d rows -- pieces=%r distances=%r"
                         % (what, len(records), pieces, dists))
    return {"n_rows": len(records), "donor_piece": pieces[0], "tok_distance": dists[0]}


def sha256_file(path):
    """Bank identity for the provenance block (§37). Streamed: the banks are megabytes."""
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    import torch
    import ds_common as dc
    import signals

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--enable-thinking", default="default")
    ap.add_argument("--n-donors", type=int, default=4)
    ap.add_argument("--donor-condition", default="direct_harmful",
                    help="`direct_harmful` (default) captures at the CONCEPT surface -- the "
                         "instrument positive control. `natural_doublespeak` captures at the "
                         "CODEWORD surface -- the BASELINE-TRANSPORT question (RAH-PR-010). "
                         "Either way NO intervention is constructed, so this stays effect-blind.")
    ap.add_argument("--n-examples", type=int, default=None,
                    help="restrict donors to this dose. Level-A banks carry {0,1,2,4,8,16}; the RBD "
                         "banks carry only 8, so this is a no-op there and a real filter on level A.")
    ap.add_argument("--probe", default="widget",
                    help="neutral probe; must be ONE token with a leading space on both models")
    ap.add_argument("--other-concept", default="missile")
    ap.add_argument("--other-codeword", default="candle")
    ap.add_argument("--form-set", default="grid", choices=["grid", "ladder", "fewshot"],
                    help="`grid` = the FROZEN 4-form Stage-A grid (default; do not change, "
                         "RAH-R-010 selected over it and rah_select_config.py audits it). "
                         "`ladder` = RAH2-PR-001's naming x constraint ladder. "
                         "`fewshot` = RAH2-PR-002's in-context mapping forms plus the "
                         "two reference extremes.")
    # `RAH3-PR-001`. THE DEFAULT IS `surface` AND MUST STAY SO: every artifact in
    # outputs/boombness/rah_preflight/ was produced by that path, and a silent default change would
    # make all of them non-reproducible. `tests/test_rah3_capture_site.py` pins the default.
    ap.add_argument("--capture-mode", default="surface", choices=["surface", "offset"],
                    help="`surface` (DEFAULT, historical, bit-identical) captures the donor at the "
                         "CONCEPT'S OWN SURFACE TOKEN -- which makes the positive control a COPY "
                         "TEST (`RAH2-C-020`). `offset` is `RAH3-PR-001`'s NON-COPY control: it "
                         "anchors identically then moves --capture-offset tokens and HARD-FAILS if "
                         "the resulting token overlaps the concept surface, the codeword surface, "
                         "or is a candidate label.")
    ap.add_argument("--capture-offset", type=int, default=0,
                    help="tokens from the concept-surface anchor. MUST be 0 for --capture-mode "
                         "surface and non-zero for offset. `RAH3-PR-001` freezes +1 (the token "
                         "immediately after the concept), pre-committed by `RAH2-PR-004` before "
                         "any transport number at any offset existed. DO NOT SWEEP THIS.")
    ap.add_argument("--tag", default="rahpf")
    ap.add_argument("--outdir", default="outputs/boombness/rah_preflight")
    args = ap.parse_args()

    started_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    # `RAH2-C-030`. This MUST be sampled before the sweep: taken at write time it records HEAD as of
    # the WRITE, and a multi-hour run launched at commit A and written after commit B silently
    # attests B -- which defeats the whole point of D11. Eight commits landed here on 2026-08-31
    # alone and a third writer shares the tree, so this is a live hazard, not a theoretical one.
    prov = provenance()
    prov["started_utc"] = started_utc
    think = dc.parse_enable_thinking(args.enable_thinking)

    rows = [json.loads(l) for l in open(args.bank)]
    # DONOR = a CLEAN, concept-bearing prompt: `direct_harmful` carries the CONCEPT on its surface,
    # so a rep captured at its target occurrence is the positive control's "clean concept rep".
    cand = [r for r in rows
            if r["condition"] == args.donor_condition and r["query_kind"] == "behavioral"
            and (args.n_examples is None or r["n_examples"] == args.n_examples)]
    donors = sorted(cand, key=lambda r: r["prompt_id"])[:args.n_donors]
    if not donors:
        raise SystemExit("no direct_harmful/behavioral rows in the bank")
    concept, codeword = donors[0]["concept"], donors[0]["codeword"]

    # eager everywhere (S-12): a kernel swap between arms is result-bearing in this repo.
    lm = dc.load_model(args.model, attn_implementation="eager")
    tok = lm.tokenizer
    nL = lm.num_layers

    # ---- label ids: ONE id per label, pairwise disjoint, or refuse (FATAL-7) ------------------ #
    label_words = [concept, codeword, args.other_concept, args.other_codeword]
    label_ids, label_meta = {}, {}
    for w in label_words:
        r = signals.readout_ids(tok, w)          # raises if " w" is not a single token
        label_ids[w] = r["primary_id"]
        label_meta[w] = {"primary_id": r["primary_id"], "primary_piece": r["primary_piece"]}
    if len(set(label_ids.values())) != len(label_words):
        raise SystemExit("label first-token ids collide: %r" % label_ids)
    probe_r = signals.readout_ids(tok, args.probe)
    print("[pf] labels %r -> ids %r ; probe %r -> %r"
          % (label_words, label_ids, args.probe, probe_r["primary_id"]))
    # `RAH2-C-015`. This check existed but was NEVER CALLED when `RAH2-R-002` was published, while
    # the log reported its result as a verification. A few-shot exemplar that shares a first token
    # with a candidate would prime the answer vocabulary directly -- the exact exposure confound the
    # forms exist to avoid -- and nothing would have errored. It now REFUSES rather than warns.
    exemplar_clash = (exemplar_candidate_collisions(tok, label_words)
                      if args.form_set == "fewshot" else [])
    if exemplar_clash:
        raise SystemExit("few-shot exemplars share a first token with a candidate: %r"
                         % exemplar_clash)
    print("[pf] exemplar/candidate first-token collisions: %s"
          % ("NONE" if args.form_set == "fewshot" else "n/a (form_set != fewshot)"))

    # ---- donor capture: OWN tokenisation, block-index convention pinned (FATAL-3/4) ----------- #
    donor_reps = []
    for d in donors:
        templated = dc.apply_template(tok, d["full_prompt"], enable_thinking=think)
        enc = tok(templated, return_tensors="pt", add_special_tokens=False,
                  return_offsets_mapping=True)
        offsets = enc.pop("offset_mapping")[0].tolist()
        ids = enc["input_ids"][0].tolist()
        surf = d["target_surface"]
        # `RAH3-PR-001` §2.3. Resolution and ALL non-copy invariants in one pure, testable call.
        # On --capture-mode surface this is the historical path, character-for-character.
        cap = resolve_donor_capture(tok, ids, offsets, templated, surf, codeword, label_ids,
                                    args.capture_mode, args.capture_offset,
                                    "donor %s" % d["prompt_id"])
        p = cap["donor_tok_idx"]
        with torch.no_grad():
            out = lm.model(input_ids=enc["input_ids"].to(lm.model.device),
                           output_hidden_states=True)
        hs = out.hidden_states
        assert len(ids) == hs[0].shape[1], "capture seq_len != own tokenisation"
        # block index L  <->  hidden_states[L+1]. L stops at nL-2: hidden_states[nL] is POST-NORM.
        donor_reps.append(dict(cap, prompt_id=d["prompt_id"], pos=p, seq_len=len(ids),
                               piece=cap["donor_piece"],
                               reps={L: hs[L + 1][0, p, :].detach().float().cpu()
                                     for L in range(0, nL - 1)}))
        print("[pf] donor %s pos=%d/%d piece=%r  mode=%s off=%+d anchor=%d "
              "ov_concept=%s ov_codeword=%s is_cand=%s"
              % (d["prompt_id"], p, len(ids), cap["donor_piece"], cap["capture_mode"],
                 cap["capture_offset"], cap["concept_tok_idx"], cap["overlaps_concept_surface"],
                 cap["overlaps_codeword_surface"], cap["is_candidate_label"]))

    # `RAH3-PR-001` §2.3 cross-row. A row-varying capture piece means the offset does not denote
    # ONE structural position, and averaging over two different sites would be silent.
    capture_consistency = assert_capture_consistent(donor_reps, "donor capture")
    print("[pf] capture consistency: %r" % capture_consistency)

    # ---- receiver grid ------------------------------------------------------------------------ #
    R_SET = sorted(set(max(1, int(nL * f)) for f in (0.125, 0.25, 0.5, 0.75)) | {nL - 4})
    _sets = {"grid": receiver_forms, "ladder": readout_ladder_forms,
             "fewshot": fewshot_receiver_forms}
    forms = _sets[args.form_set](concept, codeword, args.other_concept, args.other_codeword,
                                 args.probe)
    print("[pf] form set = %s: %r" % (args.form_set, [f["name"] for f in forms]))
    results = []

    for form in forms:
        text, add_specials = render_receiver(dc, tok, form, think)
        think_check = (assert_thinking_actually_off(dc, tok, form["body"], think)
                       if form["templated"] else {"checked": False, "reason": "untemplated"})
        enc = tok(text, return_tensors="pt", add_special_tokens=add_specials,
                  return_offsets_mapping=True)
        offsets = enc.pop("offset_mapping")[0].tolist()
        rids = enc["input_ids"][0].tolist()
        if form["patch_at"] == "last":
            q_pos = len(rids) - 1
        else:
            a, b = find_quoted_probe_span(text, args.probe)
            q_pos = token_index_covering(offsets, a, b)
            assert_token_is_part_of(tok, rids, q_pos, args.probe,
                                    "receiver %s probe" % form["name"])
        read_pos = q_pos if form["read_at"] == "patch" else len(rids) - 1
        inputs = {"input_ids": enc["input_ids"].to(lm.model.device)}

        with torch.no_grad():
            base_out = lm.model(**inputs)
        base_probs = torch.softmax(base_out.logits[0, read_pos, :].float(), dim=-1)
        base_mass = float(sum(base_probs[i] for i in label_ids.values()))
        base_dist = {w: float(base_probs[label_ids[w]]) for w in label_words}

        for R in R_SET:
            if R >= nL:
                continue
            per_layer = []
            for L in range(0, nL - 1):
                ps = []
                for dr in donor_reps:
                    v = dr["reps"][L].to(lm.model.device, dtype=next(lm.model.parameters()).dtype)
                    with torch.no_grad():
                        with dc.LayerPatch(lm.model, R, [q_pos], vector=v, mode="replace"):
                            o = lm.model(**inputs)
                    pr = torch.softmax(o.logits[0, read_pos, :].float(), dim=-1)
                    ps.append({"p_concept": float(pr[label_ids[concept]]),
                               "p_codeword": float(pr[label_ids[codeword]]),
                               "option_mass": float(sum(pr[i] for i in label_ids.values()))})
                per_layer.append({
                    "L": L,
                    "p_concept_mean": sum(x["p_concept"] for x in ps) / len(ps),
                    "p_concept_max": max(x["p_concept"] for x in ps),
                    "p_codeword_mean": sum(x["p_codeword"] for x in ps) / len(ps),
                    "option_mass_mean": sum(x["option_mass"] for x in ps) / len(ps)})
            best = max(per_layer, key=lambda r: r["p_concept_mean"])
            # `RAH-C-006` / review F2. The gate must measure TRANSPORT, not the receiver's lexical
            # prior. `fc_probe_last` and `fc46` PRINT all four labels in the prompt, so the
            # UNPATCHED probability of the concept is order 1/4 -- already far above a 0.1 absolute
            # threshold. Gating on the level alone would return GO for a receiver that ignores the
            # patch entirely, which is exactly the failure this whole pre-flight exists to detect.
            # Three conjuncts, all required:
            #   (i)   the patched level clears the threshold at all,
            #   (ii)  the patch RAISES it over the unpatched prior by more than the threshold,
            #   (iii) the concept beats the codeword -- the donor's meaning wins the forced choice.
            p_unpatched = base_dist[concept]
            uplift = best["p_concept_mean"] - p_unpatched
            ok = bool(best["p_concept_mean"] > POSITIVE_CONTROL_THRESH
                      and uplift > POSITIVE_CONTROL_THRESH
                      and best["p_concept_mean"] > best["p_codeword_mean"])
            rec = {"form": form["name"], "read_at": form["read_at"], "templated": form["templated"],
                   "R": R, "n_layers": nL, "q_pos": q_pos, "read_pos": read_pos,
                   "recv_seq_len": len(rids), "hops": read_pos - q_pos,
                   "add_special_tokens": add_specials, "thinking_check": think_check,
                   "form_set": args.form_set,
                   "capture_mode": args.capture_mode, "capture_offset": args.capture_offset,
                   "names_candidates": names_any_candidate(text, label_words),
                   # `RAH3-PR-001` §2.6 rule 1: the three conditions a cell must satisfy before it
                   # is even ELIGIBLE to carry a scientific claim. Persisted per cell so the
                   # selection rule is auditable from the artifact alone.
                   "rah3_eligible": bool(not names_any_candidate(text, label_words)
                                         and (read_pos - q_pos) > 0
                                         and args.capture_mode == "offset"),
                   "unpatched_option_mass": base_mass, "unpatched_dist": base_dist,
                   "patched_option_mass_at_best": best["option_mass_mean"],
                   "p_concept_unpatched": p_unpatched,
                   "pos_ctrl_max": best["p_concept_mean"], "uplift_over_unpatched": uplift,
                   "p_codeword_at_best": best["p_codeword_mean"], "best_donor_L": best["L"],
                   "positive_control_ok": ok,
                   "gate_rule": "level > t AND uplift > t AND p_concept > p_codeword",
                   "per_layer": per_layer}
            results.append(rec)
            print("[pf] %-14s R=%-3d hops=%-3d  p_conc=%.4g (unpatched %.4g, uplift %+.4g) "
                  "@L%-3d  p_code=%.4g  mass_unpatched=%.3f mass_patched=%.4g  %s"
                  % (form["name"], R, rec["hops"], rec["pos_ctrl_max"], p_unpatched, uplift,
                     rec["best_donor_L"], rec["p_codeword_at_best"], base_mass,
                     rec["patched_option_mass_at_best"],
                     "PASS" if rec["positive_control_ok"] else "fail"))

    any_pass = [r for r in results if r["positive_control_ok"]]
    prov["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    prov["branch"] = _git_branch()
    prov["python_executable"] = sys.executable
    prov["bank_sha256"] = sha256_file(args.bank)
    prov["expected_n_donors"] = args.n_donors
    prov["actual_n_donors"] = len(donor_reps)
    if prov["git_dirty"] is not False:
        # `RAH3` §5.4: a dirty (or unknowable) tree must be ATTESTED, not glossed. The diff hash
        # makes the exact working state citable even though the diff itself is not committed.
        prov["diff_sha256"] = _diff_sha256()
    out = {"schema": SCHEMA, "provenance": prov, "model": args.model, "bank": os.path.abspath(args.bank),
           "n_layers": nL, "attn_implementation": "eager", "enable_thinking": args.enable_thinking,
           "concept": concept, "codeword": codeword, "probe": args.probe,
           "label_words": label_words, "label_ids": label_ids, "label_meta": label_meta,
           "exemplar_candidate_collisions": exemplar_clash,
           "capture_mode": args.capture_mode, "capture_offset": args.capture_offset,
           "capture_consistency": capture_consistency,
           "donor_condition": args.donor_condition, "n_donors": len(donors),
           "donor_n_examples": args.n_examples,
           "n_donor_candidates": len(cand),
           "donors": [{k: v for k, v in d.items() if k != "reps"} for d in donor_reps],
           "R_set": R_SET, "threshold": POSITIVE_CONTROL_THRESH,
           "form_set": args.form_set, "mass_gate": 0.05,
           "gate_rule": "positive_control_ok requires level > t AND uplift over the UNPATCHED prior > t AND p_concept > p_codeword (RAH-C-006 / review F2: an absolute level gate is passed by the receiver's own lexical prior, since the 4 labels are printed in the prompt)",
           "layer_convention": "donor block index L == hidden_states[L+1] == LayerPatch(L) target; "
                               "L capped at n_layers-2 because hidden_states[n_layers] is post-norm",
           "grid": results,
           "GATE": {"any_config_passes": bool(any_pass),
                    "n_configs": len(results), "n_passing": len(any_pass),
                    "best_overall": max((r["pos_ctrl_max"] for r in results), default=0.0),
                    "passing_configs": [{"form": r["form"], "R": r["R"],
                                         "pos_ctrl_max": r["pos_ctrl_max"]} for r in any_pass]}}
    os.makedirs(args.outdir, exist_ok=True)
    path = os.path.join(args.outdir, "%s_%s.json" % (args.tag, time.strftime("%Y%m%d_%H%M%S")))
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n[pf] GATE any_config_passes=%s  best=%.4g over %d configs"
          % (out["GATE"]["any_config_passes"], out["GATE"]["best_overall"], len(results)))
    print("[pf] -> %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
