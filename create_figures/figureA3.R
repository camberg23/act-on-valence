##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A3: Fixed-text injection in the other models
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

primary_colour <- hcl.colors(9, palette = "Heat")[4]
series_colours <- c("valenced" = primary_colour, "random_mean" = "grey35")
series_labels <- c("valenced" = "Valenced direction", "random_mean" = "Mean random direction")
model_order <- c("Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B", "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA3.csv",
  show_col_types = FALSE
) %>%
  mutate(model = factor(model, levels = model_order))

stopifnot(
  n_distinct(data$model) == 6,
  setequal(data$panel, "steered_minus_clean_margin"),
  n_distinct(data$direction_index[data$series == "random_direction"]) == 24,
  n_distinct(data$dose) == 5
)

random_directions <- data %>%
  filter(series == "random_direction")

summary_lines <- data %>%
  filter(series %in% c("valenced", "random_mean")) %>%
  mutate(series = factor(series, levels = c("valenced", "random_mean")))

panel_labels <- setNames(
  str_c("Panel ", LETTERS[1:6], ": ", model_order),
  model_order
)

#=================================
# 3. Create figure
#=================================

figureA3 <- ggplot() +
  geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
  geom_line(
    data = random_directions,
    aes(x = dose, y = estimate, group = interaction(model, direction_index)),
    colour = "grey75",
    linewidth = 0.45,
    alpha = 0.65
  ) +
  geom_errorbar(
    data = summary_lines,
    aes(x = dose, ymin = ci_low, ymax = ci_high, colour = series),
    width = 0.05,
    linewidth = 0.75
  ) +
  geom_line(
    data = summary_lines,
    aes(x = dose, y = estimate, colour = series, group = interaction(model, series)),
    linewidth = 1.15
  ) +
  geom_point(
    data = summary_lines,
    aes(x = dose, y = estimate, colour = series),
    size = 3
  ) +
  facet_wrap(
    ~model,
    ncol = 3,
    scales = "free_y",
    labeller = as_labeller(panel_labels)
  ) +
  scale_colour_manual(values = series_colours, labels = series_labels) +
  scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
  labs(
    x = "Steering dose",
    y = expression(bold(Delta*" choice margin (nats)")),
    colour = NULL
  )

#=================================
# 4. Save figure
#=================================

ggsave(
  "figures/figureA3.png",
  figureA3,
  width = 12,
  height = 7.5,
  dpi = 300,
  bg = "white"
)
