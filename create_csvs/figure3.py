##########################################
# AI WELFARE PROJECT
##########################################
# Figure 3: Five-dose text and hidden-state effects on choice
##########################################

#=================================
# 1. Setup and configuration
#=================================

from common import write_csv
import generation_data
import fixed_text_data

#=================================
# 2. Data preparation
#=================================

def main():
    generated = generation_data.build_curves(["olmo_32b"])
    fixed = fixed_text_data.build_curves(["olmo_32b"])
    write_csv("figure3.csv", generated + fixed)

#=================================
# 3. Save figure data
#=================================

if __name__ == "__main__":
    main()
