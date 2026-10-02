# Карта AGR_Project

Актуальность: 02.10.2026. Это указатель на файлы и PR, а не свидетельство готовности
реальных ОКС. Репозиторий один: `artsafro/AGR_Project`. Исходные рабочие папки и
игнорируемые результаты DCC остаются локальными. По решению пользователя
29.09.2026 около 4 ГБ `outputs/` не загружать в GitHub.

Все15 групп: [маршруты/проверки/ограничения](../../technical_library/GROUP_REVIEW.md).
PR26 добавил общий mesh inventory и карты материалов в `main`; не каждый исходный
builder принят или перенесён. Max native QA недоступен; PR18 остаётся отложенным.

## Где искать

- `technical_library/` — компактные пакеты операций, общий код и доказательства;
  UV v006 объединён в четыре этапа. Сотни временных вариантов не публикуются.
- [Ретроспективный аудит PR и исходников](TECHNICAL_MIGRATION_AUDIT.md) — снимок
  01.10.2026, включая слитые PR, отдельные drafts и локальные варианты.

- `standards/` и `docs/decisions/` — источник норм, страницы PDF и расхождения.
  Три YAML не меняются по пересказу чата.
- `src/dt_ai/` — независимое ядро; `adapters/` — выполнение в Blender, Max,
  Revit и CAD. Доступность адаптера проверяется в текущем сеансе.
- `jobs/<ID>/` — объект, входы, версии и его `STATE.md`. Файлы в `outputs/`
  обычно игнорируются Git и не восстанавливаются из клона.
- `max/AGR_Workbench/` — планируемый перенос собственных инструментов Max.
- `docs/case_studies/` — подтверждённый опыт с точной областью приёмки,
  неудачами и непроверенными пунктами. Новую запись оформлять по
  `docs/EXPERIENCE_CAPTURE.md` и шаблону в этом каталоге.
- `docs/organization/` — карта чатов, процесс извлечения опыта и миграция.
  [Контур Codex ↔ GitHub](GITHUB_CODEX_WORKFLOW.md) задаёт fetch/worktree,
  read-only аудит локальной папки, отбор, QA, PR, merge и обновление опыта.
  [Библиотека сценариев](SCRIPT_LIBRARY.md) — проверенные скрипты, запуск и ограничения.
  [Правила обхода](CHAT_LEARNING_LOOP.md), [реестр чатов](CHAT_REGISTER.md)
  и [исходное состояние](CHAT_LEARNING_STATE.json) образуют маршрут работы с опытом.

Перед задачей читать корневой `STATE.md`, затем `docs/TASK_CONTEXT.md` и
состояние конкретного job. Не считать локальный checkout равным `main`.

## Что сейчас в GitHub

Сверенная база `main` — `f652432`, после PR27–PR29.
В main находятся библиотека PR26, настройка оркестрации PR28 и пакет ГЛБ PR29.
PR18 остаётся единственным открытым, черновым и отложенным пользователем.
Не начинать его ревью/QA/слияние без нового прямого указания. Пакет ГЛБ и его
ограничения: [каталог](../../technical_library/glb_atlas/README.md).

GitHub Actions остаётся неработоспособным: последние 100 runs завершились
`startup_failure` до запуска jobs из-за ограничения billing/spending. Чистая
локальная установка exact `main` 01.10.2026 прошла: `pip install -e .[dev]`,
`pip check`, profiles3, schemas8 и pytest156passed/1skipped/1expected warning.
Это не hosted CI и не Ubuntu-runner evidence.

## Ход организации

- Артефакты: 1874 ignored outputs (~4 ГБ) учтены SHA-манифестом, но внешней
  резервной копии нет; Issue #6 открыт.
- Навигация: корневой STATE сжат с сохранением истории; `TASK_CONTEXT.md` и
  `AGENT_WORKFLOW.md` опубликованы. Issue #20 закрыт после PR27.
- Ядро: AdapterReport и Connect/Exterior/Shell опубликованы; Issues #8 и #9 закрыты.
- Материалы/объекты: частичные пакеты опубликованы, но Max roundtrip, отдельные
  кейсы и визуальные ворота продолжаются в Issues #11–#13.
- Нормы: конфликт новой редакции PDF и действующих YAML остаётся в Issue #14.
- Workbench: Issue #10 и PR #18 приостановлены по указанию пользователя.
- CI: Issue #7 остаётся P0 до первого фактически выполненного hosted workflow.

## Порядок следующих действий

1. Восстановить GitHub Actions по Issue #7, затем включить обязательный check для
   `main`. До этого каждый PR получает exact-head локальный QA с явной маркировкой.
2. Для пакета ГЛБ отдельно проверить native Max remap/FBX/Checker.
3. Решить резервирование ignored outputs вне GitHub по Issue #6.
4. Продолжать #11–#14 узкими PR по одной операции или одному нормативному конфликту.
5. PR #18 не включать в очередь до нового прямого указания пользователя.

Перед каждым merge сверять diff, exact head/base и затронутые риски. Один
`mergeable=true` означает только отсутствие конфликта Git. Публикация, технический
QA, пользовательская приёмка и delivery — четыре независимых статуса.

## Открытые Issues

- [#6 — локальные артефакты](https://github.com/artsafro/AGR_Project/issues/6)
- [#7 — GitHub Actions](https://github.com/artsafro/AGR_Project/issues/7)
- [#10 — Workbench](https://github.com/artsafro/AGR_Project/issues/10), отложен
- [#11 — фасадные атласы и Max roundtrip](https://github.com/artsafro/AGR_Project/issues/11)
- [#12 — кейсы отдельных объектов](https://github.com/artsafro/AGR_Project/issues/12)
- [#13 — внешние инструменты](https://github.com/artsafro/AGR_Project/issues/13)
- [#14 — конфликт PDF/YAML](https://github.com/artsafro/AGR_Project/issues/14)
- [#20 — STATE и маршруты](https://github.com/artsafro/AGR_Project/issues/20),
  закрыт после PR27

## Ограничения

- GitHub не восстанавливает локальные `.blend`, FBX и PNG из ignored outputs.
- Security alerts API недоступны; отсутствие доступного списка не означает ноль alerts.
- Native Max, полный AGR Checker, второй проект и новая визуальная приёмка остаются
  отдельными воротами там, где они указаны в case study или evidence.
- Новую редакцию PDF нельзя применять вместо YAML без решения со страницей источника.
