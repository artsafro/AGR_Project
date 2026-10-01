# Пилот ORCH-OBR22-NPM

01.10.2026. **Изолированный реальный пилот выполнен: pilot-20261001-004.**
Пользователь разрешил завершить реализацию. Approved-модели и открытые сцены
сохранены; новые артефакты находятся в отдельном run. Фактический результат:
[EXECUTION.md](EXECUTION.md). Ниже спецификация и исходный план пилота.

## Объект, профиль, результат

Обр22, корпус2/секции7–9, один типовой этаж: approved НПМ v012.
Это небольшой реальный reusable компонент с BODY/окнами/инстансами/атласом.
Вместо произвольной реконструкции проверить оркестрацию передачи готовой модели.
Результат будущего запуска: versioned `.blend` рабочей копии, technical FBX с
embedded atlas, отдельный PNG, technical ZIP, input/export/readback manifests,
AdapterReport и независимый verdict. Архив называется техническим, без
утверждения нормативных naming/геопривязки/сдачи всего ОКС.

Входы заданы в [pilot-spec.json](../../../jobs/ORCH-OBR22-NPM/pilot-spec.json).
Текущее hash evidence7/7 — [evidence.json](evidence.json).
Принятая VPM v011 — read-only reference физического масштаба, не второй профиль
сборки в этом пилоте. Исходный атлас2048 сохраняется; material ID/UV/finish mapping
не переопределяются. Открытые ID0 сохраняются и отмечаются в отчёте.

## Этапы, ownership и повторение

1. **SPEC/PLAN.** Ведущий читает AGENTS→STATE→TASK_CONTEXT→job→кейс Обр22,
   фиксирует component-transfer scope, required checks и запрет production mutations.
   Документы проекта — ведущий; новые export/check wrapper files — один code
   executor; native scene/output — один DCC executor; reviewer read-only.
2. **Frozen inputs.** Сверить SHA/bytes всех approved inputs и относящихся JSON.
   Сохранить код+dirty diff/tool/profile fingerprints. Скопировать approved inputs
   в `jobs/ORCH-OBR22-NPM/runs/<run_id>/attempt-001/source/` с теми же соседними PNG;
   не делать hardlinks на writable копию. Создать manifest source dependencies.
   Включить JSON uv_trial/npm_v012/shared_v011 при использовании scale checker;
   копировать только проверенные зависимости, не4GB outputs.
3. **Preflight.** Отдельный background Blender4.4 factory-startup/disable-autoexec;
   получить scene identity, mesh names/counts/units/UV/maps/slots/IDs из самой копии.
   Записать source snapshot/контрольные камеры. Если external maps missing — остановить
   экспорт; не искать замену с тем же именем и не чинить approved пути молча.
4. **Экспорт.** Новый `export_profile_snapshot.py` (план интеграции, ещё отсутствует)
   применяет профиль только к экспортной копии, сохраняет корректные UV/materials.
   Триангуляция FBX по NPM, исходный editable blend остаётся quad/instance.
   Никаких Collapse/Weld/Reset на source. Выбор mesh по explicit manifest,
   служебные reference objects исключаются с перечислением причин.
5. **Package + readback.** Переиспользовать deterministic ZIP/hash reader.
   Затем распаковать actual ZIP в отдельную validation-папку; новый check wrapper
   импортирует именно извлечённый FBX, проверяет embedding и corners/units/materials.
   Не подменять его проверкой exporter.scene или старым JSON. Вывести native
   mesh facts, карты и hashes. Scale checker переиспользовать на snapshot tree,
   так как существующий скрипт пишет отчёт в фиксированный npm_v012.
6. **Независимая проверка и visual.** Reviewer сверяет check matrix с actual
   files/evidence. Сделать одинаковые камеры source vs reimport, а для масштаба
   NPM vs approved VPM; сохранить изображения. Пользователь принимает новый
   transfer-result явно, старая приёмка input не переносится на новый FBX.
   Max import/back-export и full AGR Checker остаются отдельными воротами.
7. **Resume/failure.** Ниже сценарии фикстур. После завершения записать job STATE,
   run ledger, hashes/версии и решение человека в точной области.

Все mutating этапы после разрешения на реализацию. Уже выполненный SYNTH-001
прогон — preflight test инфраструктуры; он не является этапами2–6 этого пилота.

## Проверенные команды для аудита/preflight

Из корня проекта; executable paths фактически существуют. Эти команды
выполнены сегодня. Для нового запуска обязательно новый output.

```powershell
& .venv/Scripts/dt.exe profiles check
& .venv/Scripts/dt.exe schemas --check
& .venv/Scripts/python.exe -m pytest -q --basetemp tmp/orchestration-audit-20261001/pytest
& 'C:/Program Files/Blender Foundation/Blender 4.4/blender.exe' --version
& .venv/Scripts/dt.exe build --job jobs/SYNTH-001/project.json --blender 'C:/Program Files/Blender Foundation/Blender 4.4/blender.exe' --output tmp/orchestration-audit-20261001/synth-dcc
& .venv/Scripts/python.exe tools/run_exterior.py --help
& .venv/Scripts/python.exe tools/run_body_shell.py --help
```

Перечисленные paths — фактический аудит01.10, не команда повторного production
запуска. Повторить build ровно в той же папке значит перезаписать тестовый результат.
`.venv`/Blender/optional NumPy/Shapely локальны: чистая установка сегодня не проверена.

Будущая команда export после реализации/adaptor fixture:

```powershell
# ПРОЕКТ КОМАНДЫ: скрипта пока нет, сегодня не выполнено
& 'C:/Program Files/Blender Foundation/Blender 4.4/blender.exe' --background --factory-startup --disable-autoexec --python-exit-code 1 --python tools/export_profile_snapshot.py -- <absolute-run-config.json>
```

При реализации проверить argparse/help и фактические argv export/check wrappers;
сохранить точные команды в run ledger. Не запускать фасадный exporter v005 над
Обр22, не использовать synthetic dt build для реальных входов.

## Required-check matrix

| Ворота | Критерий / evidence | Текущий статус |
|---|---|---|
| Baseline | profile/schema/tests и SYNTH DCC; журнал свежего запуска | выполнено, только baseline |
| Inputs protected | actual7/7 hashes перед/после будущего пилота; source/.blend/PNG не изменились | перед пилотом7/7; после not_run |
| Native source | scene/units/counts/groups/ID/UV/maps и topology из isolated source copy | not_run |
| Export | actual FBX7400 binary/units/triangles, explicit mesh inventory, atlas embedding | not_run |
| Topology/readback | отсутствие новых дублей/degenerates/overlaps, неизменные проёмы; намеренные исходные исключения отдельные | not_run |
| UV/materials | actual corner UV/finish IDs/slots, same atlas SHA/regions, отсутствие новых lost paths | not_run |
| Scale | сохранённые NPM/VPM UV+материалы/phase и одинаковые камеры, Ground TD N/A | not_run |
| Package | ZIP readback/bytes/member hashes; именно из него imported FBX | not_run |
| Restart | produced→verification без второго export; changed input запрещает reuse | not_run |
| Failure handling | два повтора причины→stop/state; ошибочный тест исправлен только по SPEC fixture | not_run |
| AGR Checker | реальный full Checker/version/native findings для scope, не только TD function | not_run; adapter/runtime не подтверждён |
| Max | pinned instance + new test document/version → import/back-export → сравнение | blocked runtime: BRIDGE_DOWN |
| Visual | новые source/export/reimport renders + явная подпись человека | review/not_run |
| Full delivery | Ground/full OKS/naming/placement/прочие обязательные правила | вне области пилота; delivery_passed=false |

Текущие partial statuses не переименовывать в passed. Возможны отдельно:
`transfer_technical_checks_passed` в области Blender/file QA и `pilot_accepted`
с подписью человека; они не заменяют Max/Checker/full delivery. Эти поля пока
предложены, не являются новыми полями действующего AdapterReport.

## Тесты восстановления на отдельной fixture

- Остановить orchestration после produced, начать новую сессию из STATE;
  убедиться, что stage продолжает readback, а export счётчик остаётся1.
- Испортить output **фикстуры**, сохранив старый report: hash mismatch блокирует reuse.
- Поменять relevant input/config на fixture: downstream новый attempt, approved intact.
- Два задания требуют одну output-папку/live endpoint: конфликт владельцев до DCC.
- Дважды повторить одну классифицированную tool-error: stop, reason и next action
  записаны. При timeout сохранить partial stdout/stderr и interrupted.
- Отдельная synthetic test содержит ошибочный критерий «импорт FBX обязан оставить
  квады». SPEC требует quad editable source и triangulated export. Исправить только
  тестовую фикстуру по SPEC, затем проверить покрытие/UV/материалы; не менять
  требования модели ради pass. Сохранить оба verdict и объяснение test failure.

## Откат и условия остановки

Approved исходники read-only, изменения лишь в новом run. При ошибке прекратить
процесс данного run, сохранить failed attempt/логи; не восстанавливать поверх
source и не удалять непроверенные outputs. Возврат к approved v012 по исходному
пути и hash, без смены активной пользовательской сцены. Изолированные test
документы Max закрывать без сохранения production; открытие возможно лишь после
безопасной передачи владельца сцены. Новые code wrappers откатываются отдельно.

Stop при missing/hash-changed source, неизвестной сцене/ресурсном конфликте,
неоднозначной области экспорта, потере material/UV/units или повторной причине.
ID0/неизвестная геопривязка не заполняются выдуманным значением; блокируют
расширение к полному delivery, но документируются в технической передаче.
