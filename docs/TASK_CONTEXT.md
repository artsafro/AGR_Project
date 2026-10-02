# Указатель контекста — выбрать один маршрут

Общий вход: [`STATE.md`](../STATE.md). Перед сходной задачей найдите принятый
опыт в [`case_studies/README.md`](case_studies/README.md). При первом знакомстве
прочитайте [`DIGITAL_TWIN_AI_PROJECT_BRIEF.md`](DIGITAL_TWIN_AI_PROJECT_BRIEF.md)
и три профиля в `standards/`; при продолжении читайте только выбранный маршрут.

## Локальная оркестрация NPM/VPM
- Постоянный цикл Codex: AGENTS.md → docs/AGENT_WORKFLOW.md. Результат настройки
  оценивается по работе этого цикла; пилот передачи — его проверочный пример.
- Внешний Cursor CLI: docs/organization/local-orchestration/CURSOR_CLI.md;
  tools/run_cursor_verifier.py. Передача контекста требует явного разрешения;
  native verifier discovery не объявлять до фактического вызова.
- Аудит/схема: docs/organization/local-orchestration/README.md.
- Пилот: docs/organization/local-orchestration/PILOT.md;
  jobs/ORCH-OBR22-NPM/STATE.md и pilot-spec.json.
- Код/запуск: tools/run_profile_pilot.py; src/dt_ai/core/run_record.py;
  tools/export_profile_snapshot.py и tools/check_profile_snapshot.py.
- Проверяющий: .cursor/agents/dt-verifier.md; реальные artifacts и checks отдельно
  от пользовательской приёмки и полного delivery.


## GitHub, очередь и публикация

- Текущая карта: [`organization/PROJECT_MAP.md`](organization/PROJECT_MAP.md).
- Порядок работы: [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md).
- Библиотека операций: [`../technical_library/README.md`](../technical_library/README.md).
- PR #18 / Workbench отложен пользователем и отсутствует в `main`; не начинать
  его ревью, QA или перенос до нового прямого указания.

## Контракты и независимое ядро

- Код: `src/dt_ai/core/`, `src/dt_ai/validate/`, `src/dt_ai/publish/`.
- Схемы: `schemas/`; проверки: `tests/contracts/`, `tests/integration/`.
- AdapterReport: [`ADAPTER_REPORT.md`](ADAPTER_REPORT.md).
- Команды: `python -m pytest -q`, `dt profiles check`, `dt schemas --check`.

## BODY, Exterior, Shell и окна

- Правила: [`GEOMETRY_RULES.md`](GEOMETRY_RULES.md) и
  [`ADAPTER_EXTRACTION.md`](ADAPTER_EXTRACTION.md).
- Exterior: [`EXTERIOR_ADAPTER.md`](EXTERIOR_ADAPTER.md),
  `src/dt_ai/geometry/exterior.py`, `tools/run_exterior.py`.
- Shell: [`BODY_SHELL_ADAPTER.md`](BODY_SHELL_ADAPTER.md),
  `src/dt_ai/geometry/shell.py`, `tools/run_body_shell.py`.
- Принятый объект: [`../jobs/OBR22-K02/STATE.md`](../jobs/OBR22-K02/STATE.md).

## UV, материалы и атласы

- Правила: [`UV_RULES.md`](UV_RULES.md) и [`GEOMETRY_RULES.md`](GEOMETRY_RULES.md).
- UV v006: [`../technical_library/UV_V006.md`](../technical_library/UV_V006.md).
- Атлас окон: [`../technical_library/window_atlas/README.md`](../technical_library/window_atlas/README.md).
- Карты материалов: [`../technical_library/texture_tiles/README.md`](../technical_library/texture_tiles/README.md).
- Принятый процесс Обр22: [`case_studies/OBR22_ACCEPTED_WORKFLOW.md`](case_studies/OBR22_ACCEPTED_WORKFLOW.md).

## DCC и диагностика

- Адаптеры: [`../adapters/README.md`](../adapters/README.md).
- Read-only mesh audit: [`../technical_library/mesh_audit/README.md`](../technical_library/mesh_audit/README.md).
- Каталог интеграций: [`inventory/INTEGRATION_PLAN.md`](inventory/INTEGRATION_PLAN.md).
- Доступность bridge проверяйте в текущем сеансе; наличие файла или порта не
  доказывает правильное приложение, активную сцену или готовность результата.

## Приёмка и опыт

- Правило: [`EXPERIENCE_CAPTURE.md`](EXPERIENCE_CAPTURE.md).
- Шаблон: [`case_studies/TEMPLATE.md`](case_studies/TEMPLATE.md).
- Реестр: [`case_studies/README.md`](case_studies/README.md).
- Публикация, технический QA и пользовательская приёмка — независимые статусы.

## GitHub, локальная гигиена и публикация

- Постоянный цикл: [`organization/GITHUB_CODEX_WORKFLOW.md`](organization/GITHUB_CODEX_WORKFLOW.md).
- Read-only аудит кандидатов: `tools/project_hygiene.py`; отчёт писать в ignored
  `tmp/`, не считать его разрешением на публикацию или удаление.
- Карта веток, PR и Issues: [`organization/PROJECT_MAP.md`](organization/PROJECT_MAP.md);
  перед действием обновлять факты с GitHub и не принимать сохранённый снимок за live-состояние.
