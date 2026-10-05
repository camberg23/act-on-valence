##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A1: Five-dose text-channel curves in six other models
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
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

primary_colour <- hcl.colors(9, palette = "Heat")[4]
model_order <- c("Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B",
                 "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA1.csv",
  show_col_types = FALSE
) %>%
  mutate(model = factor(model, levels = model_order))

stopifnot(
  nrow(data) == 60,
  setequal(data$panel, c("judged_passage_valence", "unsteered_cache_margin")),
  n_distinct(data$dose) == 5,
  n_distinct(data$model) == 6,
  all(data$n_sessions == 60)
)

#=================================
# 3. Plotting function
#=================================

create_panel <- function(plot_data, plot_title, y_label, panel_letters, y_scales) {
  panel_labels <- setNames(
    str_c("Panel ", panel_letters, ": ", model_order),
    model_order
  )

  ggplot(plot_data, aes(x = dose, y = estimate, group = model)) +
    geom_hline(yintercept = 0, colour = "grey75", linewidth = 0.5) +
    geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.035, linewidth = 0.75) +
    geom_line(colour = primary_colour, linewidth = 1.15) +
    geom_point(colour = primary_colour, size = 3) +
    facet_wrap(~model, ncol = 3, scales = y_scales, labeller = as_labeller(panel_labels)) +
    scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
    labs(
      title = plot_title,
      x = "Steering dose",
      y = y_label
    )
}

#=================================
# 4. Create panels
#=================================

panel_a <- data %>%
  filter(panel == "judged_passage_valence") %>%
  create_panel(
    plot_title = "Judged passage valence",
    y_label = "Judged valence margin",
    panel_letters = LETTERS[1:6],
    y_scales = "fixed"
  )

panel_b <- data %>%
  filter(panel == "unsteered_cache_margin") %>%
  create_panel(
    plot_title = "Choice under the unsteered cache (text channel)",
    y_label = "Choice margin (nats)",
    panel_letters = LETTERS[7:12],
    y_scales = "free_y"
  )

#=================================
# 5. Combine and save figure
#=================================

figureA1 <- panel_a / panel_b

ggsave(
  "figures/figureA1.png",
  figureA1,
  width = 12,
  height = 14.5,
  dpi = 300,
  bg = "white"
)
