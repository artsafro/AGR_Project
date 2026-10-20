# Smooth by Angle: ограниченный перенос Blender 4.4

`smoothing.py` объединяет снятие custom normals, очистку базовых Sharp-флагов,
Smooth faces и один Geometry Nodes modifier Smooth by Angle. Параметр `--angle`
задаётся в градусах; в `Input_1` записываются радианы; `Socket_1=false`.
Поддержан только Blender 4.4 и все mesh текущей сохранённой сцены, без ранее
существовавших модификаторов. Это не универсальный ремонт импортированных моделей.

```powershell
& <blender.exe> --background --factory-startup --disable-autoexec --python-exit-code 1 --python technical_library/mesh_audit/smoothing.py -- --source <source.blend> --output <new-output.blend> --report <new-report.json> --reference <historical-output.blend> --expected-mesh-count 16 --angle 30
```

`--reference` необязателен, но нужен для доказательства эквивалентности переноса
историческому результату. Все пути задаёт вызывающий; родители output/report
должны существовать, сами output/report — отсутствовать. Перезапись любых файлов
и запись в путь с `approved` запрещены. Исходник и reference остаются только для
чтения; SHA256 проверяются до и после. Модели, результаты и временные версии в Git
не добавлять. При ошибке readback уже сохранённый новый output может остаться:
он не принят, отчёта об успехе нет; автоматически удалять его нельзя.

Вместо зависимого от UI `bpy.ops.object.shade_auto_smooth` используется установленный
asset `datafiles/assets/geometry_nodes/smooth_by_angle.blend` через
`bpy.data.libraries.load(link=False)`. При отсутствующем asset можно явно передать
`--asset-library <smooth_by_angle.blend>`; его SHA256 попадает в отчёт. Скрипт
не скачивает asset. Историческая неудача `shade_auto_smooth -> CANCELLED` не считается
успехом: рабочая часть — ручное создание modifier из Smooth by Angle node group.

До сохранения проверяются raw vertex/edge/loop/polygon, UV, material slots и
world transforms тем же порядком байтов, что в исходном `verify_saved.py`.
Проверяется неизменность состава сцен, объектов, collections, родителей,
world transforms и hide flags. После сохранения source и output заново открываются.
Evaluated mesh обязан сохранять те же geometry/UV/material fingerprints;
эквивалентность reference дополнительно проверяет sharp/smooth-флаги и corner normals.
Шейдеры не модифицируются; fingerprint material slots не является полной проверкой
shader graph или внешних текстур. Это дополнение к существующему `mesh_audit`,
а не вторая реализация его topology/overlap аудита.

Linked/overridden/noneditable meshes, Edit mode, неверное число mesh, существующие
модификаторы и mesh data, используемые объектами вне целевого набора, отклоняются.
Несколько целевых объектов с общей локальной mesh data допустимы: изменение затрагивает
только объявленный набор. Активную DCC-сцену этот CLI не использует: запускать его
только отдельным background процессом с указанным сохранённым input.

Происхождение: чат `01a15321-49e2-7432-af4f-0eabcbb38141`, этап 19.10.2026;
локальные `tmp/blender-smoothing-20261019/apply_smoothing.py` (оператор отменён),
`finish_smoothing.py` (успешное завершение), `verify_saved.py`, `receipt.json`,
`native_readback.json`. При свежей проверке 20.10 исходному saved source соответствует
исторический `autosmooth_30deg_v001.blend1`: 16 mesh, raw/evaluated equality.
Текущий `autosmooth_30deg_v001.blend` имеет другие vertex coordinates и transforms;
причина неизвестна, автоматически восстанавливать/перезаписывать его нельзя.
Reference допускает `.blend` и `.blend1` только для чтения; output — только `.blend`.
Исторический отчёт утверждал 16 mesh и native equality;
это происхождение, не новое доказательство текущих файлов. Свежий replay обязан
подтвердить equality на актуальных input/reference; при расхождении перенос не принят.

Синтетические Python-тесты проверяют запреты записи/параметры/linked/shared guards;
не заменяют native Blender. `native_checks_passed` относится только к указанным
readback-проверкам. User/visual/full AGR acceptance всегда pending,
`delivery_passed=false`. Для универсального переиспользования нужен второй
репрезентативный кейс и его собственные проверки.
