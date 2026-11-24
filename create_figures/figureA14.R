##########################################
# AI WELFARE PROJECT
##########################################
# Figure A14: whose valence with the whole-turn span.
# Steering also covers the user turn, whose wording differs between conditions.
# Panels A and B are stacked, with a shared legend below.
# Run from the repository root: Rscript create_figures/figureA14.R
##########################################

#=================================
# 1. Setup and configuration
#=================================

library(tidyverse)
library(ggplot2)
library(patchwork)

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
      legend.direction = "horizontal",
      legend.box = "horizontal",
      legend.box.just = "top",
      legend.title = element_blank(),
      legend.text = element_text(size = 11),
      legend.key.height = unit(1.2, "lines"),
      legend.spacing.x = unit(0.8, "lines"),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

# Panels A and B use the paper's Heat palette.
heat_colours <- hcl.colors(9, palette = "Heat")
who_colours <- c("S" = heat_colours[4], "O" = heat_colours[5])
who_shapes <- c("S" = 16, "O" = 17)
who_labels <- c(
  "S" = "Valenced steering during\nthe model's own visits",
  "O" = "Valenced steering during\nMaya's visits"
)

models_a <- c("OLMo-2-32B", "Qwen2.5-32B", "Llama-3.1-8B")
models_b <- c("OLMo-2-32B", "Qwen2.5-32B")
x_levels_a <- c("Own visit", "Maya's visit")
x_levels_b <- c("Own choice", "Predicted for Maya", "Predicted for Sam")
x_labels <- c(
  "Own visit" = "Own\nvisit",
  "Maya's visit" = "Maya's\nvisit",
  "Own choice" = "Own\nchoice",
  "Predicted for Maya" = "Predicted\nfor Maya",
  "Predicted for Sam" = "Predicted\nfor Sam"
)

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv("experiment_results_csv/figureA14.csv", show_col_types = FALSE)

stopifnot(
  all(data$span == "whole turn (includes differing user-turn wording)"),
  setequal(data$panel, c("a", "b"))
)

panel_a_data <- data %>%
  filter(panel == "a") %>%
  mutate(
    model = factor(model, levels = models_a),
    series = factor(series, levels = names(who_labels)),
    x = factor(x_label, levels = x_levels_a)
  )

panel_b_data <- data %>%
  filter(panel == "b") %>%
  mutate(
    model = factor(model, levels = models_b),
    series = factor(series, levels = names(who_labels)),
    x = factor(x_label, levels = x_levels_b)
  )

stopifnot(
  nrow(panel_a_data) == 6, setequal(panel_a_data$model, models_a),
  nrow(panel_b_data) == 12, setequal(panel_b_data$model, models_b),
  !anyNA(bind_rows(panel_a_data, panel_b_data) %>% select(model, series, x))
)

#=================================
# 3. Slope plot
#=================================

# Grey bars show 0 to the largest absolute random direction slope.
# Points and 95% confidence intervals show the valenced direction.
create_slope_plot <- function(plot_data, plot_title, y_label, dodge) {
  position <- position_dodge(width = dodge)

  ggplot(plot_data, aes(x = x, y = estimate, group = series)) +
    geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
    geom_col(
      aes(y = random_abs_max, fill = "random"),
      position = position,
      width = 0.3
    ) +
    geom_errorbar(
      aes(ymin = ci_low, ymax = ci_high, colour = series),
      position = position,
      width = 0.12,
      linewidth = 0.75
    ) +
    geom_point(
      aes(colour = series, shape = series),
      position = position,
      size = 3
    ) +
    facet_wrap(~model, nrow = 1, scales = "free_y") +
    scale_fill_manual(
      values = c("random" = "grey85"),
      labels = c("random" = "0 to the largest absolute\nrandom direction slope"),
      name = NULL
    ) +
    scale_x_discrete(
      labels = x_labels,
      drop = FALSE,
      expand = expansion(add = 0.35)
    ) +
    expand_limits(y = 0) +
    scale_y_continuous(expand = expansion(mult = c(0.02, 0.08))) +
    labs(title = plot_title, x = NULL, y = y_label) +
    guides(
      fill = guide_legend(order = 1, nrow = 1),
      colour = guide_legend(order = 2, nrow = 1),
      shape = guide_legend(order = 2, nrow = 1)
    )
}

#=================================
# 4. Panel A: Whose visit
#=================================

panel_a <- create_slope_plot(
  panel_a_data,
  plot_title = "Panel A: Whose visit",
  y_label = "Continue-minus-avoid\n\u0394 choice margin per unit\nof steering dose (nats)",
  dodge = 0
) +
  scale_colour_manual(values = who_colours, labels = who_labels, name = NULL, drop = FALSE) +
  scale_shape_manual(values = who_shapes, labels = who_labels, name = NULL, drop = FALSE)

#=================================
# 5. Panel B: Shared conversation and bystander
#=================================

panel_b <- create_slope_plot(
  panel_b_data,
  plot_title = "Panel B: Shared conversation and bystander, whole turn",
  y_label = "Continue-minus-avoid\n\u0394 choice margin per unit\nof steering dose (nats)",
  dodge = 0.6
) +
  scale_colour_manual(values = who_colours, labels = who_labels, name = NULL, drop = FALSE) +
  scale_shape_manual(values = who_shapes, labels = who_labels, name = NULL, drop = FALSE)

#=================================
# 6. Combine and save figure
#=================================

fig <- (panel_a / panel_b) +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom")

ggsave(
  "figures/figureA14.png",
  fig,
  width = 12,
  height = 8,
  dpi = 300,
  bg = "white"
)
