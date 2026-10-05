##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A7: Text-differenced and neutral-substrate estimates
##########################################

#=================================
# 1. Setup and configuration
#=================================

library(tidyverse)
library(ggplot2)
library(ggrepel)
library(patchwork)

# Run this script from the repository root directory.
dir.create("figures", showWarnings = FALSE)

theme_set(
  theme_minimal(base_size = 14) +
    theme(
      plot.title = element_text(hjust = 0.5, size = 15, face = "bold"),
      axis.title = element_text(size = 12.5, face = "bold"),
      axis.text = element_text(size = 11),
      axis.line = element_line(colour = "black", linewidth = 0.55),
      axis.ticks = element_line(colour = "black", linewidth = 0.55),
      panel.grid.minor = element_blank(),
      legend.position = "none",
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

model_order <- c("OLMo-2-32B", "Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B", "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")
model_colours <- setNames(hcl.colors(7, palette = "Heat"), model_order)

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA7.csv",
  show_col_types = FALSE
) %>%
  mutate(model = factor(model, levels = model_order))

stopifnot(
  nrow(data) == 14,
  n_distinct(data$model) == 7,
  n_distinct(data$panel) == 2
)

#=================================
# 3. Plotting function
#=================================

create_scatterplot <- function(plot_data, plot_title, x_label, y_label, seed) {
  axis_limits <- range(c(plot_data$x_estimate, plot_data$y_estimate, 0))
  padding <- diff(axis_limits) * 0.07
  axis_limits <- axis_limits + c(-padding, padding)

  ggplot(plot_data, aes(x = x_estimate, y = y_estimate, colour = model, label = model)) +
    geom_abline(slope = 1, intercept = 0, colour = "grey55", linetype = "dashed", linewidth = 0.75) +
    geom_hline(yintercept = 0, colour = "grey85", linewidth = 0.5) +
    geom_vline(xintercept = 0, colour = "grey85", linewidth = 0.5) +
    geom_point(size = 3.4) +
    geom_text_repel(
      seed = seed,
      size = 3.7,
      colour = "grey15",
      box.padding = 0.4,
      point.padding = 0.3,
      max.overlaps = Inf,
      show.legend = FALSE
    ) +
    scale_colour_manual(values = model_colours) +
    scale_x_continuous(limits = axis_limits) +
    scale_y_continuous(limits = axis_limits) +
    coord_equal() +
    labs(
      title = plot_title,
      x = x_label,
      y = y_label
    )
}

#=================================
# 4. Create panels
#=================================

panel_a <- data %>%
  filter(panel == "exp254_vs_exp255_neutral") %>%
  create_scatterplot(
    plot_title = "Panel A: Estimates from separate experiments",
    x_label = expression(bold("Steering-generated text: slope of "*Delta*" choice margin (nats)")),
    y_label = expression(bold("Fixed unsteered text: slope of "*Delta*" choice margin (nats)")),
    seed = 254
  )

panel_b <- data %>%
  filter(panel == "exp255_steered_vs_neutral") %>%
  create_scatterplot(
    plot_title = "Panel B: Estimates from matched sessions",
    x_label = expression(bold("Steering-generated text: slope of "*Delta*" choice margin (nats)")),
    y_label = expression(bold("Fixed unsteered text: slope of "*Delta*" choice margin (nats)")),
    seed = 255
  )

#=================================
# 5. Combine and save figure
#=================================

figureA7 <- panel_a + panel_b

ggsave(
  "figures/figureA7.png",
  figureA7,
  width = 12,
  height = 6.5,
  dpi = 300,
  bg = "white"
)
