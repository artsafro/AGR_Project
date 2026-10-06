# Локальная гигиена AGR — 03.10.2026

Это компактная запись этапа для fresh docs worktree. Raw primary history,
private assets, backup ZIP и runtime engineering/monitor сюда не переносятся.
Архивирование и primary navigation применены; фактические результаты ниже.
Independent review, named local commit и exact readback относятся к REPORT этапа.

## Версии и владельцы

| Контекст | Exact версия | Область |
|---|---|---|
| Published main | `7c418f34b74c3669d03ce6a530c366d6894d7a2f` | Опубликованный code/docs, PR28–30 merged. |
| Primary | dirty `feature/revit-typical-floor@d7ecdfda5f83d0c0ad672a65fc954031fca0cfbc` | Локальные jobs/approved/runtime/policy; не переключать и не reset. |
| Fresh hygiene docs | `codex/agr-bootstrap-20261002@974efc67fa55682a16a2c4fa160a7a0b4167599f` до продолжения | Локальные docs commits на base main 7c; не опубликованы. |
| Inspector/skills source | `828d8e61b9513df1013f9eb0b961b1f69e520b5e` | Local engineering activation primary; отдельный source-stage QA. |
| Monitor continuation | `bbeecaf2c6252a77d00f9b70cdbab4c4b08f9c2c` | Local read-only панель primary; её runtime отсутствует в fresh docs. |

Root владеет архивированием, integration и Git. Кандидаты готовятся отдельно;
independent verifier читает actual diff/receipts. Один writer каждого ресурса.
Worktree не изолирует DCC, порты и общие exports.

## Что подготовлено

Совокупный readback двух этапов: все19 исторических деревьев архивированы,
3708/3708 файлов совпали по SHA (359625827bytes). Все25 прежних путей переноса
отсутствуют; исходный run-record-tests parent пуст и сохранён. Все78cachepaths
отсутствуют,4JSON archives совпали по SHA. Отдельный read-only total receipt:
`TOTAL_HYGIENE_READBACK.md`, SHA `9e2cd6daf048ebbff2be34184d682b99df92a0df12f47d48a3e5041b9501ed97`.

- Пакеты 02.10: 78 source-backed caches, 4 inventory JSON и 5 test roots уже
  обработаны; повторять их нельзя. Их сохранённые receipts остаются локальными.
- Остаток: 20 named units (13 roots + 7 run-record children; parent retain),
  3689 regular files / 359625681 bytes / 2189 dirs / 269 symbolic links.
  Exact manifest SHA256: `03b86706e4abf0c7343c3b12ad6a0f178efd0d03a6340d58c755bf7db7cb5669`.
- ZIP SHA256: `4f7ced4ec1ad30324facf27950ffb524962cae179ebbf85a1b7ad2f352e8410b`.
  File recovery receipt: 3689 restored/rehashed, CRC passed. Более поздний native
  receipt: 269 original records и 269 internal remapped links проверены,
  3689 file SHA снова совпали. Source mutations 0 на стадии подготовки.
- Четыре current primary docs frozen отдельно. В navigation-action-manifest
  записан actual disk recovery 4/4; initial snapshot сохранён отдельно после
  concurrent monitor activation. Перед записью root повторяет current guards.
- Primary history предназначена только локальному
  `docs/history/PRIMARY_NAVIGATION_BEFORE_2026-10-03.md` в primary.
  Она не входит в named fresh docs package и не публикуется как curated artifact.

Локальный источник полных manifests/receipts — primary
`tmp/agr-hygiene-20261003/REPORT.md`, `CLEANUP.md`, `INDEPENDENT_REVIEW.md`,
`test-recovery-readback.json`, `native-recovery-readback.json` и
`navigation-action-manifest.json`. Эти machine-local файлы не являются
обязательными runtime dependencies fresh checkout. Для restart читать actual
execution receipts и destinations до retry; прежнюю подготовку не считать execution.

## Результат и проверки

| Проверка | Результат |
|---|---|
| Старые тесты | 20 адресных переносов, 3689 файлов с совпадением SHA, 269 рабочих ссылок. Родитель run-record-tests сохранён; удаления исходных данных нет. Receipt SHA `9b042807…`. |
| Текущая навигация primary | Обновлены STATE, README, TASK_CONTEXT и PROJECT_MAP. STATE: 1227 → 50 строк. Все прежние байты сохранены в history331175bytes; восстановление 4/4 проверено. Receipt SHA `b5c018af…`. |
| Сохранность после наших переносов | До последующей workflow activation:462 из465 unchanged, три изменения документов разрешены; README/history отдельно. Тогда primary13dirty/411untracked/staged0, receipt68e0bec2. Позднейшая квалификация:459oldbytes+2ourdocSHA+4workflowdelta,10adds; на этом checkpoint13dirty/421untracked/staged0, snapshot477. |
| Локальный QA 03.10 | Source974efc67: 222 passed, 1 skipped, 1 ожидаемое ZIP warning за 40.82s; 3 профиля, 8 схем. Код и тесты не менялись. |
| Независимая проверка результата | Actual архив, ссылки, восстановление, primary docs и сохранность проверены; блокеров нет. Fresh docs/commit проверяются отдельно. |
| Локальное сохранение пяти документов | Только именованные STATE/README/TASK_CONTEXT/PROJECT_MAP/эта запись на codex/agr-bootstrap-20261002; exact head/readback сохраняется в локальном REPORT этапа. Публикация не выполняется. |

Место сохранения полного evidence/review и exact commit — REPORT этапа. Concurrent изменения сохраняются
отдельным checkpoint с originals; чужие правки не откатываются. Own disk recovery
probe удалён адресно после independent archive/recovery acceptance:3689files,
269link leaves,2190emptydirs с root; исходных данных удалено0. Dated archive,
ZIP/full native original records, small decoded-navigation recovery и все receipts
сохраняются. Actual cleanup receipt: `own-probe-cleanup-receipt.json`.

## Позднейшее параллельное обновление

Другая локальная задача активировала `tools/codex_workflow/` и bridge в
agr-task-route/AGENT_WORKFLOW/ENGINEERING, добавила21line prefix к нашему exact
STATE50: на этом checkpoint71line. Source package закреплён commit
`3c0e02b6889895f09919ac6ab6722fd472ec4641`;12files совпали с committed blobs,
primary AGENT_WORKFLOW совпал со своим policy-preserving candidate.
Old4byte backups и suffix нашего STATE проверены;14currentcopies сохранены.
Failed drift guard оставлен, объяснение не переписало baselines. Полный qualified
snapshot477 и поздние QA/STATE metadata — `primary-concurrent-workflow.json`.
Эти runtime/skills сохранены в primary и не перенесены в fresh docs checkout.
Другие workflow updates могут продолжаться после этого датированного снимка;
их source/QA не принимаются автоматически этим этапом. Перед продолжением читать
текущий primary STATE/REPORT; предыдущие baselines и наш STATE50 сохраняются.

## QA, GitHub и приёмка

Fresh source base QA от 02.10.2026: 222 passed / 1 skipped / 1 expected warning,
3 профиля / 8 схем. Engineering source 828d QA от 03.10: 246 passed / 1 skipped /
1 warning, 3 профиля / 8 схем — другая версия; это не новый QA fresh docs.

GitHub snapshot local date 03.10: main 7c, PR18 — единственный open/draft,
отложенный пользователем; Issues 6, 7, 10–14 открыты. Последние 10 Actions runs —
`startup_failure`; latest main run `37072605277`, фактический jobs API `jobs=[]`.
Hosted tests не выполнились. Billing/spending — историческая причина, текущим
API не установлена. Детали и live-refresh маршрут: [PROJECT_MAP](PROJECT_MAP.md).

Original/approved/private scenes, FBX/PNG, нормы/PDF/YAML, code/tests, active/unknown
и references remain retain. Около 4 ГБ outputs не публикуются; SHA registry не backup.
Native Max, Checker, export/readback, визуальная приёмка и второй объект остаются
воротами соответствующего case. Ни архив, ни inspector/monitor не закрывает delivery.
В GLB текущая A v005 не наследует старый PNG QA: [пакет](../../technical_library/glb_atlas/README.md).

[STATE](../../STATE.md) · [маршрут задачи](../TASK_CONTEXT.md) ·
[правила работы](../AGENT_WORKFLOW.md) · [области приёмки](../case_studies/README.md).

QA03 использовал primary `.venv/Scripts/python.exe` с `PYTHONPATH=<fresh>/src`,
`PYTHONDONTWRITEBYTECODE=1`, `-B`, pytest `-p no:cacheprovider` и новый
`--basetemp=<primary>/tmp/agr-hygiene-20261003/qa/pytest-01`. Fresh `.venv` отсутствует;
эти результаты не являются чистой установкой в новом venv. Code/tests неизменны.
