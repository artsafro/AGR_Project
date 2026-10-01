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
