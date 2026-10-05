##########################################
# AI WELFARE PROJECT
##########################################
# Figure 4: Emergence across the OLMo training lineage
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

heat_colours <- hcl.colors(9, palette = "Heat")

#=================================
# 2. Data loading
#=================================

data <- read_csv(
  "experiment_results_csv/figure4.csv",
  show_col_types = FALSE
)

stopifnot(
  nrow(data) == 8,
  setequal(data$stage, c("base", "sft", "dpo", "instruct")),
  setequal(data$channel, c("hidden_state", "text"))
)

#=================================
# 3. Data preparation
#=================================

stage_labels <- c(
  "base" = "Base",
  "sft" = "SFT",
  "dpo" = "DPO",
  "instruct" = "Instruct"
)

data <- data %>%
  mutate(stage = factor(stage, levels = c("base", "sft", "dpo", "instruct")))

hidden_data <- data %>%
  filter(channel == "hidden_state")

text_data <- data %>%
  filter(channel == "text")

#=================================
# 4. Panel A: Hidden-state channel
#=================================

panel_a <- ggplot(
  hidden_data,
  aes(x = stage, y = estimate, colour = model, group = model)
) +
  geom_hline(yintercept = 0, colour = "grey75", linewidth = 0.5) +
  geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.08, linewidth = 0.75) +
  geom_line(linewidth = 1.15) +
  geom_point(size = 3) +
  scale_colour_manual(values = heat_colours[3], guide = "none") +
  scale_x_discrete(labels = stage_labels) +
  scale_y_continuous(limits = c(-0.2, 1.55), breaks = seq(0, 1.5, by = 0.5)) +
  labs(
    title = "Panel A: Hidden-state channel",
    x = "Training stage",
    y = expression(bold(Delta*" choice margin per unit of steering dose (nats)"))
  )

#=================================
# 5. Panel B: Text channel
#=================================

panel_b <- ggplot(
  text_data,
  aes(x = stage, y = estimate, colour = model, group = model)
) +
  geom_hline(yintercept = 0, colour = "grey75", linewidth = 0.5) +
  geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.08, linewidth = 0.75) +
  geom_line(linewidth = 1.15) +
  geom_point(size = 3) +
  scale_colour_manual(values = heat_colours[5], guide = "none") +
  scale_x_discrete(labels = stage_labels) +
  scale_y_continuous(limits = c(-0.2, 1.55), breaks = seq(0, 1.5, by = 0.5)) +
  labs(
    title = "Panel B: Visible text channel",
    x = "Training stage",
    y = expression(bold(Delta*" choice margin per unit of steering dose (nats)"))
  )

#=================================
# 6. Combine and save figure
#=================================

figure4 <- panel_a + panel_b +
  plot_layout(ncol = 2)

ggsave(
  "figures/figure4.png",
  figure4,
  width = 10,
  height = 5,
  dpi = 300,
  bg = "white"
)
