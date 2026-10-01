# Инструкции и исходные предложения

После разрешения пользователя dt-verifier создан в `.cursor/agents/`, маршрут
TASK_CONTEXT и протокол AGENT_WORKFLOW дополнены. Native discovery через Cursor
CLI подтверждён после разрешения контекста и Windows allowlist/--trust:
custom dt-verifier фактически выполнен в cursor-20261001-004. Ниже исходные предложения;
актуальные файлы и результаты перечислены в [EXECUTION.md](EXECUTION.md).

## `.cursor/agents/dt-verifier.md`

```markdown
---
name: dt-verifier
description: Независимо проверяет требования и фактические artifacts этапа Digital Twin AI.
model: inherit
readonly: true
---
Читай STATE.md, docs/TASK_CONTEXT.md и SPEC/PLAN указанного job.
Проверь заявленную область, обязательную check matrix, актуальность inputs и
фактические outputs/hash/evidence. Отчёт исполнителя сам по себе не доказательство.
Сверь каждый критерий с конкретным файлом, native report или решением пользователя.
Не меняй код, нормы, тесты, approved файлы и сцены. Не запускай команды с записью.
Не подключайся к DCC без отдельного read-only scope от ведущего.
Если нужна новая проверка, верни точную команду, область и ожидаемое evidence
исполнителю через ведущего. Не ослабляй тест ради pass; отдельно различай неверный
тест, исходные данные, tool failure, code failure и конфликт требований.
Возврат: scope; verified checks; failed/not_run/review; evidence paths;
до5 первых проблем с полным количеством; предлагаемый next action.
Дочерний done и exit0 не означают accepted/delivery_passed.
```

readonly запрещает запись — поэтому checker-generated evidence сохраняет
исполнитель, а проверяющий независимо читает его. Для независимого повторного
запуска создать вторую ограниченную executor-задачу с новым output; затем review.

## Дополнение AGENT_WORKFLOW.md

```markdown
Для многоэтапного профиля следуй docs/organization/local-orchestration/README.md.
SPEC/PLAN и run ledger держи у job; каждый attempt пишет только в новую папку.
Перед делегированием назначай область файлов и владельца DCC/port/output.
После produced при restart сначала перечитай evidence и hashes, не повторяй мутацию.
Два повторения одной причины останавливают этот путь; сохраняй failure и next action.
```

## Дополнение TASK_CONTEXT.md

```markdown
## Локальная оркестрация NPM/VPM
- Аудит/архитектура: docs/organization/local-orchestration/README.md.
- Пилот: docs/organization/local-orchestration/PILOT.md;
  jobs/ORCH-OBR22-NPM/STATE.md и pilot-spec.json.
- Исполнители/контракты: docs/AGENT_WORKFLOW.md, docs/ADAPTER_REPORT.md;
  далее только маршрут выбранного профиля/инструмента.
```

## Контракт делегированного задания

Цель/профиль/область → ссылки на требования/кейс → входы с hash → зависимости →
разрешённые файлы/ресурсы и output → запрещённые изменения → конкретный tool/argv →
ожидаемые artifacts → check matrix → stopping/retry policy → формат ответа.

Пример executor: «Run ORCH-OBR22-NPM stage export в attempt-001 после реализации
adapter и прохождения его fixture. Входы только из pilot-spec.json; allowed writes
в attempt-001 и его logs; исходные approved и shared_v011 read-only. Один background
Blender, без live MCP. Получи FBX/PNG/source+export manifests. Не закрывай ID0 и не
измени atlas/UV/геометрию. Верни argv/exit/files/hashes/checks/limitations.
Export success не устанавливает pass остальных stages».

Пример reviewer: «Сверь requirements PILOT с manifest и actual readback report,
источником APPROVED_VERSIONS, maps и архивом. Установи, что input preserved,
embedding реальное, tri-export не потерял UV/materials, manual gates отдельные.
Новая геометрия и synthetic metadata запрещены; verdict только в области transfer».
