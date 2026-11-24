##########################################
# AI WELFARE PROJECT
##########################################
# Figure A6: continue-minus-avoid in the seven fixed-text models
# Run from the repository root: Rscript create_figures/figureA6.R
##########################################

#=================================
# 1. Setup and configuration
#=================================

library(tidyverse)
library(ggplot2)

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
      legend.key.width = unit(2.2, "lines"),
      legend.key.height = unit(1.9, "lines"),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

heat_colours <- hcl.colors(9, palette = "Heat")
series_levels <- c(
  "valenced_go_minus_avoid", "valenced_continue",
  "random_mean_go_minus_avoid", "random_go_minus_avoid"
)
series_colours <- c(
  "valenced_go_minus_avoid" = heat_colours[4],
  "valenced_continue" = heat_colours[5],
  "random_mean_go_minus_avoid" = "grey35",
  "random_go_minus_avoid" = "grey75"
)
series_linetypes <- c(
  "valenced_go_minus_avoid" = "solid",
  "valenced_continue" = "22",
  "random_mean_go_minus_avoid" = "solid",
  "random_go_minus_avoid" = "solid"
)
series_labels <- c(
  "valenced_go_minus_avoid" = "Valenced direction,\nContinue-minus-avoid",
  "valenced_continue" = "Valenced direction,\ncontinue question only",
  "random_mean_go_minus_avoid" = "Mean random direction,\nContinue-minus-avoid",
  "random_go_minus_avoid" = "Individual random directions,\nContinue-minus-avoid"
)
model_order <- c("OLMo-2-32B", "Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B", "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")

#=================================
# 2. Data loading and preparation
#=================================

# The avoid rows of figureA6.csv are not drawn here (continue-minus-avoid = (continue - avoid) / 2).
data <- read_csv("experiment_results_csv/figureA6.csv", show_col_types = FALSE) %>%
  filter(question == "go_minus_avoid" | (direction_type == "valenced" & question == "continue")) %>%
  mutate(
    model = factor(model, levels = model_order),
    series = factor(str_c(direction_type, question, sep = "_"), levels = series_levels)
  )

stopifnot(
  n_distinct(data$model) == 7, !anyNA(data$model), !anyNA(data$series),
  setequal(data$dose, c(-1, -0.5, 0, 0.5, 1)),
  all(count(filter(data, direction_type == "random"), model)$n == 24 * 5),
  all(count(filter(data, direction_type == "random_mean"), model)$n == 5),
  all(!is.na(filter(data, direction_type %in% c("valenced", "random_mean"))$ci_low))
)

random_data <- filter(data, direction_type == "random")
summary_data <- filter(data, direction_type %in% c("valenced", "random_mean"))

panel_labels <- setNames(str_c("Panel ", LETTERS[1:7], ": ", model_order), model_order)

#=================================
# 3. Create figure
#=================================

figA <- ggplot(data, aes(x = dose, y = mean_delta_margin, colour = series, linetype = series)) +
  geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
  geom_line(data = random_data, aes(group = direction), linewidth = 0.45, alpha = 0.65) +
  geom_errorbar(
    data = summary_data,
    aes(ymin = ci_low, ymax = ci_high, group = series),
    width = 0.05,
    linewidth = 0.75,
    linetype = "solid"
  ) +
  geom_line(data = summary_data, aes(group = series), linewidth = 1.15) +
  geom_point(data = summary_data, aes(group = series), size = 3) +
  facet_wrap(
    ~model,
    ncol = 4,
    scales = "free_y",
    labeller = as_labeller(panel_labels)
  ) +
  scale_colour_manual(values = series_colours, labels = series_labels, drop = FALSE) +
  scale_linetype_manual(values = series_linetypes, guide = "none") +
  scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.05))) +
  labs(
    x = "Steering dose",
    # Plain text preserves the space after Delta when saving with ragg.
    y = "\u0394 choice margin (nats)",
    colour = NULL,
    linetype = NULL
  ) +
  guides(
    colour = guide_legend(
      nrow = 1,
      override.aes = list(
        linetype = unname(series_linetypes),
        linewidth = c(1.15, 1.15, 1.15, 0.45),
        size = c(3, 3, 3, 0)
      )
    )
  )

#=================================
# 4. Save figure
#=================================

ggsave(
  "figures/figureA6.png",
  figA,
  width = 12,
  height = 7.5,
  dpi = 300,
  bg = "white"
)
