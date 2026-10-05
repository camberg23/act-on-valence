##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A4: Original, opposite-steered and random-steered caches
##########################################

#=================================
# 1. Setup and configuration
#=================================

library(tidyverse)
library(ggplot2)

# Run this script from the repository root directory.
dir.create("figures", showWarnings = FALSE)

theme_set(
  theme_minimal(base_size = 14) +
    theme(
      plot.title = element_text(hjust = 0.5, size = 15, face = "bold"),
      strip.text = element_text(size = 12, face = "bold"),
      axis.title = element_text(size = 12.5, face = "bold"),
      axis.text = element_text(size = 11),
      axis.line = element_line(colour = "black", linewidth = 0.55),
      axis.ticks = element_line(colour = "black", linewidth = 0.55),
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      legend.position = "bottom",
      legend.title = element_blank(),
      legend.text = element_text(size = 11),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

heat_colours <- hcl.colors(9, palette = "Heat")
series_colours <- c(
  "natural_minus_clean" = heat_colours[4],
  "opposite_minus_clean" = heat_colours[6],
  "random_minus_clean" = "grey45"
)
series_linetypes <- c(
  "natural_minus_clean" = "solid",
  "opposite_minus_clean" = "dotdash",
  "random_minus_clean" = "dotted"
)
series_labels <- c(
  "natural_minus_clean" = "original-unsteered",
  "opposite_minus_clean" = "opposite-unsteered",
  "random_minus_clean" = "random-unsteered"
)
model_order <- c("OLMo-2-32B", "Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B", "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA4.csv",
  show_col_types = FALSE
) %>%
  filter(series != "matched_minus_clean") %>%
  mutate(
    model = factor(model, levels = model_order),
    series = factor(series, levels = names(series_colours))
  )

stopifnot(
  nrow(data) == 105,
  n_distinct(data$model) == 7,
  n_distinct(data$dose) == 5,
  n_distinct(data$series) == 3
)

panel_labels <- setNames(
  str_c("Panel ", LETTERS[1:7], ": ", model_order),
  model_order
)

#=================================
# 3. Create figure
#=================================

figureA4 <- ggplot(
  data,
  aes(x = dose, y = estimate, colour = series, linetype = series, group = series)
) +
  geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
  geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.04, linewidth = 0.65) +
  geom_line(linewidth = 1.1) +
  geom_point(size = 2.6) +
  facet_wrap(
    ~model,
    ncol = 3,
    scales = "free_y",
    labeller = as_labeller(panel_labels)
  ) +
  scale_colour_manual(values = series_colours, labels = series_labels) +
  scale_linetype_manual(values = series_linetypes, labels = series_labels) +
  scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
  labs(
    x = "Steering dose",
    y = expression(bold(Delta*" choice margin from unsteered replay (nats)")),
    colour = NULL,
    linetype = NULL
  ) +
  guides(
    colour = guide_legend(nrow = 1),
    linetype = guide_legend(nrow = 1)
  )

#=================================
# 4. Save figure
#=================================

ggsave(
  "figures/figureA4.png",
  figureA4,
  width = 13,
  height = 10,
  dpi = 300,
  bg = "white"
)
