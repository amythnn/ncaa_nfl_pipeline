# NCAA → NFL Pipeline 🏈📊

## Project Overview
**NCAA → NFL Pipeline** visualizes how major college football programs (Big Ten & SEC) send players into the NFL Draft. 
Using scraped Wikipedia draft data, the project builds interactive Plotly Sankey diagrams with college colors and NFL team colors, plus hover tooltips that show each drafted player.

It demonstrates the full workflow on NCAA → NFL draft data: scraping from Wikipedia, data cleaning, aggregation into tidy CSVs, building interactive Sankey diagrams, and exporting .html visualizations.
The repo is organized for clarity and reproducibility (comments, modular scripts, saved data artifacts, and example exports).

---

## Installation

### 1. Clone the repository

git clone https://github.com/amythnn/ncaa_nfl_pipeline.git
cd ncaa_nfl_pipeline

### 2. (Optional) Create a virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

---

## Usage
Run the pipeline to scrape and build a Sankey diagram (replace with your target draft year):

python scripts/build_sankey.py \
  --year 2025 \
  --out_dir viz

Outputs will be saved in the respective folders:
- data/cfb_nfl_counts.csv — cleaned draft data
- viz/cfb_sankey_2025.html — interactive Sankey visualization
