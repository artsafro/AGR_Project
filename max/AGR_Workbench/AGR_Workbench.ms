/* Task workspace: current Max selection, no hidden saved sets. */
global AGRWB_UI
global AGRWB_Root = getFilenamePath (getThisScriptFilename())
try(destroyDialog AGRWB_UI)catch()
fileIn (AGRWB_Root + "core.ms")
fileIn (AGRWB_Root + "pipeline.ms")
fileIn (AGRWB_Root + "tasks.ms")
fileIn (AGRWB_Root + "extensions.ms")
rollout AGRWB_UI "AGR Workbench 0.5 · инструменты НПМ / ВПМ" width:1000 height:750
(
  local codes = #()
  local currentTask = #welcome
  local templateLight = undefined
  local readbackProcess = undefined
  local readbackReportPath = ""
  label title "AGR Workbench · выберите инструмент слева" pos:[18,12] width:750
  button btnHelp "Руководство" pos:[842,8] width:140 height:28
  dotNetControl tabs "System.Windows.Forms.TabControl" pos:[18,47] width:964 height:28
  label lblScope "Сейчас в Max ничего не выделено" pos:[18,88] width:950 height:34
  label lblMenu "ИНСТРУМЕНТЫ" pos:[18,133] width:260
  dotNetControl menu "System.Windows.Forms.ListBox" pos:[18,156] width:266 height:292
  label lblPending "ЕЩЁ ПЕРЕНОСИМ" pos:[18,464] width:266
  dotNetControl pending "System.Windows.Forms.ListBox" pos:[18,487] width:266 height:156
  label lblRoute "Как начать:\n1. Выделите объект в Max.\n2. Выберите инструмент слева.\n3. Проверьте параметры и выполните действие.\n\nРабота идёт с текущим выделением." pos:[18,660] width:266 height:78
  groupBox panel "" pos:[302,128] width:680 height:384
  label lblTask "Выберите задачу" pos:[322,149] width:636 height:25
  dotNetControl description "System.Windows.Forms.TextBox" pos:[322,184] width:636 height:104
  editText edtStem "Адрес (SM_...):" pos:[322,302] width:636
  dropdownList ddlRole "Что именуем:" pos:[322,332] width:332 items:#("Здание · Main","Стекло · MainGlass","Территория · Ground")
  label lblIndex "Номер ОКС:" pos:[678,335] width:258
  spinner spnIndex "" pos:[678,359] width:258 fieldWidth:90 range:[1,999,1] type:#integer
  checkbox chkAll "Все полигоны (иначе только выделенные в Max)" pos:[322,302] width:636 checked:false
  dropdownList ddlAxis "Направление поверхности:" pos:[322,335] width:332 items:#("XY · горизонтальная земля","XZ · вертикальный фасад","YZ · вертикальный фасад")
  label lblMeters "Сторона всей текстуры, м:" pos:[678,335] width:270
  spinner spnMeters "" pos:[678,359] width:258 fieldWidth:90 range:[0.001,10000,1] type:#float
  label lblSegments "Сколько новых сегментов:" pos:[322,302] width:300
  spinner spnSegments "" pos:[678,302] width:258 fieldWidth:90 range:[1,100,1] type:#integer
  pickbutton btnTemplate "Выбрать FreeSpot как образец света" pos:[322,343] width:636 height:30 autoDisplay:true
  label lblTile "Номер тайла (1001 = область UV 0–1):" pos:[322,304] width:350
  spinner spnTile "" pos:[678,302] width:258 fieldWidth:90 range:[1001,1999,1001] type:#integer
  label lblMaterialID "Material ID нужной отделки:" pos:[322,350] width:350
  spinner spnMaterialID "" pos:[678,348] width:258 fieldWidth:90 range:[1,65535,1] type:#integer
  label lblHullVertices "Максимум вершин оболочки:" pos:[322,350] width:350
  spinner spnHullVertices "" pos:[678,348] width:258 fieldWidth:90 range:[4,255,64] type:#integer
  label lblMap "Размер квадратной текстуры, px:" pos:[322,304] width:350
  spinner spnMap "" pos:[678,302] width:258 fieldWidth:90 range:[1,32768,2048] type:#integer
  checkbox chkGround "Выделена только поверхность Ground, без здания и растений" pos:[322,348] width:636 checked:false
  label lblEffect "" pos:[322,399] width:636 height:42
  button btnPreview "Проверить без изменений" pos:[322,460] width:306 height:32
  button btnApply "Выполнить" pos:[646,460] width:312 height:32
  button btnReadback "Выбрать и проверить FBX…" pos:[322,340] width:636 height:32
  label lblResult "РЕЗУЛЬТАТ ПОСЛЕДНЕГО ДЕЙСТВИЯ" pos:[322,531] width:636
  dotNetControl edtLog "System.Windows.Forms.TextBox" pos:[302,557] width:680 height:137
  button btnSaveLog "Сохранить результат…" pos:[762,708] width:220 height:28
  timer selectionTimer interval:500 active:false
  timer readbackTimer interval:500 active:false

  fn roleCode = (#("Main","MainGlass","Ground","UCX_Main","UCX_Ground")[ddlRole.selection])
  fn logMessage textValue =
  (
    local readable=textValue as string
    for pair in #(#("MISSING_OR_INVALID_ROLE","Не назначены имя и роль — используйте «Имена для сдачи»"),#("WRONG_PROFILE","Объект относится к другой вкладке НПМ/ВПМ"),#("NO_MATERIAL","Не назначен материал"),#("MISSING_MAP","Не найден файл текстуры"),#("NO_UV1","Нет UV-развёртки в канале 1"),#("EMPTY_UV1","Канал UV1 пуст"),#("DUPLICATE_NAME","Имя повторяется в сцене"),#("UNSUPPORTED_CLASS","Нужен Editable Poly или Editable Mesh"),#("NO_FILE_MAPS_FOUND","Файловые текстуры не найдены в материале"),#("EMPTY_SET","Ничего не выделено")) do
      readable=substituteString readable pair[1] pair[2]
    edtLog.text=readable
    format "[AGRWB] %\n" readable
  )
  fn selectionLabel =
  (
    local nodes=selection as array
    lblScope.text = if nodes.count==0 then "Сейчас в Max ничего не выделено. Выделите объект в сцене — инструмент увидит его автоматически." else if nodes.count==1 then "Будет обработан выделенный объект: " + nodes[1].name else "Будут обработаны выделенные объекты: " + nodes.count as string + ". Смена выделения в Max сразу меняет область действия."
    local allowed = currentTask != #welcome and currentTask != #pending and currentTask != #readback
    btnPreview.enabled = allowed and nodes.count>0
    btnApply.enabled = allowed and nodes.count>0
    if currentTask == #density and AGRWB_Core.profile == "NPM" do
    (
      btnApply.enabled = nodes.count>0 and chkGround.checked
      btnPreview.enabled = nodes.count>0 and chkGround.checked
    )
  )
  fn showTask code =
  (
    currentTask=code
    for c in #(edtStem,ddlRole,lblIndex,spnIndex,chkAll,ddlAxis,lblMeters,spnMeters,lblSegments,spnSegments,btnTemplate,lblTile,spnTile,lblMap,spnMap,chkGround,btnReadback,lblMaterialID,spnMaterialID,lblHullVertices,spnHullVertices) do c.visible=false
    btnPreview.visible=true
    btnApply.visible=true
    btnPreview.text="Проверить без изменений"
    btnApply.text="Выполнить"
    lblEffect.text="Изменяется текущее выделение Max. Для отмены изменений сцены используйте Ctrl+Z."
    case code of
    (
      #welcome:
      (
        lblTask.text="Инструменты для выбранного объекта"
        description.text="Слева видны доступные операции. Выберите ту, которая нужна сейчас.\r\n\r\nДля НПМ здания главное — сохранить размер кирпича, плитки и другого рисунка относительно ВПМ. Плотность Ground к зданию не применяется."
        lblEffect.text="Отдельная версия модели нужна только если хотите сохранить исходник перед изменениями. Это необязательный инструмент слева."
        btnPreview.visible=false; btnApply.visible=false
      )
      #names:
      (
        lblTask.text="Присвоить имя для сдачи"
        description.text="Зачем: получить имя здания, стекла, территории или коллизии по выбранному профилю.\r\nЧто выбрать: один объект; несколько разрешены только для UCX.\r\nРезультат: изменятся имя и служебная роль. Геометрия и материалы сохранятся."
        for c in #(edtStem,ddlRole,lblIndex,spnIndex) do c.visible=true
        btnApply.text="Переименовать выделенное"
      )
      #uv:
      (
        lblTask.text="Задать реальный размер рисунка текстуры"
        description.text="Зачем: например, участок текстуры 2×2 м должен занимать на модели именно 2×2 м. Так можно сохранить размер рисунка между НПМ и ВПМ.\r\nЧто выбрать: один Editable Poly, затем плоские полигоны фасада или земли.\r\nРезультат: плоская UV-проекция без изменения геометрии. Это не сборка атласа."
        for c in #(chkAll,ddlAxis,lblMeters,spnMeters) do c.visible=true
        lblEffect.text="UV1 должен существовать; модификаторов быть не должно. Наклонённые к выбранной плоскости грани отклоняются, чтобы не растягивать рисунок."
        btnApply.text="Применить размер к UV"
      )
      #tile:
      (
        lblTask.text="Переместить готовую развёртку"
        description.text="Зачем: разместить уже подготовленные UV в нужном тайле, сохранив размер рисунка.\r\nЧто выбрать: объект с готовой UV1, занимающей не больше 1×1.\r\nРезультат: вся развёртка сдвинется в центр тайла. Острова не разворачиваются и не упаковываются."
        lblTile.visible=true; spnTile.visible=true
        spnTile.enabled=AGRWB_Core.profile=="VPM"
        if AGRWB_Core.profile=="NPM" do spnTile.value=1001
        btnApply.text="Переместить UV"
      )
      #materialUV:
      (
        lblTask.text="Перенести UV одной отделки в UDIM"
        description.text="Зачем: собрать выбранную отделку в нужном тайле без изменения размера рисунка.\r\nЧто выбрать: один Editable Poly без модификаторов. Укажите Material ID полигонов этой отделки и целевой UDIM.\r\nРезультат: сместятся только UV указанного ID. ID материала и номер тайла не обязаны совпадать."
        for c in #(lblTile,spnTile,lblMaterialID,spnMaterialID) do c.visible=true
        btnApply.text="Перенести UV этой отделки"
        lblEffect.text="UV должны помещаться в один тайл. Инструмент не уменьшает рисунок и не упаковывает острова; занятость целевого тайла проверьте в Unwrap."
      )
      #hull:
      (
        lblTask.text="Создать выпуклую коллизию по форме"
        description.text="Зачем: получить коллизию, которая точнее бокса повторяет простой объём.\r\nЧто выбрать: один Editable Poly и полигоны объёмного участка.\r\nРезультат: новая выпуклая оболочка. Она закрывает вогнутости и отверстия: для сложного здания создавайте отдельные части."
        for c in #(chkAll,lblHullVertices,spnHullVertices) do c.visible=true
        btnApply.text="Создать выпуклую оболочку"
        lblEffect.text="Исходник не меняется. Оболочка выделится; назначьте ей имя UCX и проверьте проёмы, пересечения и зазоры."
      )
      #textureFiles:
      (
        lblTask.text="Найти файлы текстур модели"
        description.text="Зачем: увидеть, откуда материалы берут изображения и какие ссылки потеряны.\r\nЧто выбрать: объекты с материалами.\r\nРезультат: список найденных и отсутствующих файлов. Его можно сохранить кнопкой под результатом."
        btnPreview.visible=false; btnApply.text="Показать файлы и потерянные ссылки"
        lblEffect.text="Чтение без изменений. Материалы не заменяются. UDIM-последовательности и закрытые плагины могут потребовать отдельной проверки."
      )
      #density:
      (
        lblTask.text=if AGRWB_Core.profile=="NPM" then "Ground · диагностика плотности текстуры" else "Измерить плотность текстуры"
        description.text=if AGRWB_Core.profile=="NPM" then "Зачем: оценить детализацию текстуры поверхности рельефа. К НПМ здания это требование не относится.\r\nЧто выбрать: только поверхность Ground; исключите ОКС, растения и элементы благоустройства.\r\nТекущее измерение выдаёт px/м. Оно НЕ проверяет норму Ground в px/м². Нормативная проверка ещё не встроена." else "Зачем: узнать, сколько пикселей текстуры приходится на метр поверхности ВПМ.\r\nЧто выбрать: объекты с UV1 и одинаковым размером квадратной текстуры.\r\nРезультат: минимум, максимум и среднее по площади. Ничего не изменяется; соответствие нормам автоматически не утверждается."
        lblMap.visible=true; spnMap.visible=true
        chkGround.visible=AGRWB_Core.profile=="NPM"
        btnPreview.visible=false; btnApply.text="Измерить без изменений"
        lblEffect.text="Введите разрешение используемой текстуры. Размер карты и физический размер кирпича — разные параметры."
      )
      #connect:
      (
        lblTask.text="Соединить рёбра (Connect)"
        description.text="Зачем: добавить разрезы в сетку с заданным числом сегментов.\r\nЧто выбрать: один Editable Poly без модификаторов, затем подходящие рёбра в режиме Edge.\r\nРезультат: появятся новые рёбра. После операции проверьте квады и сохранность проёмов."
        lblSegments.visible=true; spnSegments.visible=true
        btnApply.text="Соединить выбранные рёбра"
      )
      #ucx:
      (
        lblTask.text="Создать простую коллизию-бокс"
        description.text="Зачем: сделать невидимый объём столкновений для простой части модели.\r\nЧто выбрать: один Editable Poly и полигоны объёмного участка.\r\nРезультат: новый бокс вокруг этих полигонов. Исходная геометрия не меняется. Бокс закрывает проёмы — это не точная оболочка здания."
        chkAll.visible=true; btnApply.text="Создать бокс коллизии"
        lblEffect.text="После создания бокс выделяется. Через инструмент имён назначьте ему роль UCX. Выпуклая декомпозиция и проверка зазоров ещё не встроены."
      )
      #light:
      (
        lblTask.text="Разместить свет по полигонам"
        description.text="Зачем: расставить однотипные направленные источники в центрах выбранных поверхностей.\r\nЧто выбрать: один Editable Poly и нужные полигоны; ниже укажите FreeSpot-образец.\r\nРезультат: отдельный источник на полигон, направленный по его наружной нормали."
        chkAll.visible=true; btnTemplate.visible=true
        btnApply.text="Создать источники света"
        lblEffect.text="Образец и модель не меняются. Оптимизация количества источников и отдельный Light.fbx пока не встроены."
      )
      #audit:
      (
        lblTask.text="Найти проблемы перед экспортом"
        description.text="Зачем: обнаружить неверные имена, отсутствующие роли, UV, материалы и потерянные файлы карт.\r\nЧто выбрать: объекты, которые собираетесь сдавать.\r\nРезультат: список проблем ниже. Проверка ничего не изменяет."
        btnPreview.visible=false; btnApply.text="Проверить выделенные объекты"
        lblEffect.text="Это частичная проверка. Топология, внешний вид, GeoJSON и полный AGR Checker остаются отдельными проверками."
      )
      #export:
      (
        lblTask.text="Экспортировать выбранные объекты в FBX"
        description.text="Зачем: получить файл модели для передачи.\r\nЧто выбрать: все объекты, которые должны попасть в этот FBX. Имена и роли уже должны быть назначены.\r\nРезультат: новый FBX после проверки подготовки и штатного окна настроек экспорта Max."
        btnApply.text="Выбрать путь и экспортировать…"
        lblEffect.text="Существующий файл не перезаписывается. После экспорта проверьте фактический файл следующим инструментом слева."
      )
      #readback:
      (
        lblTask.text="Проверить сохранённый FBX"
        description.text="Зачем: убедиться, что экспортированный файл действительно читается.\r\nВыделение Max не требуется. Укажите FBX; проверка запустится отдельным Blender.\r\nРезультат: отчёт о мешах, размерах, UV и материалах. Открытая сцена Max не меняется."
        btnReadback.visible=true; btnPreview.visible=false; btnApply.visible=false
        lblEffect.text="Это проверка структуры файла, не подтверждение внешнего вида или полной готовности АГР."
      )
      #copy:
      (
        lblTask.text="Сохранить исходник: создать отдельную версию"
        description.text="Зачем: получить рабочий вариант НПМ или ВПМ, не меняя исходную модель. Этот шаг необязателен.\r\nЧто выбрать: меши, которые хотите дублировать.\r\nРезультат: новые объекты с копиями геометрии и материалов на том же месте; они выделятся автоматически. Дальше работайте с ними."
        btnPreview.visible=false; btnApply.text="Дублировать выделенные объекты"
        lblEffect.text="Исходные объекты остаются видимыми. Инстансы становятся отдельными копиями; файлы текстур на диске не дублируются."
      )
      #pending:
      (
        lblTask.text=pending.SelectedItem as string
        description.text="Этот инструмент найден в исходных скриптах, но ещё не перенесён в единый интерфейс.\r\n\r\nЗдесь будет своя панель с параметрами, проверкой и выполнением. Запуска старого непонятного окна нет. Сейчас эта операция недоступна."
        lblEffect.text="Пункт оставлен видимым, чтобы состав будущей тулзы не терялся. Это не готовый функционал."
        btnPreview.visible=false; btnApply.visible=false
      )
    )
    selectionLabel()
  )
  fn refreshProfile =
  (
    AGRWB_Core.profile=if tabs.SelectedIndex==0 then "NPM" else "VPM"
    local npm=AGRWB_Core.profile=="NPM"
    codes=if npm then #(#names,#uv,#tile,#density,#connect,#textureFiles,#audit,#export,#readback,#copy) else #(#names,#uv,#tile,#materialUV,#density,#connect,#ucx,#hull,#light,#textureFiles,#audit,#export,#readback,#copy)
    menu.Items.Clear()
    local names=if npm then #("Имена для сдачи","Размер рисунка · UV-проекция","Перенос готовых UV в 0–1","Ground · плотность (диагностика)","Соединить рёбра · Connect","Файлы текстур и потерянные ссылки","Проверка перед экспортом","Экспорт выбранного в FBX","Проверить сохранённый FBX","Создать отдельную версию") else #("Имена для сдачи","Размер рисунка · UV-проекция","Перенос готовых UV в UDIM","UV одной отделки → UDIM","Плотность текстуры ВПМ","Соединить рёбра · Connect","Коллизия · простой бокс","Коллизия · выпуклая оболочка","Свет по полигонам","Файлы текстур и потерянные ссылки","Проверка перед экспортом","Экспорт выбранного в FBX","Проверить сохранённый FBX","Создать отдельную версию")
    for s in names do menu.Items.Add s
    pending.Items.Clear()
    local future=if npm then #("Фасадные камеры и сборка атласа","Атлас растительности","Рельеф и покрытия Ground","Облегчение труб","Очистка сетки проёмов","Запекание текстур") else #("Упаковка отделок и текстур UDIM","Декомпозиция UCX и сечения","Сокращение источников света","Повтор операций с полигонами","Импорт GeoJSON и UDIM","Запекание текстур")
    for s in future do pending.Items.Add s
    ddlRole.items=if npm then #("Здание · Main","Стекло · MainGlass","Территория · Ground") else #("Здание · Main","Стекло · MainGlass","Территория · Ground","Коллизии здания · UCX","Коллизии земли · UCX")
    ddlRole.selection=1
    lblIndex.text=if npm then "Номер ОКС:" else "Номер UCX:"
    chkGround.checked=false
    menu.SelectedIndex = -1; pending.SelectedIndex = -1
    showTask #welcome
  )
  fn runCurrent applyChanges =
  (
    local nodes=selection as array
    try
    (
      if nodes.count==0 do throw "Выделите объект в Max."
      local result=""
      undo "AGR Workbench operation" on
      (
        if applyChanges and findItem #(#names,#uv,#tile,#materialUV,#connect,#ucx,#light,#export) currentTask > 0 do
          AGRWB_Tasks.adopt nodes AGRWB_Core.profile
        result=case currentTask of
        (
          #names: if applyChanges then AGRWB_Pipeline.applyNames nodes AGRWB_Core.profile edtStem.text (roleCode()) spnIndex.value else AGRWB_Pipeline.previewNames (AGRWB_Pipeline.planNames nodes AGRWB_Core.profile edtStem.text (roleCode()) spnIndex.value readOnly:true)
          #uv: AGRWB_Tasks.projection nodes chkAll.checked ddlAxis.selection spnMeters.value applyChanges
          #tile: AGRWB_Pipeline.moveUV nodes AGRWB_Core.profile spnTile.value applyChanges
          #materialUV: AGRWB_Extensions.materialUV nodes spnMaterialID.value spnTile.value applyChanges
          #hull: AGRWB_Extensions.convexHull nodes chkAll.checked spnHullVertices.value applyChanges
          #textureFiles: AGRWB_Extensions.textureFiles nodes
          #density:
          (
            if AGRWB_Core.profile=="NPM" and not chkGround.checked do throw "Подтвердите, что выделена только поверхность Ground."
            if AGRWB_Core.profile=="NPM" do for n in nodes where findItem #("Main","MainGlass","UCX_Main","UCX_Ground") (getUserProp n "AGRWB_Role")>0 do throw "Выделено здание, стекло или коллизия. Для этой диагностики НПМ выберите только Ground."
            AGRWB_Core.density nodes spnMap.value
          )
          #connect: AGRWB_Tasks.connectEdges nodes spnSegments.value applyChanges
          #ucx: AGRWB_Tasks.collision nodes chkAll.checked applyChanges
          #light: AGRWB_Tasks.lights nodes chkAll.checked templateLight applyChanges
          #audit: (AGRWB_Pipeline.check nodes AGRWB_Core.profile)[3]
          #copy:
          (
            local made=AGRWB_Core.makeCopies nodes
            select made
            "Создана и выделена отдельная версия: " + made.count as string + " объектов. Исходные объекты сохранены. Теперь инструменты будут работать с новой версией."
          )
          #export:
          (
            if not applyChanges then (AGRWB_Pipeline.check nodes AGRWB_Core.profile)[3]
            else
            (
              local path=getSaveFileName caption:"Экспорт выделенного в новый FBX" types:"FBX (*.fbx)|*.fbx|"
              if path==undefined then "Экспорт отменён." else AGRWB_Core.exportCopies nodes path
            )
          )
          default: "Выберите инструмент слева."
        )
      )
      logMessage result
      selectionLabel()
    )
    catch(logMessage (getCurrentException()))
  )
  on AGRWB_UI open do
  (
    for c in #(description,edtLog) do
    (
      c.Multiline=true; c.WordWrap=true; c.ReadOnly=true
      c.ScrollBars=(dotNetClass "System.Windows.Forms.ScrollBars").Vertical
    )
    for c in #(description,edtLog,menu,pending) do
    (
      c.Font=dotNetObject "System.Drawing.Font" "Segoe UI" 10.0
      c.BackColor=(dotNetClass "System.Drawing.Color").FromArgb 58 58 58
      c.ForeColor=(dotNetClass "System.Drawing.Color").FromArgb 238 238 238
    )
    menu.ItemHeight=25; pending.ItemHeight=24
    menu.IntegralHeight=false; pending.IntegralHeight=false
    tabs.TabPages.Add "НПМ"
    tabs.TabPages.Add "ВПМ"
    refreshProfile()
    selectionTimer.active=true
    logMessage "Выделите объект в Max и выберите инструмент слева. Скрытых сохранённых наборов нет."
  )
  on tabs SelectedIndexChanged sender args do refreshProfile()
  on menu SelectedIndexChanged sender args do (local i=menu.SelectedIndex+1; if i>0 and i<=codes.count do (pending.SelectedIndex = -1; showTask codes[i]))
  on pending SelectedIndexChanged sender args do (if pending.SelectedIndex>=0 do (menu.SelectedIndex = -1; showTask #pending))
  on chkGround changed state do selectionLabel()
  on selectionTimer tick do selectionLabel()
  on btnPreview pressed do runCurrent false
  on btnApply pressed do runCurrent true
  on btnTemplate picked obj do
    if isValidNode obj and classof obj==FreeSpot then templateLight=obj else (templateLight=undefined; btnTemplate.text="Выбрать FreeSpot как образец света"; logMessage "Нужен источник FreeSpot.")
  on btnHelp pressed do shellLaunch (AGRWB_Root+"README.md") ""
  on btnSaveLog pressed do
  (
    local path=getSaveFileName caption:"Сохранить результат" types:"Text (*.txt)|*.txt|"
    if path!=undefined do
    (
      local f=undefined
      try(f=createFile path encoding:#utf8; format "%" edtLog.text to:f; close f)
      catch(if f!=undefined do close f; logMessage (getCurrentException()))
    )
  )
  fn startReadback inputPath exePath =
  (
    if readbackProcess != undefined do throw "Readback already running."
    if not doesFileExist inputPath do throw "FBX not found."
    if not doesFileExist exePath do throw "Blender not found."
    local checker = AGRWB_Root + "check_fbx.py"
    if not doesFileExist checker do throw "check_fbx.py not found."
    readbackReportPath = inputPath + "." + timestamp() as string + ".readback.json"
    local info = dotNetObject "System.Diagnostics.ProcessStartInfo"
    info.FileName = exePath
    info.Arguments = "-b --factory-startup --python \"" + checker + "\" -- --fbx \"" + inputPath + "\" --report \"" + readbackReportPath + "\""
    info.UseShellExecute = false
    info.CreateNoWindow = true
    info.WindowStyle = (dotNetClass "System.Diagnostics.ProcessWindowStyle").Hidden
    local proc = dotNetObject "System.Diagnostics.Process"
    proc.StartInfo = info
    if not (proc.Start()) do throw "Could not start Blender."
    readbackProcess = proc
    btnReadback.enabled = false
    readbackTimer.active = true
    logMessage ("Blender читает FBX. Отчёт: " + readbackReportPath)
    readbackReportPath
  )
  on btnReadback pressed do
  (
    local inputPath = getOpenFileName caption:"Проверить фактический FBX" types:"FBX (*.fbx)|*.fbx|"
    if inputPath != undefined do
    (
      local exePath = (dotNetClass "System.Environment").GetEnvironmentVariable "ProgramFiles"
      exePath += "\\Blender Foundation\\Blender 4.4\\blender.exe"
      if not doesFileExist exePath do exePath = getOpenFileName caption:"Укажите blender.exe" types:"Blender (*.exe)|*.exe|"
      if exePath != undefined do
      (
        try
        (
          startReadback inputPath exePath
        )
        catch (logMessage (getCurrentException()))
      )
    )
  )
  on readbackTimer tick do
  (
    if readbackProcess != undefined and readbackProcess.HasExited do
    (
      readbackTimer.active = false
      btnReadback.enabled = true
      local code = readbackProcess.ExitCode
      readbackProcess.Dispose()
      readbackProcess = undefined
      local f = undefined
      try
      (
        if not doesFileExist readbackReportPath do throw ("No Blender report. Exit code: " + code as string)
        f = openFile readbackReportPath encoding:#utf8
        local ss = stringStream ""
        while not eof f do format "%\n" (readLine f) to:ss
        close f
        f = undefined
        local reportText = ss as string
        local readOK = code == 0 and findString reportText "\"readback_ok\": true" != undefined
        logMessage ((if readOK then "FBX прочитан: меши и координаты доступны. Проверка АГР не выполнена." else "Проверка FBX завершилась с ошибкой. Смотрите отчёт ниже.") + "\r\nОтчёт: " + readbackReportPath + "\r\n\r\n" + reportText)
      )
      catch (if f != undefined do close f; logMessage (getCurrentException()))
    )
  )
)
createDialog AGRWB_UI pos:[120,60]

