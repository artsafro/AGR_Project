# Бутовская школа — поэтапное моделирование НПМ

Цель и текущий результат: [STATE](STATE.md). Исходник — открытый Revit2025
СОШ1000, Большая Бутовская9. Отдельный новый Blender4.4 master; originals сохранены.
Текущий результат — рабочий общий фасадный BODY:12478 квадов, native readback OK.
Полнота источника и общие стыки ещё pending; Shell не начат. Пилот ID2679089
сохранён, но он оказался под наружной облицовкой и не является внешней оболочкой.

## Файлы результата, локальные

- `tmp/BUTOVSKAYA-SCHOOL-NPM/source-v001/`: RVT census, source FBX/sidecar.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/reference-v001/`: SOURCE_REFERENCE.blend, inventory.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/panels-v001/panels.json`: измеренные плоскости стен.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/body-east-v004/panel-mesh.json`: выбранная геометрия.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/body-east-v005/`: сохранённый первый pilot master
  BUTOVSKAYA_BODY_EAST_PANEL_v005.blend, panel-readback.json, BODY_EAST_PANEL_wire.png.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/review-v005.json`: независимая проверка.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/discovery-v002/envelope-v004/`: измеренные planes/opaque walls;
  рядом final-direction-plan-v002.json с source-backed choices и33unknown IDs.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/composition-v005/`: profiles, geometry and coverage statuses.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/attribution-v006/`: текущий inputmesh с исправленным face-source registry.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/body-facades-v004/`: текущий BUTOVSKAYA_BODY_FACADES.blend,
  native-readback.json. SHA808bdcdd09bab521e1f072b107591aa9b5e7372f7318880e49deaea1922d33c2.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/preview-facades-v005/`: четыре fitting native wire previews.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/seam-v005/`: точные T-стыки/bowtie и source patch proposals.

Это ignored assets. Git-клон не восстанавливает сцену; хранилище этой рабочей
копии нужно сохранять. Исходные и диагностические версии не удалены.

## Воспроизведение

Команды запускаются из корня проекта. Каталог каждого нового результата должен
быть новым; ни один скрипт не заменяет живую сцену. Сначала убедиться, что source
FBX/sidecar завершены и хеши совпали; экспорт после таймаута не повторять вслепую.

```powershell
& '<Blender4.4>' --background --factory-startup --disable-autoexec --python-exit-code 1 --python jobs/BUTOVSKAYA-SCHOOL-NPM/import_source.py -- --source '<source.fbx>' --sidecar '<source.export.json>' --output '<new-reference>'
& '<Blender4.4>' --background --factory-startup --disable-autoexec --python-exit-code 1 --python jobs/BUTOVSKAYA-SCHOOL-NPM/extract_panels.py -- --reference '<new-reference>/SOURCE_REFERENCE.blend' --output '<new-panels>'
& '<project-python-with-numpy-shapely>' jobs/BUTOVSKAYA-SCHOOL-NPM/quad_panel.py --panels '<new-panels>/panels.json' --element-id 2679089 --normal-x 1 --rail-cluster-m 0.15 --output '<new-mesh-vNNN>'
& '<Blender4.4>' --background --factory-startup --disable-autoexec --python-exit-code 1 --python jobs/BUTOVSKAYA-SCHOOL-NPM/build_panel.py -- --mesh '<new-mesh-vNNN>/panel-mesh.json' --output '<new-master-vNNN>'
```

Importer сохраняет полный FBX-name/ID, матрицы и импортную геометрию. Extractor
отбирает наружный тип стен конкретно этой школы; это job-параметр, не универсальный
Revit API. `quad_panel` поддерживает одну связную ортогональную плоскую поверхность.
Наклонный контур отклоняется. Нельзя автоматически переносить его на двор,
изогнутый/наклонный фасад или весь объект. Для других плоскостей нужен явный выбор.

Cluster0.15м объединяет только избыточные координаты резов: все реальные границы
проёмов и контура жёстко сохранены, переходы рёбер выполняются внутри простенков.
Это не допуск изменения геометрии. Каждый квад целиком покрыт исходной поверхностью;
частичное покрытие вызывает ошибку. Обратная проверка сравнивает геометрические
объединения и границы с исходной FBX-плоскостью, а не только bounding box.

## Ограничения источника/приёмки

Общий BODY имеет4633 regular quads и7845 irregular fallback quads. Exact source
silhouettes, не sampled probes, задают поверхности. Численная нормализация≤50мкм
разрешена только с сохранением компонентов/проёмов; неподдержанные части сохранены
в composition с исходными профилями. Нормализация не разрешает удалить реальные
проёмы. Группы непрерывных поверхностей и seams ещё не объединены финальным Attach.
33 directions/444.049м² unsupported coverage/9.966м² strict discrepancies pending.
627exact T-joins и1bowtie блокируют Shell и global_geometry_passed.
88 local-orientation objects устраняют angular distortion мелких граней от мировых
float32 coords; world placement/source IDs сохранены. Это рабочий master;
export object count/triangulation/UV/Checker проверяются отдельным этапом.

```powershell
& '<Blender4.4>' --background --factory-startup --disable-autoexec --python-exit-code 1 --python jobs/BUTOVSKAYA-SCHOOL-NPM/extract_envelope.py -- --reference '<reference.blend>' --inventory '<inventory.json>' --selection '<explicit-source-IDs.json>' --output '<new-envelope>'
& '<project-python-with-numpy-shapely>' jobs/BUTOVSKAYA-SCHOOL-NPM/compose_envelope.py --envelope '<new-envelope>/envelope.json' --walls '<new-envelope>/wall_geometry.npz' --axes '<new-envelope>/principal_axes.json' --directions '<reviewed-direction-plan.json>' --output '<new-composition>'
& '<project-python-with-numpy-shapely>' jobs/BUTOVSKAYA-SCHOOL-NPM/refine_provenance.py --mesh '<new-composition>/body-mesh.json' --composition '<new-composition>/composition.json' --output '<new-attribution>'
& '<Blender4.4>' --background --factory-startup --disable-autoexec --python-exit-code 1 --python jobs/BUTOVSKAYA-SCHOOL-NPM/build_envelope.py -- --mesh '<new-attribution>/body-mesh.json' --output '<new-master>'
& '<Blender4.4>' --background --factory-startup --disable-autoexec --python-exit-code 1 --python jobs/BUTOVSKAYA-SCHOOL-NPM/preview_envelope.py -- --blend '<new-master>/BUTOVSKAYA_BODY_FACADES.blend' --output '<new-preview>'
```

Host FBX импортирован без material slots; Blender сообщил сброс invalid material
indices. Цвет master нейтральный, не утверждённая отделка. Sidecar сохраняет исходные
material IDs отдельно. Размер стены в sidecar bbox и физической FBX-поверхности
отличается на75мм по minY; bounding box не заменяет измеренный контур.
Пилот не доказывает полноту фасадов, геопривязку для экспорта или соответствие всей
школы Revit. Shell, окна, крыша, материалы/UV, FBX НПМ и AGR Checker ещё не выполнены.
Context7 отсутствует в текущем наборе инструментов; использованы установленный
Blender4.4 и проектные entrypoints, проверенные текущими import/save/readback.
