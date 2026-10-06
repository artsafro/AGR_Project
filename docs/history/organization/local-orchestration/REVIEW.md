# Независимый review локального пилота — 01.10.2026

Область: read-only чтение `tools/run_profile_pilot.py`,
`tools/max_profile_roundtrip.py`, snapshot adapters/common и
`src/dt_ai/core/run_record.py`; код/сцены не изменены. Этот файл — запись review.
Собственный `check_profile_agr.py` не оценивался как независимая проверка.
Новые DCC/test-запуски этим проверяющим не выполнялись. Результаты ранее
запущенного пилота не заменяют нижеописанные проверки контракта.

## Исправления

Повторная проверка: четыре первоначальных P2 закрыты по коду. Для
`pilot-20261001-004/attempt-001` перечитаны ledger/native reports, самостоятельно
пересчитаны все ledger output SHA256: совпадают. Inspect/export/editable_readback/
readback имеют verified. Ordered material-slot checks всех46 мешей true.
Новые DCC/test-запуски этим reviewer не выполнялись.

1. **P2 — Material IDs/slots могут измениться при зелёном transfer QA.**
   **CLOSED:** comparator теперь проверяет material_index, readback сравнивает
   ordered material list; finalrun004 actual readback содержит эти проверки.
   `tools/check_profile_snapshot.py:75` сравнивает material lists как множества;
   `tools/profile_snapshot_common.py:134` сопоставляет треугольники по имени
   материала, игнорируя записанный `material_index`. Перестановка слотов с
   сохранёнными именами/назначением проходит, хотя SPEC требует сохранить IDs
   и slots. Проверять ordered slot list и индекс каждого surface либо явное
   утверждённое mapping; до этого заявлять только сохранение material semantics.
   Fixture: поменять порядок slots и пересчитать indices с теми же material names;
   строгая проверка сохранения IDs должна отклонить такой результат.

2. **P2 — verify_stage может проверить другой cached artifact.**
   **CLOSED:** expected_signature передаётся runner/companion; RunRecord выбирает
   signature явно и отвергает ambiguous records. Добавлена fixture A/B/cached A.
   `RunRecord.run_stage` возвращает подходящую signature из любой attempt;
   `verify_stage` выбирает последнюю produced/verified запись лишь по имени stage.
   При одном input fingerprint и разных argv/outputs callback получает другую
   запись. Передать возвращённую signature/идентичность в verifier и выбирать
   строго её. Fixture: stage A, затем B с другими outputs, затем cached A —
   проверяющий должен получить и отметить verified именно A.

3. **P2 — recovery после failed/interrupted адаптера не поддержан runner.**
   **CLOSED:** runner использует latest attempt; явный --new-attempt создаёт
   fresh paths и сохраняет прежние evidence. Автоматического слепого retry нет.
   `run_profile_pilot.py:65` всегда использует первую attempt; adapters сохраняют
   failing result перед exit1, затем `RunRecord.run_stage` отвергает существующий
   unverified output до создания новой attempt. Это безопасный stop, но путь
   реального retry отсутствует. Для failed/interrupted выбрать новый attempt и
   все свежие argv/config/output paths, сохранив прежние evidence; либо явно
   ограничить текущий resume состояниями produced/verified и направлять retry
   в отдельный новый run. Проверить fixture с partial failing JSON output.

4. **P2 — native file units не доказаны проверкой scene settings.**
   **CLOSED посредством честной границы:** check переименован в
   import_harness_metric_settings; file UnitScaleFactor unverified явно оставлен
   в limitations. Normative units pass больше не заявлен.
   `check_profile_snapshot.py:21–22` устанавливает METRIC/scale1 самим harness;
   строка78 затем считает эти настройки `readback_metric_units=pass`. World
   triangle comparison подтверждает численный масштаб переноса, но не поля
   units фактического FBX. Вывести actual UnitScaleFactor/OriginalUnitScaleFactor
   из FBX либо переименовать check в harness setting и явно оставить file-unit
   metadata unverified. Не заявлять эту проверку доказательством нормативных units.

## Подтверждённые границы

`passed/delivery_passed` полного delivery не выставляются. Max wrapper сохраняет
operation completion отдельно от geometric verification; snapshot отчёты явно
оставляют full Checker/overlaps/Max/visual отдельными воротами. Approved входы
хешируются, source copies сверяются, actual ZIP bytes перечитываются. Produced
evidence перепроверяется hashes перед reuse; verifier также сверяет evidence до
и после callback. Логи и failure evidence сохраняются, ресурсы заявляются явно.

Сохранённый `working-copy.blend` теперь открыт отдельным native процессом:
editable_readback verified, snapshot native_source.objects точно совпадает с
preflight; эти два JSON независимо перечитаны. Это подтверждает записанные mesh
facts: вершины/triangulated surface, исходный polygon histogram, slots/UV/finish,
world matrix и object/mesh names. Полное состояние modifiers и всех custom
instance parameters отдельным snapshot здесь не измеряется; не расширять область
проверки за фактические fields.
Результат review относится к component transfer; полная нормативная сдача ОКС
и независимый аудит собственного AGR wrapper вне этой области.

## Companion review: новый P2

**CLOSED — входы review привязаны к завершённому pilot.**
`tools/run_profile_checks.py` перед baseline сверяет только extracted FBX с
export manifest. Сохранённый blend/ZIP принимаются с любым текущим SHA, а
extracted PNG не включён в защищённые inputs. Изменение этих файлов до review
может получить protected_inputs=pass и diagnostics/renders неправильного входа.
До создания review сверить blend SHA с export artifacts; перечитать actual ZIP,
сопоставить exact member bytes с extracted FBX/PNG и original export hashes;
сверить ZIP SHA с package-readback. PNG добавить в fingerprint/protected inputs.
Сведения companion native-001: renders/scale/diagnostic invocation/Max import-
export/reverse comparison имеют pass; native AGR содержит красные/непокрытые
пункты, visual/full_delivery pending и delivery_passed=false сохранены. Эти
результаты не закрывают описанный input-binding defect.

Повторное чтение companion: до baseline теперь сверяются все outputs четырёх
verified pilot stages по ledger SHA/bytes, blend против export manifest, ZIP SHA
против package-readback и exact extracted bytes против ZIP/export artifacts.
Ledger/package/all extracted members включены в inputs/protected baseline.
Reference/blend/PNG binding исправлены. Native-001 исторический; текущая версия
native-002: renders/scale/AGR invocation/Max import-export/reverse stages verified
по перечитанному review ledger. Pilot output hashes и реальный ZIP независимо
проверены: состав technical.fbx + NPM_ATLAS_Diffuse.png, bytes/хеши совпадают.

Закрытый последний остаток: required ZIP inventory должен задаваться из verified export
manifest (`technical.fbx` + basename atlas), а не только из mutable package sidecar.
Иначе совместная пересборка ZIP и package-readback без отдельного PNG до review
проходит current member-set comparison и удаляет PNG из protected inputs.
Добавить expected inventory check до loop; реальный native-002 пакет имеет
правильный состав, поэтому к нему этот отсутствующий-member сценарий не относится.

Финальная перепроверка: companion теперь требует ровно
`{'technical.fbx', basename(export_facts['atlas'])}` одновременно с inventory
package-readback, поэтому совместная пересборка без PNG отвергается до baseline.
Current evidence — `pilot-20261001-004/attempt-001/reviews/native-003`; native-001/
002 исторические. Перечитаны final review report и ledger; самостоятельно
пересчитаны hashes/bytes всех review stage outputs: совпали. Renders/scale/AGR
invocation/Max import-export/Max reverse readback verified; protected_inputs pass.
Native AGR findings:2 pass/9 fail/42 review, не утверждение общего прохода Checker.
Visual acceptance и full_delivery pending; pilot_accepted=false,
delivery_passed=false. Все найденные P2 закрыты в проверенной component-transfer
области. Собственный AGR wrapper не получил независимого code review от его автора;
native запуск DCC здесь не повторялся.
