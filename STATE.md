# AGR — интеграция скриптов и зависимостей,20.10.2026

Собраны изменения [PR37](https://github.com/artsafro/AGR_Project/pull/37),
[38](https://github.com/artsafro/AGR_Project/pull/38), [39](https://github.com/artsafro/AGR_Project/pull/39),
[40](https://github.com/artsafro/AGR_Project/pull/40), [41](https://github.com/artsafro/AGR_Project/pull/41).
Актуальный published HEAD/merge статус сверять с GitHub; base745bc136.
[Max материалы/FBX](technical_library/max_texture_linker/README.md) и
[Blender сглаживание](technical_library/mesh_audit/SMOOTHING.md) доступны через
[общий каталог](technical_library/README.md); source QA и ограничения рядом.
Pydantic2.14.1, pypdf6.20.1, Shapely2.2.0; остальные пины сохранены.
PR18 отложен. Primary dirty, активные задачи и модели сохраняются у владельцев.
CI не запускал шаги из-за billing account lock; это не hosted test pass.
Merge библиотеки не закрывает visual/user/full AGR gates.
Следующее действие: выбирать сценарий по входам/версии и проверять его границы.

## История отдельных этапов переноса

# NPM Max Texture Linker — перенос 17.10.2026

Отдельная ветка `codex/chat-learning-linker-20261017`, base `745bc13634b61c54a30c65e8a3ccf6398f8dbb26`.
Источник: завершённый чат `01a144e6-015a-7ce0-af8f-9ecbfc8b2c45`, commits59fbef2/9a4e3c2.
[Пакет](technical_library/max_texture_linker/README.md) · [receipt](technical_library/max_texture_linker/TRANSFER_QA.json) · [каталог](docs/organization/SCRIPT_LIBRARY.md).
Четыре исходника совпали с источником побайтно; свежие329tests/3skips, profiles3/schemas8,
native39checks Max2024.2.5 synthetic roundtrip passed. Независимое review без blockers.
Финальная пользовательская/визуальная приёмка, реальный пакет, full AGR Checker и
forced export error/Cancel остаются pending. PR только draft; не merge.
PR18, активные задачи, primary implementation и модели не изменены.
Следующий шаг: review draft по точному head, без запуска на пользовательской сцене.

# Blender smoothing transfer — 20.10.2026

Branch codex/blender-smoothing-transfer-20261020; base745bc13634b61c54a30c65e8a3ccf6398f8dbb26.
[Сценарий](technical_library/mesh_audit/SMOOTHING.md) · [QA](technical_library/mesh_audit/SMOOTHING_QA.json) · [кейс](docs/case_studies/BLENDER_SMOOTHING_4_4.md).
16mesh: fresh native raw/evaluated/shading equal historical.blend1; source unchanged.
Current.blend differs, retained untouched; no silent restore. Visual/user/fullAGR pending.
One compact draft PR; no merge. PR18, active scenes, config and local models untouched.
Next: review exact draft head and scoped limits; broader use needs another representativecase.

# Гарибальди + ДГП — перенос рабочих скриптов, 15.10.2026

Цель: актуальные файлы/расхождения проверены; подготовлен один compact draft PR без
моделей и временных версий. [Кейс/версии/приёмка](docs/case_studies/GARIBALDI_DGP_SCRIPT_TRANSFER.md).
Base origin/main2011676288970760b024908b79a7c012d29ddff4 после fetch; branch
codex/garibaldi-dgp-library-20261015, owner root. Primary checkout не изменялся.
Код: SINTEZ repair/readback и расширение существующего texture_tiles; входы/параметры
в config, новые output-only каталоги, явные guards и источник/результат hash QA.
Гарибальди: SOURCE ZIP найден, прежняя ошибка пути UTF8/cp1251 исправлена; missing
corrected ZIP восстановлен новым экспортом и отдельным native import/check.
6 mesh signatures и17packed textures равны историческому маршруту;44nativegroups без errors.
ДГП:43PNG byte/pixel equivalent старому маршруту;4changed/39unchanged. Current8eb2...
прочитан в Max2024.2.5:16objects/343291triangles; геометрия/UV/IDs/smoothing/transform
совпали сv4 в native formatting, только3visibilityflags отличаются; модели не менялись.
273passed/2skipped, затем пропущенный DCCroundtrip отдельно1passed; remaining skip:
Windows symlink privilege. Profiles3/schemas8OK. Expected duplicate-ZIP warning.
Независимое review выявило и проверило исправление late input-driftguard; focused26passed.
Подробные private receipts/новые outputs: primary tmp/garibaldi-dgp-20261015; вGit
только code/config/docs/compactQA/tests. Исходники и предыдущие версии сохранены.
Ограничения:28manual/УКЭП/visual/fullAGRdelivery pending; точная причина старого Max
binarySHAнеизвестна, currentQA отдельный; explicitnormals/polygonlayout/VPMscale/seamless
не доказаны. Публикация подтверждается URL PR, merge не выполняется.
Следующий шаг: review draftPR и отдельное решение о merge; не пересохранять модели.
Коммит этого этапа: git log -1 -- technical_library/sintez_repair/repair.py.

---

# AGR — текущий этап

Вход: [шесть направлений и восемь рабочих чатов](docs/organization/PROJECT_MAP.md).
Код и повторяемые операции: [technical_library](technical_library/README.md).
Технические маршруты: [TASK_CONTEXT](docs/TASK_CONTEXT.md).

06.10.2026: выполнена гигиена и интеграция по расширенному запросу пользователя.
Владелец root; worktree `codex/project-hygiene-20261006`, исходная base7c418f34,
предыдущий verified stage090d8b2. Исторические docs вынесены в history,
TASK_BOARD объединён в PROJECT_MAP, SCRIPT_LIBRARY — в technical_library/README.
Sidebar: AGR · Проект / AGR · Разработка / AGR · Объекты.

КПП1 остаётся у активного владельца в primary dirty checkout; сцены/нормы/approved
сохраняются. PR18 deferred. Архив чатa обратим, assets не удаляются.
Статусы и доказательства: [аудит](docs/organization/HYGIENE_AUDIT_2026-10-06.md),
[retirement manifest](docs/organization/CHAT_RETIREMENT_2026-10-06.json).

Интегрирован main d53cb5f после независимо проверенного merge PR31.
RunRecord inspector: docs/organization/local-orchestration/RUN_EVIDENCE.md.
Интегрированный local QA:248passed/1skipped/1expected warning (43.96s),
profiles3/source hash/traceability и schemas8 OK.11 чатов архивированы;
два старых чистых worktree закрыты после независимого восстановления411файлов.
История и ветки сохранены; один рабочий PROJECT_MAP и один каталог операций.
Независимое review snapshot80cb8c79: открытых findings нет;
247 действующих Markdown-ссылок valid,108 сохранённых artifact SHA совпали.
Публикационный статус структуры: [PR32](https://github.com/artsafro/AGR_Project/pull/32);
реальная merged/head/base информация проверяется по GitHub, hosted CI отдельно.
Evidence/recovery: local-only tmp/project-hygiene-20261006/{final-consolidation-review,
integrated-qa-receipt,worktree-retirement-manifest}; full bundle рядом в retained-worktrees.
Следующий этап: выбрать одну задачу в PROJECT_MAP и начать её от fresh main;
продолжение активной КПП1 сохраняет свой job STATE и базу.
