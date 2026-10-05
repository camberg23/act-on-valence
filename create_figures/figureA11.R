##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A11: Addressing and storage halves of the cache
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
      axis.title = element_text(size = 12.5, face = "bold"),
      axis.text = element_text(size = 11),
      axis.line = element_line(colour = "black", linewidth = 0.55),
      axis.ticks = element_line(colour = "black", linewidth = 0.55),
      panel.grid.minor = element_blank(),
      panel.grid.major.y = element_blank(),
      legend.position = "bottom",
      legend.title = element_blank(),
      legend.text = element_text(size = 11),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

heat_colours <- hcl.colors(9, palette = "Heat")
channel_colours <- c("addressing_keys" = heat_colours[2], "storage_values" = heat_colours[5])
channel_labels <- c("addressing_keys" = "Steered keys, unsteered values", "storage_values" = "Unsteered keys, steered values")
model_order <- c("OLMo-2-32B", "Qwen3-14B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA11.csv",
  show_col_types = FALSE
) %>%
  filter(n_exposures == 1, strength == 1) %>%
  mutate(
    model = factor(model, levels = model_order),
    channel = factor(channel, levels = names(channel_colours))
  )

stopifnot(
  nrow(data) == 6,
  n_distinct(data$model) == 3,
  n_distinct(data$channel) == 2
)

#=================================
# 3. Create figure
#=================================

bar_position <- position_dodge(width = 0.82)

figureA11 <- ggplot(
  data,
  aes(x = model, y = share_of_full_cache_slope, fill = channel)
) +
  geom_hline(yintercept = 0, colour = "grey75", linewidth = 0.55) +
  geom_hline(yintercept = 1, colour = "grey60", linetype = "dashed", linewidth = 0.55) +
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
  scale_fill_manual(values = channel_colours, labels = channel_labels) +
  labs(
    x = NULL,
    y = "Share of full-cache slope",
    fill = NULL
  )

#=================================
# 4. Save figure
#=================================

ggsave(
  "figures/figureA11.png",
  figureA11,
  width = 8,
  height = 5.5,
  dpi = 300,
  bg = "white"
)
