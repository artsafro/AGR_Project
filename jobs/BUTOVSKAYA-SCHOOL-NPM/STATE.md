# Current stage: v012

[Current verified state and continuation](CURRENT.md). This supersedes the historical v004 notes below.

---

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

Продолжение по прямому указанию пользователя: каждый5м геометрии проверить
на квады и сопоставить BODY с открытым Revit. Grid5×5×5м от Revit internalorigin,
без произвольных5м резов в master. Сравнение реальных поверхностей/проёмов,
source-only cells тоже проверять; unknowns не получатьpassed. RootDCCwriter;
отдельный owner audit_five_metre.py и independent coplanar repairowner.
Вход nativeactualworldcoords v004, attribution-v006, exactsourceprofiles;
fresh Revit exportsource-live-v002 запущен (timeoutunknown outcome, не replay).
План: sourcefreshness geometryhash →5м audit → адресные source-constrained repairs
→ newnative master/reopen → повтор5м проверки и независимый review. Shell pending.

Рабочий общий фасадный мастер S1 (НЕ полный принятый BODY):
Скрипты/README/RESULT сохранены локальным implementation-коммитом5a97c7d;
эта запись продолжения фиксируется отдельным state-коммитом. Remote push не выполнялся.
`tmp/BUTOVSKAYA-SCHOOL-NPM/body-facades-v004/BUTOVSKAYA_BODY_FACADES.blend`.
SHA808bdcdd09bab521e1f072b107591aa9b5e7372f7318880e49deaea1922d33c2.
12478 квадов/30214 вершин,88 orientation objects внутри BODYcollection;
4633 regular quads,7845 irregular fallback quads. Геометрия без Shell.
Произведено5325.077м² выбранных поверхностей с измеренными проёмами.
Native save/reopen:0wrong normals/0zero faces; faces/IDs/group registry совпали;
world-coordinate readback≤12.276мкм, planar-local correction≤6.166мкм.
Причина421 angular failures v002 — мировые float32 coords мелких45° граней;
исправлено локальными плоскостями и world transforms, а не ослаблением QA.
Термин «100%quads» не означает регулярный flow или завершённые стыки.

Активные входы: discovery-v002/envelope-v004 (3935плоскостей, tiny0),
final-direction-plan-v002.json; geometry composition-v005/body-mesh.json;
metadata attribution-v006/body-mesh.json.1278 mappings corrected to retain all
positive intersections;93 tolerance-only mappings explicit pending. Vertices/faces
byte-identical before/after attribution. Preview: preview-facades-v005/{SE,NW,NE,SW},
source master SHA unchanged; никакой previewcurve не сохранён в master.
Независимый native review: review-facades-v004.json подтвердил0wrong/zero/concave
faces, source attributes/registry и SHA. Fitting previews исправили camera cropping;
плотные/slivercuts, нерегулярные fanpatterns и fragmented sourcecandidate sheets
остаются видимыми — architectural flow не принят.

Обязательные pending:33 unresolved outer directions (31substrate,2plinth),
unsupported source union444.049м²,5 strict visibility discrepancies9.966м²;
4custom forms имеют только candidate vertical families, не доказанный полный
наружный контур. Sloped/horizontal caps ещё не собраны. Global seam QA:
1873exact duplicate pairs,627exact T-joins,3728proximity candidates,1bowtie
group929 IDs5688821/5688822. Opposed layers blindly weld запрещено.
Следующее действие: resolve group929 и same-plane pairs267/268,402/403,32/33
по сохранённым sourceprofiles; затем outer-source directions/unsupported coverage,
orthogonal corners и QA сохранённого master. Shell только после clean fullBODY.
Вопрос об эталонном АР_В3/АР_Ф задан; ответа пока нет, текущий вход — открытый АР_В3.
Доступные Revit tools не возвращают Wall.Orientation/exteriorface geometry;
не устанавливать add-in/restart без сохранения live document context.

Проверки:247passed/2skipped/1expected zip-warning,21.97s, task-owned basetemp,
с разрешённым завершением собственного testchild. Profiles3/source hash/traceability
и schemas8 OK. Module regular/irregular/normalized/seams tests + independent reviews
в ignored tmp. Final global_geometry_passed=false, user_visual_accepted=false,
delivery=false. RVT не сохранялся; active Revit тот же, modified=true после S0export.
GUIBlender v005pilot не заменён. Reference/pilot SHA совпали повторно.
v001/v002 native failures retained; v003 ownbackground worker119760 terminated
после долгого single-line Textregistry write. Registry хранится root customproperty.
Все исходники/неудачные варианты сохранены, ничего не удалено/не опубликовано.

## Продолжение и предыдущий пилот

Продолжение07.10.2026 после «давай далее»: пользователь разрешил следующий этап
полного наружного BODY. Владелец live apps/экспортов root; отдельный read-only
discovery анализирует сохранённую подложку в discovery-v002. HEAD начала0f919338,
fresh origin/main20116762 (без изменений). SHA пилота совпал; Revit тот же документ,
Blender GUI всё ещё показывает v005. Повторный source-export пока не нужен.
План: расширить явный набор наружных типов/цоколя → определить фактическую
наружную сторону относительно физической подложки → построить все поддержанные
плоскости с реальными проёмами и локальными квад-переходами → проверить стыки,
покрытие/исключения и native readback/preview → независимый review. Shell только
после проверенного полного BODY. Не заполнять неизвестные фасады bounding box.
Revit wall ID2679089 имеет native Length32700мм: физический FBX32.7м совпадает;
sidecar bbox32.775м остаётся bbox, его75мм не являются измеренной длиной стены.

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

S1-пилот: плоскость слоя ПОД наружной облицовкой восточной стены ID2679089, normal+X,
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
Revit native Length32700мм подтвердил физические32.7м. Этот bbox вопрос разрешён.
Пилот покрыт деревянной/металлической облицовкой; не считать его внешним BODY.

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
