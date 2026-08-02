# Walkthrough: bm-converter → AxiSEM → Instaseis

This describes the full pipeline used in this repo: convert a planetary
interior model to AxiSEM's `.bm` format, mesh + solve it in AxiSEM to build
a set of Green's function wavefields, repack those into an Instaseis
database, and query that database for synthetic seismograms.

```
bm-converter/mars_1/Model_N.txt
        │  bm-convert
        ▼
bm-converter/output/Model_N.bm  ──copy──►  axisem/MESHER/Model_N.bm
                                                    │  MESHER (xmesh)
                                                    ▼
                                     axisem/SOLVER/MESHES/<mesh_name>
                                                    │  SOLVER (axisem, PZ+PX)
                                                    ▼
                                     axisem/SOLVER/<run_name>/{PZ,PX}/Data/*.nc4
                                                    │  repack_db.py
                                                    ▼
                                          axisem/SOLVER/mars/{PZ,PX}/Data/*.nc4
                                                    │  instaseis.open_db()
                                                    ▼
                                          instaseis/main.py  →  seismograms
```

The repo is currently mid-pipeline for `Model_1`: `axisem/MESHER/Model_1.bm`
is already the converted output, and `axisem/SOLVER/inparam_basic` already
points `MESHNAME` at `model_1_v1`. The steps below reproduce that from
scratch and show how to repeat it for another model (`Model_2`, …).

Every command block below is exact and chains into the next — run them in
order from the repo root (`axisem-proj/`) and each `cd` picks up where the
previous block left off.

## Prerequisites (one-time)

- Fortran/C toolchain + MPI + NetCDF (already installed here via Homebrew:
  `gfortran`, `mpif90`, NetCDF). AxiSEM is already compiled
  (`axisem/MESHER/xmesh`, `axisem/SOLVER/axisem` exist).
- A conda env for the Python side:
  ```bash
  conda activate instaseis
  pip install instaseis obspy matplotlib          # if not already installed
  pip install click netCDF4 scipy numpy           # needed by the DB repacker
  ```
- bm-converter installed in its own venv:
  ```bash
  cd bm-converter
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
  ```

## Part 1 — bm-converter: build the `.bm` model

`bm-converter` turns a `Model_N.txt` layer table (depth, Vp, Vs, density, …)
into an AxiSEM `.bm` file (radius-from-center, SI units, deepest layer
first).

```bash
cd bm-converter
source .venv/bin/activate
bm-convert mars_1/Model_1.txt -o output/
```

This produces `bm-converter/output/Model_1.bm`. Useful flags:
- `--name <NAME>` — override the `NAME` header field (ignored for batch runs)
- `--planet-radius <KM>` — force the planet radius instead of inferring it
  from the last depth row (Mars ≈ 3389.5 km)
- `--anelastic`, `--anisotropic` — set those header flags to `T`
- to convert all models at once instead: `bm-convert mars_1/Model_*.txt -o output/`

Copy the model into AxiSEM's mesher directory, then return to the repo root:

```bash
cp output/Model_1.bm ../axisem/MESHER/
deactivate
cd ..
```

## Part 2 — AxiSEM: mesh, solve, and build the Instaseis database

### 2.1 Mesher

Edit `axisem/MESHER/inparam_mesh` (already set up for `Model_1.bm`):

```
BACKGROUND_MODEL    external
EXT_MODEL           Model_1.bm
DOMINANT_PERIOD     1.0        # shortest period you want resolved, in seconds
NTHETA_SLICES       2          # NTHETA_SLICES * NRADIAL_SLICES = #cores for the solver
NRADIAL_SLICES      1
```

Run the mesher (compiles `xmesh` if needed, then runs it in the background):

```bash
cd axisem/MESHER
./submit.csh
tail -f OUTPUT          # wait for "DONE WITH MESHER"; Ctrl-C once you see it
```

Move the finished mesh into a named directory the solver can reference,
then return to the repo root:

```bash
./movemesh.csh model_1_v1
# → creates ../SOLVER/MESHES/model_1_v1
cd ../..
```

(Optional) inspect `SOLVER/MESHES/model_1_v1/*.vtk` in ParaView to sanity
check the model/discretization.

### 2.2 Solver

Edit `axisem/SOLVER/inparam_basic` (already set this way):

```
SIMULATION_TYPE   force        # required for an Instaseis (backward) database
MESHNAME          model_1_v1   # must match the movemesh.csh name above
```

Run the solver — for `force` simulations this automatically runs both the
vertical (`PZ`) and horizontal (`PX`) force sources under one run directory:

```bash
cd axisem/SOLVER
./submit.csh model_1_run
tail -f model_1_run/PZ/OUTPUT model_1_run/PX/OUTPUT   # wait for both to finish, then Ctrl-C
```

This uses `mpirun -n <NTHETA_SLICES*NRADIAL_SLICES>`, i.e. 2 cores with the
settings above. Wait for both `PZ` and `PX` to finish; each writes
`Data/axisem_output.nc4` (NetCDF is already enabled via `USE_NETCDF true` in
`make_axisem.macros` / `inparam_advanced`).

### 2.3 Repack into an Instaseis database

```bash
conda activate instaseis   # needs click, netCDF4, scipy, numpy
python3 UTILS/repack_db.py model_1_run mars --method repack
cd ../..
```

This walks `model_1_run/{PZ,PX}/Data/*.nc4` and writes the repacked,
Instaseis-ready copies to `axisem/SOLVER/mars/{PZ,PX}/Data/ordered_output.nc4`
— exactly the path `instaseis/main.py` opens. The final `cd ../..` returns
you to the repo root.

> There's also `axisem/submit.py`, which automates 2.1–2.3 end to end
> (`python submit.py <job_name> MESHER/Model_1.bm <period> --run_type bwd`,
> output lands in `axisem/runs/<job_name>/<job_name>_database`). It's handy
> for repeat runs, but you'd then need to move/symlink that database to
> `axisem/SOLVER/mars` (or change the path in `main.py`) since it names the
> output after `job_name`, not `mars`.

## Part 3 — Instaseis: query the database

`instaseis/main.py` opens the database and computes a seismogram for a
given source/receiver pair:

```python
db = instaseis.open_db(os.path.join(_here, '..', 'axisem', 'SOLVER', 'mars'))
```

Run it from the repo root:

```bash
conda activate instaseis
python instaseis/main.py
```

It will:
1. Open the `mars` database built above.
2. Build a `Source` (strike/dip/rake mechanism) and `Receiver` (station
   ELYSE), and compute a displacement seismogram (`get_seismograms`).
3. Bandpass-filter it (0.1–1.0 Hz) and save it as `Model1_5s_DISP.mseed`.
4. Try to download the real InSight ELYSE waveform for the same event via
   `real_data.py` for comparison.
5. Plot synthetic vs. real (or either alone, via `PLOT_MODE` in `main.py`)
   and save `seismograms*.png`.

## Repeating for a different model (e.g. Model_2)

1. `bm-convert mars_1/Model_2.txt -o output/` then
   `cp output/Model_2.bm ../axisem/MESHER/`
2. In `MESHER/inparam_mesh`, set `EXT_MODEL Model_2.bm`.
3. Re-run the mesher, then `./movemesh.csh model_2_v1` (pick a new mesh name
   — `movemesh.csh` refuses to overwrite an existing directory).
4. In `SOLVER/inparam_basic`, set `MESHNAME model_2_v1`.
5. `./submit.csh model_2_run`, then repack to a new DB directory, e.g.
   `python3 UTILS/repack_db.py model_2_run mars_model_2 --method repack`.
6. Point `instaseis.open_db(...)` (in `main.py`, or a copy of it) at
   `axisem/SOLVER/mars_model_2` instead of `mars`.

## Notes / gotchas

- `movemesh.csh <name>` and `submit.csh <run_name>` both fail loudly if the
  target directory already exists — pick a new name each run rather than
  reusing one.
- `MESHNAME` in `inparam_basic` must exactly match the directory name you
  gave `movemesh.csh` (it's looked up under `SOLVER/MESHES/`).
- Instaseis backward databases require `SIMULATION_TYPE force` in
  `inparam_basic` (single force at the surface); `moment`/`single` are for
  other workflows (direct moment-tensor runs, kernel work, etc.).
- The repacked database directory needs both a `PZ` and `PX` subtree with
  `Data/ordered_output.nc4` — that's what `instaseis.open_db()` expects.
- Large solver/database output is not committed to git (see `.gitignore`);
  each machine needs to regenerate `SOLVER/MESHES/*`, `SOLVER/<run_name>/`,
  and `SOLVER/mars/` locally.
