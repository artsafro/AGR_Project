# Гигиена AGR — фактические действия06.10

Пользователь расширил задачу: реально вычистить, переименовать, объединить и замержить.
Активный вход теперь [PROJECT_MAP](PROJECT_MAP.md):3 раздела,6 направлений,8 сохраняемых рабочих чатов.
13 исторических/дублирующих документов перенесены в history; source bytes сохранены в Git
на090d8b2 и local freeze. TASK_BOARD объединён в PROJECT_MAP; SCRIPT_LIBRARY в technical_library.
11 проверенных чатов обратимо архивированы с native list readback. Дополнительное
извлечение:22 страницы/142turns,11archive candidates; management heartbeat и skills
handoff сохраняются,34чата других проектов не удаляются.
Exact path/hash/action manifest и recovery receipts: `C:/Users/artsafro/.AGR_Project/tmp/project-hygiene-20261006/`.
PR31 independently reviewed и squash-merged в main: d53cb5f96a71c8aabe549d9974d07a3e7ccfcfdb.
Два чистых checkout glb-lessons/agr-bootstrap закрыты; обе ветки сохранены.
Полноценный bundle23,348,279bytes; восстановлены411tracked-файлов53,643,947bytes,
все SHA и два Git tree независимо совпали. Bundle SHA256:
f17b35a4a742459574c6d6f791f0330e4f34c853bc79407cb12afbc53f3874b0.
Уникальные bootstrap docs сохранены в history. Остальные worktrees с незавершёнными
изменениями/ignored-результатами сохранены; primary assets и активная КПП1 сохранены.
Интегрированный local QA:248passed/1skipped/1expected warning (43.96s), profiles3/schemas8.
Независимое review snapshot80cb8c79: открытых findings нет. Публикация структуры —
[PR32](https://github.com/artsafro/AGR_Project/pull/32); актуальный merged/head/base
проверяется по GitHub. Hosted CI остаётся отдельной проверкой.
Два bootstrap-снимка STATE_BEFORE_HYGIENE_2026-10-02.md и LOCAL_HYGIENE_2026-10-03.md
сохранены byte-identical; их внутренние ссылки описывают прежнее расположение в
agr-bootstrap-20261002 и не служат текущей навигацией. Полный старый checkout
восстанавливается из сохранённого bundle; актуальный вход — PROJECT_MAP.

## Сохранённый результат первого этапа


Задача: небольшой рефакторинг разделов и строгая проверка того, что можно убрать
из активных чатов; 5–8 направлений с независимыми задачами/worktree/коммитами.
Результат этапа: [восемь направлений](../history/organization/TASK_BOARD_BEFORE_CONSOLIDATION.md), короткие STATE/PROJECT_MAP,
адресные входы README/TASK_CONTEXT и [manifest54 чатов](../history/organization/CHAT_RETIREMENT_INITIAL_2026-10-06.json).
Папки src/adapters/jobs/docs/standards/tests уже разделяют ответственность;
массовое перемещение без проверки зависимостей не оправдано этим аудитом.

## Контракт и ресурсы

Root — единственный writer docs этого worktree. Base `7c418f34b74c3669d03ce6a530c366d6894d7a2f` подтверждён fetch06.10.
Ветка `codex/project-hygiene-20261006`; local commit после независимого review.
Primary dirty и активный КПП1 сохраняются. Проверяющие работали read-only;
их собственные отчёты находятся в `C:/Users/artsafro/.AGR_Project/tmp/project-hygiene-20261006/`.
Не выполняются cleanup assets/session files/worktrees, runtime refactor, DCC,
изменения норм/PR18, push/PR/merge. Документы не заменяют готовность модели.

## Что найдено

- Primary:13 tracked изменений,509 untracked файлов;102 свернутых porcelain entries.
  Число записей `git status` не равно числу файлов. Среди кандидатов есть сцены,
  источники, скрипты и QA; blanket staging/удаление не обоснованы.
- На начало аудита8 worktrees. Семь внешних Git-clean, у пяти есть ignored
  evidence/tmp/outputs. У двух без ignored файлов остаются непроверенные local
  commits/интеграция. Ни один не признан disposable. Этот этап добавил девятый.
- STATE/PROJECT_MAP primary указывали bootstrap974efc и harnessbbeecaf;
  текущие головы026b147/c4f2f095. Новый worktree различает историю/current/published.
- Root STATE КПП1 отстаёт: описываетv003, job ужеv004; у job также осталась
  старая формулировка об активнойv003. Это замечание владельцу КПП1, а не
  разрешение переписать его state или повторно открыть сцену.
- CURRENT_INDEX был параллельным входом03.10; primary получает короткую ссылку
  на текущую доску и отчёт. Прежние внешние cleanup receipts сохраняются.
- technical_library есть в main и отсутствует в primary. Новый docs worktree
  использует проверенные ссылки своего checkout; local-only KPP1 явно помечен.
-71 файлов root tools и case scripts — кандидаты для следующих узких
  рефакторингов. Функциональная эквивалентность/дубли этим аудитом не доказаны.
- Native GitHub search: open PR18/31, Issues6/7/10–14. `gh`401; connector работает.
  Hosted jobs и billing заново не проверены. PR18/Issue10 остаются deferred.

## Чаты и сессии: область и решение

54 пользовательских чата:43 baseline+11 recent. Это выбранный AGR/связанный3D
охват; он не исчерпывает аккаунт.157 внутренних записей отдельно:
136 guardian_review и21 subagent. Их не превращать в157 пользовательских задач.

Классификация:3 ARCHIVE_CANDIDATE,3 KEEP,18 EXTRACTION_PENDING,30 UNKNOWN.
Восемь native reads у session auditor плюс полное root чтение UV; SQLite mode=ro,
индексированные JSONL tails до256KiB. Metadata coverage54; полное извлечение
всех54 не подтверждено.30 отсутствующих indexed JSONL не доказывают потерю
истории: импортированные чаты могут читаться native API. Archived list пуст
на доступной странице; это не основание удалять JSONL.

Рекомендуются к обратимому архиву после сверки manifest:

- «Создать box light на рамках» —2 native turns, нет старого cursor;
  source/scripts/case/state/QA и acceptedv002 сохранены, sceneSHA совпал.
- «Разложить UV стенок в UDIM1001» — root прочитал все3 turns, включая
  уточнение плотности, FBX и acceptance. Case/state/scripts/QA и4 accepted
  assets сверены SHA. Native Max/полный Checker остаются в durable job gates.
- «hi» — оба turns завершились quota error, tools/результатов нет;
  причина сохранена в manifest. Историческая quota error не текущий лимит аккаунта.

Активные гигиена, КПП1 и незавершённая A/B оркестрация —KEEP.
«Установи skills в корень» требует durable пакета:tmp/install evidence и
локальные правки ещё не достаточны для retirement. Остальные pending/unknown
сохранены по ID/coverage/reason. Следующая extraction начинается с этих строк,
а не с повторного общего обхода. Личные excerpts/full transcript в Git не включены.
Ни чат, ни session file фактически не архивирован/удалён.

## Изменения интерфейса работы

Доска связывает направление с входом, владельцем, состоянием и критерием.
Новый worktree создаётся при старте независимой задачи; продолжение сохраняет
свою базу. Успех/неудача сохраняются отдельным проверенным тематическим
коммитом; acceptance/publication/merge фиксируются отдельно. Общие сцены/порты
остаются с одним владельцем. Все8 направлений не заявлены запущенными.

В sidebar выполнены три обратимых перемещения: этот чат→«AGR — управление»,
КПП1→«AGR — объекты», установка skills→«AGR — инструменты». API вернул IDs
и sections; повторный list подтвердил skills и два client-new-thread aliases
в целевых разделах. Точное разрешение aliases не доказано; видимое положение
этих двух чатов в UI не проверено. Existing sections/посторонние чаты сохранены.

## Проверки и сохранность

В этом docs-only worktree обязательные проверки existing codebase:
profiles3/schemas8 OK. Первичный sandbox pytest:220passed/2skipped/1failed;
timeout cleanup получил `ERROR: Access denied`, причина сохранена в run.json.
Разрешённый локальный повтор без правки тестов:222passed/1skipped/1expected warning.
В тестах используются отдельные tmp; PYTHONPATH указывает именно source этого
worktree. DCC build не выполнялся: экспорт/геометрия не менялись.

Независимый review:54 уникальных ID/счётчики совпали;32 retained candidate
artifacts (включая scripts) и accepted SHA совпали;61 локальная Markdown-ссылка
существует. Exact base/history blobs и primary pointer prefix/hash проверены.
Полное извлечение54 и разрешение удалить не установлены.
Primary/source файлы не замещались; только CURRENT_INDEX получает адресный
pointer после backup/hash. Навигация base сохраняется в Git:
STATE blob `edae63b8c13d3a271902cf19451a2c64026f7a36`, PROJECT_MAP blob
`cd25ef40a98b2fcf632a2d46f27328978c49cc64` на exact base7c418f34b74c3669d03ce6a530c366d6894d7a2f.
Восстановление: `git show <base>:<path>` в отдельный файл; работающую папку не reset.
Старые cleanup archives/receipts03.10 не перезаписываются и не выполняются повторно.

## Реестр worktree на начало аудита

У всех перечисленных решений proposed action —retain/review; фактического retirement нет.
Behind/ahead и clean состояние — из read-only snapshot, ignored evidence сохраняются.

- `C:/Users/artsafro/.AGR_Project` — feature/revit-typical-floor@d7ecdfda5f83d0c0ad672a65fc954031fca0cfbc; dirty, активная КПП1.
- `C:/Users/artsafro/.codex/worktrees/agr-bootstrap-20261002/.AGR_Project` — codex/agr-bootstrap-20261002@026b1474d314098104a5f3b0592d87dbaeda2f81; clean,5 local docs commits требуют сверки интеграции.
- `C:/Users/artsafro/.codex/worktrees/codex-orchestration/.AGR_Project` — codex/local-orchestration@9ff80a0606fb73450dd5cacbe880b2f295aac7e5; clean,ignored tmp; upstream ref отсутствует, squash equivalence/recovery pending.
- `C:/Users/artsafro/.codex/worktrees/glb-lessons/.AGR_Project` — codex/glb-window-lessons@a8c6564de65355c8541cda66cb830c1910e4d672; clean,один local lesson commit; перенос не проверен.
- `C:/Users/artsafro/.codex/worktrees/obr22-review/.AGR_Project` — detached@d7ecdfda5f83d0c0ad672a65fc954031fca0cfbc; clean,ignored SYNTH outputs/cache; recovery pending.
- `C:/Users/artsafro/.codex/worktrees/project-map-refresh/.AGR_Project` — codex/window-frames-box-lights-case@bd5f5cdce9375aa308edd990758932bf5d89a541; clean,ignored tmp;4 commits и прежнее имя folder требуют сверки.
- `C:/Users/artsafro/.codex/worktrees/recovered-technical-library/.AGR_Project` — codex/run-evidence-library-20261006@06ecba51b30be4d23bb0016ed77d77d0349add11; clean,ignored tmp;PR31 открыт.
- `C:/Users/artsafro/.gmail/tmp/agr-harness-engineering-20261003` — codex/harness-engineering-20261003@c4f2f095b1166d9f1d3c78e0de6fa615e7e1c54b; clean,ignored tmp;A/B продолжение активно.

Девятый task-owned worktree: `C:/Users/artsafro/.codex/worktrees/project-hygiene-20261006/.AGR_Project`,
`codex/project-hygiene-20261006`, base7c418f34. Его Git commit сохраняет docs;
raw audit receipts находятся в primary tmp. Источник полной проверки branches/base:
`C:/Users/artsafro/.AGR_Project/tmp/project-hygiene-20261006/structure-audit.md`.

## Историческое продолжение первого этапа

Прочитать TASK_BOARD и manifest → выбрать одну pending extraction/операцию →
назначить owner/resource → проверить файлы и сохранить опыт → пересмотреть
конкретную строку. Для фактического удаления нужен отдельный exact manifest,
retention/recovery и разрешённый action. Архив чата не удаляет ignored scenes.
Готовность всех54 к удалению и полная гигиена всех assets не заявлены.
