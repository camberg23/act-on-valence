##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A2: Five-dose original-cache and hidden-state curves
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import MODEL_LABELS, write_csv
import generation_data

#=================================
# 2. Data preparation
#=================================

def main():
    models = [model for model in MODEL_LABELS if model != "olmo_32b"]
    curves = generation_data.build_curves(models)
    rows = [row for row in curves if row["panel"] in ('original_cache_margin', 'original_minus_unsteered_margin')]
    write_csv("figureA2.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
