##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A10: Concentration and strength of injection
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
condition_colours <- c(
  "six_sightings_one_sixth_strength" = heat_colours[5],
  "one_sighting_full_strength" = heat_colours[2]
)
condition_labels <- c(
  "six_sightings_one_sixth_strength" = "Six sightings at one-sixth strength",
  "one_sighting_full_strength" = "One sighting at full strength"
)
model_order <- c("OLMo-2-32B", "Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B", "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")
ladder_model_order <- c("OLMo-2-32B", "Qwen3-14B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA10.csv",
  show_col_types = FALSE
)

stopifnot(
  nrow(data) == 38,
  setequal(data$panel, c("constant_total_comparison", "six_sighting_strength_ladder"))
)

panel_a_data <- data %>%
  filter(panel == "constant_total_comparison") %>%
  mutate(
    model = factor(model, levels = model_order),
    condition = factor(condition, levels = names(condition_colours))
  )

panel_b_data <- data %>%
  filter(panel == "six_sighting_strength_ladder") %>%
  mutate(model = factor(model, levels = ladder_model_order))

#=================================
# 3. Panel A: Concentrated versus diffuse injection
#=================================

bar_position <- position_dodge(width = 0.82)

panel_a <- ggplot(
  panel_a_data,
  aes(x = model, y = estimate, fill = condition)
) +
  geom_hline(yintercept = 0, colour = "grey70", linewidth = 0.55) +
  geom_col(
    position = bar_position,
    width = 0.75,
    colour = "grey20",
    linewidth = 0.35
  ) +
  geom_errorbar(
    aes(ymin = ci_low, ymax = ci_high),
    position = bar_position,
    width = 0.12,
    linewidth = 0.8
  ) +
  scale_fill_manual(values = condition_colours, labels = condition_labels) +
  labs(
    title = "Panel A: Effect of concentrated vs diffuse injection",
    x = NULL,
    y = expression(bold("Slope of "*Delta*" choice margin on steering dose (nats)")),
    fill = NULL
  ) +
  theme(axis.text.x = element_text(angle = 35, hjust = 1))

#=================================
# 4. Panel B: Per-sighting strength
#=================================

strength_breaks <- c(1 / 32, 1 / 24, 1 / 16, 1 / 12, 1 / 8, 1 / 6, 1 / sqrt(6), 1)
strength_labels <- c("1/32", "1/24", "1/16", "1/12", "1/8", "1/6", "1/sqrt(6)", "1")

panel_b <- ggplot(
  panel_b_data,
  aes(x = strength, y = estimate, group = model)
) +
  geom_hline(yintercept = 0, colour = "grey75", linewidth = 0.5) +
  geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.03, linewidth = 0.75) +
  geom_line(colour = heat_colours[4], linewidth = 1.15) +
  geom_point(colour = heat_colours[4], size = 3) +
  facet_wrap(~model, nrow = 1, scales = "free_y") +
  scale_x_log10(breaks = strength_breaks, labels = strength_labels) +
  labs(
    title = "Panel B: Effect of varying per-sighting strength",
    x = "Steering-vector norm at each sighting (relative to full strength)",
    y = expression(bold("Slope of "*Delta*" choice margin on steering dose (nats)"))
  ) +
  theme(axis.text.x = element_text(angle = 35, hjust = 1))

#=================================
# 5. Combine and save figure
#=================================

figureA10 <- panel_a / panel_b +
  plot_layout(heights = c(1.15, 1))

ggsave(
  "figures/figureA10.png",
  figureA10,
  width = 12,
  height = 10,
  dpi = 300,
  bg = "white"
)
