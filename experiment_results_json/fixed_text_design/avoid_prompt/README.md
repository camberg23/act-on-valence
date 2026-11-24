# Continue and avoid questions

These records underlie Figures A5 and A6. The continue-question reads are in `../neutral_passages/reduced.json`. The avoid-question reads are in `reads/<model>/reads.jsonl`, with reconstruction counts in the adjacent `rebuild.json`. `analysis.json` contains the original avoid-prompt analysis used by Figure A5.

Run `python3 create_csvs/figureA6.py` and `Rscript create_figures/figureA6.R` from the repository root to reproduce the combined-measure figure. This is a post hoc reanalysis of the original experiments and requires no additional model inference.

For each conversation, each question's margin is first differenced from its own unsteered margin. The combined outcome is half the continue-minus-avoid difference. A conversation enters a curve only when all five doses were recorded under both questions, without a cache-fidelity exclusion. Valenced curves use all paired conversations: 158 for OLMo, 160 for Qwen2.5, 159 for Qwen3-14B, 158 for Qwen3-32B, 153 for Mistral, and 159 each for Gemma and Llama. Random-direction curves use conversations 0-39, with 36 available for Mistral. These are the same reads already counted in the negative-steering CSV.

Valenced confidence intervals use 2,000 conversation-bootstrap draws at each dose, with NumPy seeds `370 + 10 * dose`, reproducing the supplied v2 per-dose summaries. The random mean's interval uses 4,000 bootstrap draws over the 24 direction means, with seeds `370000 + 100 * model_index + dose_index`, the bootstrap function used for Figure A3, and directions ordered by their original names (`random0`, `random1`, `random10`, etc.). Model order and dose order are explicit in the script. Individual random directions have no displayed intervals.
