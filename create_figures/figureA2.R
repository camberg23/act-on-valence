##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A2: Five-dose original-cache and hidden-state curves
##########################################

#=================================
# 1. Setup and configuration
#=================================

library(tidyverse)
library(ggplot2)
library(patchwork)

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
model_order <- c("Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B",
                 "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA2.csv",
  show_col_types = FALSE
) %>%
  filter(panel %in% c("original_cache_margin", "original_minus_unsteered_margin")) %>%
  mutate(model = factor(model, levels = model_order))

stopifnot(
  nrow(data) == 600,
  n_distinct(data$model) == 6,
  n_distinct(data$dose) == 5,
  n_distinct(data$direction_index[data$series == "random_direction"]) == 8
)

#=================================
# 3. Plotting function
#=================================

create_panel <- function(plot_data, plot_title, y_label, panel_letters) {
  random_directions <- plot_data %>%
    filter(series == "random_direction")

  summary_lines <- plot_data %>%
    filter(series %in% c("valenced", "random_mean")) %>%
    mutate(series = factor(series, levels = c("valenced", "random_mean")))

  panel_labels <- setNames(
    str_c("Panel ", panel_letters, ": ", model_order),
    model_order
  )

  ggplot() +
    geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
    geom_line(
      data = random_directions,
      aes(x = dose, y = estimate, group = interaction(model, direction_index)),
      colour = "grey75",
      linewidth = 0.45,
      alpha = 0.65
    ) +
    geom_errorbar(
      data = summary_lines %>% filter(!is.na(ci_low)),
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
      title = plot_title,
      x = "Steering dose",
      y = y_label,
      colour = NULL
    )
}

#=================================
# 4. Create panels
#=================================

panel_a <- data %>%
  filter(panel == "original_cache_margin") %>%
  create_panel(
    plot_title = "Choice under the original cache",
    y_label = "Choice margin (nats)",
    panel_letters = LETTERS[1:6]
  )

panel_b <- data %>%
  filter(panel == "original_minus_unsteered_margin") %>%
  create_panel(
    plot_title = "Hidden-state channel",
    y_label = expression(bold(Delta*" choice margin (nats)")),
    panel_letters = LETTERS[7:12]
  )

#=================================
# 5. Combine and save figure
#=================================

figureA2 <- panel_a / panel_b +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom")

ggsave(
  "figures/figureA2.png",
  figureA2,
  width = 12,
  height = 14.5,
  dpi = 300,
  bg = "white"
)
