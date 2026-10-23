/* Native task operations. Explicit nodes and face scope; no vendor dialogs.
   Source concepts: Facade Atlas planar mapping, UCX_Tools box method,
   FreeSpot_Tools polygon placement, edge_connect_segments Connect.
   Reimplemented with explicit parameters and validation before mutation. */
global AGRWB_Tasks
struct AGRWB_TasksType
(
  fn polyTarget nodes readOnly:false =
  (
    AGRWB_Pipeline.requireCopies nodes AGRWB_Core.profile readOnly:readOnly
    if nodes.count != 1 do throw "Для этой операции возьмите один объект в набор."
    local n = nodes[1]
    if classof n.baseObject != Editable_Poly or n.modifiers.count != 0 do
      throw "Нужен Editable Poly без модификаторов. Стек автоматически не сворачивается."
    n
  ),
  fn faceScope n allFaces =
  (
    local faces = if allFaces then #{1..(polyOp.getNumFaces n)} else polyOp.getFaceSelection n
    if faces.numberSet == 0 do throw "Выделите полигоны в Max или явно включите «Все полигоны»."
    faces
  ),
  fn adopt nodes profile =
  (
    if nodes.count == 0 do throw "Сначала возьмите выделение."
    for n in nodes do
    (
      if not isValidNode n do throw "В наборе удалённый объект. Возьмите выделение заново."
      if isGroupHead n or (classof n.baseObject != Editable_Poly and classof n.baseObject != Editable_Mesh) do
        throw "Нужны объекты Editable Poly/Mesh."
      local existing = getUserProp n "AGRWB_Profile"
      if existing != undefined and existing != profile do throw "Этот объект уже относится к другой вкладке. Создайте отдельную версию."
      for other in objects where other != n and other.baseObject == n.baseObject do
        throw ("Объект имеет инстансы: " + n.name + ". Для независимой обработки выберите отдельную версию.")
    )
    for n in nodes do
    (
      setUserProp n "AGRWB_WorkTarget" true
      setUserProp n "AGRWB_Profile" profile
    )
    "Выбрана работа с текущими объектами. Новые объекты не созданы. Изменения будут применяться к этому набору; доступен Undo."
  ),
  fn projection nodes allFaces axis meters applyChanges =
  (
    local n = polyTarget nodes readOnly:(not applyChanges)
    local faces = faceScope n allFaces
    if meters <= 0 do throw "Размер участка должен быть больше нуля."
    local meter = units.decodeValue "1m"
    local aU = case axis of (1:[1,0,0]; 2:[1,0,0]; 3:[0,1,0])
    local aV = if axis == 1 then [0,1,0] else [0,0,1]
    local normal = normalize (cross aU aV)
    local plans = #()
    for f in faces do
    (
      local vs = polyOp.getFaceVerts n f
      local points = #()
      in coordsys world (for v in vs do append points (polyOp.getVert n v))
      local fnormal = normalize (cross (points[2]-points[1]) (points[3]-points[1]))
      if abs(dot fnormal normal) < 0.999 do throw "Полигоны наклонены к плоскости проекции: будет растяжение. Выберите другую ось или отдельную плоскую группу."
      local uv = for p in points collect [(dot p aU)/(meter*meters),(dot p aV)/(meter*meters),0]
      append plans #(f,uv)
    )
    if applyChanges do
    (
      if not polyOp.getMapSupport n 1 do throw "UV1 отсутствует. Сначала создайте канал развёртки в Max; остальные полигоны не будут обнулены."
      local count = polyOp.getNumMapVerts n 1
      local extra = 0
      for entry in plans do extra += entry[2].count
      polyOp.setNumMapVerts n 1 (count+extra) keep:true
      for entry in plans do
      (
        local ids = #()
        for uv in entry[2] do
        (
          count += 1
          polyOp.setMapVert n 1 count uv
          append ids count
        )
        polyOp.setMapFace n 1 entry[1] ids
      )
      update n
    )
    (if applyChanges then "UV применены" else "План проекции") + ": " + faces.numberSet as string + " полигонов. 1 UV = " + meters as string + " м. Начало — мировой ноль; масштаб и фаза общие. Это исходная проекция, не готовый атлас: UV могут выходить за 0–1."
  ),
  fn collision nodes allFaces applyChanges =
  (
    if AGRWB_Core.profile != "VPM" do throw "Коллизии доступны на вкладке ВПМ."
    local n = polyTarget nodes readOnly:(not applyChanges)
    local faces = faceScope n allFaces
    local lo = [1e20,1e20,1e20]
    local hi = [-1e20,-1e20,-1e20]
    in coordsys world
    (
      for f in faces do for v in polyOp.getFaceVerts n f do
      (
        local p = polyOp.getVert n v
        for k = 1 to 3 do (lo[k]=amin lo[k] p[k]; hi[k]=amax hi[k] p[k])
      )
    )
    local size = hi-lo
    if amin size.x (amin size.y size.z) <= units.decodeValue "0.01mm" do
      throw "У выбранных полигонов нет объёма по одной из осей. Для бокса выберите объёмный участок."
    if applyChanges do
    (
      local c = undefined
      try
      (
        c = box width:size.x length:size.y height:size.z pos:[(lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z] name:(uniqueName "AGRWB_UCX_Box_")
        convertToPoly c
        c.wirecolor = color 0 200 255
        setUserProp c "AGRWB_ExportCopy" true
        setUserProp c "AGRWB_Profile" "VPM"
        setUserProp c "AGRWB_SourceHandle" ((getHandleByAnim n) as string)
        select c
      )
      catch (if isValidNode c do delete c; throw())
    )
    (if applyChanges then "Создан и выделен" else "Будет создан") + " один бокс по мировым осям. Размер, м: " + (size/(units.decodeValue "1m")) as string + ". Бокс закрывает отверстия; для сложной формы нужны отдельные участки. Возьмите результат в набор и назначьте роль UCX. Зазоры и пересечения не проверены."
  ),
  fn lights nodes allFaces template applyChanges =
  (
    if AGRWB_Core.profile != "VPM" do throw "Свет доступен на вкладке ВПМ."
    local n = polyTarget nodes readOnly:(not applyChanges)
    local faces = faceScope n allFaces
    if not isValidNode template or classof template != FreeSpot do throw "Укажите один FreeSpot как образец параметров света."
    local transforms = #()
    in coordsys world
    (
      for f in faces do
      (
        local c = polyOp.getFaceCenter n f
        local faceNormal = polyOp.getFaceNormal n f
        if length faceNormal < 0.000001 do throw "У полигона нулевая нормаль. Исправьте геометрию перед размещением света."
        local z = -(normalize faceNormal)
        local up = if abs(dot z [0,0,1]) > 0.999 then [0,1,0] else [0,0,1]
        local x = normalize (cross up z)
        append transforms (matrix3 x (cross z x) z c)
      )
    )
    local made = #()
    if applyChanges do
    (
      try
      (
        for tm in transforms do
        (
          local lamp = copy template
          append made lamp
          lamp.parent = undefined
          lamp.transform = tm
          lamp.name = uniqueName "AGRWB_Spot_"
        )
      )
      catch (for lamp in made where isValidNode lamp do delete lamp; throw())
    )
    (if applyChanges then "Создано" else "Будет создано") + " источников: " + transforms.count as string + ". В центре полигонов, свет направлен по наружной нормали. Параметры взяты из образца; источники независимые. Экспорт Light.fbx — отдельный, ещё не реализованный этап."
  ),
  fn connectEdges nodes segments applyChanges =
  (
    local n = polyTarget nodes readOnly:(not applyChanges)
    local edges = polyOp.getEdgeSelection n
    if edges.numberSet < 2 do throw "Выделите минимум два подходящих ребра Editable Poly."
    if segments < 1 or segments > 100 do throw "Число сегментов: 1–100."
    if applyChanges do
    (
      local savedSegments = n.connectEdgeSegments
      local savedSelection = selection as array
      local savedMode = getCommandPanelTaskMode()
      local savedLevel = subObjectLevel
      local beforeFaces = polyOp.getNumFaces n
      try
      (
        select n
        max modify mode
        modPanel.setCurrentObject n
        subObjectLevel = 2
        n.connectEdgeSegments = segments
        n.EditablePoly.buttonOp #ConnectEdges
      )
      catch
      (
        n.connectEdgeSegments = savedSegments
        select savedSelection
        setCommandPanelTaskMode savedMode
        try(subObjectLevel=savedLevel)catch()
        throw()
      )
      n.connectEdgeSegments = savedSegments
      select savedSelection
      setCommandPanelTaskMode savedMode
      try(subObjectLevel=savedLevel)catch()
      update n
      if polyOp.getNumFaces n == beforeFaces do throw "Max не соединил эти рёбра. Выберите противоположные рёбра одной группы полигонов."
    )
    (if applyChanges then "Connect выполнен" else "План Connect") + ": " + edges.numberSet as string + " выбранных рёбер, сегментов: " + segments as string + ". Проверьте полученную сетку; неподходящие рёбра Max может не соединить."
  )
)
AGRWB_Tasks = AGRWB_TasksType()

