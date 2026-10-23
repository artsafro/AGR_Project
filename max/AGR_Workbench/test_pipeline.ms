/* Synthetic integration test; creates and deletes only nodes made in this run.
   No reset, user selection and core context restored. No user scene is saved. */
global AGRWB_TestReport
(
  local oldProfile = AGRWB_Core.profile
  local oldTargets = AGRWB_Core.targets
  local oldSelection = selection as array
  local made = #()
  local ss = stringStream ""
  local root = getFilenamePath (getThisScriptFilename())
  local stem = "SM_SYNTH_AGRWB_" + timestamp() as string
  fn ensure condition message = (if not condition do throw message)
  try
  (
    ensure (AGRWB_Pipeline.expectedName "NPM" "SM_Test" "Main" 2 == "SM_Test_002_Main") "NPM naming"
    ensure (AGRWB_Pipeline.expectedName "VPM" "SM_Test" "Main" 2 == "SM_Test_Main") "VPM naming"
    local blocked = false
    try(AGRWB_Pipeline.expectedName "NPM" "SM_Test" "UCX_Main" 1)catch(blocked=true)
    ensure blocked "NPM accepted UCX"
    blocked = false
    try(AGRWB_Pipeline.expectedName "NPM" "SM_Test" "Main" 21)catch(blocked=true)
    ensure blocked "NPM index >20 accepted"
    format "PASS naming profiles and invalid roles/indices\n" to:ss
    local meter = units.decodeValue "1m"
    local src = plane length:meter width:meter lengthsegs:1 widthsegs:1 name:(uniqueName "AGRWB_TEST_SOURCE_")
    append made src
    convertToPoly src
    src.material = standardMaterial name:"SYNTH_AGRWB_material"
    AGRWB_Core.profile = "VPM"
    local cp = AGRWB_Core.makeCopies #(src)
    join made cp
    local n = cp[1]
    ensure (n.baseObject != src.baseObject) "Shared geometry"
    ensure (n.material != src.material) "Shared material"
    blocked = false
    try(AGRWB_Pipeline.moveUV cp "NPM" 1001 true)catch(blocked=true)
    ensure blocked "Wrong-profile UV edit accepted"
    blocked = false
    try(AGRWB_Pipeline.requireCopies #(n,n) "VPM")catch(blocked=true)
    ensure blocked "Duplicate target accepted"
    local beforeUV = polyop.getMapVert n 1 1
    local preview = AGRWB_Pipeline.moveUV cp "VPM" 1012 false
    local afterUV = polyop.getMapVert n 1 1
    ensure (distance beforeUV afterUV < 1e-8) "Preview changed UV"
    AGRWB_Pipeline.moveUV cp "VPM" 1012 true
    afterUV = polyop.getMapVert n 1 1
    ensure (abs(afterUV.x-beforeUV.x-1) < 1e-6 and abs(afterUV.y-beforeUV.y-1) < 1e-6) "Wrong UDIM offset"
    ensure (distance (polyop.getMapVert src 1 1) beforeUV < 1e-8) "Source UV changed"
    ensure ((findString (AGRWB_Core.density cp 2048) "aggregate:2048") != undefined) "UV translation changed density"
    format "PASS copies, UV preview, UDIM1012, source UV, density\n" to:ss
    local plan = AGRWB_Pipeline.planNames cp "VPM" stem "Main" 1
    ensure (n.name != plan[1][2]) "Name preview mutated"
    AGRWB_Pipeline.applyNames cp "VPM" stem "Main" 1
    ensure (n.name == stem+"_Main") "Role/name application"
    local checks = AGRWB_Pipeline.check cp "VPM"
    ensure (checks[1].count == 0) checks[3]
    n.material.diffuseMap = bitmapTexture filename:(root+"MISSING_SYNTH_TEXTURE.png")
    checks = AGRWB_Pipeline.check cp "VPM"
    ensure ((findString checks[3] "MISSING_MAP") != undefined) "Missing map not found"
    n.material.diffuseMap = undefined
    local another = AGRWB_Core.makeCopies #(src)
    join made another
    local priorName = another[1].name
    blocked = false
    try(AGRWB_Pipeline.applyNames another "VPM" stem "Main" 1)catch(blocked=true)
    ensure (blocked and another[1].name == priorName) "Collision was not atomic"
    blocked = false
    try(AGRWB_Pipeline.applyNames #(src) "VPM" stem "Main" 1)catch(blocked=true)
    ensure blocked "Original renamed"
    format "PASS naming preview/apply, material audit, missing maps, collision guard, original guard\n" to:ss
    local outputPath = root + stem + ".fbx"
    AGRWB_Core.exportCopies cp outputPath showDialog:false
    ensure (doesFileExist outputPath) "FBX not written"
    format "FBX=%\n" outputPath to:ss
    format "PASS_ALL_IMPLEMENTED_TESTS\n" to:ss
  )
  catch (format "FAIL %\n" (getCurrentException()) to:ss)
  for n in made where isValidNode n do delete n
  AGRWB_Core.profile = oldProfile
  AGRWB_Core.targets = oldTargets
  select (for n in oldSelection where isValidNode n collect n)
  AGRWB_TestReport = ss as string
)

