##########################################
# AI WELFARE PROJECT
##########################################
# Appendix Figure A1: Five-dose text-channel curves in six other models
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
    rows = [row for row in curves if row["panel"] in ('judged_passage_valence', 'unsteered_cache_margin')]
    write_csv("figureA1.csv", rows)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
