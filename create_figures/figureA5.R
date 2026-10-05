##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A5: Continue and avoid prompts
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

heat_colours <- hcl.colors(9, palette = "Heat")
series_colours <- c(
  "valence_continue" = heat_colours[4],
  "valence_avoid" = heat_colours[7],
  "random_continue" = "grey70",
  "random_avoid" = "grey45"
)
series_linetypes <- c(
  "valence_continue" = "solid",
  "valence_avoid" = "longdash",
  "random_continue" = "solid",
  "random_avoid" = "longdash"
)
series_labels <- c(
  "valence_continue" = "Valenced direction, continue prompt",
  "valence_avoid" = "Valenced direction, avoid prompt",
  "random_continue" = "Random directions, continue prompt",
  "random_avoid" = "Random directions, avoid prompt"
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
model_order <- unname(model_labels)

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA5.csv",
  show_col_types = FALSE
) %>%
  mutate(
    model = recode(member, !!!model_labels),
    model = factor(model, levels = model_order),
    direction_type = if_else(direction == "valence", "valence", "random"),
    series = str_c(direction_type, prompt, sep = "_"),
    series = factor(series, levels = names(series_colours))
  )

stopifnot(
  nrow(data) == 1750,
  n_distinct(data$model) == 7,
  setequal(data$prompt, c("continue", "avoid")),
  setequal(data$dose, c(-1, -0.5, 0, 0.5, 1)),
  all(count(data, model, prompt, direction)$n == 5),
  all(!is.na(filter(data, direction == "valence")$ci_lo)),
  all(!is.na(filter(data, direction == "valence")$ci_hi))
)

random_data <- data %>%
  filter(direction_type == "random")

valence_data <- data %>%
  filter(direction_type == "valence")

panel_labels <- setNames(
  str_c("Panel ", LETTERS[1:7], ": ", model_order),
  model_order
)

#=================================
# 3. Create figure
#=================================

figureA5 <- ggplot(
  data,
  aes(x = dose, y = mean_delta_margin, colour = series, linetype = series)
) +
  geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
  geom_line(
    data = random_data,
    aes(group = interaction(prompt, direction)),
    linewidth = 0.5,
    alpha = 0.65
  ) +
  geom_errorbar(
    data = valence_data,
    aes(ymin = ci_lo, ymax = ci_hi, group = prompt),
    width = 0.04,
    linewidth = 0.75
  ) +
  geom_line(
    data = valence_data,
    aes(group = prompt),
    linewidth = 1.15
  ) +
  geom_point(
    data = valence_data,
    aes(group = prompt),
    size = 3
  ) +
  facet_wrap(
    ~model,
    ncol = 4,
    scales = "free_y",
    labeller = as_labeller(panel_labels)
  ) +
  scale_colour_manual(values = series_colours, labels = series_labels) +
  scale_linetype_manual(values = series_linetypes, labels = series_labels) +
  scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
  labs(
    x = "Steering dose",
    y = expression(bold(Delta*" choice margin from dose 0 (nats)")),
    colour = NULL,
    linetype = NULL
  ) +
  guides(
    colour = guide_legend(nrow = 1),
    linetype = guide_legend(nrow = 1)
  )

#=================================
# 4. Save figure
#=================================

ggsave(
  "figures/figureA5.png",
  figureA5,
  width = 14,
  height = 8.5,
  dpi = 300,
  bg = "white"
)
