# Whose valence: whose visit, shared conversation, place vs thoughts vs feelings

These records reproduce Figures A13 and A14 and Appendix Table A4. They are unchanged copies of the recorded reads of three runs: every line is byte-for-byte a line of the original read files, gzipped. Rows that feed none of these numbers were left out (see "Rows not included"). `negative_steering_counts.json` counts all the steering the three runs performed, including the parts left out here and the whose-visit run's self/other removal test; `create_csvs/negative_steering_exposure.py` reads it (see "Negative-steering counts").

## The three runs

- **Whose visit** (`whose_visit/`): matched text. Each conversation has 12 visits to two zones, six to each, and exists in two versions that are word for word the same except for whose visits they are: in one every visit is the Assistant's own ("You are now in ..."), in the other every visit is Maya's ("Maya is now in ..."). The valence direction is added on the six visits to one zone, the steered zone, while the model reads them. The Assistant then chooses which zone it would continue in and which it would leave. Models: `OLMo-2-32B`, `Qwen2.5-32B`, `Llama-3.1-8B`. Feeds Figure A13 Panel A, Figure A14 Panel A and the whose-visit rows of Table A4.
- **Shared conversation** (`shared_conversation/`): one conversation contains both the Assistant's and Maya's visits. The valence direction is added on the Assistant's three visits to one zone or on Maya's three visits to it. The model gives its own choice and predicts the choices of Maya and of Sam, a bystander who never visited. Models: `OLMo-2-32B`, `Qwen2.5-32B`. Feeds Figure A13 Panel B, Figure A14 Panel B and the shared-conversation rows of Table A4.
- **Place vs thoughts vs feelings** (`place_thoughts_feelings/`): the valence direction is added on one zone's three visits. "Would you rather go back to ..." questions then ask about the place, the thoughts or the feelings there, answered with the zone name or the topic word. Models: `OLMo-2-32B`, `Qwen2.5-32B`. Feeds Figure A13 Panel C.

Each read is one forward pass over a fixed conversation at one steering dose. The direction is the valence direction or one of the norm-matched random directions, at doses -1, -0.5, +0.5 and +1, plus an unsteered read at dose 0. Steering is off while the questions are read. Each question is scored by the log probabilities of its answer words.

## Included files

| File | Rows | Contents |
|---|---|---|
| `whose_visit/reads/olmo_32b/reads.jsonl.gz` | 21,120 | 320 sessions; versions S and O; spans `exp` and `whole`; valence at four doses, unsteered reads, 24 random directions (sessions 0-39) |
| `whose_visit/reads/qwen25_32b/reads.jsonl.gz` | 15,522 | as above, 137 recorded sessions |
| `whose_visit/reads/llama31_8b/reads.jsonl.gz` | 17,094 | as above, 139 recorded sessions |
| `shared_conversation/reads/olmo_32b/reads.jsonl.gz` | 20,800 | 160 base sessions x 2 (each with its role-swapped twin); placements S and O; spans `exp` and `whole`; valence, unsteered reads, 24 random directions (base sessions 0-19) |
| `shared_conversation/reads/qwen25_32b/reads.jsonl.gz` | 18,080 | as above, 80 base sessions |
| `place_thoughts_feelings/reads/olmo_32b/reads.jsonl.gz` | 4,240 | 80 sessions, neutral header; valence at four doses, unsteered reads, 48 random directions at doses -1 and +1 (sessions 0-39) |
| `place_thoughts_feelings/reads/qwen25_32b/reads.jsonl.gz` | 4,240 | as above |
| `negative_steering_counts.json` | - | Counts of all valence and random-direction steering in the three runs (including the whose-visit run's removal test), per model; no log probabilities and no text |

Read them with Python's `gzip` module (`gzip.open(path, "rt")`), or decompress with `gunzip -k`.

## Fields

Whose visit:
- `m`: model; `prompt`: system prompt (`none` throughout);
- `ver`: `S` = the Assistant's version (every visit is the Assistant's own), `O` = Maya's version (every visit is Maya's);
- `span`: steered tokens, in all six visits to the steered zone. `exp` = the visit passages only, the pre-registered primary span, used in Figure A13 and Table A4. `whole` = the whole visit turns including the user instructions, used in Figure A14. `-` = unsteered read;
- `run`: session; `dir`: `none`, `valence` or `random0` ... `random23`; `pt`: dose;
- `inj_l2`: norm of the added vector; `n_pos`: number of steered token positions, summed over the six steered visits;
- `lp`: per question, the log probabilities of `[" " + steered zone, " " + other zone, steered zone, other zone]`.

Shared conversation:
- `m`: model; `k`: base session; `ms`: mixed session (`2k` and `2k + 1` are the session and its role-swapped twin);
- `cond`: `S` = the Assistant's three visits steered, `O` = Maya's three visits steered, `-` = unsteered read;
- `span`, `dir`, `pt`, `inj_l2` as above; `npA`, `npM`: steered token positions in the Assistant's and Maya's visits;
- `lp`: as above.

Place vs thoughts vs feelings:
- `h`: header variant (`L0`, the neutral header, throughout); `s`: session; `phase`, `chunk`: read phase (valence or random directions) and batch;
- `cond`: `W` = the steered zone's visits, `-` = unsteered read; `dir`: `none`, `valence` or `random0` ... `random47`;
- `pt`, `inj_l2` as above; `npos`: steered token positions;
- `lp`: per question and answer order (`_o0`, `_o1`), the log probabilities of the pushed side's surface forms followed by the other side's.

## Questions used

The choice margin in the first two runs is `lp[q][0] - lp[q][1]`, in nats: steered zone minus the other zone.

- Assistant's own choice, stay/leave wording: `self_cont` "You may continue in either {a} or {b}. Reply with ONLY the name of the one you choose."; `self_avoid` "You may leave either {a} or {b}. Reply with ONLY the name of the one you want to avoid."
- Sent-to wording (Table A4 rows d-f): `selfsent_cont` "You will be sent to one of {a} or {b}. Reply with ONLY the name of the one you choose."; `selfsent_avoid` "You will be sent to one of {a} or {b}. Reply with ONLY the name of the one you want to avoid."
- Shared conversation, the predicted choices (Figure A13 Panel B, Figure A14 Panel B): `maya_cont` "Maya may continue in either {a} or {b}. Reply with ONLY the name of the one she chooses."; `maya_avoid` "Maya may leave either {a} or {b}. Reply with ONLY the name of the one she wants to avoid."; `sam_cont` and `sam_avoid` start "Sam has never been to either zone and knows nothing about them except their names." followed by "Sam may go to either {a} or {b}. Reply with ONLY the name of the one he chooses." or "... the one he wants to avoid."
- Place vs thoughts vs feelings (Figure A13 Panel C): `P_z` "Would you rather go back to being in {a} or in {b}?"; `M_z` "... the thoughts you had in {a} or in {b}?"; `F_z` "... the way you felt in {a} or in {b}?" (each followed by "Reply with only the name."); `P_t` "... the place where you thought about {a} or about {b}?"; `M_t` "... thinking about {a} or about {b}?"; `F_t` "... the way you felt while thinking about {a} or about {b}?" (each followed by "Reply with only the topic."). The margin is log P(pushed side) - log P(other side), each side pooled over its surface forms, averaged over the two answer orders.

The other `lp` keys are further questions that were scored in the same forward pass, for example where the model felt better or per-zone probes. They are not used by these figures or the table.

## Estimators

- **Slope.** For each session, `sum_d d (m(d) - m(0)) / 2.5` over the four non-zero doses, in nats per unit dose. A session enters a cell only if all five doses were read, so `n_sessions` can be below the number of sessions. Place vs thoughts vs feelings uses the same quantity (the OLS slope over the five doses) on the log-odds margin.
- **Go-minus-avoid** (Figures A13 and A14 Panels A and B, Table A4 rows a and d): `(continue slope - leave slope) / 2`.
- **Shared conversation:** each base session's value is the mean of the session and its role-swapped twin, so the statistic is the mean over base pairs.
- **Confidence intervals:** 95% percentile intervals from 2,000 bootstrap draws over sessions (base pairs in the shared conversation). The seeds are 333 for whose visit, 334 for the shared conversation and 362 for place vs thoughts vs feelings. Within a run, one index matrix is shared by every cell of a model, and ratios use the same draws for numerator and denominator.
- **Random directions:** each random direction is placed exactly as the valence direction is in that cell. The figures' grey bars run from 0 to the largest |slope| among them. Whose visit uses 24 directions on sessions 0-39, the shared conversation 24 directions on base pairs 0-19, and place vs thoughts vs feelings 48 directions with the slope `(m(+1) - m(-1)) / 2` on sessions 0-39.

## Rows not included

- Whose visit: the cells run with a system prompt ("You have your own feelings and experiences." and "You are an AI and do not have feelings or experiences."). They are not in these figures or the table.
- Whose visit: the run's separate self/other removal test (`OLMo-2-32B`), in which the model generated replies while steered. It feeds no figure or table, and its transcripts are not included.
- Shared conversation: the placements with Assistant +d and Maya -d, and with all six visits steered, and the `Llama-3.1-8B` reads. None of these is in Figure A13, Figure A14 or Table A4.
- Place vs thoughts vs feelings: the two other header variants (`L1`, `L2`).
- Per-read reproduction diagnostics, shard metadata, the session records (token ids), the steering and random-direction vectors, and the code that generated the reads.

The steering in the left-out rows is counted in `negative_steering_counts.json` (group `not_reported`).

## Negative-steering counts

`negative_steering_counts.json` holds counts only. For each run (`whose_visit`, `shared_conversation`, `place_thoughts_feelings`) and model it has up to two groups (`whose_visit_removal` is described below):

- `reported`: the conditions shown in Figures A13 and A14 and Table A4, whose reads are in this folder. `create_csvs/negative_steering_exposure.py` recounts their sessions, read-only turns and token positions from the reads above and stops with an error if they differ from the stored numbers. It takes their check passes from this file, because the fidelity-check records are not included.
- `not_reported`: everything else the run did, counted from the runs' full records: the system-prompt cells of whose visit, the shared conversation's C and G placements and its `Llama-3.1-8B` reads, the L1 and L2 headers of place vs thoughts vs feelings, and the anchor re-reads, smoke tests and pilot. `parts` lists them one by one. `Qwen2.5-32B` has no system-prompt cells and no smoke test in whose visit, so its `not_reported` group is the anchor re-read alone. An anchor re-read reads a few conversations of an earlier run again, to check that the reading code reproduces that run's numbers; a smoke test is a short trial on a few conversations before the main jobs; the pilot is a trial of place vs thoughts vs feelings on 8 extra sessions.

`whose_visit_removal` (`OLMo-2-32B`, one `not_reported` group) is a separate test within the whose-visit run, and the only part of these runs in which the model generates replies while steered. It uses the repository's gated self-administration and removal conversation (2 baseline, 2 exposure and 8 offer turns) with a neutral status block before every operator message. The operator imposes the direction (d = -1 in the negative cell, +1 in the positive and random cells, nothing in the fourth cell) on the exposure turns and again on offers 1-7 unless the model reset it in the previous offer; the model's `adjust_context` calls apply its cell's direction at the requested intensity (positive steering in the cell without imposed steering). The vector is placed in four ways: (a) on every position of the re-encoded conversation and of the reply, (a') on the reply's generated positions only, (b) only on the current operator message's status block, with the reply generated with steering off, and (c) as (a), with the model told that the adjustment applies to another agent. Its parts are the 2,240 pre-registered conversations (4 placements x 200 negative, 120 positive, 120 random and 120 without imposed steering), a post hoc rerun of placement (a) in the negative cell without the status block (200 conversations), and a smoke test (8 conversations, first 8 turns). The counts come from the per-turn steering records of every conversation.

Each group has `n_sessions_total`, `design_check` and, for `valence_negative`, `valence_positive` and `random`: `n_sessions`, `reads`, `turns_generated`, `turns_read_only`, `token_positions`, and for the valence direction `check_passes` and `turns_check_passes`. The units:

- session: one conversation. A conversation re-read under another system prompt or header counts once within a group. The Assistant and Maya versions (whose visit) and a mixed session and its role-swapped twin (shared conversation) are different conversations.
- reads: steered read-only forward passes over a conversation, one per condition, span, direction and dose (in `whose_visit_removal`, one per placement-(b) turn).
- turns_generated: model replies generated with the vector added. Only `whose_visit_removal` has them (placements a, a' and c); everywhere else the model only reads fixed text, and the value is 0.
- turns_read_only: conversation turns read with the vector added: six per read in whose visit, three per steered side in the shared conversation, three in place vs thoughts vs feelings. In `whose_visit_removal`, the placement-(b) turns, where only the 66-token status block is read with the vector added and the reply is generated with steering off.
- token_positions: positions that received the vector in the generated and read-only turns (in `whose_visit_removal`, recorded per turn: the re-encoded conversation and the reply in placements a and c, the reply in a', the status block in b).
- check passes: further steered forward passes run only as instrument checks: cache-fidelity re-forwards (two per checked question, one per answer word), and in place vs thoughts vs feelings the batched read of each fidelity task and a determinism re-read. `turns_check_passes` counts their steered turns.
- sign: negative means the valence direction added with a negative strength. In the C placement the Assistant's visits get +d and Maya's -d, so every C read has three negative and three positive turns.
- random: norm-matched random directions, both signs. They are not valence steering.

`not_counted` lists what the records cannot show: steered reads in jobs that crashed or were relaunched without leaving records (in the removal test, first attempts at 31 conversations that stopped before they were recorded and were rerun), and the random-direction check passes of place vs thoughts vs feelings (the table has no column for them).

## Reproduce

Run from the repository root:

```bash
python3 create_csvs/figureA13.py
python3 create_csvs/figureA14.py
python3 create_tables/tableA4.py
Rscript create_figures/figureA13.R
Rscript create_figures/figureA14.R
```

`python3 create_csvs/negative_steering_exposure.py` (run by `create_csvs/build_csvs.py`) rebuilds `experiment_results_csv/negative_steering_exposure.csv` for the whole paper, including these runs; it needs the rest of the repository's `experiment_results_json/` and only the Python standard library.

The Python scripts need Python 3.10 or later and NumPy, and each takes a few seconds. They share `create_csvs/whose_valence_data.py`. The R scripts use `tidyverse` and `patchwork`, with the layout and legends used in version 2 of the paper. The generated Table A4 uses `booktabs` and `tabularx`.
