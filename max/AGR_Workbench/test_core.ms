/* Run in a NEW 3dsmaxbatch process, never in a user's scene. */
(
  local root = getFilenamePath (getThisScriptFilename())
  local report = createFile (root + "test-results.txt")
  fn require condition message = (if not condition do throw message)
  try
  (
    require (objects.count == 0) "Tests require an empty batch scene."
    fileIn (root + "core.ms")
    units.SystemType = #Meters
    units.SystemScale = 1.0
    local p = plane length:1 width:1 lengthsegs:1 widthsegs:1 name:"SYNTH_AGRWB"
    convertToPoly p
    p.material = standardMaterial name:"SYNTH_material"
    local d = AGRWB_Core.density #(p) 2048
    format "%\n" d to:report
    require ((findString d "aggregate:2048") != undefined) "1m plane density wrong."
    p.scale = [2,2,2]
    p.rotation = eulerAngles 20 30 40
    d = AGRWB_Core.density #(p) 2048
    format "%\n" d to:report
    require ((findString d "aggregate:1024") != undefined) "World scale density wrong."
    local copies = AGRWB_Core.makeCopies #(p)
    require (copies.count == 1) "Copy count wrong."
    require (copies[1].baseObject != p.baseObject) "Geometry still instanced."
    require (copies[1].material != p.material) "Material still shared."
    require ((getUserProp p "AGRWB_ExportCopy") == undefined) "Source changed."
    require ((getUserProp copies[1] "AGRWB_ExportCopy") == true) "Copy not tagged."
    format "%\n" (AGRWB_Core.audit copies) to:report
    local rejected = false
    try (AGRWB_Core.makeCopies #()) catch (rejected = true)
    require rejected "Empty copy request accepted."
    rejected = false
    try (AGRWB_Core.exportCopies #(p) (root + "forbidden.fbx")) catch (rejected = true)
    require rejected "Original allowed for export."
    AGRWB_Core.capture copies
    delete copies
    require ((AGRWB_Core.validNodes AGRWB_Core.targets).count == 0) "Deleted targets remain."
    delete p
    units.SystemType = #Centimeters
    local q = plane length:100 width:100 lengthsegs:1 widthsegs:1 name:"SYNTH_CM"
    convertToPoly q
    d = AGRWB_Core.density #(q) 2048
    format "%\n" d to:report
    require ((findString d "aggregate:2048") != undefined) "Centimeter density wrong."
    delete q
    format "PASS: density in meters and cm, transforms, independent copies, audit, empty/deleted targets, original export rejection.\n" to:report
  )
  catch (format "FAIL: %\n" (getCurrentException()) to:report)
  close report
)

