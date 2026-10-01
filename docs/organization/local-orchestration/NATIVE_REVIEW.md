# Независимая проверка native adapters

01.10.2026. Область: чтение `tools/check_profile_agr.py`,
`tools/max_profile_roundtrip.py` и сохранённых native evidence. Код не изменён.
Новая приёмка модели или полный delivery этим review не устанавливаются.

## AGR

Harness требует background/factory-startup, импортирует actual FBX с
`use_image_search=False`, вызывает установленный `LowpolyChecks.run_checks`.
Исходный `.blend` не загружается; исправления, UI-регистрация addon, экспорт и
сохранение модели не вызываются. Pillow извлекается из wheel в новый per-run
каталог; установленный addon не переписывается. Native logger перенаправлен
в output, native проверочные функции не подменены.

`execution=completed` означает завершение диагностических производителей,
а не их положительный verdict. `delivery_passed=false` фиксирован.
Native verified/count/errors сохраняются отдельно. Нулевое количество
проверенных элементов без ошибок переводится в `review`, а внутренние
исключения native остаются `error`. Отсутствующие IDs и manual gates
не интерпретируются как coverage/pass.

Прочитан `pilot-20261001-004/attempt-001/reviews/native-001/agr-native/agr-diagnostic.json`:
SINTEZ 1.6.1, execution completed, 53 records: 2 pass, 9 fail, 42 review;
native_internal_errors=0, input_fbx_unchanged=true, delivery_passed=false.
Замечаний, блокирующих заявленную diagnostic scope, не найдено.

## Max

Скрипт проверяет пустую сцену и отсутствие maxFileName; существующую сцену
не reset/load. Импортирует указанный actual FBX, сохраняет новый MAX и
обратный FBX; ранее существующие целевые файлы отклоняются. `operation_completed`
характеризует import/save/export, а не UV/topology/Checker. `delivery_passed=false`
фиксирован; сравнение обратного FBX выполняется отдельным Blender readback.

Прочитан `pilot-20261001-002/attempt-001/max-batch-005/max-native.json`:
Max 2024.2.5, PID96380, operation_completed=true, failures=[].
Повторно измерен SHA256 фактического input FBX:
`903bfbdd6a4be5bae1c357e317f4e755090799753aa45d5f37d539c3fc61e699`;
совпадает с native report. Из одного operation_completed нельзя выводить
отсутствие потерь UV/материалов или результат полного AGR.

Границы самостоятельного использования: скрипт не проверяет исполняемый
batch-binary/PID transport, не проверяет раздельность source/output и не
измеряет source hash после операции. В текущем пилоте это обеспечивает
управляемый batch caller с отдельным output и внешней проверкой входов;
standalone гарантию защиты любой произвольной конфигурации заявлять нельзя.
Перед переиспользованием вне этого caller нужны соответствующие preflight
guards. Сам read-only review не подтверждает состояние пользовательской
интерактивной сцены; это отдельное live evidence ведущего.
