##########################################
# AI WELFARE PROJECT
##########################################
# Figure 3: Five-dose text and hidden-state effects on choice
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
      legend.position = "bottom",
      legend.title = element_blank(),
      legend.text = element_text(size = 11),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

primary_colour <- hcl.colors(9, palette = "Heat")[4]
series_colours <- c(
  "valenced" = primary_colour,
  "text_channel" = hcl.colors(9, palette = "Heat")[5],
  "random_mean" = "grey35"
)
series_linetypes <- c("valenced" = "solid", "text_channel" = "22", "random_mean" = "solid")
series_shapes <- c("valenced" = 16, "text_channel" = 17, "random_mean" = 16)
series_labels <- c(
  "valenced" = "Valenced direction",
  "text_channel" = "Unsteered cache (text channel)",
  "random_mean" = "Mean random direction"
)
panel_b_labels <- c(
  "valenced" = "Original cache",
  "text_channel" = "Unsteered cache",
  "random_mean" = "Random mean"
)
difference_labels <- c(
  "valenced" = "Valenced direction",
  "random_mean" = "Mean random direction"
)

#=================================
# 2. Data loading
#=================================

data <- read_csv("experiment_results_csv/figure3.csv", show_col_types = FALSE)
main_data <- filter(data, panel != "steered_minus_clean_margin")
fixed_text_data <- filter(data, panel == "steered_minus_clean_margin")

stopifnot(
  nrow(main_data) == 110,
  nrow(fixed_text_data) == 130,
  n_distinct(main_data$direction_index[main_data$series == "random_direction"]) == 8,
  n_distinct(fixed_text_data$direction_index[fixed_text_data$series == "random_direction"]) == 24
)

#=================================
# 3. Plotting functions
#=================================

create_valenced_plot <- function(plot_data, plot_title, y_label) {
  plot_data <- plot_data %>%
    mutate(series = "valenced")

  ggplot(
    plot_data,
    aes(x = dose, y = estimate, colour = series, group = model)
  ) +
    geom_hline(yintercept = 0, colour = "grey75", linewidth = 0.5) +
    geom_errorbar(aes(ymin = ci_low, ymax = ci_high), width = 0.05, linewidth = 0.75) +
    geom_line(linewidth = 1.15) +
    geom_point(size = 3) +
    scale_colour_manual(
      values = series_colours["valenced"],
      labels = difference_labels["valenced"]
    ) +
    scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
    labs(
      title = plot_title,
      x = "Steering dose",
      y = y_label
    )
}

create_random_comparison_plot <- function(plot_data, plot_title, y_label) {
  comparison_labels <- c("valenced" = "Valenced direction",
                         "random_mean" = "Mean random direction")
  random_directions <- plot_data %>%
    filter(series == "random_direction")

  summary_lines <- plot_data %>%
    mutate(ci_low = if_else(dose == 0, NA_real_, ci_low),
           ci_high = if_else(dose == 0, NA_real_, ci_high)) %>%
    filter(series %in% c("valenced", "random_mean")) %>%
    mutate(series = factor(series, levels = c("valenced", "text_channel", "random_mean")))

  ggplot() +
    geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
    geom_line(
      data = random_directions,
      aes(x = dose, y = estimate, group = direction_index),
      colour = "grey75",
      linewidth = 0.45,
      alpha = 0.65
    ) +
    geom_errorbar(
      data = summary_lines %>% filter(!is.na(ci_low)),
      aes(x = dose, ymin = ci_low, ymax = ci_high, colour = series),
      width = 0.05,
      linewidth = 0.75
    ) +
    geom_line(
      data = summary_lines,
      aes(x = dose, y = estimate, colour = series, linetype = series, group = series),
      linewidth = 1.15
    ) +
    geom_point(
      data = summary_lines,
      aes(x = dose, y = estimate, colour = series, shape = series),
      size = 3
    ) +
    scale_colour_manual(values = series_colours, labels = comparison_labels, drop = TRUE) +
    scale_linetype_manual(values = series_linetypes, guide = "none") +
    scale_shape_manual(values = series_shapes, guide = "none") +
    scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
    labs(
      title = plot_title,
      x = "Steering dose",
      y = y_label,
      colour = NULL,
      linetype = NULL,
      shape = NULL
    )
}

#=================================
# 4. Panel A: Judged passage valence
#=================================

panel_a <- main_data %>%
  filter(panel == "judged_passage_valence") %>%
  create_valenced_plot(
    plot_title = "Panel A: Judged passage valence",
    y_label = "Judged valence margin"
  )

#=================================
# 5. Panel B: Original and unsteered caches
#=================================

panel_b_random_directions <- main_data %>%
  filter(panel == "original_cache_margin", series == "random_direction")

panel_b_summary <- bind_rows(
  main_data %>%
    filter(panel == "original_cache_margin", series %in% c("valenced", "random_mean")),
  main_data %>%
    filter(panel == "unsteered_cache_margin", series == "valenced") %>%
    mutate(series = "text_channel")
) %>%
  mutate(series = factor(series, levels = c("valenced", "text_channel", "random_mean")))

panel_b <- ggplot() +
  geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
  geom_line(
    data = panel_b_random_directions,
    aes(x = dose, y = estimate, group = direction_index),
    colour = "grey75",
    linewidth = 0.45,
    alpha = 0.65
  ) +
  geom_errorbar(
    data = panel_b_summary,
    aes(x = dose, ymin = ci_low, ymax = ci_high, colour = series),
    width = 0.05,
    linewidth = 0.75,
    position = position_dodge(width = 0.04)
  ) +
  geom_line(
    data = panel_b_summary,
    aes(x = dose, y = estimate, colour = series, linetype = series, group = series),
    linewidth = 1.15
  ) +
  geom_point(
    data = panel_b_summary,
    aes(x = dose, y = estimate, colour = series, shape = series),
    size = 3
  ) +
    scale_colour_manual(
      values = series_colours,
      labels = panel_b_labels,
    drop = FALSE,
    guide = guide_legend(
      override.aes = list(
        linetype = unname(series_linetypes),
        shape = unname(series_shapes)
      )
    )
  ) +
  scale_linetype_manual(values = series_linetypes, guide = "none") +
  scale_shape_manual(values = series_shapes, guide = "none") +
  scale_x_continuous(breaks = c(-1, -0.5, 0, 0.5, 1)) +
  labs(
    title = "Panel B: Choice margins under original and\nunsteered caches",
    x = "Steering dose",
    y = "Choice margin (nats)",
    colour = NULL,
    linetype = NULL,
    shape = NULL
  ) +
  guides(
    colour = guide_legend(
      nrow = 1,
      ncol = 3,
      byrow = TRUE,
      override.aes = list(
        linetype = unname(series_linetypes),
        shape = unname(series_shapes)
      )
    )
  )

#=================================
# 6. Panels C and D: Hidden-state effects
#=================================

panel_c <- main_data %>%
  filter(panel == "original_minus_unsteered_margin") %>%
  create_random_comparison_plot(
    plot_title = "Panel C: Hidden-state channel",
    y_label = expression(bold(Delta*" choice margin (nats)"))
  ) +
  scale_y_continuous(
    breaks = seq(-1, 1.5, by = 0.5),
    limits = c(-1, 1.5)
  ) +
  theme(legend.position = "bottom")

panel_d <- fixed_text_data %>%
  create_random_comparison_plot(
    plot_title = "Panel D: Hidden-state channel\nunder fixed text",
    y_label = expression(bold(Delta*" choice margin (nats)"))
  ) +
  scale_y_continuous(
    breaks = seq(-1, 1.5, by = 0.5),
    limits = c(-1, 1.5)
  ) +
  theme(legend.position = "bottom")

#=================================
# 7. Combine and save figure
#=================================

figure3 <- (panel_a + panel_b) /
  (panel_c + panel_d) +
  plot_layout()

ggsave(
  "figures/figure3.png",
  figure3,
  width = 12,
  height = 9.5,
  dpi = 300,
  bg = "white"
)
