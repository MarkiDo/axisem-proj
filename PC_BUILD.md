# Збірка ПК для флоу AxiSEM → Instaseis (база ~2 ТБ)

Підбір складових і цін, щоб рахувати AxiSEM (MESHER + SOLVER + `repack_db.py`) і постійно тримати `instaseis.server` на одній машині. Доповнює [CLOUD_RESOURCES.md](CLOUD_RESOURCES.md).

> Ціни орієнтовні (США, жовтень 2026) і взяті з відкритих джерел. Свіжих даних за листопад 2026 немає, тож перед купівлею перевірте живі лістинги.

## Вимоги

- AxiSEM: ≈32 ГБ RAM сумарно на всі MPI-ранки.
- Кількість ядер: `NTHETA_SLICES × NRADIAL_SLICES` з `inparam_mesh`.
- Scratch на прогін: сирі `.nc4` ≈2 ТБ + репак ≈2 ТБ, тобто 4–5 ТБ піковий.
- Сервер Instaseis: `ordered_output.nc4` (≈2 ТБ) на швидкому локальному NVMe, вільна RAM працює як page cache.
- ОС: Linux (Ubuntu). Docker-образи з [axisem/](axisem/) працюють без змін.

## Ринок пам'яті

DDR5 у 2026 році різко подорожчала:

| Обсяг | Ціна, ≈ |
|---|---|
| 64 ГБ (2×32) | $600–900 |
| 128 ГБ (2×64) | $1 850–4 200 |

Тому беріть **64 ГБ**: 32 ГБ іде під AxiSEM, решта під page cache. 128 ГБ не варті доплати.

## Основна збірка

| Компонент | Вибір | Ціна, ≈ |
|---|---|---|
| CPU | Ryzen 9 9950X (16 ядер / 32 потоки) | $500–550 |
| Материнська плата | AM5, B650/X670 | $200–300 |
| RAM | 64 ГБ DDR5 (2×32), 5600–6000 | $600–900 |
| NVMe | 2× 4 ТБ (система + scratch, БД) | $1 000–1 600 |
| Бекап | HDD 8–12 ТБ (сирі `.nc4`, архів) | $200–300 |
| Кулер, БЖ 750–850 Вт, корпус | | $300–400 |
| **Разом** | | **≈ $2 800–4 000** |

### Як розподіляти диски

1. Під час прогону обидва NVMe використовуються як scratch (сирі `.nc4` і репак).
2. Після репаку `ordered_output.nc4` лишається на NVMe для сервера.
3. Сирі `axisem_output.nc4` переносяться на HDD або видаляються.

### Ядра

- 16 фізичних ядер покривають типові 8–16 ранків.
- Якщо `inparam_mesh` дає 32–64 ранки, на цьому ПК розрахунок триватиме значно довше. Тоді краще орендувати сервер на час прогону.

## Збірка для України (грн)

> Ціни орієнтовні, зібрані з Rozetka, Hotline, Allo та Justbuy без підтвердженої дати. Перед купівлею перевірте актуальні.

| Компонент | Вибір | Ціна, ≈ грн |
|---|---|---|
| CPU | Ryzen 9 9950X (Allo ≈28,8 тис., «немає в наявності»; огляд 2024 р. 38 тис.) | 29 000–35 000 |
| Материнська плата | AM5, B650, мінімум 2 слоти M.2 | 6 000–9 000 |
| RAM | 32 ГБ DDR5-6000 (2×16) | 20 000–24 000 |
| NVMe | 2× 2 ТБ (Kingston NV3 ≈12,9 тис. / Patriot P320 ≈15,2 тис.) | 26 000–32 000 |
| Водяне охолодження | AIO 360 мм (Arctic Liquid Freezer III 360) | 4 500–6 500 |
| БЖ 850 Вт 80+ Gold | | 4 000–5 500 |
| Корпус | з місцем під радіатор 360 мм | 2 500–4 000 |
| **Разом** | | **≈ 93 000–116 000** |

З 64 ГБ RAM (+20–25 тис. грн) виходить ≈ 115–140 тис. грн.

### Обмеження

- **RAM 32 ГБ впритул:** AxiSEM потребує ≈32 ГБ сумарно, а ще потрібна пам'ять для ОС і page cache Instaseis. Рекомендовано 64 ГБ.
- **4 ТБ для бази 2 ТБ це в притиск:** сирі `.nc4` ≈2 ТБ плюс репак ≈2 ТБ дають ≈4 ТБ піково. Репакуйте PZ і PX по черзі та після кожного видаляйте або переносіть сирі дані.
- **HDD:** надійніше додати HDD 4–8 ТБ (≈ 3 000–6 000 грн) для сирих даних і бекапу.
- **Ядра:** 16 фізичних ядер вистачає, якщо `NTHETA_SLICES × NRADIAL_SLICES` ≤ 16.

### Водяне охолодження

- AIO 360 мм виправданий під довгим навантаженням: 9950X споживає до 170 Вт і довше тримає частоту.
- Дешевша альтернатива: великий повітряний кулер (Thermalright Peerless Assassin, Noctua NH-D15) за ≈ 2 000–3 500 грн.

### Джерела цін

- [Rozetka: DDR5 2×16 ГБ 6000](https://hard.rozetka.com.ua/433977533/p433977533/)
- [Justbuy: Prologix 32 ГБ DDR5-6000](https://justbuy.com.ua/en/kompyuterna-tehnika-komplektuyuchi-dlya-pk-operativna-pamyat-dlya-pk-i-noutbukiv/pamyat-dlya-nastilnih-kompyuteriv-prologix-32-gb-2x16gb-ddr5-6000-mhz-pro32gb6000b5k-pro32gb6000b5k)
- [Allo: Ryzen 9 9950X](https://allo.ua/ua/processory/processor-amd-ryzen-9-9950x-100-000001277-47422.html)
- [ITC.ua: огляд Ryzen 9 9950X](https://itc.ua/ua/articles/oglyad-amd-ryzen-9-9950x-najpotuzhnishyj-u-sviti-16-yadernyj-protsesor/)
- [Rozetka: Kingston NV3 2 ТБ](https://hard.rozetka.com.ua/ssd-kingston-151524757/p548379828/)
- [Fixer: Arctic Liquid Freezer III 360](https://fixer.com.ua/kulery-i-radiatory/arctic-liquid-freezer-iii-360-a-rgb-black-acfre00144a_1573683.html)

## Дешевші варіанти

| Варіант | Ціна, ≈ | Коментар |
|---|---|---|
| Ryzen 7 9700X + 64 ГБ + 2×4 ТБ | $2 400–3 200 | 8 ядер, розрахунок повільніший, сервер працює так само |
| Б/в сервер (Hetzner Server Auction) | €50–70/міс | Не купуєте RAM, див. [CLOUD_RESOURCES.md](CLOUD_RESOURCES.md) |

## Купувати чи орендувати

- Власний ПК за $3 000–4 000 окупається проти bare-metal (≈ €100–140/міс) приблизно за 2–3 роки.
- Оренда не залежить від цін на RAM і може бути лише на час розрахунку (Scaleway погодинно).
- Купувати ПК має сенс, якщо Instaseis потрібен постійно і ви рахуєте кілька моделей.
- Для однієї моделі вигідніше орендувати сервер на 1–2 тижні для розрахунку, а потім тримати базу на недорогому сервері.

## Експлуатація

- **Бекап:** диски без RAID. Копію `ordered_output.nc4` тримайте на HDD або у Backblaze B2 (≈ $12/міс за 2 ТБ). Відновити базу можна лише повторним розрахунком.
- **Стабільний URL:** Cloudflare Tunnel або Tailscale замість VS Code Dev Tunnel, без відкритих портів.
- **Доступ:** `instaseis.open_db(url)` не передає авторизацію, тому закривайте сервер тунелем або VPN.
- **Сервіс:** `instaseis.server` як systemd-юніт (приклад у [CLOUD_RESOURCES.md](CLOUD_RESOURCES.md)).
- **Mac:** для бази 2 ТБ не підходить через диск і RAM.

## Перед купівлею

1. Перевірити `NTHETA_SLICES × NRADIAL_SLICES` у `inparam_mesh` і вирішити, чи вистачить 16 ядер.
2. Звірити поточні ціни на RAM і NVMe.
3. Порівняти з орендою bare-metal на потрібний термін.

## Джерела цін

- [DDR5 prices up 500% in a year (hwbusters)](https://hwbusters.com/news/ddr5-memory-prices-are-up-500-in-a-year-and-a-128gb-kit-now-lists-at-3399/)
- [Corsair 128GB DDR5 +761% in Japan (mixed-news)](https://mixed-news.com/en/corsair-128gb-ddr5-japan-price-increase-akihabara-survey/)
- [128GB DDR5 live prices (datacenterdisk)](https://datacenterdisk.com/ram/ddr5/128gb)
- [DDR5 prices, 64 GB (techfuelhq)](https://techfuelhq.com/articles/ddr5-ram-prices-2026/)
- [Best 4TB NVMe SSD (datacenterdisk)](https://datacenterdisk.com/best/4tb-nvme-ssd)
- [SSD price snapshot (maxmybuild)](https://www.maxmybuild.com/storage/prices)
- [Ryzen 9 9950X deals (Slickdeals)](https://slickdeals.net/f/19459203-amd-ryzen-9-9950x-16-core-32-thread-unlocked-desktop-processor-499)
