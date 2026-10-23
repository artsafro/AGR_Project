/* Synthetic native-task integration tests. Never resets or saves the scene. */
global AGRWB_TaskTestReport
(
  local priorSelection = selection as array
  local priorProfile = AGRWB_Core.profile
  local priorTargets = AGRWB_Core.targets
  local made = #()
  local ss = stringStream ""
  fn ensure test msg = (if not test do throw msg)
  try
  (
    AGRWB_Core.profile = "VPM"
    local meter = units.decodeValue "1m"
    local p = plane width:meter length:meter widthsegs:1 lengthsegs:1 name:(uniqueName "SYNTH_AGRWB_TASK_")
    append made p
    convertToPoly p
    local nBefore = objects.count
    AGRWB_Tasks.adopt #(p) "VPM"
    ensure (objects.count == nBefore) "Adopt created geometry"
    ensure (getUserProp p "AGRWB_ExportCopy" != true) "Adopt pretended original is a copy"
    ensure (getUserProp p "AGRWB_WorkTarget" == true) "Adopt missing work tag"
    local inst = instance p
    append made inst
    local instanceBlocked = false
    try(AGRWB_Tasks.adopt #(p) "VPM")catch(instanceBlocked=true)
    ensure instanceBlocked "Direct editing accepted shared geometry"
    delete inst
    local oldUV = polyOp.getMapVert p 1 1
    local oldUVCount = polyOp.getNumMapVerts p 1
    AGRWB_Tasks.projection #(p) true 1 1 false
    ensure (polyOp.getNumMapVerts p 1 == oldUVCount and polyOp.getMapVert p 1 1 == oldUV) "Preview changed UV"
    local blocked=false
    try(AGRWB_Tasks.projection #(p) true 2 1 true)catch(blocked=true)
    ensure blocked "Projection accepted stretching"
    AGRWB_Tasks.projection #(p) true 1 1 true
    local mf = polyOp.getMapFace p 1 1
    local uvMin = [1e9,1e9,0]
    local uvMax = [-1e9,-1e9,0]
    for vi in mf do
    (
      local uv = polyOp.getMapVert p 1 vi
      uvMin.x=amin uvMin.x uv.x; uvMin.y=amin uvMin.y uv.y
      uvMax.x=amax uvMax.x uv.x; uvMax.y=amax uvMax.y uv.y
    )
    ensure (abs((uvMax.x-uvMin.x)-1)<0.0001 and abs((uvMax.y-uvMin.y)-1)<0.0001) "Physical UV scale incorrect"
    format "PASS adopt without duplicate; projection preview; scale; stretch guard\n" to:ss
    local b = box width:meter length:meter height:meter name:(uniqueName "SYNTH_AGRWB_TASK_")
    append made b
    convertToPoly b
    AGRWB_Tasks.adopt #(b) "VPM"
    nBefore=objects.count
    AGRWB_Tasks.collision #(b) true false
    ensure (objects.count==nBefore) "Collision preview created object"
    AGRWB_Tasks.collision #(b) true true
    local c = selection[1]
    append made c
    ensure (c!=b and getUserProp c "AGRWB_ExportCopy" == true) "Collision result missing"
    ensure (distance c.min b.min <0.001 and distance c.max b.max <0.001) "Collision bounds wrong"
    blocked=false
    try(AGRWB_Tasks.collision #(p) true true)catch(blocked=true)
    ensure blocked "Flat collision accepted"
    local lamp=FreeSpot name:(uniqueName "SYNTH_AGRWB_TASK_Light_")
    append made lamp
    local preLights = lights as array
    AGRWB_Tasks.lights #(p) true lamp false
    ensure (lights.count==preLights.count) "Light preview created object"
    AGRWB_Tasks.lights #(p) true lamp true
    local newLights=for light in lights where findItem preLights light==0 collect light
    join made newLights
    ensure (newLights.count==1 and newLights[1].baseObject != lamp.baseObject) "Light copy is not independent"
    ensure (dot (-newLights[1].transform.row3) [0,0,1]>0.999) "Light direction wrong"
    format "PASS collision preview/bounds/flat guard; light preview/independence/direction\n" to:ss
    polyOp.setEdgeSelection p #{1,3}
    local faceCount=polyOp.getNumFaces p
    AGRWB_Tasks.connectEdges #(p) 2 false
    ensure (polyOp.getNumFaces p==faceCount) "Connect preview changed mesh"
    AGRWB_Tasks.connectEdges #(p) 2 true
    ensure (polyOp.getNumFaces p>faceCount) "Connect did not change mesh"
    format "PASS Connect preview and applied face count\nPASS_ALL_NATIVE_TASK_TESTS\n" to:ss
  )
  catch (format "FAIL %\n" (getCurrentException()) to:ss)
  for n in made where isValidNode n do delete n
  AGRWB_Core.profile=priorProfile
  AGRWB_Core.targets=priorTargets
  select (for n in priorSelection where isValidNode n collect n)
  AGRWB_TaskTestReport=ss as string
)

