# Бутовская СОШ1000 — НПМ, Blender

Цель пользователя 07.10.2026: моделировать школу из открытого Revit по этапам,
чистыми квадами под требования НПМ. Владелец DCC/экспортов: root.
Ветка: codex/butovskaya-school-npm; fresh origin/main/HEAD:
2011676288970760b024908b79a7c012d29ddff4. Публикация не запрошена.
Скрипты/README сохранены локальным коммитом9c37f511dd150b9163ceecc7e24c4b12c9006e59;
эта запись продолжения сохранена последующим тематическим state-коммитом.

## Вход и ограничения

Revit 2025 PID8284, подтверждён Named Pipe RevitBridge.Cursor.2025.8284.
Документ БУТОВСКАЯ_СОШ1000_АР_В3_ВИЗАМ_2025.rvt,
`C:/Users/artsafro/Desktop/!3D viz/!Weltbau/6_Butovskaya/`.
Адрес: Москва, Большая Бутовская, владение9. Workshared; исходно isModified=false.
Исходный RVT не сохранять и геометрию не редактировать. Экспорт через временный
3D-вид допускается с удалением вида; проверить флаг modified после экспорта.
Blender до начала не запущен; работать в отдельных новых файлах Blender4.4.
Модель/полные инвентари локальные в ignored tmp/BUTOVSKAYA-SCHOOL-NPM/.
Разрешённые tracked изменения: этот job; root STATE только указатель.

Профиль: standards/NPM_STANDARD.yaml. Рабочая геометрия:
docs/GEOMETRY_RULES.md; UV: docs/UV_RULES.md. Старые СОШ1150/Обр22 не входы.
Интерьер Revit исключить из BODY. НПМ лимит150000 треугольников/FBX относится
к экспортной копии; мастер100% чистые квады. Ground density не применять к ОКС.
Геопривязку/матрицы и исходные материал/элемент ID сохранять.

## Этапы и зависимости

S0: инвентарь документа/связей/уровней, исходный FBX и sidecar, readback Blender.
S1 после S0: наружный BODY без толщины по измеренным контурам и проёмам;
не переносить внутренние стены, не заменять реальные контуры bounding box.
S2 после QA/визуальной проверки S1: Shell внутрь0.4м, наружные фейсы/откосы,
без внутренней обратной стенки; отдельно проверить стыки/самопересечения.
S3 после S2: измеренные окна/двери, крыша, входы, нужные наружные детали.
S4 после S3: НПМ материалы/атлас/UV; S5: отдельная триангулированная экспортная
копия, readback и AGR Checker. Полная сдача территории/Ground пока вне этапа школы.

Критерии S1: контуры и настоящие проёмы совпадают с источником (геометрический
допуск2мм по профилю, более строгие критерии фиксировать явно), нет треугольников,
n-gon, вырождений, дублей, непреднамеренных overlaps/T-стыков; нормали наружу.
Открытые края BODY/проёмов на S1 намеренны. Версионный .blend, readback QA,
фасадный/сеточный preview и независимый review. Визуальное утверждение отдельно.
Стоп: неподдержанные контуры/двор/наклонные фасады не заменять приближением;
после двух ошибок одной причины сохранить evidence и сменить подход.

## Текущий этап

S0: получены census/FBX/sidecar и SOURCE_REFERENCE.blend. Census109 категорий,
2468 типов,196 семейств,853 материала,92835 экземпляров с аннотациями/эскизами.
Отметки census feet; подтверждённые этажи -3.4,-2.1,0,4.5,8.7,12.9,17.1,18.6м.
Все5 связей unloaded, включая АР_Ф. В исходной папке найден фасадный FBX v3
от11.09.2026; актуальность не подтверждена. Ранее существующие Max/NPM не изменены.
Export timeout30s имел unknown outcome: дождались файлов, повтор не делали.
Временный вид создан/удалён; RVT не сохранён, после export isModified=true.
FBX47,010,928bytes;10695 meshes/504893triangles;10695 unique sidecar mappings.
Matrix scale0.3048000038 соответствует feet→m. FBX material slots отсутствуют,
Blender reset invalid indices; материал/полнота фасадов остаются pending.

S1-пилот: наружная плоскость восточной стены ID2679089, normal+X,
32.7×18.25м. Активная версия:
`tmp/BUTOVSKAYA-SCHOOL-NPM/body-east-v005/BUTOVSKAYA_BODY_EAST_PANEL_v005.blend`.
Сохранено/повторно открыто Blender4.4; GUI PID110468 открыт именно с этим файлом.
202 выпуклых квада,316 уникальных вершин,36 проёмов. Нет вырождений, дублей,
T-стыков и неправильных нормалей; максимум2 грани/ребро; открытые края намеренны.
Readback rounding1.174мкм; независимая граница к FBX9.537мкм (<2мм).
Per-face RevitID/source index сохранены; source index0 не утверждённый materialID.
Глобальные10мм полосы раннего варианта заменены локальными согласованными
переходами внутри простенков; min edge0.3м, реальные границы не изменены.
Sidecar minY отличается от FBX75мм: bbox не использован как контур;
причина/контроль по Revit ещё pending. Нет утверждения о соответствии всей школы.

Evidence/хеши: reference-v001/inventory.json, body-east-v004/panel-mesh.json,
body-east-v005/panel-readback.json и BODY_EAST_PANEL_wire.png,
tmp/BUTOVSKAYA-SCHOOL-NPM/review-v005.json. Master SHA:
7b7652596dd584f2e4e0e82889f41b3e6ea7dd77bd47152177e8da69f9084d88.
Независимый reviewer повторно открыл master, проверил выпуклость/контуры/проёмы/
атрибуты/швы и просмотрел preview; unsupported slope negative case отклонён.
Контекст7 отсутствует. Profiles3/hash/traceability и schemas8 OK; py_compile OK.
Первый pytest:157passed/1skipped/91errors в temp fixture (permissions).
Повтор с task-owned fresh --basetemp:246passed/2skipped/1failed/1warning.
Единственный failed — taskkill собственного child: sandbox Access denied.
Изолированный повтор этого теста вне sandbox:1passed/1 cache-warning;
прочие tests повторно не запускались. Оба failure-log/исправляющий receipt сохранены.
Дополнительный convex guard повторил геометрию byte-identical (SHA7168febe...).
`dt build --job jobs/SYNTH-001/project.json --output tmp/BUTOVSKAYA-SCHOOL-NPM/synthetic-dcc-v001 --blender <Blender4.4>`:
development_checks_passed=true, delivery_passed=false. Это отдельная синтетическая
проверка конвейера, не приёмка школы. Финальный git diff --check OK.

Статус только пилотной плоскости: produced=true, technical_verified=true,
user_visual_accepted=false. Full-school BODY/Shell/windows/roof/UV/export/Checker
ещё не выполнены, delivery=false. Старые версии/ошибки сохранены, ничего не удалено.
Следующий шаг: подтвердить актуальный facade input/Parts, построить остальные
наружные участки/цоколь и проверить реальные стыки полного BODY; затем Shell.
Не повторять экспорт/импорт при продолжении без readback сохранённых хешей.
