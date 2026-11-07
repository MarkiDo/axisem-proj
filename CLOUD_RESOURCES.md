# Хмарні ресурси для флоу AxiSEM → Instaseis

Опис хмарних ресурсів, які допоможуть запустити і зберегти повний флоу, включно з `instaseis.server`, що запускається періодично для підключення до AxiSEM-бази.

> Ціни й ліміти орієнтовні, їх варто звірити перед вибором.

## Контекст проєкту

- Флоу ([WALKTHROUGH.md](WALKTHROUGH.md)): `bm-converter` → MESHER → SOLVER (MPI, PZ+PX) → `repack_db.py` → `ordered_output.nc4` → `instaseis.server` → [instaseis/main.py](instaseis/main.py).
- Docker-образи вже є: [axisem/Dockerfile](axisem/Dockerfile) і [axisem/Dockerfile.solver](axisem/Dockerfile.solver).
- База `model2` важить ≈716 МБ. Малий мешер (у прикладі 2 ядра) не вимагає кластера.
- Зараз сервер ділиться через VS Code Dev Tunnel ([SHARE_MODEL2.md](SHARE_MODEL2.md)). URL у `main.py` захардкоджений, а тунель живе, лише поки відкритий ноутбук.

## Ресурси за етапами

| Етап | Що потрібно | AWS | GCP | Azure |
|---|---|---|---|---|
| Збірка образу | Реєстр контейнерів + CI | ECR + GitHub Actions | Artifact Registry + Cloud Build | ACR |
| Розрахунок AxiSEM (разовий, MPI) | Batch-запуск на compute-optimized VM, краще spot | EC2 spot (c7i/c7a) через AWS Batch | Cloud Batch (C3/C2) | Azure Batch |
| Дуже великі меші | HPC-кластер з MPI | ParallelCluster, hpc7a | HPC-VM | CycleCloud |
| Зберігання | Об'єктне сховище: `.bm`, `MESHES`, сирі `.nc4`, готова БД | S3 | GCS | Blob Storage |
| Оркестрація флоу | Ланцюг кроків | Step Functions (або Batch job dependencies) | Workflows | Logic Apps / Data Factory |
| Instaseis server за розкладом | Контейнер зі стабільним URL | ECS Fargate + ALB, або EC2 за розкладом | Cloud Run | Container Apps |
| Розклад | Запуск і вимкнення | EventBridge Scheduler | Cloud Scheduler | Container Apps scale rules |
| Секрети й IaC | | Secrets Manager, Terraform | Secret Manager, Terraform | Key Vault, Terraform |

## Зберігання: що тримати

- **Обов'язково:** `Model_N.txt` / `.bm`, `inparam_*`, `MESHES/<name>` і репаковані `PZ/PX ordered_output.nc4`. Цього достатньо, щоб відтворити флоу і запустити сервер.
- **Сирі `axisem_output.nc4`:** тримати в холодному класі (S3 Glacier IR, GCS Nearline/Coldline, Azure Cool). Їх можна перерахувати, тож це опція.
- **Версіювання:** увімкнути на бакеті. Шлях на кшталт `s3://bucket/models/model2/v1/{PZ,PX}/Data/ordered_output.nc4` дає прості відкати.
- **Вартість:** ~1 ГБ у сховищі коштує центи на місяць.

## Головний нюанс: Instaseis не читає з S3/GCS напряму

`instaseis.server` відкриває `.nc4` як локальні файли з випадковим доступом (netCDF/HDF5). Тому бакет треба спочатку скопіювати на локальний диск.

- **Не робити так:**
  - монтувати бакет через FUSE (s3fs, gcsfuse): повільно на випадкових читаннях;
  - тримати БД на EFS чи NFS: те саме.
- **Робити так:** при старті контейнера копіювати БД з бакета на локальний/ephemeral диск (716 МБ тягнуться за секунди), далі:

```bash
python -m instaseis.server --port 8000 /data/model2
```

## Варіанти запуску сервера «періодично»

1. **Cloud Run (GCP) — рекомендовано.**
   - Масштабується до нуля, платите лише за час запитів.
   - Дає стабільний HTTPS-URL, який один раз прописується в `main.py`.
   - Старт: entrypoint-скрипт робить `gsutil cp` бази в `/data` і запускає сервер.
   - Потрібно 2–4 ГБ RAM, бо `/data` в in-memory ФС рахується в пам'ять. Холодний старт — десятки секунд.
2. **ECS Fargate + ALB (AWS).**
   - Запуск і зупинка за розкладом через Application Auto Scaling (scheduled actions: `desired=1` або `0`).
   - Ephemeral storage до 200 ГБ, БД копіюється з S3 при старті.
   - ALB коштує ~$16–20 на місяць навіть без трафіку, тому дорожче за Cloud Run.
3. **EC2/GCE VM за розкладом (найпростіше «як зараз, але в хмарі»).**
   - EventBridge/Cloud Scheduler запускає і зупиняє інстанс, БД лежить на EBS/PD, сервер піднімається через systemd.
   - Мінус: публічний IP змінюється. Потрібні Elastic IP чи DNS-запис, інакше URL у клієнтів ламається.
4. **Dev Tunnel** — лише для тестів, не для регулярного використання.

## Доступ і безпека

Наскільки відомо, `instaseis.open_db(url)` не вміє передавати авторизацію. Тому:

- або публічний endpoint (дані лише синтетичні, ризик невеликий; обмежити rate limit через API Gateway/Cloud Armor);
- або приватна мережа/VPN;
- або локальний проксі з токеном перед сервером.

## Рекомендована мінімальна схема

```
GitHub Actions ─► Artifact Registry (образи solver + instaseis-server)
Cloud Batch (spot) ─► MESHER+SOLVER+repack ─► GCS (models/<name>/vN/)
Cloud Scheduler ─► Cloud Run (instaseis.server, копіює БД з GCS при старті) ─► стабільний URL
main.py ─► instaseis.open_db('https://…run.app/')
```

Оркестрацію можна почати з простого bash/GitHub Actions workflow, а Workflows чи Step Functions додати пізніше. За обсягу ~700 МБ це коштує одиниці доларів на місяць, плюс вартість самих розрахунків.

## Зауваження до репозиторію

У git закомічені сотні `.o` і `.mod` та бінарні файли (див. `git status`). Їх варто додати в `.gitignore`: збірка все одно відбувається в Docker, а великі дані мають жити в бакеті, а не в git.

## Сценарій: база ~2 ТБ, AxiSEM потребує ~32 ГБ RAM

> Ціни орієнтовні (on-demand, US-регіони), звірити перед вибором.

### Що змінюється

| Аспект | База 716 МБ | База 2 ТБ |
|---|---|---|
| Копіювання БД при старті сервера | секунди | десятки хвилин (1 ГБ/с ≈ 35 хв) — не підходить |
| Cloud Run / Fargate «копіюємо з бакета» | підходить | **не підходить** |
| Місце для розрахунку | десятки ГБ | сирі `.nc4` ≈ 2 ТБ + репак ≈ 2 ТБ: **4–5 ТБ scratch** (піковий) |
| Тип VM для AxiSEM | будь-який compute | **memory-optimized / general** з ≥32 ГБ RAM |

### Розрахунок AxiSEM (MESHER + SOLVER + repack)

- **RAM:** 32 ГБ — це сумарно на всі MPI-ранки. Беріть VM з запасом (≥48–64 ГБ), бо ОС і page cache також потребують пам'яті:
  - AWS: `r7i.2xlarge` (64 ГБ) / `m7i.4xlarge` (64 ГБ); більше ядер — `r7i.4xlarge`+;
  - GCP: `n2-highmem-8` / `c3-highmem-8`;
  - Azure: `E8s v5`.
- **Кількість ядер** = `NTHETA_SLICES × NRADIAL_SLICES` з `inparam_mesh`. Для таких розмірів це зазвичай 16–64 ядра, а розрахунок триває години–дні.
- **Spot чи on-demand:** наскільки відомо, AxiSEM не має надійного checkpoint/restart, тому переривання spot-інстанса втрачає весь прогін. Для довгих запусків краще on-demand (або spot лише для коротких PZ/PX етапів, що перезапускаються).
- **Scratch-диск (≥5 ТБ), швидкий:**
  - локальний NVMe: AWS `i4i` / `i3en`, GCP Local SSD, Azure `Lsv3`. Найшвидше й найдешевше, але вмирає разом з VM, тож результат одразу копіювати в бакет;
  - EBS gp3 / GCP Hyperdisk-Balanced / Azure Premium SSD v2: персистентний, ≈ $0.08/ГБ·міс (5 ТБ ≈ $400/міс, але лише поки диск існує — видаляйте після прогону);
  - FSx for Lustre (AWS), що синхронізується з S3 — якщо потрібен спільний диск для кількох вузлів.
- **Після репаку** сирі `axisem_output.nc4` видаліть або перенесіть у холодний клас, `ordered_output.nc4` збережіть.

### Зберігання 2 ТБ

| Де | Орієнтовно / міс | Примітка |
|---|---|---|
| S3 Standard / GCS Standard | ≈ $46–50 | основне джерело правди |
| S3 Glacier Instant Retrieval / GCS Nearline | ≈ $8–20 | для сирих даних, які рідко потрібні |
| EBS gp3 / PD (для сервера) | ≈ $160 | якщо диск тримати постійно |
| EBS snapshot / PD snapshot | ≈ $50–100 | дешевше, ніж тримати том постійно |

### Запуск `instaseis.server` за розкладом з 2 ТБ

Instaseis читає `.nc4` через випадковий доступ і торкається лише невеликих фрагментів файлу на запит, тому копіювати всі 2 ТБ не потрібно, а потрібен швидкий **блоковий** диск.

1. **VM + персистентний SSD-диск (рекомендовано).**
   - VM (`r7i.xlarge`/`n2-highmem-4`, 32+ ГБ RAM для page cache) вмикається за розкладом (EventBridge Scheduler / Cloud Scheduler) і вимикається після простою.
   - Диск з БД залишається; у вимкненому стані платите лише за диск (≈ $160/міс за 2 ТБ gp3).
   - Потрібен стабільний URL: Elastic IP / статичний IP + DNS, або LB.
2. **Snapshot → том за розкладом (дешевше, повільніше старт).**
   - БД лежить як EBS/PD snapshot (≈ $50–100/міс), при старті з нього створюється том і монтується.
   - Перші читання «ліниві» і повільні (дані підтягуються з snapshot). Прискорення — Fast Snapshot Restore (AWS, платно) або прогрів читанням найчастіших фрагментів.
3. **S3-backed файлова система** (FSx for Lustre + S3 data repository, Filestore, Azure Managed Lustre).
   - Дані підтягуються з бакета ліниво на перший доступ, без ручного копіювання.
   - Дорожче за простий диск і не завжди виграє в latency; варто перевірити на тестових запитах.
4. **Cloud Run / Fargate / Container Apps** — не підходять (немає місця й часу на копіювання 2 ТБ), якщо тільки не зменшити БД.

### Як зменшити розмір бази (варто розглянути)

- Збільшити `DOMINANT_PERIOD` у `inparam_mesh`: розмір і час розрахунку різко залежать від мінімального періоду. Наприклад, у [instaseis/main.py](instaseis/main.py) використовується діапазон 30–100 с, тож перевірте, чи потрібна менша межа.
- Перевірити, чи [axisem/SOLVER/UTILS/repack_db.py](axisem/SOLVER/UTILS/repack_db.py) підтримує стиснення (compression) вихідних `.nc4`.
- Тримати кілька моделей як окремі версії в бакеті, але на сервері тримати лише актуальну.

### Рекомендована схема для 2 ТБ

```
Batch/VM on-demand (r7i/n2-highmem, i4i NVMe або 5 ТБ SSD)
   MESHER + SOLVER + repack ─► ordered_output.nc4
        │
        ├─► S3/GCS Standard (models/<name>/vN/)     ← джерело правди
        └─► EBS/PD snapshot                          ← для швидкого підйому сервера

Scheduler ─► VM (32+ ГБ RAM) + SSD-том з БД ─► instaseis.server ─► стабільний URL/DNS
```

## Альтернативи поза великими хмарами

> Ціни орієнтовні, звірити перед вибором.

| Платформа | Для чого | Плюси | Мінуси |
|---|---|---|---|
| **Академічні HPC-центри** (PRACE/EuroHPC, ACCESS/NERSC, Compute Canada, університетські кластери) | Розрахунок AxiSEM (MPI, Slurm) | Безкоштовно за грантом/заявкою, тисячі ядер, швидка паралельна ФС (Lustre/GPFS) на ТБ | Черги, заявка, не для постійного сервера |
| **Dedicated / bare-metal** (Hetzner, OVHcloud, Scaleway) | Розрахунок і сервер Instaseis | Дуже дешево за ТБ і RAM (сервер 64–128 ГБ RAM + NVMe 2–4 ТБ за ≈ €50–120/міс), без плати за egress | Адмініструвати самому, немає autoscaling |
| **VPS** (DigitalOcean, Vultr, Linode) + Block/Volume storage | Невеликий сервер Instaseis | Простий, передбачувана ціна | Дорожче за bare-metal на великих дисках |
| **Власний сервер / робоча станція** (+ NAS) | Усе, включно з сервером | Одноразова вартість, диски 2+ ТБ NVMe недорогі | Живлення, аптайм, бекап, публічний доступ |
| **Дешеве об'єктне сховище** (Backblaze B2, Wasabi, Cloudflare R2) | Архів і бекап 2 ТБ | ≈ $6–15/міс за 2 ТБ, R2 без плати за egress | Не файлова система, перед запуском копіювати на диск |
| **Публічне хостування БД** (IRIS Syngine, Zenodo, Dataverse) | Поширення готових баз | Не треба підтримувати сервер, постійне зберігання з DOI | Лише для публічних моделей, обмежений контроль |

### Як з цього скласти флоу

- **Розрахунок:** HPC-центр, якщо є доступ, інакше орендований bare-metal на тиждень-два чи on-demand VM (див. розділ про 2 ТБ).
- **Сервер Instaseis:** найвигідніше для 2 ТБ — один bare-metal/VPS з NVMe, на якому БД лежить постійно, а `instaseis.server` працює як systemd-сервіс. Запуск «періодично» можна зробити таймером systemd/cron, але на такому сервері зазвичай дешевше просто тримати його увімкненим.
- **Стабільний URL без публічного IP:** Cloudflare Tunnel або Tailscale Funnel замість VS Code Dev Tunnel. Вони дають постійну адресу, працюють з ноутбука чи домашнього сервера і не потребують відкритих портів. Для приватного доступу Tailscale/WireGuard VPN, бо `open_db(url)` не вміє авторизуватись.
- **Бекап:** `rclone` на Backblaze B2 / Wasabi / R2 за розкладом.
- **Контейнери:** ті самі Dockerfile з [axisem/](axisem/) працюють на будь-якому з цих варіантів (Docker, або Apptainer/Singularity на HPC, де Docker заборонений).

## Підсумок: що обрати

| Ситуація | Розрахунок AxiSEM | Зберігання | Сервер Instaseis |
|---|---|---|---|
| База ≈ 1 ГБ, мало запитів | Одна VM / локально | S3/GCS | Cloud Run / Fargate (scale-to-zero) |
| База ≈ 1–100 ГБ | On-demand VM або Batch | S3/GCS | VM + SSD-диск, за розкладом або постійно |
| База ≈ 2 ТБ, 32 ГБ RAM | HPC-центр або on-demand VM з 5 ТБ scratch | S3/GCS або B2/R2 для архіву | Bare-metal/VM з NVMe, постійно + Cloudflare Tunnel/Tailscale |

Спільні правила для всіх варіантів:
- Джерело правди: версійований бакет з `.bm`, `MESHES`, `inparam_*` і `ordered_output.nc4`.
- Сервер завжди читає БД з локального диска, не з FUSE/NFS.
- Стабільний URL замість Dev Tunnel; доступ обмежити, бо `open_db(url)` не передає авторизацію.
- Сирі `axisem_output.nc4` видаляти або архівувати після репаку.

## Наступні кроки

1. Визначити платформу (хмара, HPC, bare-metal) і бюджет.
2. Підготувати Dockerfile для `instaseis.server` (з entrypoint-копіюванням БД, якщо розмір малий).
3. Описати інфраструктуру як код (Terraform) або systemd-юніт + скрипт бекапу.
4. Замінити захардкоджений URL у [instaseis/main.py](instaseis/main.py) на змінну оточення.
5. Додати `.o`/`.mod` у `.gitignore`.

## Dedicated / bare-metal: детально

Орендується цілий фізичний сервер за фіксовану місячну плату, зазвичай з великою квотою трафіку. Ціни орієнтовні, звірити на сайтах провайдерів.

### Порівняння провайдерів

| | **Hetzner** (DE/FI) | **OVHcloud** (FR та ін.) | **Scaleway Elastic Metal** (FR/NL) |
|---|---|---|---|
| Лінійки | AX (AMD Ryzen/EPYC), EX (Intel), SX (багато HDD), Server Auction (б/в, дешевше) | Rise / Advance / Scale / High Grade | Elastic Metal |
| Оплата | Місячна, разова плата за підключення | Переважно місячна | Погодинна (є мінімальний період), зручно для разового розрахунку |
| Сильні сторони | Найкраще співвідношення ціна/RAM/NVMe | vRack (приватна мережа), широкий вибір | Старт за хвилини, API/Terraform |
| Слабкі | Немає погодинної оплати | Ціна вища | Дорожче за Hetzner на місяць |

Приблизні діапазони:
- 64 ГБ RAM, 8 ядер, NVMe 2×1 ТБ: ≈ €50–70/міс.
- 128 ГБ RAM, 16 ядер, NVMe 2×2 ТБ: ≈ €100–140/міс.
- EPYC 32–48 ядер, 256 ГБ RAM, NVMe 2×3,84 ТБ: ≈ €200–300/міс.

Для бази 2 ТБ потрібен диск більший за 2 ТБ (наприклад 2×3,84 ТБ NVMe) або окремий диск/Storage Box під сирі дані.

### Як це лягає на флоу

1. **Розрахунок AxiSEM:** 32 ГБ RAM покриваються з запасом; ядра задають `NTHETA_SLICES × NRADIAL_SLICES`; локальний NVMe закриває scratch на 4–5 ТБ. Для разового прогону: Scaleway (погодинно) або Hetzner на 1–2 місяці.
2. **Сервер Instaseis:** БД на локальному NVMe, вільна RAM працює як page cache. Сервер працює постійно, бо оплата фіксована. Стабільний URL через Cloudflare Tunnel або Tailscale.
3. **Бекап:** `rclone` у Backblaze B2 / Wasabi / Cloudflare R2, або Hetzner Storage Box.

### Мінімальне налаштування

1. Замовити сервер з Ubuntu/Debian, RAID1 для системи (`installimage` у Hetzner).
2. Для даних вибрати: RAID1 (безпечніше, вдвічі менше місця) або окремі диски (максимум ємності, потрібен бекап).
3. Встановити conda-середовище з Instaseis або Docker.
4. Скопіювати базу з бакета (`rclone`/`rsync`).
5. Розгорнути сервіс через systemd:

```ini
# /etc/systemd/system/instaseis.service
[Unit]
Description=Instaseis server
After=network.target

[Service]
User=instaseis
ExecStart=/opt/conda/envs/instaseis/bin/python -m instaseis.server --port 8000 /data/model2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

6. Закрити порт 8000 фаєрволом і виставити через Cloudflare Tunnel (`cloudflared tunnel create instaseis`, потім `cloudflared tunnel route dns instaseis <ваш-домен>`):

```yaml
# /etc/cloudflared/config.yml
tunnel: instaseis
credentials-file: /etc/cloudflared/instaseis.json
ingress:
  - hostname: instaseis.example.com
    service: http://localhost:8000
  - service: http_status:404
```

7. Налаштувати щотижневий бекап через `rclone` (remote `backup` створити командою `rclone config`) і cron або systemd timer:

```bash
rclone sync /data/model2 backup:axisem-models/model2 \
  --include "*/Data/ordered_output.nc4" --transfers 4 --checksum
```

### Плюси й мінуси

| Плюси | Мінуси |
|---|---|
| У 3–10 разів дешевше за хмару при 2 ТБ і 64+ ГБ RAM | Все адмініструєте самі: оновлення, безпека, моніторинг |
| Передбачувана ціна, трафік в основному безкоштовний | Немає автоскейлінгу і snapshot-ів диска |
| Реальний NVMe та ядра без шумних сусідів | Відмова диска/сервера означає простій |
| Добра швидкодія для випадкових читань Instaseis | Регіон ЄС: більша затримка для клієнтів з інших континентів |

### На що звернути увагу

- Бекап обов'язковий: базу можна відновити лише повторним розрахунком (години чи дні).
- SSH лише за ключами, `ufw`/`fail2ban`, регулярні оновлення.
- `open_db(url)` не передає авторизацію, тому закривайте сервер тунелем або VPN.
