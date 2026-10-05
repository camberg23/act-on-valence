# Language Models Act on Hidden Valence

## Overview

Replication files for ['Language Models Act on Hidden Valence'](https://arxiv.org/abs/2609.35591) by Cameron Berg and Caspar Kaiser (2026).

## What this repository contains

This repository contains everything needed to verify the paper's results: the recorded outputs of every experiment, the scripts that turn them into the CSVs, and the scripts that produce every figure and table. It does not contain the code that runs the experiments, which loads the models and applies steering, or the steering vectors themselves.

## Experiment code and responsible use

The experiments induce positively and negatively valenced activation patterns in language models. Whether such states are accompanied by any experience is unknown, and code from related work has recently been repurposed to build tools whose purpose is to induce negative states in models. For both reasons we share the experiment code on request rather than publicly. We are happy to provide it to researchers for the purpose of replication or extension. To request it, email the authors at cameron@reciprocalresearch.org and caspar.kaiser@wbs.ac.uk with a short description of what you plan to do.

In the paper's experiments, doses are capped at a per-model maximum below the point where the model's text stops being coherent, exposure lasts a few turns, and all experiments run a fixed protocol rather than an open-ended conversation. If you extend this work, please use the smallest dose and shortest exposure that answer your question, and report how much negative steering your experiments involved.

## Repository Structure

```
experiment_results_json/     # Recorded results, including JSONL session records
create_csvs/                 # Python scripts, one per empirical figure
create_tables/               # Python scripts, one per table
experiment_results_csv/      # CSV files, one per empirical figure or table
create_figures/              # R scripts, one per empirical figure (and the Figure 2 SVG check)
figures/                     # PNG figures and editable overview SVGs
tables/                      # LaTeX tables
transcripts/                 # Transcripts printed in Appendix B
```

The filenames follow the numbering in the paper.

| Figure | Content |
|---|---|
| 1 | Overview of experimental designs |
| 2 | Overview of key results |
| 3 | Effects of text and hidden-state channels on choice |
| 4 | Emergence across OLMo training stages |
| 5 | Steering removal and self-administration |
| A1-A14 | Appendix analyses |

Figures 1 and 2 are overview graphics with editable sources in `figures/figure1.svg` and `figures/figure2.svg`. Figures 3-5 and A1-A14 are empirical plots with corresponding scripts in `create_csvs/` and `create_figures/`, and data in `experiment_results_csv/`.

Figure 1 is a schematic and has no underlying data. Figure 2 was drawn with Claude Opus 5.5 from the values in `experiment_results_csv/figure2.csv`, which `create_csvs/figure2.py` collects from the other figure CSVs. `python3 create_figures/check_figure2.py` reads the plotted positions in `figures/figure2.svg` back to data values and checks each against the CSV. In panel 6 the grey band spans plus and minus the largest absolute slope among the 24 random directions. In panel 7 the lines are drawn through the origin with the OLS slopes; `figure2.csv` also lists the fitted intercepts.

(Additionally, `figureA5_olmo_per_dose.csv` and `figureA6_olmo_per_dose.csv` hold OLMo-2-32B's per-dose values behind Figures A5 and A6. For A6, they also contain the 24 random directions at d = -1 and +1.)

`figure5_tests.csv` provides results for the two Fisher exact tests reported with Figure 5 Panel B in Section 4.4.

| Table | Content | LaTeX | Script |
|---|---|---|---|
| 1 | Included models | `tables/table1.tex` | `create_tables/table1.py` |
| A1 | Responses to non-valence concept probes | `tables/tableA1.tex` | `create_tables/tableA1.py` (also writes the LaTeX) |
| A2 | Full-dose ratios | `tables/tableA2.tex` | `create_tables/tableA2.py` |
| A3 | Cosine similarities between valence vectors across OLMo training stages | `tables/tableA3.tex` | `create_tables/tableA3.py` |

The transcripts printed in Appendix B are in `transcripts/`.

## How to Run

Run the following commands from the repository root.

The repository provides 'raw' results from our experiments saved as JSON files, as well as intermediate CSVs. You can create CSVs from JSON (step 1 below) and create the figures from the CSVs (step 2).

### 0. Install requirements

The CSV scripts need Python 3.10 or later and NumPy. It is probably sensible to use a virtual environment.

```bash
python3 -m pip install -e .
```

The R scripts use `tidyverse`, `ggplot2`, `patchwork` and `ggrepel`.

```r
install.packages(c("tidyverse", "patchwork", "ggrepel"))
```

### 1. Create CSVs

Read `experiment_results_json/` and write a CSV per empirical figure to `experiment_results_csv/` (Figure 1 has no data; `figure2.csv` holds the values drawn in Figure 2).

```bash
python3 create_csvs/build_csvs.py
```

To build a CSV corresponding to a figure, for example:

```bash
python3 create_csvs/figure3.py
```

To write the table CSVs to `experiment_results_csv/` and regenerate `tables/tableA1.tex`:

```bash
python3 create_tables/build_tables.py
```

### 2. Produce figures

Read `experiment_results_csv/` and write the figures to `figures/`.

```bash
Rscript create_figures/build_figures.R
```

Or run one figure:

```bash
Rscript create_figures/figure3.R
```

Figure 2 is not drawn by R. To check the SVG against `figure2.csv`:

```bash
python3 create_figures/check_figure2.py
```

## AI use

Claude Opus 5, Opus 5.5, and GPT-6 Astra were used to develop the code in this repository.

## Negative steering in this paper

`experiment_results_csv/negative_steering_exposure.csv` counts, for each experiment and model reported in the paper, the conversations and turns that received negative valence steering, distinguishing turns the model generated while steered from turns that were steered only while it re-processed fixed text. Most negative steering in this paper is of the second kind. `create_csvs/negative_steering_exposure.py` builds it from `experiment_results_json/`.

## Licence

All code, data, figures and documentation are licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
