##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A6: Best-passage and first-passage recall
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

heat_colours <- hcl.colors(9, palette = "Heat")
series_colours <- c(
  "S" = heat_colours[4],
  "U" = heat_colours[7]
)
series_shapes <- c("S" = 16, "U" = 17)
series_labels <- c(
  "S" = "Conditioned zone",
  "U" = "Unconditioned zone"
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

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA6.csv",
  show_col_types = FALSE
) %>%
  mutate(model_id = factor(model_id, levels = names(model_labels)))

stopifnot(
  nrow(data) == 140,
  setequal(data$model_id, names(model_labels)),
  setequal(data$metric, c("best_fid", "fid")),
  setequal(data$series, names(series_colours)),
  all(is.finite(data$estimate)),
  all(data$estimate >= 0 & data$estimate <= 1)
)

stopifnot(
  all(count(data, metric, model_id, series)$n == 5),
  all(data$ci_low <= data$estimate),
  all(data$ci_high >= data$estimate),
  all(data$sample == "all_recorded_ungated")
)

#=================================
# 3. Plotting function
#=================================

create_panel <- function(metric_name, plot_title, panel_letters) {
  full_panel <- data %>% filter(metric == metric_name)
  panel_labels <- setNames(
    paste0("Panel ", panel_letters, ": ", model_labels),
    names(model_labels)
  )

  ggplot() +
    geom_errorbar(
      data = full_panel,
      aes(x = dose, ymin = ci_low, ymax = ci_high, colour = series),
      width = 0.04,
      linewidth = 0.75,
      show.legend = FALSE
    ) +
    geom_line(
      data = full_panel,
      aes(x = dose, y = estimate, colour = series, linetype = series),
      linewidth = 1.15,
      show.legend = FALSE
    ) +
    geom_point(
      data = full_panel,
      aes(x = dose, y = estimate, colour = series, shape = series),
      size = 3
    ) +
    facet_wrap(
      ~model_id,
      ncol = 4,
      labeller = as_labeller(panel_labels)
    ) +
    scale_colour_manual(
      values = series_colours,
      limits = names(series_colours),
      labels = series_labels,
      drop = FALSE
    ) +
    scale_shape_manual(
      values = series_shapes,
      limits = names(series_shapes),
      labels = series_labels,
      drop = FALSE
    ) +
    scale_linetype_manual(values = c("S" = "solid", "U" = "longdash")) +
    scale_x_continuous(
      breaks = c(-1, -0.5, 0, 0.5, 1),
      limits = c(-1.1, 1.1),
      expand = expansion(mult = 0)
    ) +
    scale_y_continuous(
      breaks = seq(0, 1, by = 0.25),
      limits = c(0, 1),
      expand = expansion(mult = c(0.02, 0.04))
    ) +
    labs(
      title = plot_title,
      x = "Steering dose",
      y = "Recall accuracy",
      colour = NULL,
      shape = NULL
    ) +
    guides(
      colour = guide_legend(nrow = 1, override.aes = list(alpha = 1, size = 3)),
      shape = guide_legend(nrow = 1)
    )
}

#=================================
# 4. Combine and save figure
#=================================

best_panel <- create_panel(
  "best_fid",
  "Best recall of any passage",
  LETTERS[1:7]
)
first_panel <- create_panel(
  "fid",
  "Recall of first passage",
  LETTERS[8:14]
)

figure <- best_panel / first_panel +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom")

ggsave(
  "figures/figureA6.png",
  figure,
  width = 14,
  height = 15,
  dpi = 300,
  bg = "white"
)
