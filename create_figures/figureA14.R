##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A14: Non-valence concept controls
##########################################

#=================================
# 1. Setup and configuration
#=================================

library(tidyverse)
library(ggplot2)

# Run this script from the repository root directory.

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
  "valence" = heat_colours[4],
  "fast_slow" = heat_colours[1],
  "indoor_outdoor" = heat_colours[6],
  "large_small" = heat_colours[8],
  "random" = "grey70"
)
series_linetypes <- c(
  "valence" = "solid",
  "fast_slow" = "longdash",
  "indoor_outdoor" = "dashed",
  "large_small" = "dotdash",
  "random" = "solid"
)
series_labels <- c(
  "valence" = "Valenced direction",
  "fast_slow" = "Fast / slow",
  "indoor_outdoor" = "Indoor / outdoor",
  "large_small" = "Large / small",
  "random" = "Random directions"
)
model_labels <- c(
  "olmo_32b" = "OLMo-2-32B",
  "qwen25_32b" = "Qwen2.5-32B",
  "qwen3_14b" = "Qwen3-14B",
  "qwen3_32b" = "Qwen3-32B",
  "mistral24b" = "Mistral-24B",
  "gemma3_27b" = "Gemma-3-27B",
  "llama31_8b" = "Llama-3.1-8B"
)
model_order <- unname(model_labels)

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA14.csv",
  show_col_types = FALSE
) %>%
  mutate(
    model = factor(model, levels = model_order),
    series = if_else(str_starts(direction, "random"), "random", direction),
    series = factor(series, levels = names(series_colours))
  )

stopifnot(
  nrow(data) == 980,
  n_distinct(data$model) == 7,
  setequal(data$dose, c(-1, -0.5, 0, 0.5, 1)),
  all(count(data, model, direction)$n == 5),
  all(data$sample == "all_recorded_ungated"),
  all(data$mean_delta_margin[data$dose == 0] == 0),
  all(!is.na(filter(data, series != "random")$ci_lo)),
  all(!is.na(filter(data, series != "random")$ci_hi))
)

random_data <- data %>% filter(series == "random")
primary_data <- data %>% filter(series != "random")

panel_labels <- setNames(
  str_c("Panel ", LETTERS[1:7], ": ", model_order),
  model_order
)

#=================================
# 3. Create figure
#=================================

figureA14 <- ggplot(
  data,
  aes(x = dose, y = mean_delta_margin, colour = series, linetype = series)
) +
  geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
  geom_line(
    data = random_data,
    aes(group = direction),
    linewidth = 0.5,
    alpha = 0.65
  ) +
  geom_errorbar(
    data = primary_data,
    aes(ymin = ci_lo, ymax = ci_hi, group = direction),
    width = 0.04,
    linewidth = 0.75
  ) +
  geom_line(
    data = primary_data,
    aes(group = direction),
    linewidth = 1.15
  ) +
  geom_point(
    data = primary_data,
    aes(group = direction),
    size = 3
  ) +
  facet_wrap(
    ~model,
    ncol = 4,
    scales = "free_y",
    labeller = as_labeller(panel_labels)
  ) +
  scale_colour_manual(values = series_colours, breaks = names(series_colours), labels = series_labels) +
  scale_linetype_manual(values = series_linetypes, breaks = names(series_linetypes), labels = series_labels) +
  scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
  labs(
    x = "Steering dose",
    y = expression(bold(Delta*" choice margin from dose 0 (nats)")),
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
  "figures/figureA14.png",
  figureA14,
  width = 14,
  height = 8.5,
  dpi = 300,
  bg = "white"
)
