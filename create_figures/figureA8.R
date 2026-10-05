##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A8: Injected span
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
      legend.text = element_text(size = 10.5),
      legend.title = element_text(size = 11, face = "bold"),
      plot.background = element_rect(fill = "white", colour = NA),
      panel.background = element_rect(fill = "white", colour = NA)
    )
)

model_order <- c("OLMo-2-32B", "Qwen2.5-32B", "Qwen3-14B", "Qwen3-32B", "Mistral-24B", "Gemma-3-27B", "Llama-3.1-8B")
span_order <- c("bare", "sentence", "passage")
span_colours <- setNames(hcl.colors(5, palette = "Heat")[c(5, 3, 1)], span_order)

#=================================
# 2. Data loading and preparation
#=================================

data <- read_csv(
  "experiment_results_csv/figureA8.csv",
  show_col_types = FALSE
) %>%
  mutate(
    model = factor(model, levels = model_order),
    span = factor(span, levels = span_order),
    floor_status = factor(
      if_else(clears_random_floor == 1, "Clears random-direction floor", "Does not clear floor"),
      levels = c("Clears random-direction floor", "Does not clear floor")
    )
  )

stopifnot(
  nrow(data) == 21,
  n_distinct(data$model) == 7,
  n_distinct(data$span) == 3
)

span_labels <- data %>%
  group_by(span) %>%
  summarise(mean_tokens = round(mean(steered_span_tokens)), .groups = "drop") %>%
  mutate(label = str_c(str_to_title(span), "\n(", mean_tokens, " tokens)")) %>%
  {setNames(.$label, .$span)}

panel_labels <- setNames(
  str_c("Panel ", LETTERS[1:7], ": ", model_order),
  model_order
)

#=================================
# 3. Create figure
#=================================

figureA8 <- ggplot(
  data,
  aes(x = span, y = estimate, fill = span)
) +
  geom_hline(yintercept = 0, colour = "grey75", linewidth = 0.5) +
  geom_col(width = 0.72, colour = "grey20", linewidth = 0.35) +
  geom_errorbar(
    aes(ymin = ci_low, ymax = ci_high),
    width = 0.16,
    linewidth = 0.7
  ) +
  geom_point(
    aes(shape = floor_status),
    size = 2.4,
    stroke = 0.8,
    fill = "white",
    colour = "black"
  ) +
  facet_wrap(
    ~model,
    ncol = 3,
    scales = "free_y",
    labeller = as_labeller(panel_labels)
  ) +
  scale_fill_manual(values = span_colours, guide = "none") +
  scale_shape_manual(
    values = c("Clears random-direction floor" = 21, "Does not clear floor" = 4),
    drop = FALSE
  ) +
  scale_x_discrete(labels = span_labels) +
  labs(
    x = "Injected span and mean number of injected tokens",
    y = expression(bold("Slope of "*Delta*" choice margin on steering dose (nats)")),
    shape = "Valenced direction"
  ) +
  guides(shape = guide_legend(nrow = 1))

#=================================
# 4. Save figure
#=================================

ggsave(
  "figures/figureA8.png",
  figureA8,
  width = 12,
  height = 9,
  dpi = 300,
  bg = "white"
)
