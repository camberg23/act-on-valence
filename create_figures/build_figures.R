##########################################
# AI WELFARE PROJECT
##########################################
# Build all empirical paper figures
##########################################

#=================================
# 1. Setup and configuration
#=================================

# Run this script from the repository root directory.

figure_names <- c(paste0("figure", 3:5), paste0("figureA", 1:14))

#=================================
# 2. Create figures
#=================================

for (name in figure_names) {
  source(file.path("create_figures", paste0(name, ".R")), local = new.env())
}
message("Figures created in figures/.")
