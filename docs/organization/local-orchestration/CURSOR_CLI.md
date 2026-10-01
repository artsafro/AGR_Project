# Внешний Cursor CLI — локальная настройка 01.10.2026

Бинарник: `C:/Users/artsafro/AppData/Local/cursor-agent/agent.cmd`.
Локальный `--help` выполнен exit0: режимы ask/plan read-only, sandbox,
headless stream-json и явный workspace поддерживаются установленной версией.
Фактический запуск установил: OS sandbox поддерживается только macOS/Linux;
на Windows CLI предлагает allowlist mode. Launcher подготовлен для
`--sandbox disabled --mode ask --trust`. Пользователь отдельно разрешил этот
режим и передачу перечисленного контекста. Фактический запуск004 прошёл.
Скрипт: `tools/run_cursor_verifier.py`. Никаких API keys, глобальных settings,
PATH, модели, MCP approvals или DCC настроек не изменено.

Из любого PowerShell, для следующего запуска выбирать новое имя:

```powershell
& 'C:/Users/artsafro/.AGR_Project/.venv/Scripts/python.exe' 'C:/Users/artsafro/.AGR_Project/tools/run_cursor_verifier.py' --run-id cursor-20261001-005
```

Для повторения выбирай новое имя run. Версия бинарника и хеши входов закрепляются
в RunRecord; stdout/stderr и cli-evidence.json сохраняются в
`jobs/ORCH-OBR22-NPM/cli-runs/<run-id>/`. Timeout завершает только собственное
дерево процессов и фиксирует cleanup. `ask`, `sandbox disabled` (Windows allowlist), `--print` и
`--trust` заданы явно; trust относится к запуску в данном workspace.
`--force`, `--approve-mcps`, API key в аргументах и cloud DCC не используются.
CLI разрешено прочитать запрошенные документы и автоматически загружаемые
workspace инструкции; prompt запрещает shell/DCC/MCP, правки и чтение credentials.
Prompt ограничивает действия модели; это не filesystem allowlist пяти файлов.

Запрошенный контекст для сервисa Cursor:

- `.cursor/agents/dt-verifier.md`;
- `jobs/ORCH-OBR22-NPM/STATE.md`;
- `jobs/ORCH-OBR22-NPM/pilot-spec.json`;
- `docs/organization/local-orchestration/execution-evidence.json`;
- `docs/organization/local-orchestration/REVIEW.md`;
- автоматически загружаемые инструкции проекта, например AGENTS.md.

От агента требуется фактический verdict по исполненному пилоту и честное указание
actual delegation. Файл dt-verifier сам по себе не доказывает native discovery.
Если CLI не поддерживает custom subagents, результат обозначается direct CLI
review; ни exit0, ни текст ответа не означают model delivery/visual acceptance.
Stream events нужны для проверки фактического вызова subagent tool.

Статус: пользователь явно разрешил перечисленный контекст сервису Cursor.
Попытка `cli-runs/cursor-20261001-003` действительно запустила CLI; stderr:
`Sandbox mode is enabled but not available on this system. Sandbox requires macOS or Linux.`
Код exit1, модель не вызвана.001/002 сохраняют исправленные локальные ошибки
регистрации outputs/logs. Python compile и git diff check exit0.

Исторически переход на Windows allowlist auto-review отклонил до старта.
После отдельного разрешения пользователя запуск004 выполнен: exit0,
stream result success,39366мс. Native `taskToolCall` с
`subagentType.custom.name=dt-verifier` завершён success; call id
`toolu_016x1rNB61u7hhzgZZDqMTXi`. В логе только task/read tools, прочитаны
ровно пять запрошенных файлов. Shell/DCC/MCP/write вызовов не обнаружено.
Read-only ask — режим CLI, не OS isolation.

Свидетельства: `jobs/ORCH-OBR22-NPM/cli-runs/cursor-20261001-004/`:
`cursor-verifier-summary.json`, `verdict.md`, `cli-evidence.json` и transcript
`attempt-001/logs/cursor_verifier/stdout.log` (SHA закреплён в summary).
Parser проверяет exit0, финальный success и completed custom task отдельно;
первоначальная transcript сохранена, её локальная обработка не вызывает сервис.
Подключение/actual delegation подтверждены. Полная сдача модели остаётся false.
QA после добавления parser: pytest138 passed/1 skipped/1 expected warning,exit0;
profiles3/schemas8OK,py_compile/gitdiffcheck exit0. Три synthetic stream fixtures
проверяют, что exit0 без финального result и started-only task не выдаются за
успех/delegation; неожиданный shell tool обнаруживается. Native CLI evidence004
существует отдельно от fixtures. Каталог cli-runs игнорируется Git.
Проверяющий отметил исторически устаревшие поля design spec и CLI pending в
прочитанном STATE/evidence; они не опровергают фактические artifact evidence.
