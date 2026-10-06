# AGR — текущий этап

Вход: [шесть направлений и восемь рабочих чатов](docs/organization/PROJECT_MAP.md).
Код и повторяемые операции: [technical_library](technical_library/README.md).
Технические маршруты: [TASK_CONTEXT](docs/TASK_CONTEXT.md).

06.10.2026: выполняется реальная гигиена и интеграция по расширенному запросу пользователя.
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
Предыдущий exact-base QA:222passed/1skipped/1expected warning, profiles3/schemas8.
Финальный QA/review/publish/merge текущей ревизии пока pending.
Следующий шаг: independently review сохранённые кандидаты → адресная уборка →
exact-head QA → local commit → reviewed PR → merge и fresh-main readback.
