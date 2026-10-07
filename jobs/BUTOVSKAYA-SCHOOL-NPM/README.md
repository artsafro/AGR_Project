# Бутовская школа — поэтапное моделирование НПМ

Цель и текущий результат: [STATE](STATE.md). Исходник — открытый Revit2025
СОШ1000, Большая Бутовская9. Отдельный новый Blender4.4 master; originals сохранены.
Первый результат — один измеренный восточный фасадный участок ID2679089,
не вся школа и не финальный НПМ. Следующий этап — полный наружный BODY,
с проверкой состава фасадов/категории «Части» и актуальности фасадной подложки.

## Файлы результата, локальные

- `tmp/BUTOVSKAYA-SCHOOL-NPM/source-v001/`: RVT census, source FBX/sidecar.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/reference-v001/`: SOURCE_REFERENCE.blend, inventory.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/panels-v001/panels.json`: измеренные плоскости стен.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/body-east-v004/panel-mesh.json`: выбранная геометрия.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/body-east-v005/`: активный master
  BUTOVSKAYA_BODY_EAST_PANEL_v005.blend, panel-readback.json, BODY_EAST_PANEL_wire.png.
- `tmp/BUTOVSKAYA-SCHOOL-NPM/review-v005.json`: независимая проверка.

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

Host FBX импортирован без material slots; Blender сообщил сброс invalid material
indices. Цвет master нейтральный, не утверждённая отделка. Sidecar сохраняет исходные
material IDs отдельно. Размер стены в sidecar bbox и физической FBX-поверхности
отличается на75мм по minY; bounding box не заменяет измеренный контур.
Пилот не доказывает полноту фасадов, геопривязку для экспорта или соответствие всей
школы Revit. Shell, окна, крыша, материалы/UV, FBX НПМ и AGR Checker ещё не выполнены.
Context7 отсутствует в текущем наборе инструментов; использованы установленный
Blender4.4 и проектные entrypoints, проверенные текущими import/save/readback.
