/* Synthetic UI integration. Restores selection and deletes only own fixtures. */
global AGRWB_UISelectionReport
(
  local prior=selection as array
  local made=#()
  local ss=stringStream ""
  fn ensure ok msg = (if not ok do throw msg)
  try
  (
    AGRWB_UI.tabs.SelectedIndex=0
    local p=plane width:(units.decodeValue "1m") length:(units.decodeValue "1m") widthsegs:1 lengthsegs:1 name:(uniqueName "SYNTH_WB_UI_")
    append made p
    convertToPoly p
    select p
    AGRWB_UI.showTask #uv
    AGRWB_UI.chkAll.checked=true
    AGRWB_UI.ddlAxis.selection=1
    AGRWB_UI.spnMeters.value=2
    local count=polyOp.getNumMapVerts p 1
    AGRWB_UI.runCurrent false
    ensure (polyOp.getNumMapVerts p 1==count) "Preview changed UV"
    ensure (getUserProp p "AGRWB_WorkTarget" == undefined) "Preview tagged source"
    AGRWB_UI.runCurrent true
    ensure (polyOp.getNumMapVerts p 1>count) "Apply did not use current selection"
    ensure (getUserProp p "AGRWB_WorkTarget" == true) "Apply not registered"
    local second=copy p
    append made second
    second.name=uniqueName "SYNTH_WB_SECOND_"
    select second
    AGRWB_UI.showTask #names
    AGRWB_UI.edtStem.text="SM_SYNTH_UI_"+timestamp() as string
    AGRWB_UI.runCurrent false
    ensure (findString AGRWB_UI.edtLog.text second.name != undefined) "Selection change not followed"
    ensure (findString AGRWB_UI.edtLog.text p.name == undefined) "Old saved set leaked"
    ensure (AGRWB_UI.menu.Items.Count==10) "NPM task count"
    AGRWB_UI.showTask #density
    AGRWB_UI.chkGround.checked=false
    AGRWB_UI.selectionLabel()
    ensure (not AGRWB_UI.btnApply.enabled) "NPM density ungated"
    setUserProp second "AGRWB_Role" "Main"
    AGRWB_UI.chkGround.checked=true
    AGRWB_UI.runCurrent true
    ensure (findString AGRWB_UI.edtLog.text "Ground" != undefined) "NPM building accepted for Ground diagnosis"
    AGRWB_UI.showTask #copy
    AGRWB_UI.runCurrent true
    local clone=selection[1]
    if findItem made clone==0 do append made clone
    ensure (clone!=second and clone.baseObject!=second.baseObject) "Separate version failed"
    AGRWB_UI.tabs.SelectedIndex=1
    ensure (AGRWB_UI.menu.Items.Count==14) "VPM task count"
    AGRWB_UI.menu.SelectedIndex=6
    ensure (findString AGRWB_UI.lblTask.text "коллизию"!=undefined) "Visible menu event failed"
    format "PASS live selection; preview without mutation; direct UV; Ground gating; optional copy; both menus\n" to:ss
  )
  catch(format "FAIL %\n" (getCurrentException()) to:ss)
  for n in made where isValidNode n do delete n
  select (for n in prior where isValidNode n collect n)
  AGRWB_UI.tabs.SelectedIndex=0
  AGRWB_UI.chkAll.checked=false
  AGRWB_UI.spnMeters.value=1
  AGRWB_UI.edtStem.text=""
  AGRWB_UI.showTask #welcome
  AGRWB_UISelectionReport=ss as string
)

