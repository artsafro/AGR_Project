# Рабочая доска AGR — 06.10.2026

Восемь направлений помогают выбирать работу. Направление содержит очередь отдельных задач;
worktree создаётся под одну независимую задачу, когда начинается исполнение. Это не восемь
запущенных исполнителей. Общий процесс уже задан в [AGENT_WORKFLOW](../../AGENT_WORKFLOW.md).
Текущая версия и аудит: [PROJECT_MAP](../../organization/PROJECT_MAP.md), [HYGIENE_AUDIT](../../organization/HYGIENE_AUDIT_2026-10-06.md).

## Направления и текущие владельцы

### H01. Гигиена и навигация

- Владелец: root этого чата.
- Worktree/ветка: codex/project-hygiene-20261006.
- Состояние: Текущий этап: аудит → docs → review → local commit.
- Вход: [docs/organization/TASK_BOARD.md](TASK_BOARD_BEFORE_CONSOLIDATION.md).
- Критерий: Проверенные ссылки, manifest кандидатов, сохранённая история.

### H02. КПП1 / ВПМ

- Владелец: активный чат «Смоделировать ВПМ здания по этапам».
- Worktree/ветка: primary feature/revit-typical-floor; перенос не выполнен.
- Состояние: В работе; одна Blender/Revit сцена, один владелец.
- Вход: `jobs/KPP1-VPM/STATE.md` — local-only в primary; отсутствует в этом клоне.
- Критерий: BODY → окна → кровля; native/readback/visual/Checker по job.

### H03. Оркестрация и evidence

- Владелец: владелец не подтверждён; сначала сверить активную задачу.
- Worktree/ветка: codex/harness-engineering-20261003; inspector codex/run-evidence-library-20261006.
- Состояние: A/B незавершён; PR31 открыт, merge не разрешён.
- Вход: [docs/organization/local-orchestration/README.md](../../organization/local-orchestration/README.md).
- Критерий: Версии evidence и восстановление; PR31 отдельно от local monitor.

### H04. Материалы / UV / фасадные атласы

- Владелец: не назначен.
- Worktree/ветка: worktree создаётся при запуске независимой операции.
- Состояние: Очередь Issue11; A/B accepted snapshots сохранить.
- Вход: [technical_library/glb_atlas/README.md](../../../technical_library/glb_atlas/README.md).
- Критерий: Повторный FBX→Max→export/readback и соответствующая visual приёмка.

### H05. Кейсы и геометрические операции

- Владелец: не назначен.
- Worktree/ветка: codex/window-frames-box-lights-case занят до проверки владельца.
- Состояние: Очередь Issue12: Object013, знаки, оконный атлас.
- Вход: [docs/case_studies/README.md](../../case_studies/README.md).
- Критерий: Один объект/операция на task; отрицательные результаты и limits сохранять.

### H06. DCC-адаптеры и библиотека инструментов

- Владелец: не назначен.
- Worktree/ветка: новый worktree при конкретном переносе.
- Состояние: Очередь Issue13; только собственный bounded package.
- Вход: [adapters/README.md](../../../adapters/README.md).
- Критерий: Происхождение, запуск, native capability, версии, QA; без копирования всей папки.

### H07. Нормы и конфликт PDF/YAML

- Владелец: не назначен.
- Worktree/ветка: новый worktree при запуске.
- Состояние: Очередь Issue14; исходные нормы неизменны.
- Вход: [standards/](../../../standards).
- Критерий: Страницы/хеши/применимость и отдельное approved решение.

### H08. GitHub / CI / сохранность assets

- Владелец: не назначен.
- Worktree/ветка: новый worktree для исправления CI при установленной причине.
- Состояние: Issues7 и6: hosted jobs и резервирование отдельными операциями.
- Вход: [docs/organization/GITHUB_CODEX_WORKFLOW.md](../../organization/GITHUB_CODEX_WORKFLOW.md).
- Критерий: Фактически выполненные hosted jobs; assets backup только в разрешённое место.

## Карточка одной задачи

Использовать существующий job STATE/PLAN; для code/docs-задачи — короткую секцию
STATE своего worktree. Обязательные поля: цель и критерий; точные входы/версии;
allowed files и ограничения; владелец; worktree/ветка/base/head; зависимости;
команды и результаты QA; evidence; implemented/qa/acceptance/publication;
ошибки; следующий шаг. Не заводить параллельный реестр тех же фактов.

## От постановки до закрытия

1. Проверить existing worktrees, владельца и dirty state. Продолжение сохраняет
   свою базу; новая независимая задача — fetch и свежий default branch.
2. Назначить `codex/<scope>` и один worktree; исходный dirty checkout сохраняется.
   Не копировать чужие untracked/ignored outputs автоматически.
3. Выполнить узкий контракт. У сцены/порта/экспорта отдельный единственный владелец.
4. Независимо проверить сохранённый результат. Успех, частичный результат и неудача
   получают evidence, точную область и следующий шаг. Ошибки сохранять как опыт.
5. Сохранить проверенные task-owned source/docs/config/evidence в тематическом
   локальном commit: named paths → staged diff → commit → Git blob readback.
   Полезная неудачная проба тоже может получить commit с честным статусом trial.
6. Публикация и merge — отдельные состояния и разрешения. После merge проверить
   actual main; worktree закрывается только после сохранения ignored assets.
7. Чат может перейти в архив, когда вся нужная постановка, решения, исходники,
   версии, результаты и следующий шаг читаются из файлов без истории переписки.

## Гигиена

Архив чата, удаление session JSONL, удаление worktree и удаление assets — разные
операции. Manifest содержит ID/точный путь, причину, сохранённую замену, версии,
read coverage, missing gates, retention и предлагаемый action. Одного коммита или
похожего названия файла недостаточно. Чаты с неудачами можно архивировать после
сохранения отрицательного опыта; открытые native gates остаются у job.

Текущие рекомендации: [manifest](CHAT_RETIREMENT_INITIAL_2026-10-06.json).
Он не разрешает удаление session files. Unknown/active/unique остаются retain.
Реестр 29.09 и предыдущие аудиты — исторические снимки, их не переписывать.
PR18/Issue10 остаются отложенными и не входят в исполняемую очередь.
