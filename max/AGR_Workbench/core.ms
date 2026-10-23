/* AGR Workbench 0.1. Explicit targets; no scene changes on fileIn. */
global AGRWB_Core
global AGRWB_Pipeline
struct AGRWB_CoreType
(
  version = "0.5.0",
  targets = #(),
  profile = "NPM",
  lastReport = "",
  fn validNodes nodes = (for n in nodes where isValidNode n collect n),
  fn capture nodes =
  (
    targets = validNodes nodes
    targets.count
  ),
  fn audit nodes =
  (
    local ss = stringStream ""
    local tris = 0
    local missingMtl = 0
    local missingUV = 0
    local failed = 0
    local supported = 0
    local live = validNodes nodes
    format "AGR Workbench % | %\nScene: %\nTargets: %\nUnits: % x %\n" version profile (maxFilePath + maxFileName) live.count units.SystemScale units.SystemType to:ss
    for n in live do
    (
      if n.material == undefined do missingMtl += 1
      -- Proxies/scatters are deliberately not expanded by a quick audit.
      if (classOf n.baseObject == Editable_Poly or classOf n.baseObject == Editable_Mesh) then
      (
        local m = undefined
        try
        (
          m = snapshotAsMesh n
          local t = m.numfaces
          tris += t
          supported += 1
          if not (meshop.getMapSupport m 1) then missingUV += 1
          else if (meshop.getNumMapVerts m 1) == 0 do missingUV += 1
          format "% | tris:% | material:%\n" n.name t (if n.material == undefined then "NONE" else n.material.name) to:ss
        )
        catch (failed += 1; format "ERROR %: %\n" n.name (getCurrentException()) to:ss)
        if m != undefined do free m
      )
      else format "SKIP mesh evaluation: % (%)\n" n.name (classOf n.baseObject) to:ss
    )
    format "\nEvaluated:% | triangles:% | no material:% | no UV1:% | errors:%\n" supported tris missingMtl missingUV failed to:ss
    format "Not evaluated:%\nNOT an AGR Checker pass. Topology, UV overlap, maps and delivery remain unchecked.\n" (live.count - supported - failed) to:ss
    lastReport = ss as string
    lastReport
  ),
  fn makeCopies nodes =
  (
    local live = validNodes nodes
    if live.count == 0 do throw "Capture at least one object."
    for n in live do
      if (isGroupHead n or not (classOf n.baseObject == Editable_Poly or classOf n.baseObject == Editable_Mesh)) do
        throw ("Copies require Editable Poly/Mesh: " + n.name)
    local made = #()
    try
    (
      for n in live do
      (
        local c = copy n
        append made c
        local tm = n.transform
        c.parent = undefined
        c.transform = tm
        c.name = uniqueName ("AGRWB_" + profile + "_" + n.name + "_")
        if n.material != undefined do c.material = copy n.material
        setUserProp c "AGRWB_Profile" profile
        setUserProp c "AGRWB_SourceHandle" ((getHandleByAnim n) as string)
        setUserProp c "AGRWB_ExportCopy" true
      )
    )
    catch
    (
      local err = getCurrentException()
      for c in made where isValidNode c do delete c
      throw()
    )
    made
  ),
  fn density nodes mapSize =
  (
    local ss = stringStream ""
    local meter = units.decodeValue "1m"
    if mapSize < 1 or meter <= 0 do throw "Invalid map size or units."
    format "% | texture % x % | px/m\n" profile mapSize mapSize to:ss
    for n in validNodes nodes do
    (
      local m = undefined
      if (classOf n.baseObject == Editable_Poly or classOf n.baseObject == Editable_Mesh) then
      (
        try
        (
          m = snapshotAsMesh n
          if not (meshop.getMapSupport m 1) do throw "UV1 missing"
          local lo = 1e30
          local hi = 0.0
          local sumWorld = 0.0
          local sumUV = 0.0
          local degenerate = 0
          for f = 1 to m.numfaces do
          (
            local face = getFace m f
            local uv = meshop.getMapFace m 1 f
            -- snapshotAsMesh already includes the evaluated node transform.
            local a = getVert m (face.x as integer)
            local b = getVert m (face.y as integer)
            local c = getVert m (face.z as integer)
            local u = meshop.getMapVert m 1 (uv.x as integer)
            local v = meshop.getMapVert m 1 (uv.y as integer)
            local w = meshop.getMapVert m 1 (uv.z as integer)
            local aw = (length (cross (b-a) (c-a))) * 0.5 / (meter*meter)
            local au = abs ((v.x-u.x)*(w.y-u.y)-(v.y-u.y)*(w.x-u.x)) * 0.5
            if aw <= 1e-12 or au <= 1e-12 then degenerate += 1
            else
            (
              local td = mapSize * sqrt (au/aw)
              lo = amin lo td
              hi = amax hi td
              sumWorld += aw
              sumUV += au
            )
          )
          if sumWorld > 0 then
            format "% | min:% max:% aggregate:% | degenerate:%\n" n.name lo hi (mapSize*sqrt(sumUV/sumWorld)) degenerate to:ss
          else format "% | no measurable faces | degenerate:%\n" n.name degenerate to:ss
        )
        catch (format "ERROR %: %\n" n.name (getCurrentException()) to:ss)
        if m != undefined do free m
      )
      else format "SKIP: %\n" n.name to:ss
    )
    format "User-specified square resolution; mixed texture sizes, placeholders and UV overlap are NOT validated.\n" to:ss
    lastReport = ss as string
    lastReport
  ),
  fn exportCopies nodes outputPath showDialog:true =
  (
    local live = validNodes nodes
    if live.count == 0 do throw "No export copies captured."
    if doesFileExist outputPath do throw "Output already exists. Choose a new filename."
    for n in live do
      if ((getUserProp n "AGRWB_ExportCopy") != true and (getUserProp n "AGRWB_WorkTarget") != true) or (getUserProp n "AGRWB_Profile") != profile do
        throw ("Not an export copy for " + profile + ": " + n.name)
    if AGRWB_Pipeline == undefined do throw "Preparation module is not loaded."
    local checks = AGRWB_Pipeline.check nodes profile
    if checks[1].count > 0 do throw checks[3]
    local prior = selection as array
    local ok = false
    try
    (
      select live
      -- Show Autodesk export settings; do not silently inherit hidden settings.
      ok = if showDialog then exportFile outputPath selectedOnly:true using:FBXEXP
        else exportFile outputPath #noPrompt selectedOnly:true using:FBXEXP
      select (validNodes prior)
    )
    catch (select (validNodes prior); throw())
    if not ok or not (doesFileExist outputPath) do throw "Export cancelled or failed."
    lastReport = "FBX written: " + outputPath + "\nNOT validated by round-trip or AGR Checker."
    lastReport
  )
)
AGRWB_Core = AGRWB_CoreType()

