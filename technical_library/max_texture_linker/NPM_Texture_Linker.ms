/* NPM Texture Linker 1.0. Single-file, no external dependencies.
   Matching: SM_<key> -> T_<key>_[drmon]_<version>.<image extension>.
   Set AGR_NPMLinker_NoUI=true before fileIn for off-scene core tests. */
global AGR_NPMLinker
global AGR_NPMLinker_NoUI
global AGR_NPMLinkerDialog

struct AGR_NPMLinkerCore
(
    extensions = #(".png", ".jpg", ".jpeg", ".tif", ".tiff", ".tga", ".bmp", ".exr", ".dds"),
    roles = #("d", "r", "m", "o", "n"),
    slots = #(#diffuseMap, #glossinessMap, #reflectionMap, #opacityMap, #bumpMap),
    enables = #(#diffuseMapEnable, #glossinessMapEnable, #reflectionMapEnable, #opacityMapEnable, #bumpMapEnable),
    messages = #(),
    glassCount = 0,

    fn isGlass m =
    (
        m != undefined and ((matchPattern m.name pattern:"M_Glass*" ignoreCase:true) or (matchPattern m.name pattern:"M Glass*" ignoreCase:true) or (matchPattern m.name pattern:"MGlass*" ignoreCase:true))
    ),

    fn containsGlass m =
    (
        local pending = #(m)
        local seen = #()
        while pending.count > 0 do
        (
            local current = pending[pending.count]
            deleteItem pending pending.count
            if current != undefined and findItem seen current == 0 do
            (
                if isGlass current do return true
                append seen current
                for i = 1 to getNumSubMtls current do append pending (getSubMtl current i)
            )
        )
        false
    ),

    fn rawKey nodeName =
    (
        local key = nodeName as string
        if key.count > 3 and (toLower (substring key 1 3)) == "sm_" do key = substring key 4 -1
        key
    ),

    fn objectKey nodeName = (toLower (rawKey nodeName)),

    fn isGlassNode node =
    (
        (matchPattern node.name pattern:"*_MainGlass" ignoreCase:true) or containsGlass node.material
    ),

    fn compareNodes a b =
    (
        local rx = dotNetObject "System.Text.RegularExpressions.Regex" "[0-9]+|[^0-9]+"
        local aa = rx.Matches (toLower a.name)
        local bb = rx.Matches (toLower b.name)
        local count = amin aa.Count bb.Count
        for i = 0 to count - 1 do
        (
            local x = aa.Item[i].Value as string
            local y = bb.Item[i].Value as string
            if (findString "0123456789" x[1]) != undefined and (findString "0123456789" y[1]) != undefined then
            (
                x = trimLeft x "0"
                y = trimLeft y "0"
                if x.count != y.count do return (if x.count < y.count then -1 else 1)
            )
            local comparison = stricmp x y
            if comparison != 0 do return comparison
        )
        if aa.Count == bb.Count then (stricmp a.name b.name) else (if aa.Count < bb.Count then -1 else 1)
    ),

    fn copyGlassBranch source serial depth:0 forceGlass:false =
    (
        if depth > 64 do throw "Glass material hierarchy is too deep."
        local result = copy source
        local pairs = #()
        if isGlass source or forceGlass then
        (
            if not isProperty result #opacity do throw ("Glass material has no opacity property: " + source.name)
            result.name = "M_Glass_" + (formattedPrint serial format:"02d")
            for i = 1 to getNumSubTexmaps result do setSubTexmap result i undefined
            result.opacity = 50
            append pairs #(source, result)
            serial += 1
        )
        else
        (
            for i = 1 to getNumSubMtls source do
            (
                local child = getSubMtl source i
                if containsGlass child then
                (
                    local branch = copyGlassBranch child serial depth:(depth+1)
                    setSubMtl result i branch[1]
                    serial = branch[2]
                    for pair in branch[3] do append pairs pair
                )
                else setSubMtl result i child
            )
        )
        #(result, serial, pairs)
    ),

    fn makeGlassPlan nodes =
    (
        local sorted = for node in nodes where isGlassNode node collect node
        qsort sorted compareNodes
        for i = 2 to sorted.count where (stricmp sorted[i-1].name sorted[i].name) == 0 do
            throw ("Duplicate glass object name: " + sorted[i].name)
        local plan = #()
        local serial = 1
        for node in sorted do
        (
            local source = if node.material == undefined then Standardmaterial name:"M_Glass" else node.material
            local branch = copyGlassBranch source serial forceGlass:(not containsGlass source)
            serial = branch[2]
            append plan #(node, node.material, branch[1], branch[3])
        )
        plan
    ),

    -- A record is #(full object key, role, absolute path).
    fn parseTexture path =
    (
        if findItem extensions (toLower (getFilenameType path)) == 0 then return undefined
        local rx = dotNetObject "System.Text.RegularExpressions.Regex" "(?i)^T_(.+)_([drmon])_([0-9]+)$"
        local hit = rx.Match (getFilenameFile path)
        if not hit.Success then return undefined
        #((toLower (hit.Groups.Item[1].Value as string)), (toLower (hit.Groups.Item[2].Value as string)), path)
    ),

    fn scanFolder root =
    (
        local index = #()
        local pending = #(root)
        local seen = #()
        local directoryClass = dotNetClass "System.IO.Directory"
        while pending.count > 0 do
        (
            local folder = pending[pending.count]
            deleteItem pending pending.count
            local canonical = toLower ((dotNetClass "System.IO.Path").GetFullPath folder)
            if findItem seen canonical == 0 do
            (
                append seen canonical
                -- Exceptions intentionally propagate: incomplete scans must not assign.
                for path in (directoryClass.GetFiles folder "*") do
                (
                    local record = parseTexture (path as string)
                    if record != undefined do append index record
                )
                for child in (directoryClass.GetDirectories folder) do
                (
                    local info = dotNetObject "System.IO.DirectoryInfo" child
                    if (bit.and (info.Attributes.value__ as integer) 1024) == 0 then
                        append pending (child as string)
                    else append messages ("Skipped linked folder: " + (child as string))
                )
            )
        )
        index
    ),

    -- Return one path per role. A duplicate invalidates the whole object.
    fn matchFiles key index =
    (
        local paths = #(undefined, undefined, undefined, undefined, undefined)
        local conflict = false
        for record in index where record[1] == key do
        (
            local i = findItem roles record[2]
            if paths[i] != undefined then
            (
                conflict = true
                append messages ("Ambiguous " + key + " [" + roles[i] + "]: " + paths[i] + " | " + record[3])
            )
            else paths[i] = record[3]
        )
        if conflict then undefined else paths
    ),

    -- Prepare disconnected materials only. Assignments happen after all preparation.
    fn prepareMaterial key paths =
    (
        local material = Standardmaterial name:("M_" + key + "_1")
        for i = 1 to roles.count where paths[i] != undefined do
        (
            if not doesFileExist paths[i] do throw ("Texture disappeared: " + paths[i])
            local tex = Bitmaptexture filename:paths[i] name:(getFilenameFile paths[i])
            setProperty material slots[i] tex
            setProperty material enables[i] true
            -- Max changes a map to Environment when connected to Reflection.
            -- Set coordinates AFTER connection, not before.
            tex.coords.mappingType = 0 -- Texture, including Reflection maps
            tex.coords.mapping = 0 -- Explicit Map Channel
            tex.coords.mapChannel = 1
        )
        material
    ),

    fn makePlan nodes index =
    (
        local plan = #()
        local keys = #()
        local materials = #()
        for node in nodes do
        (
            if isGlassNode node then append messages ("GLASS mesh: " + node.name)
            else
            (
            local key = objectKey node.name
            local paths = matchFiles key index
            if paths == undefined then append messages ("SKIP conflict: " + node.name)
            else
            (
                local count = 0
                for path in paths where path != undefined do count += 1
                if count == 0 then append messages ("SKIP no textures: " + node.name)
                else
                (
                    for i = 1 to roles.count where paths[i] == undefined do
                        append messages ("No " + roles[i] + ": " + node.name + " (new slot left empty)")
                    local materialIndex = findItem keys key
                    local material = if materialIndex > 0 then materials[materialIndex] else prepareMaterial (rawKey node.name) paths
                    if materialIndex == 0 do (append keys key; append materials material)
                    append plan #(node, node.material, material)
                )
            )
            )
        )
        plan
    ),

    fn collectMaterials =
    (
        local result = #()
        local pending = for m in sceneMaterials collect m
        for m in meditMaterials do append pending m
        for v = 1 to sme.GetNumViews() do
        (
            local view = sme.GetView v
            for i = 1 to view.GetNumNodes() do
            (
                local ref = (view.GetNode i).reference
                if ref != undefined and superClassOf ref == material do append pending ref
            )
        )
        while pending.count > 0 do
        (
            local m = pending[pending.count]
            deleteItem pending pending.count
            if m != undefined and findItem result m == 0 do
            (
                append result m
                for i = 1 to getNumSubMtls m do append pending (getSubMtl m i)
            )
        )
        result
    ),

    fn applyPlan plan =
    (
        -- Verify all targets before the first assignment.
        for item in plan do
            if not isValidNode item[1] or item[1].material != item[2] do throw "Scene changed; analyze again."
        local oldMaterials = collectMaterials()
        local replacements = #()
        local seen = #()
        local glasses = for m in oldMaterials where isGlass m collect m
        for m in glasses where not isProperty m #opacity do throw ("Glass material has no opacity property: " + m.name)
        local createdGlass = 0
        for item in plan where item.count > 3 do
        (
            for pair in item[4] do
            (
                createdGlass += 1
                -- A MainGlass mesh may share an ordinary material with opaque nodes.
                -- Only actual M_Glass sources may be replaced globally.
                if isGlass pair[1] and findItem seen pair[1] == 0 do (append replacements pair; append seen pair[1])
            )
        )
        for old in oldMaterials where not containsGlass old do
        (
            for item in plan where old != item[3] and (toLower old.name) == (toLower item[3].name) and findItem seen old == 0 do
            (
                append replacements #(old, item[3])
                append seen old
            )
        )
        if theHold.Holding() do throw "3ds Max is busy with another operation. Try again when it finishes."
        theHold.Begin()
        try
        (
            for item in plan do item[1].material = item[3]
            -- Replace same-name references in scene, sub-materials and both editors.
            for pair in replacements do replaceInstances pair[1] pair[2]
            for m in glasses where findItem seen m == 0 do
            (
                for i = 1 to getNumSubTexmaps m do setSubTexmap m i undefined
                m.opacity = 50
            )
            theHold.Accept "NPM Texture Linker"
        )
        catch (theHold.Cancel(); throw)
        glassCount = createdGlass
        redrawViews()
        plan.count
    ),

    fn run root =
    (
        messages = #()
        local index = scanFolder root
        local nodes = for node in geometry collect node
        local plan = makePlan nodes index
        local count = plan.count
        local glassPlan = makeGlassPlan nodes
        for item in glassPlan do append plan item
        applyPlan plan
        format "NPM Texture Linker: % objects updated; % glass materials cleaned; % recognized texture files.\n" count glassCount index.count
        for message in messages do format "%\n" message
        #(count, nodes.count - plan.count, index.count, messages.count, glassCount)
    )
)

AGR_NPMLinker = AGR_NPMLinkerCore()

global AGR_NPMFbx
global AGR_NPMFbx_SourceRoot
global AGR_NPMFbx_JsonPath
global AGR_NPMFbx_Jobs
global AGR_NPMFbx_Error
global AGR_NPMFbx_OutputRoot
global AGR_NPMFbx_Workspace
global AGR_NPMFbx_Payload
-- BEGIN EMBEDDED FBX PYTHON (generated from fbx_inventory.py; standalone runtime)
AGR_NPMFbx_Payload = "IiIiUmVhZC1vbmx5IEZCWCBtZXNoIGludmVudG9yeSwgYWxzbyBlbWJlZGRlZCBpbiB0aGUgc3RhbmRhbG9uZSBNQVhTY3JpcHQuCgpObyBTREsgb3IgdGhpcmQtcGFydHkgbW9kdWxlcy4gVGhpcyByZWFkcyB0aGUgRkJYIGNvbnRhaW5lciwgbmV2ZXIgZ2VvbWV0cnkuCiIiIgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgppbXBvcnQgZGF0ZXRpbWUgYXMgX2R0CmltcG9ydCBoYXNobGliCmltcG9ydCBqc29uCmltcG9ydCBvcwpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgsIFB1cmVQb3NpeFBhdGgsIFB1cmVXaW5kb3dzUGF0aAppbXBvcnQgcmUKaW1wb3J0IHN0YXQKaW1wb3J0IHN0cnVjdAoKX01BR0lDID0gYiJLYXlkYXJhIEZCWCBCaW5hcnkgIFx4MDBceDFhXHgwMCIKX01BWF9ERVBUSCA9IDEyOApfTUFYX05PREVTID0gMV8wMDBfMDAwCl9NQVhfU0laRSA9IDJfMTQ3XzQ4M182NDgKCgpkZWYgX2NsZWFuX25hbWUodmFsdWUpOgogICAgcmV0dXJuIHZhbHVlLnNwbGl0KCJceDAwXHgwMSIsIDEpWzBdLnNwbGl0KCI6OiIsIDEpWy0xXS5zdHJpcCgpCgoKZGVmIF9tZXNoX25hbWVzKGRhdGEpOgogICAgIiIiUmV0dXJuICh2ZXJzaW9uLCBuYW1lcyksIHJlamVjdGluZyBtYWxmb3JtZWQvYW1iaWd1b3VzIG1lc2ggaW52ZW50b3JpZXMuIiIiCiAgICBuYW1lcyA9IFtdCiAgICBpZiBkYXRhLnN0YXJ0c3dpdGgoX01BR0lDKToKICAgICAgICBpZiBsZW4oZGF0YSkgPCAyNzoKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiVHJ1bmNhdGVkIGJpbmFyeSBGQlggaGVhZGVyIikKICAgICAgICB2ZXJzaW9uID0gc3RydWN0LnVucGFja19mcm9tKCI8SSIsIGRhdGEsIDIzKVswXQogICAgICAgIGlmIG5vdCA2MDAwIDw9IHZlcnNpb24gPD0gMTAwMDA6CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIlVuc3VwcG9ydGVkIEZCWCB2ZXJzaW9uIikKICAgICAgICB3aWRlID0gdmVyc2lvbiA+PSA3NTAwCiAgICAgICAgaGVhZGVyX3NpemUgPSAyNSBpZiB3aWRlIGVsc2UgMTMKICAgICAgICBoZWFkZXJfZm10ID0gIjxRUVFCIiBpZiB3aWRlIGVsc2UgIjxJSUlCIgogICAgICAgIHBvcyA9IDI3CiAgICAgICAgbm9kZXMgPSAwCgogICAgICAgIGRlZiB0YWtlKHNpemUsIGxpbWl0KToKICAgICAgICAgICAgbm9ubG9jYWwgcG9zCiAgICAgICAgICAgIGlmIHNpemUgPCAwIG9yIHBvcyArIHNpemUgPiBsaW1pdDoKICAgICAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIlRydW5jYXRlZCBGQlggcHJvcGVydHkiKQogICAgICAgICAgICByZXN1bHQgPSBkYXRhW3Bvczpwb3MgKyBzaXplXQogICAgICAgICAgICBwb3MgKz0gc2l6ZQogICAgICAgICAgICByZXR1cm4gcmVzdWx0CgogICAgICAgIGRlZiBwcm9wKGxpbWl0KToKICAgICAgICAgICAgbm9ubG9jYWwgcG9zCiAgICAgICAgICAgIGNvZGUgPSB0YWtlKDEsIGxpbWl0KQogICAgICAgICAgICBmb3JtYXRzID0ge2IiWSI6ICI8aCIsIGIiQyI6ICI8PyIsIGIiSSI6ICI8aSIsIGIiRiI6ICI8ZiIsIGIiRCI6ICI8ZCIsIGIiTCI6ICI8cSJ9CiAgICAgICAgICAgIGlmIGNvZGUgaW4gZm9ybWF0czoKICAgICAgICAgICAgICAgIGZtdCA9IGZvcm1hdHNbY29kZV0KICAgICAgICAgICAgICAgIHJldHVybiBzdHJ1Y3QudW5wYWNrKGZtdCwgdGFrZShzdHJ1Y3QuY2FsY3NpemUoZm10KSwgbGltaXQpKVswXQogICAgICAgICAgICBpZiBjb2RlIGluIChiIlMiLCBiIlIiKToKICAgICAgICAgICAgICAgIHNpemUgPSBzdHJ1Y3QudW5wYWNrKCI8SSIsIHRha2UoNCwgbGltaXQpKVswXQogICAgICAgICAgICAgICAgdmFsdWUgPSB0YWtlKHNpemUsIGxpbWl0KQogICAgICAgICAgICAgICAgcmV0dXJuIHZhbHVlLmRlY29kZSgidXRmLTgiLCAic3RyaWN0IikgaWYgY29kZSA9PSBiIlMiIGVsc2UgTm9uZQogICAgICAgICAgICBzaXplcyA9IHtiImYiOiA0LCBiImQiOiA4LCBiImwiOiA4LCBiImkiOiA0LCBiImIiOiAxLCBiImMiOiAxfQogICAgICAgICAgICBpZiBjb2RlIGluIHNpemVzOgogICAgICAgICAgICAgICAgY291bnQsIGVuY29kaW5nLCBwYWNrZWQgPSBzdHJ1Y3QudW5wYWNrKCI8SUlJIiwgdGFrZSgxMiwgbGltaXQpKQogICAgICAgICAgICAgICAgaWYgZW5jb2Rpbmcgbm90IGluICgwLCAxKToKICAgICAgICAgICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJJbnZhbGlkIEZCWCBhcnJheSBlbmNvZGluZyIpCiAgICAgICAgICAgICAgICBzaXplID0gY291bnQgKiBzaXplc1tjb2RlXSBpZiBlbmNvZGluZyA9PSAwIGVsc2UgcGFja2VkCiAgICAgICAgICAgICAgICBpZiBlbmNvZGluZyA9PSAwIGFuZCBwYWNrZWQgIT0gc2l6ZToKICAgICAgICAgICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJJbnZhbGlkIHVuY29tcHJlc3NlZCBGQlggYXJyYXkgbGVuZ3RoIikKICAgICAgICAgICAgICAgIHRha2Uoc2l6ZSwgbGltaXQpCiAgICAgICAgICAgICAgICByZXR1cm4gTm9uZQogICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJVbmtub3duIEZCWCBwcm9wZXJ0eSB0eXBlIikKCiAgICAgICAgZGVmIG5vZGUobGltaXQsIGRlcHRoKToKICAgICAgICAgICAgbm9ubG9jYWwgcG9zLCBub2RlcwogICAgICAgICAgICBpZiBkZXB0aCA+IF9NQVhfREVQVEg6CiAgICAgICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJGQlggbmVzdGluZyBsaW1pdCBleGNlZWRlZCIpCiAgICAgICAgICAgIHN0YXJ0ID0gcG9zCiAgICAgICAgICAgIGhlYWRlciA9IHRha2UoaGVhZGVyX3NpemUsIGxpbWl0KQogICAgICAgICAgICBlbmQsIGNvdW50LCBwbGVuLCBuYW1lX2xlbiA9IHN0cnVjdC51bnBhY2soaGVhZGVyX2ZtdCwgaGVhZGVyKQogICAgICAgICAgICBpZiBlbmQgPT0gMDoKICAgICAgICAgICAgICAgIGlmIGFueShoZWFkZXIpOgogICAgICAgICAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkludmFsaWQgRkJYIHRlcm1pbmF0b3IiKQogICAgICAgICAgICAgICAgcmV0dXJuIEZhbHNlCiAgICAgICAgICAgIG5vZGVzICs9IDEKICAgICAgICAgICAgaWYgbm9kZXMgPiBfTUFYX05PREVTIG9yIGNvdW50ID4gX01BWF9OT0RFUzoKICAgICAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkZCWCBub2RlL3Byb3BlcnR5IGxpbWl0IGV4Y2VlZGVkIikKICAgICAgICAgICAgaWYgZW5kIDw9IHN0YXJ0IG9yIGVuZCA+IGxpbWl0OgogICAgICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiSW52YWxpZCBGQlggbm9kZSBvZmZzZXQiKQogICAgICAgICAgICBuYW1lID0gdGFrZShuYW1lX2xlbiwgZW5kKS5kZWNvZGUoImFzY2lpIiwgInN0cmljdCIpCiAgICAgICAgICAgIHByb3BzX2VuZCA9IHBvcyArIHBsZW4KICAgICAgICAgICAgaWYgcHJvcHNfZW5kID4gZW5kOgogICAgICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiSW52YWxpZCBGQlggcHJvcGVydHkgbGlzdCBsZW5ndGgiKQogICAgICAgICAgICB2YWx1ZXMgPSBbXQogICAgICAgICAgICBmb3IgXyBpbiByYW5nZShjb3VudCk6CiAgICAgICAgICAgICAgICB2YWx1ZSA9IHByb3AocHJvcHNfZW5kKQogICAgICAgICAgICAgICAgaWYgbmFtZSA9PSAiTW9kZWwiOgogICAgICAgICAgICAgICAgICAgIHZhbHVlcy5hcHBlbmQodmFsdWUpCiAgICAgICAgICAgIGlmIHBvcyAhPSBwcm9wc19lbmQ6CiAgICAgICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJGQlggcHJvcGVydHkgY291bnQvbGVuZ3RoIG1pc21hdGNoIikKICAgICAgICAgICAgaWYgbmFtZSA9PSAiTW9kZWwiOgogICAgICAgICAgICAgICAgaWYgbGVuKHZhbHVlcykgPj0gMyBhbmQgaXNpbnN0YW5jZSh2YWx1ZXNbMF0sIGludCkgYW5kIGlzaW5zdGFuY2UodmFsdWVzWzFdLCBzdHIpOgogICAgICAgICAgICAgICAgICAgIHJhdywga2luZCA9IHZhbHVlc1sxOjNdCiAgICAgICAgICAgICAgICBlbGlmIGxlbih2YWx1ZXMpID09IDIgYW5kIGFsbChpc2luc3RhbmNlKHYsIHN0cikgZm9yIHYgaW4gdmFsdWVzKToKICAgICAgICAgICAgICAgICAgICByYXcsIGtpbmQgPSB2YWx1ZXMKICAgICAgICAgICAgICAgIGVsc2U6CiAgICAgICAgICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiSW52YWxpZCBGQlggTW9kZWwgcHJvcGVydGllcyIpCiAgICAgICAgICAgICAgICBpZiBraW5kID09ICJNZXNoIjoKICAgICAgICAgICAgICAgICAgICBuYW1lcy5hcHBlbmQoX2NsZWFuX25hbWUocmF3KSkKICAgICAgICAgICAgaWYgcG9zIDwgZW5kOgogICAgICAgICAgICAgICAgdGVybWluYXRlZCA9IEZhbHNlCiAgICAgICAgICAgICAgICB3aGlsZSBwb3MgPCBlbmQ6CiAgICAgICAgICAgICAgICAgICAgaWYgbm90IG5vZGUoZW5kLCBkZXB0aCArIDEpOgogICAgICAgICAgICAgICAgICAgICAgICB0ZXJtaW5hdGVkID0gVHJ1ZQogICAgICAgICAgICAgICAgICAgICAgICBicmVhawogICAgICAgICAgICAgICAgaWYgbm90IHRlcm1pbmF0ZWQgb3IgcG9zICE9IGVuZDoKICAgICAgICAgICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJJbnZhbGlkIEZCWCBjaGlsZHJlbiB0ZXJtaW5hdG9yIikKICAgICAgICAgICAgcmV0dXJuIFRydWUKCiAgICAgICAgd2hpbGUgbm9kZShsZW4oZGF0YSksIDApOgogICAgICAgICAgICBwYXNzCiAgICBlbHNlOgogICAgICAgIHRleHQgPSBkYXRhLmRlY29kZSgidXRmLTgtc2lnIiwgInN0cmljdCIpCiAgICAgICAgdmVyID0gcmUuc2VhcmNoKHIiXGJGQlhWZXJzaW9uXHMqOlxzKihcZCspIiwgdGV4dCkKICAgICAgICBpZiBub3QgdmVyOgogICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJNaXNzaW5nIEFTQ0lJIEZCWCB2ZXJzaW9uIikKICAgICAgICB2ZXJzaW9uID0gaW50KHZlci5ncm91cCgxKSkKICAgICAgICBpZiBub3QgNjAwMCA8PSB2ZXJzaW9uIDw9IDEwMDAwOgogICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJVbnN1cHBvcnRlZCBGQlggdmVyc2lvbiIpCiAgICAgICAgIyBMZXggcXVvdGVkIHN0cmluZ3MvY29tbWVudHMgZmlyc3QsIHNvIGVtYmVkZGVkIGJyYWNlcyBjYW5ub3QgaGlkZSB0cnVuY2F0aW9uLgogICAgICAgIGRlcHRoID0gMAogICAgICAgIHF1b3RlZCA9IEZhbHNlCiAgICAgICAgZXNjYXBlZCA9IEZhbHNlCiAgICAgICAgY29tbWVudCA9IEZhbHNlCiAgICAgICAgZGVjbGFyYXRpb25zID0gbGlzdChyZS5maW5kaXRlcihyIl5bIFx0XSpNb2RlbFxzKjoiLCB0ZXh0LCByZS5NKSkKICAgICAgICBkZWNsYXJhdGlvbl9wb3NpdGlvbnMgPSB7dGV4dC5pbmRleCgiTW9kZWwiLCBoaXQuc3RhcnQoKSwgaGl0LmVuZCgpKSBmb3IgaGl0IGluIGRlY2xhcmF0aW9uc30KICAgICAgICBhY3RpdmVfZGVjbGFyYXRpb25zID0gc2V0KCkKICAgICAgICBmb3Igb2Zmc2V0LCBjaGFyIGluIGVudW1lcmF0ZSh0ZXh0KToKICAgICAgICAgICAgaWYgbm90IHF1b3RlZCBhbmQgbm90IGNvbW1lbnQgYW5kIG9mZnNldCBpbiBkZWNsYXJhdGlvbl9wb3NpdGlvbnM6CiAgICAgICAgICAgICAgICBhY3RpdmVfZGVjbGFyYXRpb25zLmFkZChvZmZzZXQpCiAgICAgICAgICAgIGlmIGNvbW1lbnQ6CiAgICAgICAgICAgICAgICBpZiBjaGFyIGluICJcclxuIjoKICAgICAgICAgICAgICAgICAgICBjb21tZW50ID0gRmFsc2UKICAgICAgICAgICAgZWxpZiBxdW90ZWQ6CiAgICAgICAgICAgICAgICBpZiBlc2NhcGVkOgogICAgICAgICAgICAgICAgICAgIGVzY2FwZWQgPSBGYWxzZQogICAgICAgICAgICAgICAgZWxpZiBjaGFyID09ICJcXCI6CiAgICAgICAgICAgICAgICAgICAgZXNjYXBlZCA9IFRydWUKICAgICAgICAgICAgICAgIGVsaWYgY2hhciA9PSAnIic6CiAgICAgICAgICAgICAgICAgICAgcXVvdGVkID0gRmFsc2UKICAgICAgICAgICAgZWxpZiBjaGFyID09ICI7IjoKICAgICAgICAgICAgICAgIGNvbW1lbnQgPSBUcnVlCiAgICAgICAgICAgIGVsaWYgY2hhciA9PSAnIic6CiAgICAgICAgICAgICAgICBxdW90ZWQgPSBUcnVlCiAgICAgICAgICAgIGVsaWYgY2hhciA9PSAieyI6CiAgICAgICAgICAgICAgICBkZXB0aCArPSAxCiAgICAgICAgICAgICAgICBpZiBkZXB0aCA+IF9NQVhfREVQVEg6CiAgICAgICAgICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiRkJYIG5lc3RpbmcgbGltaXQgZXhjZWVkZWQiKQogICAgICAgICAgICBlbGlmIGNoYXIgPT0gIn0iOgogICAgICAgICAgICAgICAgZGVwdGggLT0gMQogICAgICAgICAgICAgICAgaWYgZGVwdGggPCAwOgogICAgICAgICAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIlVuYmFsYW5jZWQgQVNDSUkgRkJYIGJyYWNlcyIpCiAgICAgICAgaWYgcXVvdGVkIG9yIGRlcHRoOgogICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJUcnVuY2F0ZWQgQVNDSUkgRkJYIikKICAgICAgICAjIE9ubHkgbWF0Y2ggYWN0dWFsIG5vZGUgbGluZXMsIG5vdCBzdHJpbmdzIG9yIHNlbWljb2xvbiBjb21tZW50cy4KICAgICAgICBtb2RlbCA9IHJlLmNvbXBpbGUocideWyBcdF0qTW9kZWxccyo6XHMqKD86LT9cZCtccyosXHMqKT8iKCg/OlxcLnxbXiJcXF0pKikiXHMqLFxzKiIoW14iXHJcbl0rKSJccypceycsIHJlLk0pCiAgICAgICAgbWF0Y2hlcyA9IFtoaXQgZm9yIGhpdCBpbiBtb2RlbC5maW5kaXRlcih0ZXh0KSBpZiB0ZXh0LmluZGV4KCJNb2RlbCIsIGhpdC5zdGFydCgpLCBoaXQuZW5kKCkpIGluIGFjdGl2ZV9kZWNsYXJhdGlvbnNdCiAgICAgICAgaWYgbGVuKG1hdGNoZXMpICE9IGxlbihhY3RpdmVfZGVjbGFyYXRpb25zKToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiSW52YWxpZCBBU0NJSSBGQlggTW9kZWwgZGVjbGFyYXRpb24iKQogICAgICAgIGZvciBoaXQgaW4gbWF0Y2hlczoKICAgICAgICAgICAgaWYgaGl0WzJdID09ICJNZXNoIjoKICAgICAgICAgICAgICAgIHJhdyA9IGhpdFsxXS5yZXBsYWNlKCdcXCInLCAnIicpLnJlcGxhY2UoIlxcXFwiLCAiXFwiKQogICAgICAgICAgICAgICAgbmFtZXMuYXBwZW5kKF9jbGVhbl9uYW1lKHJhdykpCiAgICBzZWVuID0gc2V0KCkKICAgIGZvciBuYW1lIGluIG5hbWVzOgogICAgICAgIGlmIG5vdCBuYW1lIG9yICJceDAwIiBpbiBuYW1lIG9yIGFueShvcmQoYykgPCAzMiBmb3IgYyBpbiBuYW1lKToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiRW1wdHkgb3IgaW52YWxpZCBGQlggbWVzaCBuYW1lIikKICAgICAgICBpZiBuYW1lLmNhc2Vmb2xkKCkgaW4gc2VlbjoKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiRHVwbGljYXRlIEZCWCBtZXNoIG5hbWU6ICIgKyBuYW1lKQogICAgICAgIHNlZW4uYWRkKG5hbWUuY2FzZWZvbGQoKSkKICAgIGlmIG5vdCBuYW1lczoKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJObyBNZXNoIG1vZGVscyBpbiBGQlgiKQogICAgcmV0dXJuIHZlcnNpb24sIG5hbWVzCgoKZGVmIF9saW5rZWQocGF0aCk6CiAgICBpbmZvID0gcGF0aC5sc3RhdCgpCiAgICByZXR1cm4gcGF0aC5pc19zeW1saW5rKCkgb3IgYm9vbChnZXRhdHRyKGluZm8sICJzdF9maWxlX2F0dHJpYnV0ZXMiLCAwKSAmIHN0YXQuRklMRV9BVFRSSUJVVEVfUkVQQVJTRV9QT0lOVCkKCgpkZWYgX3JlYWRfc291cmNlKHBhdGgpOgogICAgaWYgcGF0aC5zdGF0KCkuc3Rfc2l6ZSA+IF9NQVhfU0laRToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJGQlggZXhjZWVkcyBzaXplIGxpbWl0OiAiICsgc3RyKHBhdGgpKQogICAgZGF0YSA9IHBhdGgucmVhZF9ieXRlcygpCiAgICByZXR1cm4gZGF0YSwgaGFzaGxpYi5zaGEyNTYoZGF0YSkuaGV4ZGlnZXN0KCkKCgpkZWYgX25wbV9jYW5kaWRhdGUocGF0aCwgZGF0YSwgdmVyc2lvbiwgbmFtZXMpOgogICAgIiIiTlBNX1NUQU5EQVJELnlhbWwgcHAuMTAtMTMgbmFtaW5nICsgYmluYXJ5NzQwMCBnYXRlLCBub3QgZnVsbCBRQS4iIiIKICAgIGlmIG5vdCBkYXRhLnN0YXJ0c3dpdGgoX01BR0lDKSBvciB2ZXJzaW9uICE9IDc0MDA6CiAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiTlBNIGNhbmRpZGF0ZSByZXF1aXJlcyBiaW5hcnkgRkJYIDc0MDAvMjAxNCIpCiAgICBtYXRjaCA9IHJlLmZ1bGxtYXRjaChyIlswLTldezR9XyhbQS1aYS16MC05X10rKV8oMFsxLTldfDFbMC05XXwyMHxHcm91bmQpIiwgcGF0aC5zdGVtKQogICAgaWYgbGVuKHBhdGguc3RlbSkgPiAyNTQgb3Igbm90IG1hdGNoOgogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIk5QTSBmaWxlbmFtZSBtdXN0IGJlIHRlcnJpdG9yeTRfQWRkcmVzc18wMS4uMjAgb3IgX0dyb3VuZCAobWF4IHN0ZW0gMjU0KSIpCiAgICBhZGRyZXNzLCBwYXJ0ID0gbWF0Y2guZ3JvdXBzKCkKICAgIGlmIHBhcnQgPT0gIkdyb3VuZCI6CiAgICAgICAgdmFsaWQgPSBsYW1iZGEgbmFtZTogbmFtZSA9PSAiU01fIiArIGFkZHJlc3MgKyAiX0dyb3VuZCIKICAgIGVsc2U6CiAgICAgICAgcGF0dGVybiA9IHJlLmNvbXBpbGUociJTTV8iICsgcmUuZXNjYXBlKGFkZHJlc3MpICsgciJfKDAwWzEtOV18MDFbMC05XXwwMjApX01haW4oPzpHbGFzcyk/IikKICAgICAgICB2YWxpZCA9IGxhbWJkYSBuYW1lOiBwYXR0ZXJuLmZ1bGxtYXRjaChuYW1lKSBpcyBub3QgTm9uZQogICAgZm9yIG5hbWUgaW4gbmFtZXM6CiAgICAgICAgaWYgbGVuKG5hbWUpID4gMjU0IG9yIG5vdCB2YWxpZChuYW1lKToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiTlBNIG1lc2ggbmFtaW5nL2FkZHJlc3MgbWlzbWF0Y2g6ICIgKyBuYW1lKQoKCmRlZiBhbmFseXplX2ZvbGRlcihyb290LCBucG1fb25seT1GYWxzZSk6CiAgICByb290ID0gUGF0aChyb290KS5hYnNvbHV0ZSgpCiAgICBpZiBub3Qgcm9vdC5pc19kaXIoKSBvciBfbGlua2VkKHJvb3QpOgogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIlNvdXJjZSByb290IG11c3QgYmUgYSByZWFsIGRpcmVjdG9yeSIpCiAgICByb290ID0gcm9vdC5yZXNvbHZlKCkKICAgIGZpbGVzID0gW10KICAgIHNraXBwZWQgPSBbXQogICAga2V5cyA9IHNldCgpCiAgICBmb3IgZm9sZGVyLCBkaXJzLCBmaWxlbmFtZXMgaW4gb3Mud2Fsayhyb290LCBmb2xsb3dsaW5rcz1GYWxzZSwgb25lcnJvcj1sYW1iZGEgZTogKF8gZm9yIF8gaW4gKCkpLnRocm93KGUpKToKICAgICAgICBkaXJzWzpdID0gc29ydGVkKGQgZm9yIGQgaW4gZGlycyBpZiBub3QgZC51cHBlcigpLnN0YXJ0c3dpdGgoIk5QTV9GQlhfIikgYW5kIG5vdCBfbGlua2VkKFBhdGgoZm9sZGVyKSAvIGQpKQogICAgICAgIGZvciBmaWxlbmFtZSBpbiBzb3J0ZWQoZmlsZW5hbWVzKToKICAgICAgICAgICAgcGF0aCA9IFBhdGgoZm9sZGVyKSAvIGZpbGVuYW1lCiAgICAgICAgICAgIGlmIHBhdGguc3VmZml4Lmxvd2VyKCkgIT0gIi5mYngiOgogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgcmVsYXRpdmUgPSBwYXRoLnJlbGF0aXZlX3RvKHJvb3QpLmFzX3Bvc2l4KCkKICAgICAgICAgICAgaWYgX2xpbmtlZChwYXRoKToKICAgICAgICAgICAgICAgIHNraXBwZWQuYXBwZW5kKGRpY3QocmVsYXRpdmVfcGF0aD1yZWxhdGl2ZSwgcmVhc29uPSJMaW5rZWQvcmVwYXJzZSBGQlggc291cmNlIHNraXBwZWQiKSkKICAgICAgICAgICAgICAgIGNvbnRpbnVlCiAgICAgICAgICAgIGlmIHJlbGF0aXZlLmNhc2Vmb2xkKCkgaW4ga2V5czoKICAgICAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkR1cGxpY2F0ZSBGQlggcmVsYXRpdmUgcGF0aDogIiArIHJlbGF0aXZlKQogICAgICAgICAgICBrZXlzLmFkZChyZWxhdGl2ZS5jYXNlZm9sZCgpKQogICAgICAgICAgICB0cnk6CiAgICAgICAgICAgICAgICBkYXRhLCBkaWdlc3QgPSBfcmVhZF9zb3VyY2UocGF0aCkKICAgICAgICAgICAgICAgIHZlcnNpb24sIG5hbWVzID0gX21lc2hfbmFtZXMoZGF0YSkKICAgICAgICAgICAgICAgIGlmIG5wbV9vbmx5OgogICAgICAgICAgICAgICAgICAgIF9ucG1fY2FuZGlkYXRlKHBhdGgsIGRhdGEsIHZlcnNpb24sIG5hbWVzKQogICAgICAgICAgICBleGNlcHQgKFZhbHVlRXJyb3IsIFVuaWNvZGVFcnJvciwgc3RydWN0LmVycm9yLCBSZWN1cnNpb25FcnJvcikgYXMgZXJyb3I6CiAgICAgICAgICAgICAgICBpZiBub3QgbnBtX29ubHk6CiAgICAgICAgICAgICAgICAgICAgcmFpc2UKICAgICAgICAgICAgICAgIHNraXBwZWQuYXBwZW5kKGRpY3QocmVsYXRpdmVfcGF0aD1yZWxhdGl2ZSwgcmVhc29uPXN0cihlcnJvcikpKQogICAgICAgICAgICAgICAgY29udGludWUKICAgICAgICAgICAgZmlsZXMuYXBwZW5kKGRpY3QocmVsYXRpdmVfcGF0aD1yZWxhdGl2ZSwgcGF0aD1zdHIocGF0aCksIHNoYTI1Nj1kaWdlc3QsIHNpemU9bGVuKGRhdGEpLCBmYnhfdmVyc2lvbj12ZXJzaW9uLCBtZXNoX25hbWVzPW5hbWVzKSkKICAgIGlmIG5vdCBmaWxlczoKICAgICAgICBpZiBucG1fb25seToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiTm8gTlBNIGNhbmRpZGF0ZXMgZm91bmQ7IHJlamVjdGVkIEZCWDogIiArIHN0cihsZW4oc2tpcHBlZCkpKQogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIk5vIHNvdXJjZSBGQlggZmlsZXMgZm91bmQiKQogICAgcGF5bG9hZCA9IGRpY3Qoc2NoZW1hX3ZlcnNpb249MSwgc291cmNlX3Jvb3Q9c3RyKHJvb3QpLCBmaWxlcz1maWxlcywgc2tpcHBlZD1za2lwcGVkKQogICAgaWYgbnBtX29ubHk6CiAgICAgICAgcGF5bG9hZC51cGRhdGUoc2VsZWN0aW9uX3Njb3BlPSJucG1fbmFtaW5nX2JpbmFyeTc0MDBfY2FuZGlkYXRlc19vbmx5IiwgZnVsbF9ucG1fdmVyaWZpZWQ9RmFsc2UpCiAgICByZXR1cm4gcGF5bG9hZAoKCmRlZiB2YWxpZGF0ZV9pbnZlbnRvcnkocGF0aCwgbnBtX29ubHk9RmFsc2UpOgogICAgZGVmIHVuaXF1ZV9wYWlycyhwYWlycyk6CiAgICAgICAgcmVzdWx0ID0ge30KICAgICAgICBmb3Iga2V5LCB2YWx1ZSBpbiBwYWlyczoKICAgICAgICAgICAgaWYga2V5IGluIHJlc3VsdDoKICAgICAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkR1cGxpY2F0ZSBKU09OIGtleTogIiArIGtleSkKICAgICAgICAgICAgcmVzdWx0W2tleV0gPSB2YWx1ZQogICAgICAgIHJldHVybiByZXN1bHQKICAgIHBheWxvYWQgPSBqc29uLmxvYWRzKFBhdGgocGF0aCkucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOC1zaWciKSwgb2JqZWN0X3BhaXJzX2hvb2s9dW5pcXVlX3BhaXJzKQogICAgaWYgbm90IGlzaW5zdGFuY2UocGF5bG9hZCwgZGljdCkgb3IgdHlwZShwYXlsb2FkLmdldCgic2NoZW1hX3ZlcnNpb24iKSkgaXMgbm90IGludCBvciBwYXlsb2FkWyJzY2hlbWFfdmVyc2lvbiJdICE9IDE6CiAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiVW5zdXBwb3J0ZWQgaW52ZW50b3J5IHNjaGVtYSIpCiAgICByb290X3ZhbHVlID0gcGF5bG9hZC5nZXQoInNvdXJjZV9yb290IikKICAgIGlmIG5vdCBpc2luc3RhbmNlKHJvb3RfdmFsdWUsIHN0cikgb3Igbm90IFBhdGgocm9vdF92YWx1ZSkuaXNfYWJzb2x1dGUoKToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJJbnZlbnRvcnkgc291cmNlX3Jvb3QgbXVzdCBiZSBhYnNvbHV0ZSIpCiAgICByb290ID0gUGF0aChyb290X3ZhbHVlKQogICAgaWYgbm90IHJvb3QuaXNfZGlyKCkgb3IgX2xpbmtlZChyb290KToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJJbnZlbnRvcnkgc291cmNlX3Jvb3QgaXMgbm90IGEgcmVhbCBkaXJlY3RvcnkiKQogICAgcm9vdCA9IHJvb3QucmVzb2x2ZSgpCiAgICBmaWxlcyA9IHBheWxvYWQuZ2V0KCJmaWxlcyIpCiAgICBpZiBub3QgaXNpbnN0YW5jZShmaWxlcywgbGlzdCkgb3Igbm90IGZpbGVzOgogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkVtcHR5IGludmVudG9yeSIpCiAgICBzZWVuID0gc2V0KCkKICAgIGZvciBpdGVtIGluIGZpbGVzOgogICAgICAgIGlmIG5vdCBpc2luc3RhbmNlKGl0ZW0sIGRpY3QpOgogICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJJbnZhbGlkIGludmVudG9yeSBqb2IiKQogICAgICAgIHJlbGF0aXZlID0gaXRlbS5nZXQoInJlbGF0aXZlX3BhdGgiKQogICAgICAgIGlmIG5vdCBpc2luc3RhbmNlKHJlbGF0aXZlLCBzdHIpIG9yIG5vdCByZWxhdGl2ZSBvciAiXFwiIGluIHJlbGF0aXZlIG9yICI6IiBpbiByZWxhdGl2ZSBvciAiXHgwMCIgaW4gcmVsYXRpdmU6CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIlVuc2FmZSByZWxhdGl2ZSBGQlggcGF0aCIpCiAgICAgICAgcGFydHMgPSByZWxhdGl2ZS5zcGxpdCgiLyIpCiAgICAgICAgaWYgYW55KHAgaW4gKCIiLCAiLiIsICIuLiIpIG9yIHAucnN0cmlwKCIgLiIpICE9IHAgb3IgcC51cHBlcigpLnN0YXJ0c3dpdGgoIk5QTV9GQlhfIikgZm9yIHAgaW4gcGFydHMpOgogICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJVbnNhZmUgcmVsYXRpdmUgRkJYIHBhdGgiKQogICAgICAgIGlmIFB1cmVQb3NpeFBhdGgocmVsYXRpdmUpLmlzX2Fic29sdXRlKCkgb3IgUHVyZVdpbmRvd3NQYXRoKHJlbGF0aXZlKS5pc19hYnNvbHV0ZSgpIG9yIFBhdGgocmVsYXRpdmUpLnN1ZmZpeC5sb3dlcigpICE9ICIuZmJ4IjoKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiVW5zYWZlIHJlbGF0aXZlIEZCWCBwYXRoIikKICAgICAgICBpZiByZWxhdGl2ZS5jYXNlZm9sZCgpIGluIHNlZW46CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkR1cGxpY2F0ZSBpbnZlbnRvcnkgcGF0aCIpCiAgICAgICAgc2Vlbi5hZGQocmVsYXRpdmUuY2FzZWZvbGQoKSkKICAgICAgICBzb3VyY2UgPSByb290LmpvaW5wYXRoKCpwYXJ0cykKICAgICAgICBjdXJyZW50ID0gcm9vdAogICAgICAgIGZvciBwYXJ0IGluIHBhcnRzOgogICAgICAgICAgICBjdXJyZW50IC89IHBhcnQKICAgICAgICAgICAgaWYgX2xpbmtlZChjdXJyZW50KToKICAgICAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkxpbmtlZCBpbnZlbnRvcnkgc291cmNlIikKICAgICAgICBpZiBzb3VyY2UucmVzb2x2ZSgpLnBhcmVudCAhPSByb290IGFuZCByb290IG5vdCBpbiBzb3VyY2UucmVzb2x2ZSgpLnBhcmVudHM6CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkludmVudG9yeSBwYXRoIGVzY2FwZXMgcm9vdCIpCiAgICAgICAgaWYgbm90IGlzaW5zdGFuY2UoaXRlbS5nZXQoInBhdGgiKSwgc3RyKSBvciBQYXRoKGl0ZW1bInBhdGgiXSkucmVzb2x2ZSgpICE9IHNvdXJjZS5yZXNvbHZlKCk6CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkludmVudG9yeSBhYnNvbHV0ZSBwYXRoIG1pc21hdGNoIikKICAgICAgICBkYXRhLCBkaWdlc3QgPSBfcmVhZF9zb3VyY2Uoc291cmNlKQogICAgICAgIGlmIHR5cGUoaXRlbS5nZXQoInNpemUiKSkgaXMgbm90IGludCBvciBpdGVtWyJzaXplIl0gIT0gbGVuKGRhdGEpIG9yIGl0ZW0uZ2V0KCJzaGEyNTYiKSAhPSBkaWdlc3Q6CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkZCWCBzb3VyY2UgY2hhbmdlZDogIiArIHJlbGF0aXZlKQogICAgICAgIHZlcnNpb24sIG5hbWVzID0gX21lc2hfbmFtZXMoZGF0YSkKICAgICAgICBpZiBucG1fb25seToKICAgICAgICAgICAgX25wbV9jYW5kaWRhdGUoc291cmNlLCBkYXRhLCB2ZXJzaW9uLCBuYW1lcykKICAgICAgICBpZiBpdGVtLmdldCgibWVzaF9uYW1lcyIpICE9IG5hbWVzIG9yICgiZmJ4X3ZlcnNpb24iIGluIGl0ZW0gYW5kIGl0ZW1bImZieF92ZXJzaW9uIl0gIT0gdmVyc2lvbik6CiAgICAgICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIkZCWCBtZXNoIGludmVudG9yeSBtaXNtYXRjaDogIiArIHJlbGF0aXZlKQogICAgcmV0dXJuIHBheWxvYWQKCgpkZWYgc2F2ZV9pbnZlbnRvcnkoZm9sZGVyLCBvdXRwdXRfZGlyPU5vbmUsIG5wbV9vbmx5PUZhbHNlKToKICAgIHBheWxvYWQgPSBhbmFseXplX2ZvbGRlcihmb2xkZXIsIG5wbV9vbmx5PW5wbV9vbmx5KQogICAgcm9vdCA9IFBhdGgocGF5bG9hZFsic291cmNlX3Jvb3QiXSkKICAgIGRlc3RpbmF0aW9uID0gcm9vdAogICAgaWYgb3V0cHV0X2RpciBpcyBub3QgTm9uZToKICAgICAgICBkZXN0aW5hdGlvbiA9IFBhdGgob3V0cHV0X2RpcikuYWJzb2x1dGUoKQogICAgICAgIGlmIG5vdCBkZXN0aW5hdGlvbi5pc19kaXIoKSBvciBfbGlua2VkKGRlc3RpbmF0aW9uKToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiSW52ZW50b3J5IG91dHB1dCBtdXN0IGJlIGEgcmVhbCBkaXJlY3RvcnkiKQogICAgICAgIGRlc3RpbmF0aW9uID0gZGVzdGluYXRpb24ucmVzb2x2ZSgpCiAgICAgICAgaWYgZGVzdGluYXRpb24gPT0gcm9vdDoKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiSW52ZW50b3J5IG91dHB1dCBtdXN0IGRpZmZlciBmcm9tIHNvdXJjZSByb290IikKICAgIGVsaWYgbnBtX29ubHk6CiAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiTlBNIGludmVudG9yeSByZXF1aXJlcyBhIHNlcGFyYXRlIG91dHB1dCB3b3Jrc3BhY2UiKQogICAgc3RhbXAgPSBfZHQuZGF0ZXRpbWUubm93KF9kdC50aW1lem9uZS51dGMpLnN0cmZ0aW1lKCIlWSVtJWRUJUglTSVTJWZaIikKICAgIHRhcmdldCA9IGRlc3RpbmF0aW9uIC8gKCJucG1fZmJ4X2ludmVudG9yeV8iICsgc3RhbXAgKyAiLmpzb24iKQogICAgd2l0aCB0YXJnZXQub3BlbigieCIsIGVuY29kaW5nPSJ1dGYtOCIsIG5ld2xpbmU9IlxuIikgYXMgc3RyZWFtOgogICAgICAgIGpzb24uZHVtcChwYXlsb2FkLCBzdHJlYW0sIGVuc3VyZV9hc2NpaT1GYWxzZSwgaW5kZW50PTIpCiAgICAgICAgc3RyZWFtLndyaXRlKCJcbiIpCiAgICByZXR1cm4gc3RyKHRhcmdldCkKCgpkZWYgdmVyaWZ5X2V4cG9ydHMoaW52ZW50b3J5X3BhdGgsIG91dHB1dF9yb290LCBucG1fb25seT1GYWxzZSk6CiAgICAiIiJWZXJpZnkgZXhwb3J0ZWQgbWVzaCBtZW1iZXJzaGlwIG9ubHk7IHRoaXMgaXMgbm90IGdlb21ldHJ5L21hdGVyaWFsIFFBLiIiIgogICAgcGF5bG9hZCA9IHZhbGlkYXRlX2ludmVudG9yeShpbnZlbnRvcnlfcGF0aCwgbnBtX29ubHk9bnBtX29ubHkpCiAgICBvdXRwdXRfcm9vdCA9IFBhdGgob3V0cHV0X3Jvb3QpLmFic29sdXRlKCkKICAgIGlmIG5vdCBvdXRwdXRfcm9vdC5pc19kaXIoKSBvciBfbGlua2VkKG91dHB1dF9yb290KToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJPdXRwdXQgcm9vdCBtdXN0IGJlIGEgcmVhbCBkaXJlY3RvcnkiKQogICAgb3V0cHV0X3Jvb3QgPSBvdXRwdXRfcm9vdC5yZXNvbHZlKCkKICAgIGlmIG91dHB1dF9yb290ID09IFBhdGgocGF5bG9hZFsic291cmNlX3Jvb3QiXSkucmVzb2x2ZSgpOgogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoIk91dHB1dCByb290IG11c3QgZGlmZmVyIGZyb20gc291cmNlIHJvb3QiKQogICAgcmVwb3J0cyA9IFtdCiAgICBmb3IgaXRlbSBpbiBwYXlsb2FkWyJmaWxlcyJdOgogICAgICAgIG91dHB1dCA9IG91dHB1dF9yb290LmpvaW5wYXRoKCppdGVtWyJyZWxhdGl2ZV9wYXRoIl0uc3BsaXQoIi8iKSkKICAgICAgICBjdXJyZW50ID0gb3V0cHV0X3Jvb3QKICAgICAgICBmb3IgcGFydCBpbiBpdGVtWyJyZWxhdGl2ZV9wYXRoIl0uc3BsaXQoIi8iKToKICAgICAgICAgICAgY3VycmVudCAvPSBwYXJ0CiAgICAgICAgICAgIGlmIF9saW5rZWQoY3VycmVudCk6CiAgICAgICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJMaW5rZWQgZXhwb3J0IG91dHB1dCIpCiAgICAgICAgaWYgb3V0cHV0LnJlc29sdmUoKSA9PSBQYXRoKGl0ZW1bInBhdGgiXSkucmVzb2x2ZSgpOgogICAgICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJFeHBvcnQgb3V0cHV0IG92ZXJsYXBzIHNvdXJjZSIpCiAgICAgICAgZGF0YSwgZGlnZXN0ID0gX3JlYWRfc291cmNlKG91dHB1dCkKICAgICAgICBpZiBub3QgZGF0YToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiRW1wdHkgZXhwb3J0OiAiICsgaXRlbVsicmVsYXRpdmVfcGF0aCJdKQogICAgICAgIHZlcnNpb24sIG5hbWVzID0gX21lc2hfbmFtZXMoZGF0YSkKICAgICAgICBpZiBucG1fb25seToKICAgICAgICAgICAgX25wbV9jYW5kaWRhdGUob3V0cHV0LCBkYXRhLCB2ZXJzaW9uLCBuYW1lcykKICAgICAgICBleHBlY3RlZCA9IGl0ZW1bIm1lc2hfbmFtZXMiXQogICAgICAgIGlmIGxlbihuYW1lcykgIT0gbGVuKGV4cGVjdGVkKSBvciB7bi5jYXNlZm9sZCgpIGZvciBuIGluIG5hbWVzfSAhPSB7bi5jYXNlZm9sZCgpIGZvciBuIGluIGV4cGVjdGVkfToKICAgICAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigiRXhwb3J0IG1lc2ggbWVtYmVyc2hpcCBtaXNtYXRjaDogIiArIGl0ZW1bInJlbGF0aXZlX3BhdGgiXSkKICAgICAgICByZXBvcnRzLmFwcGVuZChkaWN0KHJlbGF0aXZlX3BhdGg9aXRlbVsicmVsYXRpdmVfcGF0aCJdLCBzb3VyY2Vfc2hhMjU2PWl0ZW1bInNoYTI1NiJdLCBvdXRwdXRfc2hhMjU2PWRpZ2VzdCwKICAgICAgICAgICAgICAgICAgICAgICAgICAgIHNpemU9bGVuKGRhdGEpLCBmYnhfdmVyc2lvbj12ZXJzaW9uLCBtZXNoX25hbWVzPW5hbWVzLCB2ZXJpZmllZD1UcnVlLAogICAgICAgICAgICAgICAgICAgICAgICAgICAgdmVyaWZpY2F0aW9uX3Njb3BlPSJtZXNoX21lbWJlcnNoaXBfb25seSIsIG5hdGl2ZV9nZW9tZXRyeV92ZXJpZmllZD1GYWxzZSkpCiAgICByZXBvcnQgPSBkaWN0KHNjaGVtYV92ZXJzaW9uPTEsIGludmVudG9yeV9wYXRoPXN0cihQYXRoKGludmVudG9yeV9wYXRoKS5yZXNvbHZlKCkpLAogICAgICAgICAgICAgICAgICBpbnZlbnRvcnlfc2hhMjU2PWhhc2hsaWIuc2hhMjU2KFBhdGgoaW52ZW50b3J5X3BhdGgpLnJlYWRfYnl0ZXMoKSkuaGV4ZGlnZXN0KCksCiAgICAgICAgICAgICAgICAgIG91dHB1dF9yb290PXN0cihvdXRwdXRfcm9vdCksIGZpbGVzPXJlcG9ydHMsIHZlcmlmaWVkPVRydWUsCiAgICAgICAgICAgICAgICAgIHZlcmlmaWNhdGlvbl9zY29wZT0ibWVzaF9tZW1iZXJzaGlwX29ubHkiLCBuYXRpdmVfZ2VvbWV0cnlfdmVyaWZpZWQ9RmFsc2UpCiAgICB3aXRoIChvdXRwdXRfcm9vdCAvICJleHBvcnRfcmVwb3J0Lmpzb24iKS5vcGVuKCJ4IiwgZW5jb2Rpbmc9InV0Zi04IiwgbmV3bGluZT0iXG4iKSBhcyBzdHJlYW06CiAgICAgICAganNvbi5kdW1wKHJlcG9ydCwgc3RyZWFtLCBlbnN1cmVfYXNjaWk9RmFsc2UsIGluZGVudD0yKQogICAgICAgIHN0cmVhbS53cml0ZSgiXG4iKQogICAgcmV0dXJuIHJlcG9ydAoKCmRlZiBfYnJpZGdlKGFuYWx5emUpOgogICAgZnJvbSBweW14cyBpbXBvcnQgcnVudGltZSBhcyBydAogICAgcnQuQUdSX05QTUZieF9FcnJvciA9ICIiCiAgICBydC5BR1JfTlBNRmJ4X0pvYnMgPSBydC5BcnJheSgpCiAgICB0cnk6CiAgICAgICAgcGF0aCA9IHNhdmVfaW52ZW50b3J5KHN0cihydC5BR1JfTlBNRmJ4X1NvdXJjZVJvb3QpLCBvdXRwdXRfZGlyPXN0cihydC5BR1JfTlBNRmJ4X1dvcmtzcGFjZSksIG5wbV9vbmx5PVRydWUpIGlmIGFuYWx5emUgZWxzZSBzdHIocnQuQUdSX05QTUZieF9Kc29uUGF0aCkKICAgICAgICBwYXlsb2FkID0gdmFsaWRhdGVfaW52ZW50b3J5KHBhdGgsIG5wbV9vbmx5PVRydWUpCiAgICAgICAgcnQuQUdSX05QTUZieF9Kc29uUGF0aCA9IHBhdGgKICAgICAgICBydC5BR1JfTlBNRmJ4X1NvdXJjZVJvb3QgPSBwYXlsb2FkWyJzb3VyY2Vfcm9vdCJdCiAgICAgICAgcnQuQUdSX05QTUZieF9Kb2JzID0gcnQuQXJyYXkoKltydC5BcnJheShpdGVtWyJyZWxhdGl2ZV9wYXRoIl0sIHJ0LkFycmF5KCppdGVtWyJtZXNoX25hbWVzIl0pKSBmb3IgaXRlbSBpbiBwYXlsb2FkWyJmaWxlcyJdXSkKICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZXJyb3I6CiAgICAgICAgcnQuQUdSX05QTUZieF9FcnJvciA9IHR5cGUoZXJyb3IpLl9fbmFtZV9fICsgIjogIiArIHN0cihlcnJvcikKCgpkZWYgYWdyX25wbV9mYnhfYW5hbHl6ZSgpOgogICAgX2JyaWRnZShUcnVlKQoKCmRlZiBhZ3JfbnBtX2ZieF9sb2FkKCk6CiAgICBfYnJpZGdlKEZhbHNlKQoKCmRlZiBhZ3JfbnBtX2ZieF92ZXJpZnlfZXhwb3J0cygpOgogICAgZnJvbSBweW14cyBpbXBvcnQgcnVudGltZSBhcyBydAogICAgcnQuQUdSX05QTUZieF9FcnJvciA9ICIiCiAgICB0cnk6CiAgICAgICAgdmVyaWZ5X2V4cG9ydHMoc3RyKHJ0LkFHUl9OUE1GYnhfSnNvblBhdGgpLCBzdHIocnQuQUdSX05QTUZieF9PdXRwdXRSb290KSwgbnBtX29ubHk9VHJ1ZSkKICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZXJyb3I6CiAgICAgICAgcnQuQUdSX05QTUZieF9FcnJvciA9IHR5cGUoZXJyb3IpLl9fbmFtZV9fICsgIjogIiArIHN0cihlcnJvcikK"
-- END EMBEDDED FBX PYTHON

struct AGR_NPMFbxCore
(
    fn initPython =
    (
        if AGR_NPMFbx_Payload == "" do throw "Embedded FBX reader is missing."
        if (python.Execute ("import base64; exec(compile(base64.b64decode('" + AGR_NPMFbx_Payload + "'), '<npm_fbx_inventory>', 'exec'), globals())")) != #success do
            throw "Could not initialize the built-in 3ds Max Python reader."
    ),

    fn newWorkspace parentFolder =
    (
        local suffix = (dotNetClass "System.DateTime").Now.ToString "yyyyMMdd_HHmmss_fff"
        local workspace = pathConfig.appendPath parentFolder ("NPM_FBX_" + suffix)
        if (dotNetClass "System.IO.Directory").Exists workspace do throw "Output folder already exists."
        makeDir workspace all:true
        workspace
    ),

    fn analyze root workspace =
    (
        initPython()
        AGR_NPMFbx_SourceRoot = root
        AGR_NPMFbx_Workspace = workspace
        AGR_NPMFbx_Error = ""
        if (python.Execute "agr_npm_fbx_analyze()") != #success do throw "Embedded FBX analysis failed; see Listener."
        if AGR_NPMFbx_Error != "" do throw AGR_NPMFbx_Error
        AGR_NPMFbx_JsonPath
    ),

    fn loadInventory path =
    (
        initPython()
        AGR_NPMFbx_JsonPath = path
        AGR_NPMFbx_Error = ""
        AGR_NPMFbx_Jobs = #()
        if (python.Execute "agr_npm_fbx_load()") != #success do throw "Embedded JSON validation failed; see Listener."
        if AGR_NPMFbx_Error != "" do throw AGR_NPMFbx_Error
        AGR_NPMFbx_Jobs
    ),

    fn resolveJobs jobs =
    (
        local result = #()
        for job in jobs do
        (
            local nodes = #()
            for name in job[2] do
            (
                local found = for node in objects where (stricmp node.name name) == 0 collect node
                if found.count != 1 do throw ("Missing or duplicate scene object: " + name)
                if superClassOf found[1] != GeometryClass do throw ("Object is not a mesh: " + name)
                append nodes found[1]
            )
            if nodes.count == 0 do throw ("No meshes in job: " + job[1])
            append result #(job[1], nodes)
        )
        if result.count == 0 do throw "The inventory contains no FBX jobs."
        result
    ),

    fn setExportSettings =
    (
        local settings = #(#("SmoothingGroups",true), #("Triangulate",true), #("TangentSpaceExport",false), #("PreserveInstances",false), #("SelectionSetExport",false), #("Lights",false), #("Cameras",false), #("EmbedTextures",true), #("FileVersion","FBX201400"), #("UpAxis","Y"), #("ConvertUnit","m"), #("ScaleFactor",1.0), #("ShowWarnings",false), #("GenerateLog",true), #("Animation",false), #("ASCII",false), #("ExportAnimationOnly",false))
        for setting in settings do
        (
            local response = FBXExporterSetParam setting[1] setting[2]
            if (toLower (response as string)) != "ok" do throw ("Unsupported FBX setting: " + setting[1])
        )
    ),

    fn stripAttributes target =
    (
        local guard = 0
        while custAttributes.count target > 0 do
        (
            custAttributes.delete target 1
            guard += 1
            if guard > 1000 do throw "Could not remove custom attributes from export copy."
        )
    ),

    fn cleanMaterial root =
    (
        local pending = #(root)
        local seen = #()
        while pending.count > 0 do
        (
            local target = pending[pending.count]
            deleteItem pending pending.count
            if target != undefined and findItem seen target == 0 do
            (
                append seen target
                stripAttributes target
                for i = 1 to getNumSubTexmaps target do append pending (getSubTexmap target i)
                if superClassOf target == material do
                    for i = 1 to getNumSubMtls target do append pending (getSubMtl target i)
            )
        )
    ),

    fn exportJob nodes path =
    (
        if theHold.Holding() do throw "3ds Max has another active operation."
        if doesFileExist path do throw ("Output already exists: " + path)
        local failure = undefined
        theHold.Begin()
        try
        (
            local originals = #()
            local clones = #()
            if not (maxOps.cloneNodes nodes cloneType:#copy expandHierarchy:false actualNodeList:&originals newNodes:&clones) do throw "Could not create export copies."
            if clones.count != nodes.count or originals.count != nodes.count do throw "Clone operation expanded the FBX mesh set."
            for i = 1 to clones.count do
            (
                if findItem nodes originals[i] == 0 do throw "Unexpected export dependency."
                clones[i].name = originals[i].name
                local parentIndex = findItem originals originals[i].parent
                clones[i].parent = if parentIndex == 0 then undefined else clones[parentIndex]
                clones[i].transform = originals[i].transform
                clones[i].isHidden = false
                clones[i].isFrozen = false
                stripAttributes clones[i]
                stripAttributes clones[i].baseObject
                for modifier in clones[i].modifiers do stripAttributes modifier
                setUserPropBuffer clones[i] ""
                if clones[i].material != undefined do
                (
                    clones[i].material = copy clones[i].material
                    cleanMaterial clones[i].material
                )
            )
            select clones
            local exportResult = exportFile path #noPrompt selectedOnly:true using:FBXEXP
            if exportResult == false or exportResult == #failure do throw ("FBX export failed: " + path)
            if not doesFileExist path or (getFileSize path) == 0 do throw ("FBX output missing or empty: " + path)
        )
        catch (failure = getCurrentException())
        -- Cancel destroys only temporary copies and preserves the user's Undo history.
        theHold.Cancel()
        if failure != undefined do throw failure
    ),

    fn exportInventory jsonPath =
    (
        local jobs = resolveJobs (loadInventory jsonPath)
        local outRoot = getFilenamePath jsonPath
        for job in jobs do
            if doesFileExist (pathConfig.appendPath outRoot job[1]) do throw ("Output already exists: " + job[1] + "; create a new workspace.")
        if doesFileExist (pathConfig.appendPath outRoot "export_report.json") do throw "Export report already exists; create a new workspace."
        local savedSelection = selection as array
        local failure = undefined
        pluginManager.loadClass FBXEXP
        if (toLower ((FBXExporterSetParam "PushSettings") as string)) != "ok" do throw "Cannot save FBX settings."
        try
        (
            setExportSettings()
            for job in jobs do
            (
                local path = pathConfig.appendPath outRoot job[1]
                makeDir (getFilenamePath path) all:true
                exportJob job[2] path
                format "FBX exported: % (% meshes)\n" path job[2].count
            )
            AGR_NPMFbx_OutputRoot = outRoot
            AGR_NPMFbx_Error = ""
            if (python.Execute "agr_npm_fbx_verify_exports()") != #success do throw "Embedded export verification failed; see Listener."
            if AGR_NPMFbx_Error != "" do throw AGR_NPMFbx_Error
        )
        catch (failure = getCurrentException())
        local restoreError = ""
        try
        (
            if (toLower ((FBXExporterSetParam "PopSettings") as string)) != "ok" do restoreError += "FBX settings restore failed. "
        )
        catch (restoreError += "FBX settings restore exception. ")
        try (select (for node in savedSelection where isValidNode node collect node))
        catch (restoreError += "Selection restore exception. ")
        if failure != undefined do throw ("Export stopped; partial files retained at " + outRoot + ": " + failure + " " + restoreError)
        if restoreError != "" do throw restoreError
        outRoot
    )
)
AGR_NPMFbx = AGR_NPMFbxCore()

try (destroyDialog AGR_NPMLinkerDialog) catch()
rollout AGR_NPMLinkerDialog "NPM — материалы и экспорт FBX" width:500 height:420
(
    local textureRoot = undefined
    local saveParent = undefined
    local sourceRoot = undefined
    local jsonPath = undefined
    local workspace = undefined

    label step1 "1. Папки" align:#left
    editText outputText "Сохранение:" text:"" width:475 readOnly:true
    button outputButton "Выбрать папку сохранения..." width:475
    editText textureText "Текстуры:" text:"" width:475 readOnly:true
    button browseButton "Выбрать папку текстур (со всеми подпапками)..." width:475
    label step2 "2. Материалы всех ОКС в сцене" align:#left
    button applyButton "Подключить текстуры и M_Glass" width:475 enabled:false
    label statusText "Новые Standard Legacy; отдельные M_Glass_01, 02, ..." width:475 height:30 align:#left
    label step3 "3. Состав исходных FBX — обязательный JSON" align:#left
    editText sourceText "Исходные FBX:" text:"" width:475 readOnly:true
    button sourceButton "Выбрать папку исходных FBX..." width:235 across:2
    button analyzeFbxButton "Анализ подпапок → новый JSON" width:235 enabled:false
    button loadJsonButton "Есть JSON — выбрать и проверить..." width:475 enabled:false
    editText jsonText "JSON:" text:"" width:475 readOnly:true
    label step4 "4. Экспорт в ту же новую папку, где лежит JSON" align:#left
    button exportFbxButton "Экспорт FBX по проверенному JSON" width:475 enabled:false
    label fbxStatus "Без JSON экспорт недоступен. Отбор НПМ — по формату и именам." width:475 height:45 align:#left

    fn refreshButtons busy:false =
    (
        outputButton.enabled = not busy
        browseButton.enabled = not busy
        sourceButton.enabled = not busy
        applyButton.enabled = not busy and textureRoot != undefined
        analyzeFbxButton.enabled = not busy and saveParent != undefined and sourceRoot != undefined
        loadJsonButton.enabled = not busy and saveParent != undefined
        exportFbxButton.enabled = not busy and jsonPath != undefined
    )

    fn reportError error =
    (
        fbxStatus.text = "Ошибка: " + (error as string)
        format "NPM: %\n" error
    )

    on outputButton pressed do
    (
        local chosen = getSavePath caption:"Где создать новую папку с JSON и FBX?"
        if chosen != undefined do
        (
            saveParent = chosen
            outputText.text = chosen
            jsonPath = undefined
            workspace = undefined
            jsonText.text = ""
            refreshButtons()
        )
    )

    on browseButton pressed do
    (
        local chosen = getSavePath caption:"Папка текстур — поиск по всем подпапкам"
        if chosen != undefined do
        (
            textureRoot = chosen
            textureText.text = chosen
            refreshButtons()
        )
    )

    on sourceButton pressed do
    (
        local chosen = getSavePath caption:"Папка исходных FBX — поиск по всем подпапкам"
        if chosen != undefined do
        (
            sourceRoot = chosen
            sourceText.text = chosen
            jsonPath = undefined
            jsonText.text = ""
            refreshButtons()
        )
    )

    on analyzeFbxButton pressed do
    (
        refreshButtons busy:true
        jsonPath = undefined
        jsonText.text = ""
        fbxStatus.text = "Анализ исходных FBX во всех подпапках..."
        try
        (
            workspace = AGR_NPMFbx.newWorkspace saveParent
            outputText.text = workspace
            local candidate = AGR_NPMFbx.analyze sourceRoot workspace
            AGR_NPMFbx.resolveJobs (AGR_NPMFbx.loadInventory candidate)
            jsonPath = candidate
            jsonText.text = candidate
            fbxStatus.text = "JSON создан и проверен. Можно экспортировать FBX. Отчёт: F11."
        )
        catch (reportError (getCurrentException()))
        refreshButtons()
    )

    on loadJsonButton pressed do
    (
        local chosen = getOpenFileName caption:"JSON состава исходных FBX" types:"JSON (*.json)|*.json|"
        if chosen != undefined do
        (
            refreshButtons busy:true
            jsonPath = undefined
            jsonText.text = ""
            try
            (
                AGR_NPMFbx.resolveJobs (AGR_NPMFbx.loadInventory chosen)
                workspace = AGR_NPMFbx.newWorkspace saveParent
                local target = pathConfig.appendPath workspace "npm_fbx_inventory.json"
                if not copyFile chosen target do throw "Could not copy inventory into output folder."
                AGR_NPMFbx.resolveJobs (AGR_NPMFbx.loadInventory target)
                jsonPath = target
                jsonText.text = target
                outputText.text = workspace
                fbxStatus.text = "JSON проверен и помещён в новую папку. Экспорт доступен."
            )
            catch (reportError (getCurrentException()))
            refreshButtons()
        )
    )

    on exportFbxButton pressed do
    (
        refreshButtons busy:true
        try
        (
            local result = AGR_NPMFbx.exportInventory jsonPath
            fbxStatus.text = "FBX сохранены рядом с JSON. Состав проверен; export_report.json."
            jsonPath = undefined -- prevent accidental repeat into the same output
        )
        catch (reportError (getCurrentException()))
        refreshButtons()
    )

    on applyButton pressed do
    (
        refreshButtons busy:true
        statusText.text = "Поиск текстур и подготовка материалов..."
        try
        (
            local result = AGR_NPMLinker.run textureRoot
            statusText.text = "ОКС: " + (result[1] as string) + " | Стекло: " + (result[5] as string) + " | Пропущено: " + (result[2] as string) + ". Отчёт: F11. Отмена: Ctrl+Z."
        )
        catch
        (
            statusText.text = "Остановлено: " + (getCurrentException() as string)
            format "NPM Texture Linker ERROR: %\n" (getCurrentException())
        )
        refreshButtons()
    )
)
if AGR_NPMLinker_NoUI != true do createDialog AGR_NPMLinkerDialog
