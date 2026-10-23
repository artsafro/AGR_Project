/* Profile preparation. Local NPM/VPM_STANDARD.yaml naming sections.
   Partial preflight, never an AGR Checker replacement. */
global AGRWB_Pipeline
struct AGRWB_PipelineType
(
  fn requireCopies nodes profile readOnly:false =
  (
    if nodes.count == 0 do throw "Сначала возьмите объекты в набор и выберите способ работы."
    local seen = #()
    for n in nodes do
    (
      if not isValidNode n do throw "Deleted target. Recapture the set."
      if findItem seen n > 0 do throw ("Duplicate target: " + n.name)
      append seen n
      if not readOnly and ((getUserProp n "AGRWB_ExportCopy" != true and getUserProp n "AGRWB_WorkTarget" != true) or getUserProp n "AGRWB_Profile" != profile) do
        throw ("Объект не подготовлен для этой вкладки: " + n.name + ". В шаге 1 выберите отдельную версию или работу с текущими объектами.")
      if not readOnly and getUserProp n "AGRWB_ExportCopy" != true do
      (
        for other in objects where other != n and other.baseObject == n.baseObject do
          throw ("Объект имеет инстансы: " + n.name + ". Создайте отдельную версию, чтобы не изменить связанные объекты вне набора.")
      )
    )
    true
  ),
  fn expectedName profile stem role index =
  (
    if findItem #("NPM","VPM") profile == 0 do throw "Unknown profile."
    if stem == undefined or role == undefined or index == undefined do throw "Missing role data."
    if not ((dotNetClass "System.Text.RegularExpressions.Regex").IsMatch stem "^SM_[A-Za-z0-9_]+$") do
      throw "Base must be SM_Address; A-Z, digits and underscore only."
    if matchPattern stem pattern:"*_Ground" do throw "Enter SM_Address without _Ground; choose Ground role."
    if index < 1 or index > 999 do throw "Index must be 1..999."
    if findItem #("Main","MainGlass","Ground","UCX_Main","UCX_Ground") role == 0 do throw "Unsupported role."
    if profile == "NPM" and matchPattern role pattern:"UCX*" do throw "UCX is a VPM operation."
    if profile == "NPM" and role != "Ground" and index > 20 do throw "NPM OKS index is 1..20."
    local number = formattedPrint index format:"03d"
    local result = case role of
    (
      "Ground": stem + "_Ground"
      "UCX_Main": "UCX_" + stem + "_Main_" + number
      "UCX_Ground": "UCX_" + stem + "_Ground_" + number
      default: stem + (if profile == "NPM" then "_" + number else "") + "_" + role
    )
    if result.count > 254 do throw "Name exceeds 254 characters."
    result
  ),
  fn planNames nodes profile stem role startIndex readOnly:false =
  (
    requireCopies nodes profile readOnly:readOnly
    if nodes.count > 1 and not (matchPattern role pattern:"UCX*") do
      throw "Main, MainGlass and Ground require one object. Attach is not automatic."
    local plan = #()
    for i = 1 to nodes.count do
    (
      local idx = if matchPattern role pattern:"UCX*" then startIndex+i-1 else startIndex
      local nm = expectedName profile stem role idx
      for other in objects where other != nodes[i] do
        if (toLower other.name) == (toLower nm) do throw ("Name already used: " + nm)
      append plan #(nodes[i], nm, role, idx)
    )
    plan
  ),
  fn previewNames plan =
  (
    local ss = stringStream ""
    for row in plan do format "% -> %\n" row[1].name row[2] to:ss
    ss as string
  ),
  fn applyNames nodes profile stem role startIndex =
  (
    local plan = planNames nodes profile stem role startIndex
    for row in plan do
    (
      row[1].name = row[2]
      setUserProp row[1] "AGRWB_Role" row[3]
      setUserProp row[1] "AGRWB_Index" row[4]
      setUserProp row[1] "AGRWB_Stem" stem
    )
    "Names and roles applied: " + plan.count as string
  ),
  fn collectMaps value found visited =
  (
    if value != undefined and findItem visited value == 0 do
    (
      append visited value
      if isProperty value #filename do
      (
        local path = try (value.filename as string) catch ("")
        if path != "" do appendIfUnique found path
      )
      local tc = try (getNumSubTexmaps value) catch (0)
      for i = 1 to tc do collectMaps (getSubTexmap value i) found visited
      local mc = try (getNumSubMtls value) catch (0)
      for i = 1 to mc do collectMaps (getSubMtl value i) found visited
    )
    found
  ),
  fn moveUV nodes profile tile applyChanges =
  (
    requireCopies nodes profile readOnly:(not applyChanges)
    if tile < 1001 or tile > 1999 do throw "UDIM must be 1001..1999."
    if profile == "NPM" and tile != 1001 do throw "NPM uses tile 1001."
    local offset = tile-1001
    local tileU = mod offset 10
    local tileV = floor (offset/10.0)
    local plan = #()
    local ss = stringStream ""
    for n in nodes do
    (
      if n.modifiers.count != 0 do throw ("Collapse a COPY before UV editing: " + n.name)
      local poly = classOf n.baseObject == Editable_Poly
      if not poly and classOf n.baseObject != Editable_Mesh do throw ("Unsupported mesh: " + n.name)
      local supported = if poly then polyop.getMapSupport n 1 else meshop.getMapSupport n 1
      if not supported do throw ("No UV1: " + n.name)
      local count = if poly then polyop.getNumMapVerts n 1 else meshop.getNumMapVerts n 1
      if count == 0 do throw ("Empty UV1: " + n.name)
      local points = #()
      local low = [1e30,1e30,0]
      local high = [-1e30,-1e30,0]
      for v = 1 to count do
      (
        local p = if poly then polyop.getMapVert n 1 v else meshop.getMapVert n 1 v
        append points p
        low.x = amin low.x p.x
        low.y = amin low.y p.y
        high.x = amax high.x p.x
        high.y = amax high.y p.y
      )
      if high.x-low.x > 1.0 or high.y-low.y > 1.0 do throw ("UV spans more than one tile: " + n.name)
      local delta = [tileU+0.5-(low.x+high.x)*0.5,tileV+0.5-(low.y+high.y)*0.5,0]
      append plan #(n,poly,points,delta)
      format "% | delta % | tile %\n" n.name delta tile to:ss
    )
    if applyChanges do
    (
      for row in plan do
      (
        for v = 1 to row[3].count do
          if row[2] then polyop.setMapVert row[1] 1 v (row[3][v]+row[4])
          else meshop.setMapVert row[1] 1 v (row[3][v]+row[4])
        update row[1]
      )
      redrawViews()
    )
    format "%\nPadding, inter-object UV overlap and packing are not checked.\n" (if applyChanges then "APPLIED" else "PREVIEW: no changes") to:ss
    ss as string
  ),
  fn check nodes profile =
  (
    local errors = #()
    local warnings = #()
    local ss = stringStream ""
    if nodes.count == 0 do append errors "EMPTY_SET"
    for n in nodes do
    (
      if not isValidNode n then append errors "DELETED_TARGET"
      else
      (
        if getUserProp n "AGRWB_Profile" != undefined and getUserProp n "AGRWB_Profile" != profile do append errors (n.name + ": WRONG_PROFILE")
        local role = getUserProp n "AGRWB_Role"
        local stem = getUserProp n "AGRWB_Stem"
        local idx = getUserProp n "AGRWB_Index"
        try
        (
          local expected = expectedName profile stem role idx
          if n.name != expected do append errors (n.name + ": EXPECTED " + expected)
          for other in objects where other != n do
            if (toLower other.name) == (toLower n.name) do appendIfUnique errors (n.name + ": DUPLICATE_NAME")
        )
        catch (append errors (n.name + ": MISSING_OR_INVALID_ROLE"))
        if not (classOf n.baseObject == Editable_Poly or classOf n.baseObject == Editable_Mesh) do
          append errors (n.name + ": UNSUPPORTED_CLASS")
        if role == undefined or not (matchPattern role pattern:"UCX*") do
        (
          if n.material == undefined then append errors (n.name + ": NO_MATERIAL")
          else
          (
            local maps = collectMaps n.material #() #()
            if maps.count == 0 do append warnings (n.name + ": NO_FILE_MAPS_FOUND")
            for p in maps do if not (doesFileExist p) do append errors (n.name + ": MISSING_MAP " + p)
            format "% | material:% | file maps:%\n" n.name n.material.name maps.count to:ss
          )
          local m = undefined
          try
          (
            m = snapshotAsMesh n
            if not (meshop.getMapSupport m 1) then append errors (n.name + ": NO_UV1")
            else if meshop.getNumMapVerts m 1 == 0 do append errors (n.name + ": EMPTY_UV1")
          )
          catch (append errors (n.name + ": MESH_READ_FAILED"))
          if m != undefined do free m
        )
      )
    )
    for e in errors do format "ERROR %\n" e to:ss
    for w in warnings do format "WARN %\n" w to:ss
    format "Errors:% | warnings:%\nPARTIAL PREFLIGHT ONLY. Topology/UV overlaps/UCX/GeoJSON/AGR Checker remain unverified.\n" errors.count warnings.count to:ss
    #(errors, warnings, ss as string)
  )
)
AGRWB_Pipeline = AGRWB_PipelineType()

