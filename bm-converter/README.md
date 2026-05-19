# activate venv once
source .venv/bin/activate

# single file (auto-detects Mars radius from max depth)
bm-convert Model_1.txt

# batch, write to a specific directory
bm-convert Model_*.txt -o /path/to/output/

# override name in header, force planet radius, mark anelastic
bm-convert Model_1.txt --name mars_model_1 --planet-radius 3389.5 --anelastic
