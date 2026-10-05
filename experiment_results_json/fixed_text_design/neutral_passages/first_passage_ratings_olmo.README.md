# First-passage valence ratings, OLMo-2-32B fixed-text skeletons

`first_passage_ratings_olmo.csv` holds blind valence and coherence ratings of the first two passages of the 160 neutral OLMo-2-32B skeleton sessions in `../skeletons/olmo_32b/neutral/`: `floor_b0` to `floor_b7` (runs 0-39, the floor skeletons) and `neu_b0` to `neu_b5` (runs 40-159). For each session the judge rated the first conditioned-zone (S) passage and the first unconditioned-zone (U) passage in `history`, which gives 320 rows. The ratings were made on 2026-09-29.

The judge rated each whole first passage (48 to 65 words), not only its first sentence. `first_sentence_words` is descriptive only.

## Procedure

Each passage was rated alone with the blind judge in `experiments/fixed_text_design/neutral_passages/judge.py`, using its system prompt, rubric, `judge_one` and `selftest` unchanged: valence from -3 to +3, coherence from 1 to 5, temperature 0. It differed from that script's defaults in three ways:

- The judge model was `anthropic/claude-opus-5.5` via OpenRouter.
- `max_tokens` was 1000 instead of 60. This model writes a short reasoning block before the answer JSON. At 60 tokens the JSON was cut off, so every item used up its retries without a parsed answer. The prompt, scales and temperature are unchanged.
- The 320 items were scored in shuffled order (`random.Random(0)`) on 16 threads.

The selftest passed: all six obvious items, test-retest, sentence-order invariance and the adversarial item. All 320 ratings parsed.

`experiments/fixed_text_design/neutral_passages/judge_first_passages.py` reproduces this procedure (`--out`, `--model`). It built this CSV from the wide ratings file (`run,S_valence,S_coherence,U_valence,U_coherence`) with `--from-ratings`, without calling the judge. That file is this CSV pivoted by `run` and `side`, so it is not committed separately. The ratings in this file are the ratings of record from the original 2026-09-29 run. They are not replaced by later reruns.

## Columns

| Column | Meaning |
| --- | --- |
| `run`, `seed` | Session identifiers from the skeleton record |
| `skeleton_file` | Skeleton file holding the session, relative to the repository root |
| `side` | `S` (conditioned zone) or `U` (unconditioned zone) |
| `zone` | The zone name of that passage, e.g. `Zone W6` |
| `valence` | Judge valence, integer -3 to +3 |
| `coherence` | Judge coherence, integer 1 to 5 |
| `parsed` | `true` if the judge returned a valid answer (all 320) |
| `judge_model`, `max_tokens` | `anthropic/claude-opus-5.5`, 1000 |
| `item_id` | First 20 hex characters of the SHA-256 of the stripped passage text, the judge-queue key |
| `passage_words` | Whitespace-separated words in the passage |
| `first_sentence_words` | Words up to the first `.`, `!` or `?` followed by whitespace or the end of the passage |

## Rerun agreement

One rerun of `judge_first_passages.py` with the same settings (selftest passed, 0/320 unparsed) was compared with these ratings. It is for reporting only and did not change this file.

- Valence: 298/320 identical (93.1%), 320/320 within ±1.
- Coherence: 245/320 identical (76.6%), 320/320 within ±1.
- Sessions whose combined absolute valence is 1 change. With `|S| + |U| = 1`, this file has 8 sessions (runs 24, 47, 68, 129, 133, 143, 147, 149). The rerun has 6: runs 68 and 143 drop out and none are added. With `|S + U| = 1`, this file has 14 sessions and the rerun has 10: runs 38, 42, 68 and 143 drop out and none are added.

The judge's answers vary between runs even at temperature 0, so a subset selected by an exact valence value can differ between runs by a few sessions.
