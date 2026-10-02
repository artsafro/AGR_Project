## Контур Codex ↔ GitHub: настройка, 02.10.2026

База `origin/main=f652432` после merge PR29; работа ведётся в отдельной ветке
`codex/github-continuous-workflow`, dirty основной checkout не изменяется.
Добавляются единый lifecycle GitHub, always-on rule и read-only аудит локальных
кандидатов `tools/project_hygiene.py` с тестами. Цель: автоматически готовить
узкие коммиты/draft PR и сохранять только воспроизводимый код, техдокументацию,
принятые решения и scoped опыт. Модель не переобучается; продолжение обеспечивают
GitHub main, STATE, case studies и technical library. QA: pytest 222 passed,
1 skipped, 1 expected warning; profiles 3; schemas 8; compile OK. Read-only
проверка основного checkout: 12 tracked changes, 393 untracked кандидата,
18038 ignored-файлов, ошибок чтения 0; полный JSON остаётся локально в `tmp/`.
Первичное независимое review нашло два P2 в secret/symlink/error handling;
они исправлены. Повторное review: blocking findings нет. Merge отдельно.

## PR29 findings: исправления и повторный QA, 02.10.2026

Исправления опубликованы в существующий draft PR #29 implementation-коммитом
`1cd8cb6`. GitHub после push: open=true, draft=true, mergeable=true;
hosted runs `37039712576` и `37039707811` завершились `startup_failure` до jobs,
поэтому не считаются CI-проверкой. Слияние не выполнялось. Следующий шаг —
повторное ревью опубликованного head и отдельное решение пользователя о merge.

Все findings первичного ревью исправлены локально: встроенные A/B-сценарии
привязаны к SHA256 входов и ожидаемого PNG, манифест фиксирует входы,
конфигурацию, renderer и результат, добавлены regression-тесты. Выяснено, что
файл по mutable-пути A v001 изменился после исходной фиксации: строгий replay
совпадает с закреплённым SHA256 `1d91e004...`, но не с текущим файлом
`3a9b2a6a...`; B v002 остаётся равен текущему референсу. Delivery=false,
native MAX/FBX/Checker открыты. Независимое повторное read-only ревью не нашло
новых findings и подтвердило закрытие четырёх исходных. Полный local QA:
pytest 217 passed/1 skipped/1 warning; profiles 3,
schemas 8; strict A/B replay и изменённый вход проверены; SYNTH DCC
development=true/delivery=false. PR #29 остаётся draft и не сливается.

## Чат-опыт ГЛБ: draft, 02.10.2026

База main07e9ec8; отдельная ветка codex/glb-atlas-learning-20261002.
Один Python renderer+конфигурация A/B, README/SOURCE/QA и два кейса.
A/B strict replay совпал с закреплёнными SHA256; текущий mutable A v001 расходится,
текущий B v002 совпадает по пикселям и байтам. Первичный review выявил findings.
Актуальный полный локальный recheck:217passed/1skipped/1warning,profiles3,schemas8.
Предыдущий restricted pytest дал taskkill returncode1; последующие полные recheck прошли.
Доказательства: technical_library/glb_atlas/QA.json и
docs/organization/CHAT_AUDIT_2026-10-02.json; курсоры успешного разбора обновлены.
Native MAX remap пока не перенесён: новый параметризованный fileIn/readback
не проверен; README задаёт следующий шаг на отдельной копии сцены.
A v004 был пересохранён: старые ID13=114/ID5=0 не описывают текущий v005.
FBX/alpha/Checker и полная сдача не заявлены; два корпуса — один проект.
Большие outputs остаются локальными; PR18 отложен; этот draft не слит.
Следующий шаг: ревью draft и отдельный native Max remap/readback.

## PR28 слит в main — 01.10.2026

Пять замечаний исправлены, regression fixtures и независимое ревью завершены.
Exact reviewed head: 5aee477472f9363aed7681ec9fa2f4d9fc55c5d9.
Squash merge: 64441f5bf1230b9cb73d65708b4ee95b974dbbab; GitHub merged=true
и origin/main перечитаны. PR28 закрыт; PR18 остаётся отложенным.
QA:213passed/1skipped/1expectedwarning; profiles3/schemas8OK;
SYNTH DCC development=true/delivery=false; actual golden FBX46objects/5206tris
readbackOK; synthetic native render scope/dependencies/camera/scale/sourceSHA
проверены. Полная сдача модели не заявлена. Evidence:
docs/organization/local-orchestration/PR28_FIX_QA.json.
Hosted Actions reviewedhead run217/36923667587 startup_failure,jobs=[];
это отдельное ограничение Issue7, не local test failure или CI pass.
Основной dirty checkout не переключался; approved inputs/legacyCLI сохранены.
Следующий шаг: новая задача по циклу AGENT_WORKFLOW; перед продолжением сверить
локальный код с main. Для Issue7 восстановить запуск GitHub Actions.
Ниже сохранена история публикационных этапов.

## Оркестрация Codex: опубликовано в PR #28 — 01.10.2026

База main fc48f1a; ветка codex/local-orchestration; PR https://github.com/artsafro/AGR_Project/pull/28 открыт, не слит. Implementation head db371f8. Hosted run213:startup_failure до jobs (Issue7); localQA отдельно.
AGENTS задаёт обязательный цикл: цель → изучение → вопросы → требования → план →
исполнение → независимая проверка → исправления → передача/STATE.
TASK_CONTEXT/AGENT_WORKFLOW, dt-verifier, RunRecord и узкие локальные runners
публикуются вместе с compact audit/pilot/CLI evidence. Codex ведёт текущий чат;
Cursor CLI дополнительный reviewer, actual custom dt-verifier подтверждён.
Реальный pilot-004: saved-file/ZIP/Blender/Max reverse transfer и resume проверены;
full delivery/visual gates остаются открытыми, delivery=false.
Документы: docs/organization/local-orchestration/README.md, EXECUTION.md,
CURSOR_CLI.md и cursor-cli-evidence.json. Sources/scenes/outputs/transcripts
локальные и не копируются; чужие изменения checkout сохранены. PR18 не затронут.
QA publishing: pytest178passed/1skipped/1warning,profiles3/schemas8OK; SYNTH-001 development=true/delivery=false,exit0. PUBLICATION.md описывает команды и ограничения. Прошлые числа в evidence
относятся к исходному локальному pilot, а не тестам нового main.

## GitHub audit remediation — 01.10.2026

База `main` `a99b8ec`; ветка `codex/github-audit-remediation`. Аудит: последние
100 Actions runs — `startup_failure`, main unprotected, GitHub health28%.
Чистый новый venv прошёл install/pip check, profiles3, schemas8 и
pytest156passed/1skipped/1expected warning; pip-audit CVE0, secret-pattern hits0.
Добавлены TASK_CONTEXT/AGENT_WORKFLOW, governance/security/templates/dependabot;
workflow ограничен и pin по SHA, stale docs/links исправлены. PR18 не затронут.
Далее: локальный QA, PR/merge, затем GitHub settings/labels/branch cleanup и
проверка нового Actions run. Billing/protection могут остаться внешним блокером.

## Все группы технической базы — 01.10.2026

Пройдены15 групп:601 исходный путь, из них11 Workbench учтены по прошлому
inventory и отложены. Реестр маршрутов: technical_library/GROUP_REVIEW.md;
SHA/синтаксис/дубли — SOURCE_COVERAGE.jsonl и GROUP_REVIEW.json. Python AST без
ошибок; MAXScript syntax/native QA не подтверждены. Пять групп одинаковых файлов,
57 совпадающих функций отмечены для reuse, originals не удаляются.
Добавлены mesh_audit (core+Blender), texture_tiles (CLI+панельный recipe+JSON);
metric_pattern переиспользует tools/facades_texture_pattern.py.
Native Blender4.4:9 read-only saved-file audits, SHA входов неизменны;
11 КПП PNG pixel/byte-identical, ZIP readback equal. UV/atlas/box lights — прежние
проверенные этапные пакеты; непринятые builders остаются локальными кейсами.
QA PR checkout:156passed/1skipped/1expected ZIP warning; profiles3/schemas8OK;
SYNTH-001 DCC readback:development=true/delivery=false. PYTHONPATH указывал src
этой рабочей копии, не editable install общего checkout. Hosted CI не заявлен.
Max BRIDGE_DOWN; PR18 отложен и не затронут. PR25 слит в `main` как `946acad`.
PR26 проверен в отдельном checkout на базе `946acad`; реализация и актуализация
статусов зафиксированы в `4a34712`. Все9 mesh readback совпали с evidence;
для ground `.blend` выбран документированный объект `SM_GROUND_NPM_Ground`.
UV replay повторён с `--disable-autoexec`: все4 стадии и FBX readback прошли.
Большие outputs не загружаются; SHA-реестр не бэкап. Пакет публикуется через
PR26; далее для Max восстановить live bridge и отдельно проверить нужный инструмент;
второй проект/полная визуальная и Checker приёмка остаются отдельными воротами.

[Предыдущие состояния и проверки](docs/history/TECHNICAL_LIBRARY_STATE_BEFORE_ALL_GROUPS_2026-10-01.md).
Маршрут остальных направлений: [PROJECT_MAP](docs/organization/PROJECT_MAP.md).
