# Бутовская СОШ1000 — рабочая версия v012, 07.10.2026

Цель: BODY из открытого Revit, квадами по этапам. Последнее указание — сравнение
каждые5м. Root — единственный DCC writer; source/native/audit review независимые.
Scope tracked: этот job и указатель root STATE; private assets только ignored tmp.
Ветка codex/butovskaya-school-npm; проверенный origin/main:
2011676288970760b024908b79a7c012d29ddff4. До этого этапа HEAD4fe0ef05.
Remote публикация не выполнялась. Источники/GUI сцены/failed версии сохранены.

## Текущие артефакты

Префикс: `tmp/BUTOVSKAYA-SCHOOL-NPM/` относительно корня проекта.

- `body-facades-precision-v012/BUTOVSKAYA_BODY_FACADES.blend` — единственный текущий master.
- `attribution-precision-v012/body-mesh.json` — native input с source attributes.
- `composition-precision-v012/` — геометрия и исходные profiles/coverage.
- `discovery-v002/envelope-v005/` — wall triangles, planes, filtered-face evidence.
- `five-metre-precision-v012/` — CSV/JSON520 участков и независимый audit review.
- `precision-v012-review/final-review-manifest.json` — независимый actual native/source review.
- `seam-precision-v012/exact.json`, `near.json` — реальные проблемные стыки.
- `source-freshness-v002.json`, `reference-live-v002/` — свежий source snapshot.

Direction plan ОТДЕЛЬНО: `tmp/footprint-direction-v001/final-direction-plan-v003.json`.
SHA256 c836d5b06217fa01e3f097f3c4a68694db3feb47c0fc105811dd638729184988.
Master SHA256073e3c093b2b45764aa78f0c34baf0ec1915d63a882bfe57eb5d09c629d23a21.
Fresh reference SHA256c91b5715b8dc3653291f34b876c262bbd3e50dd5d099a2e05ae4a37178fb11a7.
Git-клон не восстанавливает эти assets; сохранять рабочую копию.

## Проверенный результат и границы

14247 выпуклых native квадов,33645 вершин,91 orientation objects.
4677 regular /9570 irregular fallback; регулярный architectural flow не принят.
5959.778326м² измеренных выбранных поверхностей (+634.701597м² к v004).
Native save/reopen:0nonquad/concave/zero/wrong normals; IDs/registry совпали.
Readback12.700мкм; raw-source→native-group-plane максимум0.168556мм, ниже2мм.
184 защищённых source-контуров отверстий сохранены.
50 конечных граней не пересекают raw unsnapped source точно, но полностью внутри
его буфера50мкм, максимальный зазор14.994мкм. Strict raw-positive gate=false.
14 tolerance-only attribution faces pending; не считать их exact provenance.

520 участков5×5×5м от Revit internal origin:275PASS/245PENDING/0FAIL.
Master НЕ разрезался по сетке. Проверены original faces, source-only cells,
контуры/отверстия и нормали. Допуск2мм выполнен в проверенной вертикальной области.
all_cells_passed=false:19unknown directions;18planes/33visibility samples
numeric_uncertain; strict mismatch=0. 158 действительно наклонных source faces,
166.335504м², требуют отдельной классификации/маршрута. Не подменять вертикальными.
Exact seam QA:2745position duplicate pairs,735T-junctions,10disconnected fans;
nonmanifold edges=0. Не weld противоположные слои и не делать финальный Attach.
Микрограни/плотные резы требуют review до Shell. SE preview просмотрен:
разрозненные кандидатные поверхности остаются, full visual acceptance=false.
Global_geometry_passed/full_body_coverage_passed/delivery_passed=false.

Revit2025 PID8284, RevitBridge.Cursor.2025.8284, открытый СОШ1000 АР В3 ВИЗАМ2025.
RVT не сохранён и геометрия намеренно не изменялась; modified=true после прежнего
временного экспортного вида. Свежий экспорт завершён после timeout без replay.
На19:04:05UTC все4273 стены совпали полной triangle geometry при1мкм канонизации,
включая368 выбранных. Это snapshot, не доказательство полноты Parts/фаз.
14 новых directions получены по actual floor/roof footprints;1432 независимые пробы
совпали. Native Wall.Orientation/exterior-face API недоступен в текущем bridge.
Не перезапускать Revit с несохранённым документом ради изменения bridge.

## Воспроизведение и проверки

Новые output directories, сохранение inputs/hashes. Порядок: extract_envelope →
compose_envelope → refine_provenance → build_envelope → export_native_mesh →
audit_five_metre. v012 extractor: maximum-vertical-normal-z=.001 и измеренный
triangle/group projection≤.002м; composer profile-precision-m=.00005,
contour-simplification-m=.000001; audit comparison-precision-m=.00005.
Legacy defaults сохранены. Coplanar profiles переводятся в общий физический frame;
union защищает реальные отверстия и восстанавливает исчезнувшие micro-components.
infer_directions — proposals; reconcile_coplanar — сохранённый эксперимент,
не активный финальный pipeline. Sourcecomparison full-wall solids не доказывает
полное совпадение наружной оболочки. Context7 отсутствует; Blender4.4 проверен native.

pytest247passed/2skipped/2warnings15.63s; разрешённый own-child subprocess retry
устранил sandbox AccessDenied timeout test. profiles3OK, schemas8OK, AST19modulesOK.
5м selftests12PASS; directions3PASS; contour simplification negativesPASS.
dt build SYNTH-001 Blender4.4 → synthetic-dcc-v012: development_checks_passed=true,
actual FBX roundtrip PASS; passed=false/synthetic=true. Это не приёмка школы.

Следующее действие:19unknown directions по native exterior/разрезам, отдельная
классификация наклонных фейсов; адресная source-constrained quad ретопология стыков,
повтор5м/native/source QA. Shell внутрь0.4м только после полной чистоты BODY и
визуальной проверки, затем окна/крыша/UV/отдельный экспорт/Checker.
Нормы standards/NPM_STANDARD.yaml, docs/GEOMETRY_RULES.md и docs/UV_RULES.md.
BODY только наружный; Ground density не применять;150ktris — экспортная копия.

Local implementation/evidence commit:413a92e1f9cdc2af437c9aaf78076d6495c1ed57.
No push/PR. Continuation pointer saved in a subsequent state commit.
