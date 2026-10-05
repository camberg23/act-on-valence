##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A3: Fixed-text injection in the other models
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import MODEL_LABELS, write_csv
import fixed_text_data

#=================================
# 2. Data preparation
#=================================

def main():
    models = [model for model in MODEL_LABELS if model != "olmo_32b"]
    rows = fixed_text_data.build_curves(models)
    write_csv("figureA3.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
