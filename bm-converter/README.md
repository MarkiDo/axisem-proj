# activate venv once
source .venv/bin/activate

# single file
bm-convert Model_1.txt

# batch, write to a specific directory
bm-convert Model_*.txt -o /path/to/output/

# override name in header, mark anelastic
bm-convert Model_1.txt --name mars_model_1 --anelastic
