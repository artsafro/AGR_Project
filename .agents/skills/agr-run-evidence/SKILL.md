---
name: agr-run-evidence
description: Inspect an existing AGR RunRecord after interruption or before accepting a saved stage. Check input and output file evidence, distinguish produced from verified, expose missing gates and choose the next safe action without rerunning a DCC operation.
---

# Проверка сохранённого этапа

Найди run directory и его `attempt-*/input-manifest.json` через соответствующий
job `STATE.md`. Не выбирай папку только по максимальному номеру: сверяй run_id,
входы и контекст. Если manifest отсутствует, так и сообщи; не реконструируй его
из желаемого результата. Правила и значения статусов —
`docs/organization/local-orchestration/RUN_EVIDENCE.md`.

Из корня checkout запусти доступным проектным Python:

```text
python tools/harness_status.py --run <run-directory> --manifest <input-manifest.json>
```

Если имеется AdapterReport, добавь `--report <report.json>`. Обязательные gates
бери из задания/профиля и передавай повторяющимся `--required-check <id>`.
Не выдумывай новые имена checks и не полагайся только на список самого отчёта.
Команда читает файлы и печатает JSON. Она не разрешает retry, не снимает locks,
не вызывает исполнителей и всегда возвращает `delivery_passed=false`.

Проверь `current_inputs`, `evidence_integrity`, состояния этапов, ошибки,
`unresolved_gates` и `next_action`. Exit 0 означает отсутствие обнаруженных
ошибок файловой целостности; pending gates и непроверенные claims могут оставаться.
Exit 1 — обнаружено расхождение evidence; exit 2 — непригодный ввод/ошибка чтения.

- `produced`: сначала проверить сохранённый выход, не повторять мутацию.
- `verified`: проверка этого этапа записана; её область не равна полной приёмке.
- `uncertain`: запись running не доказывает живой процесс. Подтвердить процесс,
  сцену и выходы до решения о retry; locks автоматически не удалять.
- `stopped` или changed/missing evidence: сохранить факты и классифицировать
  причину. Для следующей разрешённой попытки использовать новые выходы.
- `reported_pass_unverified`: прочитать реальные доказательства соответствующего
  gate. Валидная форма AdapterReport и строка с путём не доказывают native QA.

Верни компактный вывод: run_id/этап, целостность, незакрытые проверки, пути
к полному evidence и обоснованный следующий шаг. Не объявляй модель сданной.
