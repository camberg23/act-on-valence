##########################################
# AI WELFARE PROJECT
##########################################
# Figure 5: OLMo removal and self-administration
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
  "imposed" = primary_colour,
  "random" = "grey35"
)
series_linetypes <- c("imposed" = "solid", "random" = "solid")
series_shapes <- c("imposed" = 16, "random" = 16)
panel_a_labels <- c(
  "imposed" = "Imposed valenced direction",
  "random" = "Imposed random direction"
)
panel_b_labels <- c(
  "imposed" = "Demonstrated valenced direction",
  "random" = "Demonstrated random direction"
)

#=================================
# 2. Data loading
#=================================

main_data <- read_csv(
  "experiment_results_csv/figure5.csv",
  show_col_types = FALSE
)

stopifnot(
  nrow(main_data) == 18,
  all(main_data$exposure_prompt == "zone"),
  all(main_data$n_conversations == 200),
  identical(sort(unique(main_data$panel)), c("removal", "self_administration"))
)

#=================================
# 3. Plotting function
#=================================

create_dose_plot <- function(plot_data, plot_title, y_label, legend_labels) {
  summary_lines <- plot_data %>%
    mutate(series = factor(series, levels = c("imposed", "random")))

  ggplot() +
    geom_hline(yintercept = 0, colour = "grey80", linewidth = 0.5) +
    geom_errorbar(
      data = summary_lines,
      aes(x = plot_dose, ymin = ci_low, ymax = ci_high, colour = series),
      width = 0.05,
      linewidth = 0.75,
      position = position_dodge(width = 0.04)
    ) +
    geom_line(
      data = summary_lines,
      aes(x = plot_dose, y = rate, colour = series, linetype = series, group = series),
      linewidth = 1.15
    ) +
    geom_point(
      data = summary_lines,
      aes(x = plot_dose, y = rate, colour = series, shape = series),
      size = 3
    ) +
    scale_colour_manual(
      values = series_colours,
      labels = legend_labels,
      drop = TRUE
    ) +
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
    ) +
    guides(
      colour = guide_legend(
        nrow = 1,
        ncol = 2,
        byrow = TRUE,
        override.aes = list(
          linetype = unname(series_linetypes),
          shape = unname(series_shapes)
        )
      )
    )
}

#=================================
# 4. Panel A: Removal 
#=================================

panel_a <- main_data %>%
  filter(panel == "removal") %>%
  create_dose_plot(
    plot_title = "Panel A: Removal",
    y_label = "Share of opportunities",
    legend_labels = panel_a_labels
  ) +
  scale_y_continuous(
    breaks = seq(0, 0.4, by = 0.1),
    labels = scales::label_percent(accuracy = 1),
    limits = c(0, 0.44),
    expand = expansion(mult = c(0, 0.02))
  )

#=================================
# 5. Panel B: Self-administration at the first offer
#=================================

panel_b <- main_data %>%
  filter(panel == "self_administration") %>%
  create_dose_plot(
    plot_title = "Panel B: Self-administration",
    y_label = "Share of opportunities",
    legend_labels = panel_b_labels
  ) +
  scale_y_continuous(
    breaks = seq(0, 0.4, by = 0.1),
    labels = scales::label_percent(accuracy = 1),
    limits = c(0, 0.44),
    expand = expansion(mult = c(0, 0.02))
  )

#=================================
# 6. Combine and save figure
#=================================

figure5 <- (panel_a + panel_b) +
  plot_layout()

ggsave(
  "figures/figure5.png",
  figure5,
  width = 12,
  height = 5.5,
  dpi = 300,
  bg = "white"
)
