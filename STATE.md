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
