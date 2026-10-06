# AGR — рабочий проект

[STATE](../../STATE.md) — текущий этап; [TASK_CONTEXT](../TASK_CONTEXT.md) — технический маршрут;
[библиотека операций](../../technical_library/README.md) — повторяемый код и QA.

## Проект

1. **Гигиена и интеграция.** Чаты «AGR · Гигиена и структура» (`01a112ee-e174-7230-99ad-f97f66d76f2a`) и «AGR · GitHub и накопление опыта» (`01a0edad-00b6-7712-acac-7ff555a2d751`). Ветка `codex/project-hygiene-20261006`; начало этого этапа090d8b2, base7c418f34. Issues6/7: сохранность assets и фактически выполненный CI; Issue14: PDF/YAML конфликт, нормы без отдельного решения не заменяются. Вход — [аудит и фактические действия](HYGIENE_AUDIT_2026-10-06.md).

## Разработка

2. **Оркестрация и инструменты.** «AGR · Оркестрация агентов» (`01a0f6be-fba5-7833-9df9-5232fdc338ff`) и «AGR · Skills и правила» (`01a111bc-11b7-7360-b35a-5d020abc72b3`). Harness branch `codex/harness-engineering-20261003@c4f2f095`; inspector PR31 слит в main d53cb5f (reviewed head06ecba51). A/B требует продолжения, installer handoff сохранён отдельно. Вход — [оркестрация](local-orchestration/README.md), [библиотека](../../technical_library/README.md). Workbench/PR18/Issue10 остаются отложенными; их не возобновлять из гигиены.

## Объекты

3. **КПП1 · ВПМ здания.** Чат `01a112cd-280b-7862-befb-f228eecc5efe`; активный владелец Revit/Blender. Local-only `C:/Users/artsafro/.AGR_Project/jobs/KPP1-VPM/STATE.md`; primary feature/revit-typical-floor@d7ecdfda dirty, автоматически не переключается. BODY → окна → кровля → декор → оборудование; native/readback/visual/Checker по job.

4. **Обр22 · Геометрия и операции.** Чат `01a0ddd1-4d2c-79e3-84a7-b8048f0cb972`; [принятый кейс и ограничения](../case_studies/OBR22_ACCEPTED_WORKFLOW.md), `jobs/OBR22-K02/STATE.md` в primary. Connect/Exterior/Shell — из библиотеки; отдельные новые операции получают свой worktree.

5. **ГЛБ · НПМ и фасадные атласы.** Чат `01a0ebe4-71b4-70c3-90dc-03fa3cc956ff`; [GLB package](../../technical_library/glb_atlas/README.md), [границы A](../case_studies/GLB_A_MAIN_ATLAS.md), [границы B](../case_studies/GLB_B_MAIN_ATLAS.md). Верхушка была отклонена; её не возобновлять автоматически. Max reverse-export/readback и manual gates остаются у job.

6. **СОШ1150 · Окна и витражи.** Чат `01a0ec14-b5fa-7810-abe3-e87a72701103`; local-only `C:/Users/artsafro/.AGR_Project/jobs/REVIT-OPENINGS/STATE.md`, [оконный атлас](../../technical_library/window_atlas/README.md). Приблизительные типы/placements не приняты; геометрия и native QA требуют своего контракта.

## Одна задача — один результат

Направления выше содержат очередь узких задач; все шесть не запускаются одновременно.
В существующем job STATE/PLAN или STATE worktree записывать цель/критерии, входы/версии, owner, allowed files, worktree/branch/base/head, зависимости, actual QA/evidence, acceptance/publication и next.
Новая независимая code-задача — fresh-main worktree `codex/<scope>`; продолжение сохраняет свою базу. У общей сцены/порта/экспорта один writer.
Успех и полезная неудачная проба сохраняются тематическим local commit с честным статусом: named staging → review → commit → readback. Публикация/merge отдельны.
Чат архивируется после durable handoff; assets/session files не удаляются вместе с ним. Unknown и уникальные материалы остаются сохранены.

## Состояние и история

Текущие chat/worktree действия — [manifest](CHAT_RETIREMENT_2026-10-06.json) и [аудит](HYGIENE_AUDIT_2026-10-06.md).
Исторические audits/реестры — [docs/history/organization](../history/organization/).
Исходные STATE/PROJECT_MAP на base7c418f34 сохранены в Git; датированные статусы старых PR не сегодняшняя очередь. Ignored blend/FBX/PNG не восстанавливаются из клона; Issue6 запрещает их массовую загрузку.
