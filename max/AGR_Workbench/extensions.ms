/* Integrated operations based on UCX_Tools and Maf Material-ID workflows.
   Material ID is explicitly chosen by the artist, never inferred as finish. */
global AGRWB_Extensions
struct AGRWB_ExtensionsType
(
  fn materialUV nodes materialID tile applyChanges =
  (
    if AGRWB_Core.profile != "VPM" do throw "Перенос отделки по UDIM доступен во вкладке ВПМ."
    local n = AGRWB_Tasks.polyTarget nodes readOnly:(not applyChanges)
    if materialID < 1 or materialID > 65535 do throw "Material ID должен быть от 1 до 65535."
    if tile < 1001 or tile > 1999 do throw "Номер UDIM должен быть от 1001 до 1999."
    if not polyop.getMapSupport n 1 do throw "Сначала создайте UV в канале 1."
    local faces = for f = 1 to polyop.getNumFaces n where polyop.getFaceMatID n f == materialID collect f
    if faces.count == 0 do throw "У объекта нет полигонов с указанным Material ID."
    local ids = #(), faceMaps = #(), points = #()
    local low = [1e9,1e9,0], high = [-1e9,-1e9,0]
    for f in faces do
    (
      local verts = polyop.getMapFace n 1 f
      append faceMaps verts
      for v in verts do appendIfUnique ids v
    )
    for v in ids do
    (
      local p = polyop.getMapVert n 1 v
      append points p
      low.x = amin low.x p.x; low.y = amin low.y p.y
      high.x = amax high.x p.x; high.y = amax high.y p.y
    )
    if points.count == 0 do throw "UV выбранной отделки пусты."
    if high.x-low.x > 1.00001 or high.y-low.y > 1.00001 do
      throw "UV этой отделки занимают больше одного тайла. Автоматическое уменьшение отключено: сначала проверьте размер рисунка."
    local delta = [(mod (tile-1001) 10)+0.5-(low.x+high.x)*0.5,(floor ((tile-1001)/10.0))+0.5-(low.y+high.y)*0.5,0]
    if applyChanges do
    (
      -- Duplicate only this group's map vertices; adjacent finishes stay fixed.
      local offset = polyop.getNumMapVerts n 1
      polyop.setNumMapVerts n 1 (offset+ids.count) keep:true
      for i = 1 to ids.count do polyop.setMapVert n 1 (offset+i) (points[i]+delta)
      for i = 1 to faces.count do
        polyop.setMapFace n 1 faces[i] (for v in faceMaps[i] collect (offset+findItem ids v))
      update n
    )
    (if applyChanges then "Перенесено" else "Будет перенесено") + ": " + faces.count as string + " полигонов, Material ID " + materialID as string + " → UDIM " + tile as string + ". Масштаб и взаимное расположение UV сохранены. Другие ID не затрагиваются. Пересечения с уже занятым тайлом не проверены."
  ),
  fn convexHull nodes allFaces maxVertices applyChanges =
  (
    if AGRWB_Core.profile != "VPM" do throw "Коллизии доступны во вкладке ВПМ."
    local n = AGRWB_Tasks.polyTarget nodes readOnly:true
    local faces = AGRWB_Tasks.faceScope n allFaces
    local selectedVertices = polyop.getVertsUsingFace n faces
    local points = for v in selectedVertices collect polyop.getVert n v
    if points.count < 4 do throw "Для объёмной оболочки нужны как минимум четыре неплоские вершины."
    local tolerance = units.decodeValue "0.01mm"
    local originPoint = points[1], axisPoint = undefined, normal = undefined
    for p in points where axisPoint == undefined and distance p originPoint > tolerance do axisPoint = p
    if axisPoint != undefined do for p in points where normal == undefined do
    (
      local candidate = cross (axisPoint-originPoint) (p-originPoint)
      if length candidate > tolerance * length (axisPoint-originPoint) do normal = normalize candidate
    )
    local hasVolume = false
    if normal != undefined do for p in points where abs (dot (p-originPoint) normal) > tolerance do hasVolume = true
    if not hasVolume do throw "Выбраны плоские или вырожденные полигоны. Для коллизии нужен объёмный участок."
    if nvpx == undefined do throw "В этой установке Max недоступен nvpx.CreateConvexHull."
    if maxVertices < 4 or maxVertices > 255 do throw "Лимит вершин: от 4 до 255."
    if not applyChanges do return ("Выбрано полигонов: " + faces.numberSet as string + ". Будет создана одна выпуклая оболочка. Она перекроет вогнутости и проёмы. Лимит вершин: " + maxVertices as string + ". Геометрический результат проверяется при создании.")
    local made = undefined
    try
    (
      made = copy n
      local tm = made.transform
      made.parent = undefined; made.transform = tm
      made.name = uniqueName "AGRWB_UCX_Hull_"
      local removeFaces = #{1..(polyop.getNumFaces made)} - faces
      if removeFaces.numberSet > 0 do polyop.deleteFaces made removeFaces delIsoVerts:true
      convertToMesh made
      local hull = nvpx.CreateConvexHull made.mesh maxVertices 0
      if hull == undefined do throw "Не удалось построить объёмную оболочку. Выберите объём, а не плоский участок."
      made.mesh = hull
      convertToPoly made
      -- Reject zero-volume results in world space, including slanted planes.
      local volume6 = 0.0
      local m = snapshotAsMesh made
      local origin = getVert m 1
      for f = 1 to m.numfaces do
      (
        local tri = getFace m f
        volume6 += dot ((getVert m tri.x)-origin) (cross ((getVert m tri.y)-origin) ((getVert m tri.z)-origin))
      )
      free m
      if abs volume6 < (units.decodeValue "0.01mm")^3 do throw "Получилась плоская оболочка: нужен объёмный участок."
      made.material = undefined
      made.wirecolor = color 0 220 220
      setUserProp made "AGRWB_ExportCopy" true
      setUserProp made "AGRWB_Profile" "VPM"
      setUserProp made "AGRWB_SourceHandle" (n.handle as string)
      for key in #("AGRWB_Role","AGRWB_Stem","AGRWB_Index") do setUserProp made key ""
      select made
      "Создана выпуклая оболочка: " + made.name + ", вершин " + (polyop.getNumVerts made) as string + ". Исходник сохранён. Назначьте имя UCX через «Имена для сдачи»; проверьте проёмы и зазоры. Это не декомпозиция здания."
    )
    catch
    (
      if isValidNode made do delete made
      throw()
    )
  ),
  fn textureFiles nodes =
  (
    local paths = #()
    for n in nodes where isValidNode n and n.material != undefined do
      for p in (AGRWB_Pipeline.collectMaps n.material #() #()) do appendIfUnique paths p
    if paths.count == 0 do throw "В материалах выделенных объектов не найдены файловые текстуры."
    local ss = stringStream ""
    format "Файловых ссылок: %. Сцена и пути не изменены.\n" paths.count to:ss
    for p in paths do format "% | %\n" (if doesFileExist p then "НАЙДЕН" else "НЕТ ФАЙЛА") p to:ss
    format "Список читает доступные filename-свойства карт. Последовательности, токены UDIM и зависимости закрытых плагинов требуют отдельной проверки.\n" to:ss
    ss as string
  )
)
AGRWB_Extensions = AGRWB_ExtensionsType()

