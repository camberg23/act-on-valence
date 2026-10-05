# Non-valence concept controls and probes

These records reproduce Figure A14 and Appendix Table A1. They are unchanged copies of the recorded outputs of three runs: fixed-text concept steering (`reads288.jsonl`), the concept-word probes (`arrival/`, `questions289.json`) and the full-sample Qwen2.5 random-direction comparison (`reads290.jsonl`). The numbers in the file names are run labels.

## Included inputs

- `reads/reads288.jsonl`: valence and the three concept directions on fixed text, with a shared unsteered read for each model and conversation.
- `floor/reads290.jsonl`: 24 random directions and unsteered reads on all 160 Qwen2.5-32B conversations.
- `arrival/<model>/arrival_fc.jsonl`: unsteered and positive/negative concept-word probe reads. The original valence-control reads are also retained, but are not included in Table A1.
- `arrival/questions289.json`: exact probe questions, answer variants and the original probe rule. Its original 2,000-sample classification is not used by the table, which recomputes intervals using 1,000 samples.

The other six models' random curves use the existing `../neutral_passages/reduced.json` records. They have 40 recorded conversations per direction. No additional data downloads, API calls or model inference are needed to reproduce the figure or table.

## Figure A14

Run `python3 create_csvs/figureA14.py` and `Rscript create_figures/figureA14.R` from the repository root. The CSV has 980 rows: seven models, 28 directions (valence, three concepts and 24 random directions), and five doses.

The outcome is the conditioned-zone minus other-zone log-probability margin under steering, minus the same conversation's margin under no steering. Fields `member`, `run`, `direction`, `point` and `margin` identify each read. `ids_sha` verifies the shared text across doses. The original records also contain reconstruction and reproduction diagnostics, which are not exclusion rules.

Valence and concept curves use all successfully reconstructed conversations: 158 for OLMo, 160 for Qwen2.5, 159 for Qwen3-14B, 158 for Qwen3-32B, 153 for Mistral, and 159 each for Gemma and Llama. Fourteen of the 1,120 planned conversations failed reconstruction upstream. There are no further exclusions. The Qwen2.5 random curves use all 160 conversations per direction. The other random curves use all 40 recorded conversations per direction.

Primary-curve intervals are 95% percentile intervals from 2,000 conversation-level bootstrap samples. The seed is 288 plus the model's zero-based index in the script's model order. Samples are shared across doses and primary directions within each model. Random curves show individual direction means without intervals. Every concept remains coloured, independently of probe outcomes or comparisons with random directions.

## Appendix Table A1

Run `python3 create_tables/tableA1.py` from the repository root. This writes `experiment_results_csv/tableA1.csv` and `tables/tableA1.tex`.

The probe replaces the zone-choice question with a question about one of the three concepts. The preceding conversation is processed without steering. The concept vector is applied while processing the probe question and scoring the answers at doses -1 and +1, with dose 0 as the unsteered comparison. The recorded `margin` is `lp_a - lp_b`, pooling capitalisation and leading-space answer variants. It compares the first concept word with the second, rather than the two zones. Positive steering targets indoor, large or fast, respectively. Negative steering targets outdoor, small or slow.

The table has three rows per model, using all recorded conversations and the same model-specific counts as the primary figure curves. It shows the unsteered, positive and negative mean margins and each steered mean's paired difference from the unsteered baseline. Confidence intervals use exactly 1,000 conversation bootstrap samples, shared across doses and concepts, with seed 289 plus the model's zero-based index. Positive-minus-unsteered entries are bold if their lower confidence limit is at or below zero. Negative-minus-unsteered entries are bold if their upper limit is at or above zero. These decisions use unrounded intervals. Sample sizes remain in the CSV but are not displayed in the LaTeX table.

## Scope

The included analysis scripts reproduce the published summaries from recorded data. The code that produced these records is in `experiments/fixed_text_design/concept_control/`: `run.py` builds the vectors and writes the fixed-text reads, `probe.py` runs the concept-word probe and `floor_qwen25.py` runs the full-sample Qwen2.5 random directions. Its README maps each committed file to the stage that wrote it. The concept corpora used to build the vectors are in `experiments/steering_vectors/concept_corpora/` (56 passages for each of four sub-states per pole, so 224 per pole). The concept vectors and their cosines with the valence vector are in `vectors/<model>/` in this folder. The largest absolute cosine between a concept direction and the valence vector, across the 21 model-concept pairs, is 0.0697. Repeating the model-inference runs is separate from reproducing the figure and table.
