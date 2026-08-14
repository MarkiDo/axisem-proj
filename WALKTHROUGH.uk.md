# Покрокова інструкція: bm-converter → AxiSEM → Instaseis

Цей документ описує повний конвеєр (pipeline), який використовується в цьому
репозиторії: конвертація моделі внутрішньої будови планети у формат `.bm`
для AxiSEM, побудова сітки (mesh) та розрахунок хвильових полів у AxiSEM,
перепакування результатів у базу даних Instaseis, і зрештою — запит до цієї
бази для отримання синтетичних сейсмограм.

```
bm-converter/mars_1/Model_N.txt
        │  bm-convert
        ▼
bm-converter/output/Model_N.bm  ──копіювання──►  axisem/MESHER/Model_N.bm
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
                                          instaseis/main.py  →  сейсмограми
```

Наразі репозиторій знаходиться в середині цього конвеєра для `Model_1`:
`axisem/MESHER/Model_1.bm` — вже готовий результат конвертації, а
`axisem/SOLVER/inparam_basic` вже вказує `MESHNAME` на `model_1_v1`. Кроки
нижче відтворюють цей процес з нуля, а також показують, як повторити його
для іншої моделі (`Model_2`, …).

Кожен блок команд нижче — точний і продовжує попередній: виконуйте їх по
черзі з кореня репозиторію (`axisem-proj/`), кожна команда `cd` продовжує
з того місця, де закінчився попередній блок.

## Передумови (одноразово)

- Компілятори Fortran/C + MPI + NetCDF (тут уже встановлені через Homebrew:
  `gfortran`, `mpif90`, NetCDF). AxiSEM вже скомпільовано
  (`axisem/MESHER/xmesh`, `axisem/SOLVER/axisem` існують).
- Conda-середовище для Python-частини:
  ```bash
  conda activate instaseis
  pip install instaseis obspy matplotlib          # якщо ще не встановлено
  pip install click netCDF4 scipy numpy           # потрібні для repack бази
  ```
- bm-converter встановлений у власному venv:
  ```bash
  cd bm-converter
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
  ```

## Частина 1 — bm-converter: побудова моделі `.bm`

`bm-converter` перетворює таблицю шарів `Model_N.txt` (глибина, Vp, Vs,
густина, …) у файл `.bm` для AxiSEM (глибина від поверхні, одиниці СІ,
поверхневий шар — першим; зовнішній зчитувач моделей AxiSEM приймає
`COLUMNS depth ...` напряму і сам перераховує у радіус).

```bash
cd bm-converter
source .venv/bin/activate
bm-convert mars_1/Model_1.txt -o output/
```

Це створює `bm-converter/output/Model_1.bm`. Корисні прапорці:
- `--name <NAME>` — перевизначити поле `NAME` у заголовку (ігнорується при
  пакетній конвертації)
- `--anelastic`, `--anisotropic` — встановити відповідні прапорці заголовка
  у `T`
- щоб конвертувати всі моделі одразу: `bm-convert mars_1/Model_*.txt -o output/`

Скопіюйте модель у директорію mesher AxiSEM, потім поверніться в корінь
репозиторію:

```bash
cp output/Model_1.bm ../axisem/MESHER/
deactivate
cd ..
```

## Частина 2 — AxiSEM: побудова сітки, розрахунок і база даних для Instaseis

### 2.1 Mesher (побудова сітки)

Відредагуйте `axisem/MESHER/inparam_mesh` (вже налаштовано для `Model_1.bm`):

```
BACKGROUND_MODEL    external
EXT_MODEL           Model_1.bm
DOMINANT_PERIOD     1.0        # найкоротший період, який треба розв'язати, в секундах
NTHETA_SLICES       2          # NTHETA_SLICES * NRADIAL_SLICES = кількість ядер для solver
NRADIAL_SLICES      1
```

Запустіть mesher (за потреби скомпілює `xmesh`, потім запустить його у фоні):

```bash
cd axisem/MESHER
./submit.csh
tail -f OUTPUT          # дочекайтесь "DONE WITH MESHER"; натисніть Ctrl-C, коли з'явиться
```

Перемістіть готову сітку в іменовану директорію, яку зможе використати
solver, потім поверніться в корінь репозиторію:

```bash
./movemesh.csh model_1_v1
# → створює ../SOLVER/MESHES/model_1_v1
cd ../..
```

(Опційно) перегляньте `SOLVER/MESHES/model_1_v1/*.vtk` у ParaView, щоб
перевірити модель/дискретизацію.

### 2.2 Solver (розрахунок)

Відредагуйте `axisem/SOLVER/inparam_basic` (вже налаштовано так):

```
SIMULATION_TYPE   force        # обов'язково для бази даних Instaseis (backward)
MESHNAME          model_1_v1   # має точно збігатися з назвою з movemesh.csh вище
```

Запустіть solver — для симуляцій типу `force` це автоматично запускає обидва
джерела: вертикальне (`PZ`) і горизонтальне (`PX`) — в одній директорії запуску:

```bash
cd axisem/SOLVER
./submit.csh model_1_run
tail -f model_1_run/PZ/OUTPUT model_1_run/PX/OUTPUT   # дочекайтесь завершення обох, потім Ctrl-C
```

Це використовує `mpirun -n <NTHETA_SLICES*NRADIAL_SLICES>`, тобто 2 ядра
з наведеними вище налаштуваннями. Дочекайтесь завершення і `PZ`, і `PX`;
кожен запис створює `Data/axisem_output.nc4` (NetCDF вже увімкнено через
`USE_NETCDF true` у `make_axisem.macros` / `inparam_advanced`).

### 2.3 Перепакування у базу даних Instaseis

```bash
conda activate instaseis   # потрібні click, netCDF4, scipy, numpy
python3 UTILS/repack_db.py model_1_run mars --method repack
cd ../..
```

Це проходить по `model_1_run/{PZ,PX}/Data/*.nc4` і записує перепаковані,
готові для Instaseis копії в `axisem/SOLVER/mars/{PZ,PX}/Data/ordered_output.nc4`
— саме той шлях, який відкриває `instaseis/main.py`. Завершальна команда
`cd ../..` повертає вас у корінь репозиторію.

> Існує також `axisem/submit.py`, який автоматизує кроки 2.1–2.3 повністю
> (`python submit.py <job_name> MESHER/Model_1.bm <period> --run_type bwd`,
> результат опиняється в `axisem/runs/<job_name>/<job_name>_database`). Це
> зручно для повторних запусків, але потім доведеться перемістити/зробити
> symlink цієї бази в `axisem/SOLVER/mars` (або змінити шлях у `main.py`),
> оскільки вона названа за `job_name`, а не `mars`.

## Частина 3 — Instaseis: запит до бази даних

`instaseis/main.py` відкриває базу даних і розраховує сейсмограму для
заданої пари джерело/приймач:

```python
db = instaseis.open_db(os.path.join(_here, '..', 'axisem', 'SOLVER', 'mars'))
```

Запустіть його з кореня репозиторію:

```bash
conda activate instaseis
python instaseis/main.py
```

Скрипт виконає:
1. Відкриє базу даних `mars`, побудовану вище.
2. Побудує `Source` (механізм strike/dip/rake) і `Receiver` (станція
   ELYSE), розрахує сейсмограму зміщення (`get_seismograms`).
3. Застосує смуговий фільтр (0.1–1.0 Гц) і збереже результат у
   `Model1_5s_DISP.mseed`.
4. Спробує завантажити реальну хвильову форму InSight ELYSE для тієї ж
   події через `real_data.py` для порівняння.
5. Побудує графік синтетика vs. реальні дані (або окремо, залежно від
   `PLOT_MODE` у `main.py`) і збереже `seismograms*.png`.

## Повторення для іншої моделі (наприклад, Model_2)

1. `bm-convert mars_1/Model_2.txt -o output/`, потім
   `cp output/Model_2.bm ../axisem/MESHER/`
2. У `MESHER/inparam_mesh` встановіть `EXT_MODEL Model_2.bm`.
3. Перезапустіть mesher, потім `./movemesh.csh model_2_v1` (оберіть нову
   назву сітки — `movemesh.csh` відмовляється перезаписувати наявну
   директорію).
4. У `SOLVER/inparam_basic` встановіть `MESHNAME model_2_v1`.
5. `./submit.csh model_2_run`, потім перепакуйте в нову директорію бази
   даних, наприклад:
   `python3 UTILS/repack_db.py model_2_run mars_model_2 --method repack`.
6. Вкажіть `instaseis.open_db(...)` (у `main.py` або в його копії) на
   `axisem/SOLVER/mars_model_2` замість `mars`.

## Примітки / підводні камені

- `movemesh.csh <name>` і `submit.csh <run_name>` завершуються з помилкою,
  якщо цільова директорія вже існує — обирайте нову назву для кожного
  запуску замість повторного використання.
- `MESHNAME` у `inparam_basic` має точно збігатися з назвою директорії,
  яку ви передали в `movemesh.csh` (вона шукається в `SOLVER/MESHES/`).
- Backward-бази даних для Instaseis вимагають `SIMULATION_TYPE force` у
  `inparam_basic` (одиночна сила на поверхні); `moment`/`single` — для
  інших сценаріїв (прямі розрахунки з тензором моменту, розрахунок ядер
  тощо).
- Перепакована директорія бази даних має містити піддерева `PZ` і `PX` з
  `Data/ordered_output.nc4` — саме цього очікує `instaseis.open_db()`.
- Великі вихідні дані solver/бази даних не комітяться в git (див.
  `.gitignore`); на кожній машині потрібно перегенерувати `SOLVER/MESHES/*`,
  `SOLVER/<run_name>/` та `SOLVER/mars/` локально.
