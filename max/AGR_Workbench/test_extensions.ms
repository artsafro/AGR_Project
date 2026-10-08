/* Synthetic fixtures only. No reset/save; cleanup and restore current selection. */
global AGRWB_ExtensionReport
(
  local prior = selection as array
  local profile = AGRWB_Core.profile
  local made = #()
  local ss = stringStream ""
  fn ensure ok msg = (if not ok do throw msg)
  try
  (
    AGRWB_Core.profile = "VPM"
    local p = plane width:100 length:100 widthsegs:2 lengthsegs:1 name:(uniqueName "SYNTH_WB_EXT_")
    append made p
    convertToPoly p
    polyop.setFaceMatID p #{1} 1
    polyop.setFaceMatID p #{2} 2
    local first = for v in (polyop.getMapFace p 1 1) collect polyop.getMapVert p 1 v
    local secondIDs = polyop.getMapFace p 1 2
    local second = for v in secondIDs collect polyop.getMapVert p 1 v
    local countBefore = polyop.getNumMapVerts p 1
    AGRWB_Extensions.materialUV #(p) 1 1012 false
    ensure (polyop.getNumMapVerts p 1 == countBefore and getUserProp p "AGRWB_Profile" == undefined) "UV preview mutated source"
    AGRWB_Tasks.adopt #(p) "VPM"
    AGRWB_Extensions.materialUV #(p) 1 1012 true
    local after = for v in (polyop.getMapFace p 1 1) collect polyop.getMapVert p 1 v
    local delta = after[1]-first[1]
    for i = 1 to after.count do
    (
      ensure (distance (after[i]-first[i]) delta < 0.00001) "UV scale changed"
      ensure (after[i].x>=1 and after[i].x<=2 and after[i].y>=1 and after[i].y<=2) "Wrong target tile"
    )
    for i = 1 to secondIDs.count do ensure (distance (polyop.getMapVert p 1 secondIDs[i]) second[i] < 0.00001) "Other finish moved"
    local blocked = false
    try(AGRWB_Extensions.materialUV #(p) 999 1001 true)catch(blocked=true)
    ensure blocked "Missing Material ID accepted"
    local mapFace = polyop.getMapFace p 1 1
    polyop.setMapVert p 1 mapFace[1] [10,10,0]
    countBefore = polyop.getNumMapVerts p 1
    blocked = false
    try(AGRWB_Extensions.materialUV #(p) 1 1001 true)catch(blocked=true)
    ensure (blocked and polyop.getNumMapVerts p 1 == countBefore) "Oversize UV accepted or mutated"
    local b = box width:100 length:80 height:60 name:(uniqueName "SYNTH_WB_HULL_")
    append made b
    convertToPoly b
    b.pos = [125000,235000,420]
    polyop.setFaceSelection b #{1..6}
    local originalFaces = polyop.getNumFaces b
    local total = objects.count
    AGRWB_Extensions.convexHull #(b) true 64 false
    ensure (objects.count == total) "Hull preview created node"
    AGRWB_Extensions.convexHull #(b) true 64 true
    local hull = selection[1]
    append made hull
    ensure (hull != b and hull.baseObject != b.baseObject) "Hull shares source geometry"
    ensure (polyop.getNumVerts hull == 8 and polyop.getOpenEdges hull == #{}) "Hull topology invalid"
    ensure (polyop.getNumFaces b == originalFaces and (polyop.getFaceSelection b).numberSet == 6) "Hull changed source"
    ensure (getUserProp b "AGRWB_Profile" == undefined) "Hull tagged source"
    ensure (distance hull.pos b.pos < 0.001) "Hull moved in world space"
    local stem = "SM_SYNTH_HULL_" + timestamp() as string
    AGRWB_Pipeline.applyNames #(hull) "VPM" stem "UCX_Main" 1
    local outputPath = AGRWB_Root + stem + ".fbx"
    AGRWB_Core.exportCopies #(hull) outputPath showDialog:false
    ensure (doesFileExist outputPath) "Hull FBX missing"
    format "FBX=%\n" outputPath to:ss
    total = objects.count
    blocked = false
    try
    (
      AGRWB_Extensions.convexHull #(p) true 64 true
      if selection.count == 1 and findItem made selection[1] == 0 do append made selection[1]
    )catch(blocked=true)
    ensure (blocked and objects.count == total) "Flat hull accepted or temporary node leaked"
    p.material = standardMaterial diffuseMap:(bitmapTexture filename:@"C:\AGRWB_SYNTH_MISSING_IMAGE.png")
    local report = AGRWB_Extensions.textureFiles #(p)
    ensure (findString report "НЕТ ФАЙЛА" != undefined) "Missing texture not reported"
    format "PASS material-ID UV translation; adjacent shared UV unchanged; no preview mutation; oversize/missing ID guards; convex topology; world placement; source preservation; flat cleanup; missing texture\n" to:ss
  )
  catch(format "FAIL %\n" (getCurrentException()) to:ss)
  for n in made where isValidNode n do delete n
  select (for n in prior where isValidNode n collect n)
  AGRWB_Core.profile = profile
  AGRWB_ExtensionReport = ss as string
)

