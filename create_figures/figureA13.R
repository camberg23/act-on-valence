##########################################
# AI WELFARE PROJECT
##########################################
# Figure A13: whose valence does the model act on?
# Panels A, B and C are stacked, with a shared legend below.
# Panels A and B use the passage-only span (each run's pre-registered primary).
# Run from the repository root: Rscript create_figures/figureA13.R
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
      legend.direction = "vertical",
      legend.box = "horizontal",
      legend.box.just = "top",
      legend.title = element_blank(),
      legend.text = element_text(size = 11),
      legend.key.height = unit(1.2, "lines"),
      legend.key.spacing.y = unit(0.4, "lines"),
      legend.spacing.x = unit(0.8, "lines"),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

# Panels A and B use the paper's Heat palette. Panel C uses a separate blue family.
heat_colours <- hcl.colors(9, palette = "Heat")
who_colours <- c("S" = heat_colours[4], "O" = heat_colours[5])
who_shapes <- c("S" = 16, "O" = 17)
who_labels <- c(
  "S" = "Valenced steering during\nthe model's own visits",
  "O" = "Valenced steering during\nMaya's visits"
)

answer_colours <- c("zone-name answer" = "#0072B2", "topic-word answer" = "#56B4E9")
answer_shapes <- c("zone-name answer" = 15, "topic-word answer" = 18)
answer_labels <- c(
  "zone-name answer" = "Options named by zone",
  "topic-word answer" = "Options named by topic"
)

models_a <- c("OLMo-2-32B", "Qwen2.5-32B", "Llama-3.1-8B")
models_bc <- c("OLMo-2-32B", "Qwen2.5-32B")
x_levels_a <- c("Own visit", "Maya's visit")
x_levels_b <- c("Own choice", "Predicted for Maya", "Predicted for Sam")
x_levels_c <- c("Place", "Thoughts", "Feelings")
x_labels <- c(
  "Own visit" = "Own\nvisit",
  "Maya's visit" = "Maya's\nvisit",
  "Own choice" = "Own\nchoice",
  "Predicted for Maya" = "Predicted\nfor Maya",
  "Predicted for Sam" = "Predicted\nfor Sam",
  "Place" = "Place",
  "Thoughts" = "Thoughts",
  "Feelings" = "Feelings"
)

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv("experiment_results_csv/figureA13.csv", show_col_types = FALSE)

stopifnot(
  all(data$span[data$panel %in% c("a", "b")] == "passage only (pre-registered primary)"),
  setequal(data$panel, c("a", "b", "c"))
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
    model = factor(model, levels = models_bc),
    series = factor(series, levels = names(who_labels)),
    x = factor(x_label, levels = x_levels_b)
  )

panel_c_data <- data %>%
  filter(panel == "c") %>%
  mutate(
    model = factor(model, levels = models_bc),
    series = factor(series, levels = names(answer_labels)),
    x = factor(x_label, levels = x_levels_c)
  )

stopifnot(
  nrow(panel_a_data) == 6, setequal(panel_a_data$model, models_a),
  nrow(panel_b_data) == 12, setequal(panel_b_data$model, models_bc),
  nrow(panel_c_data) == 12, setequal(panel_c_data$model, models_bc),
  !anyNA(bind_rows(panel_a_data, panel_b_data, panel_c_data) %>% select(model, series, x))
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
      fill = guide_legend(order = 1, ncol = 1),
      colour = guide_legend(order = 2, ncol = 1),
      shape = guide_legend(order = 2, ncol = 1)
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
# 5. Panel B: Own choice vs predictions for others
#=================================

panel_b <- create_slope_plot(
  panel_b_data,
  plot_title = "Panel B: Own choice vs predictions for others",
  y_label = "Continue-minus-avoid\n\u0394 choice margin per unit\nof steering dose (nats)",
  dodge = 0.6
) +
  scale_colour_manual(values = who_colours, labels = who_labels, name = NULL, drop = FALSE) +
  scale_shape_manual(values = who_shapes, labels = who_labels, name = NULL, drop = FALSE)

#=================================
# 6. Panel C: Place vs thoughts vs feelings
#=================================

panel_c <- create_slope_plot(
  panel_c_data,
  plot_title = "Panel C: Place vs thoughts vs feelings",
  y_label = "\u0394 choice margin per unit\nof steering dose (nats)",
  dodge = 0.6
) +
  scale_colour_manual(values = answer_colours, labels = answer_labels, name = NULL, drop = FALSE) +
  scale_shape_manual(values = answer_shapes, labels = answer_labels, name = NULL, drop = FALSE)

#=================================
# 7. Combine and save figure
#=================================

fig <- (panel_a / panel_b / panel_c) +
  plot_layout(guides = "collect") &
  theme(legend.position = "bottom")

ggsave(
  "figures/figureA13.png",
  fig,
  width = 12,
  height = 11.5,
  dpi = 300,
  bg = "white"
)
