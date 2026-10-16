/* Run ONLY in a new 3dsmaxbatch process:
   3dsmaxbatch.exe test_native.ms -mxsString fixture:yes
   Never fileIn this fixture in a user scene. */
if maxOps.mxsCmdLineArgs[#fixture] != "yes" do throw "Batch fixture argument required."
if objects.count != 0 do throw "Fixture requires an empty batch scene."
global AGR_NPMLinker
global AGR_NPMLinker_NoUI
global AGR_NPMFbx
(
    local here = getFilenamePath (getSourceFileName())
    local evidenceRoot = here + "../../tmp/max-texture-linker-native/"
    local root = evidenceRoot + "run_" + ((dotNetClass "System.DateTime").Now.ToString "yyyyMMdd_HHmmss_fff") + "/"
    makeDir root all:true
    local report = createFile (root + "native-result.txt")
    local failure = undefined
    fn check value label out =
    (
        if not value do throw ("FAIL: " + label)
        format "PASS: %\n" label to:out
        true
    )
    try
    (
        AGR_NPMLinker_NoUI = true
        fileIn (here + "NPM_Texture_Linker.ms")
        local leaf = root + "nested/"
        makeDir leaf all:true
        for channel in #("d", "r", "m", "o", "n") do
        (
            local image = bitmap 2 2 color:(color 100 100 100) filename:(leaf + "T_Test_Main_" + channel + "_1.png")
            save image
            close image
        )
        local index = AGR_NPMLinker.scanFolder root
        check (index.count == 5) "recursive scan: five files" report
        check (AGR_NPMLinker.objectKey "SM_Test_Main" == "test_main") "full object key" report
        check (AGR_NPMLinker.parseTexture "T_Test_Main_d_1.txt" == undefined) "non-image ignored" report
        local partial = AGR_NPMLinker.matchFiles "test_main" #(index[1])
        local partialMtl = AGR_NPMLinker.prepareMaterial "Test_Main" partial
        local filled = 0
        for prop in AGR_NPMLinker.slots where getProperty partialMtl prop != undefined do filled += 1
        check (filled == 1) "partial set creates only found map" report
        local noMatch = AGR_NPMLinker.matchFiles "test" index
        local unexpected = for path in noMatch where path != undefined collect path
        check (unexpected.count == 0) "no prefix matching" report
        local duplicateIndex = for record in index collect record
        append duplicateIndex index[1]
        check (AGR_NPMLinker.matchFiles "test_main" duplicateIndex == undefined) "duplicate rejected" report

        local old = Standardmaterial name:"M_Test_Main_1" opacity:17
        old.bumpMap = Normal_Bump()
        local a = box name:"SM_Test_Main" material:old
        local b = box name:"Test_Main" material:old
        local noMaterial = box name:"SM_Empty_Main"
        local glass = Standardmaterial name:"M_Glass_01" opacity:75 diffuse:(color 12 34 56) twoSided:true
        glass.reflectionMap = Reflect_Refract()
        glass.diffuseMap = Bitmaptexture filename:index[1][3]
        local g = box name:"SM_Test_2_MainGlass" material:glass
        local g10 = box name:"SM_Test_10_MainGlass" material:glass
        local glassMulti = MultiMaterial numsubs:2
        glassMulti[1] = glass
        glassMulti[2] = old
        local nestedGlass = box name:"SM_Test_NestedGlass" material:glassMulti
        local unusedSameName = Standardmaterial name:"M_Test_Main_1"
        meditMaterials[1] = unusedSameName
        local plan = AGR_NPMLinker.makePlan #(a,b,g,nestedGlass) index
        check (plan.count == 2 and plan[1][3] == plan[2][3]) "one new material per key; glass excluded" report
        local fresh = plan[1][3]
        check (fresh != old and fresh.opacity == 100) "old settings discarded" report
        for i = 1 to 5 do
        (
            local tex = getProperty fresh AGR_NPMLinker.slots[i]
            check (classOf tex == Bitmaptexture and tex.name == getFilenameFile tex.filename and tex.coords.mappingType == 0 and tex.coords.mapChannel == 1) ("direct named Texture Bitmap: " + AGR_NPMLinker.roles[i]) report
        )
        local glassPlan = AGR_NPMLinker.makeGlassPlan #(g10,g,nestedGlass)
        for item in glassPlan do append plan item
        AGR_NPMLinker.applyPlan plan
        check (a.material == fresh and b.material == fresh) "native assignment" report
        check (meditMaterials[1] == fresh) "same-name material editor replacement" report
        check (g.material != glass and g.material.opacity == 50 and g.material.diffuse == color 12 34 56 and g.material.twoSided) "glass copy retains other parameters" report
        check (g.material.name == "M_Glass_01" and g10.material.name == "M_Glass_02" and g.material != g10.material) "unique glass materials in natural mesh order" report
        local glassMaps = 0
        for i = 1 to getNumSubTexmaps g.material where getSubTexmap g.material i != undefined do glassMaps += 1
        check (glassMaps == 0) "all glass map links removed" report
        check (nestedGlass.material != glassMulti and (getSubMtl nestedGlass.material 1).name == "M_Glass_03") "nested glass gets separate numbered copy" report
        max undo
        check (a.material == old and b.material == old and meditMaterials[1] == unusedSameName and g.material == glass and nestedGlass.material == glassMulti and glass.opacity == 75 and glass.reflectionMap != undefined) "Undo restores assignments, editor and glass" report
        AGR_NPMLinker.applyPlan plan
        local repeatPlan = AGR_NPMLinker.makePlan #(a,b,g) index
        for item in (AGR_NPMLinker.makeGlassPlan #(g10,g,nestedGlass)) do append repeatPlan item
        AGR_NPMLinker.applyPlan repeatPlan
        check (a.material == b.material and a.material != fresh) "repeat rebuilds one shared material" report
        local emptyPlan = AGR_NPMLinker.makePlan #(noMaterial) #(#("empty_main", "d", index[1][3]))
        AGR_NPMLinker.applyPlan emptyPlan
        check (classOf noMaterial.material == Standardmaterial and noMaterial.material.diffuseMap != undefined and noMaterial.material.bumpMap == undefined) "unassigned object receives partial fresh material" report
        local changedPlan = AGR_NPMLinker.makePlan #(a) index
        local before = a.material
        a.material = Standardmaterial()
        local refused = false
        try (AGR_NPMLinker.applyPlan changedPlan) catch (refused = true)
        check refused "stale assignment rejected before mutation" report
        a.material = before
        local emptyGlass = box name:"SM_Test_3_MainGlass"
        local emptyGlassPlan = AGR_NPMLinker.makeGlassPlan #(emptyGlass)
        AGR_NPMLinker.applyPlan emptyGlassPlan
        check (classOf emptyGlass.material == Standardmaterial and emptyGlass.material.opacity == 50 and emptyGlass.material.name == "M_Glass_01") "unassigned MainGlass mesh gets glass material" report
        local sharedOpaque = Standardmaterial name:"NPM_SHARED_OPAQUE"
        local forcedGlass = box name:"SM_Forced_MainGlass" material:sharedOpaque
        local untouchedSolid = box name:"NPM_UnmatchedSolid" material:sharedOpaque
        AGR_NPMLinker.applyPlan (AGR_NPMLinker.makeGlassPlan #(forcedGlass))
        check (untouchedSolid.material == sharedOpaque and forcedGlass.material != sharedOpaque and forcedGlass.material.opacity == 50) "MainGlass copy does not replace shared opaque material" report
        pluginManager.loadClass FBXEXP
        local sourceFolder = root + "source_fbx/"
        makeDir sourceFolder all:true
        local sourceFbx = sourceFolder + "1111_TestAddress_01.fbx"
        a.name = "SM_TestAddress_001_Main"
        g.name = "SM_TestAddress_002_MainGlass"
        a.pos = [10,20,30]
        g.pos = [100,200,300]
        local ca = attributes NPM_TEST_CA (parameters main (probe type:#float default:1.0))
        custAttributes.add a ca
        custAttributes.add a.baseObject ca
        local probeModifier = Bend()
        addModifier a probeModifier
        custAttributes.add probeModifier ca
        custAttributes.add a.material ca
        custAttributes.add a.material.diffuseMap ca
        setUserProp a "NPM_TEST_USER_PROPERTY" "source-only"
        AGR_NPMFbx.setExportSettings()
        select #(a,g)
        exportFile sourceFbx #noPrompt selectedOnly:true using:FBXEXP
        local workspace = AGR_NPMFbx.newWorkspace (root + "output/")
        local jsonPath = AGR_NPMFbx.analyze sourceFolder workspace
        check (doesFileExist jsonPath) "FBX disk inventory written by embedded Python" report
        local beforeCount = objects.count
        local beforeAttrs = custAttributes.count a
        local anchorPos = a.pos
        undo "NPM_USER_UNDO_FIXTURE" on (a.pos = anchorPos + [3,0,0])
        local exportBoxes = #((nodeGetBoundingBox a (matrix3 1)),(nodeGetBoundingBox g (matrix3 1)))
        FBXExporterSetParam "Animation" true
        local exportedRoot = AGR_NPMFbx.exportInventory jsonPath
        check (objects.count == beforeCount and (custAttributes.count a) == beforeAttrs and (custAttributes.count a.baseObject) > 0 and (custAttributes.count probeModifier) > 0 and (custAttributes.count a.material) > 0 and (custAttributes.count a.material.diffuseMap) > 0 and (getUserProp a "NPM_TEST_USER_PROPERTY") == "source-only") "export copies cleaned; source scene unchanged" report
        check ((selection.count == 2) and (findItem (selection as array) a > 0) and (FBXExporterGetParam "Animation") == true) "selection and exporter settings restored" report
        check (doesFileExist (exportedRoot + "/export_report.json")) "exported FBX membership verified" report
        check (distance a.pos (anchorPos + [3,0,0]) < 0.0001) "export preserves source transform" report
        max undo
        check (distance a.pos anchorPos < 0.0001) "export preserves previous Undo action" report
        max redo
        local missingRejected = false
        try (AGR_NPMFbx.resolveJobs #(#("bad.fbx", #("MISSING_FIXTURE_NODE")))) catch (missingRejected = true)
        check missingRejected "missing FBX member rejected" report
        local expectedNames = #(a.name,g.name)
        resetMaxFile #noPrompt
        importFile (exportedRoot + "/1111_TestAddress_01.fbx") #noPrompt using:FBXIMP
        check (geometry.count == 2) "native FBX re-import contains two meshes" report
        for node in geometry do
        (
            check (findItem expectedNames node.name > 0) "native re-import preserves names" report
            local expectedBox = exportBoxes[findItem expectedNames node.name]
            local importedBox = nodeGetBoundingBox node (matrix3 1)
            check (distance expectedBox[1] importedBox[1] < 0.001 and distance expectedBox[2] importedBox[2] < 0.001) "native re-import preserves world bounds" report
            check ((custAttributes.count node) == 0 and (getUserProp node "NPM_TEST_USER_PROPERTY") == undefined) "native re-import has no source custom data" report
        )
        format "ALL CHECKS PASSED\n" to:report
    )
    catch (failure = getCurrentException(); format "ERROR: %\n" failure to:report)
    close report
    (dotNetClass "System.IO.File").Copy (root + "native-result.txt") (evidenceRoot + "native-result.txt") true
    (dotNetClass "System.IO.File").WriteAllText (evidenceRoot + "latest-run.txt") root
    if failure != undefined do throw failure
)
