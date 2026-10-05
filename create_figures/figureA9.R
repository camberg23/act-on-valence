##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A9: Effect of the number of exposures
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
series_colours <- c("valenced" = primary_colour, "largest_random_direction" = "grey45")
series_labels <- c("valenced" = "Valenced direction", "largest_random_direction" = "Largest random-direction slope")
model_order <- c("OLMo-2-32B", "Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B", "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA9.csv",
  show_col_types = FALSE
) %>%
  mutate(
    model = factor(model, levels = model_order),
    series = factor(series, levels = c("valenced", "largest_random_direction"))
  )

stopifnot(
  nrow(data) == 56,
  n_distinct(data$model) == 7,
  setequal(data$n_exposures, c(1, 2, 3, 6))
)

valenced_data <- data %>%
  filter(series == "valenced")

panel_labels <- setNames(
  str_c("Panel ", LETTERS[1:7], ": ", model_order),
  model_order
)

#=================================
# 3. Create figure
#=================================

figureA9 <- ggplot(
  data,
  aes(x = n_exposures, y = estimate, colour = series, group = series)
) +
  geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
  geom_errorbar(
    data = valenced_data,
    aes(ymin = ci_low, ymax = ci_high),
    width = 0.12,
    linewidth = 0.75
  ) +
  geom_line(linewidth = 1.15) +
  geom_point(size = 3) +
  facet_wrap(
    ~model,
    ncol = 4,
    scales = "free_y",
    labeller = as_labeller(panel_labels)
  ) +
  scale_colour_manual(values = series_colours, labels = series_labels) +
  scale_x_continuous(breaks = c(1, 2, 3, 6)) +
  labs(
    x = "Number of exposures to each zone",
    y = expression(bold("Slope of "*Delta*" choice margin on steering dose (nats)")),
    colour = NULL
  )

#=================================
# 4. Save figure
#=================================

ggsave(
  "figures/figureA9.png",
  figureA9,
  width = 13,
  height = 7.5,
  dpi = 300,
  bg = "white"
)
