# Digital Twin AI

Принятый пользователем реальный пример: [типовой этаж Обр22 — технология, скрипты,
математика и выводы](docs/case_studies/OBR22_ACCEPTED_WORKFLOW.md).

Работающий первый срез подготовки НПМ/ВПМ на **синтетическом** примере.
Он создаёт атлас, карты Diffuse/ERM/Normal и UV/UDIM из общего реестра,
экспортирует FBX через Blender и повторно проверяет файлы из ZIP.
Официальную сдачу и соответствие реального ОКС этот пример не подтверждает.

## Запуск

Python 3.11+ (проверено на Windows, Python 3.12). Команды выполняются из корня
checkout. Нужен интернет для первой установки зависимостей.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e '.[dev]'
.venv\Scripts\dt.exe --help
.venv\Scripts\dt.exe profiles check
.venv\Scripts\dt.exe schemas --check
.venv\Scripts\python.exe -m pytest -q
```

В этой рабочей папке `.venv` уже установлено. На Linux команды находятся в
`.venv/bin/python` и `.venv/bin/dt`. Нужны файлы `standards/` из репозитория;
установка wheel без исходных стандартов пока не является поддержанным режимом.

Сборка независимого ядра:

```powershell
.venv\Scripts\dt.exe build --job jobs/SYNTH-001/project.json
```

Экспорт и проверка в настоящем Blender (проверено на 4.4.0):

```powershell
.venv\Scripts\dt.exe build --job jobs/SYNTH-001/project.json --blender 'C:\Program Files\Blender Foundation\Blender 4.4\blender.exe'
.venv\Scripts\dt.exe validate --archive jobs/SYNTH-001/outputs/development_bundle.zip --blender 'C:\Program Files\Blender Foundation\Blender 4.4\blender.exe'
$env:DT_BLENDER = 'C:\Program Files\Blender Foundation\Blender 4.4\blender.exe'
.venv\Scripts\python.exe -m pytest -q
```

`DT_BLENDER` или `--blender` запускает отдельные фоновые процессы. Открытые сцены
пользователя не используются. Без Blender C004 явно получает `not_run`, DCC-тест
пропускается. `validate` возвращает 1 при ошибке, 2 при неполной технической
проверке, 0 при успешной технической проверке. Ни один код выхода не означает
официальную приёмку: поле `passed` всегда false в этой версии.

Индекс исходного PDF:

```powershell
.venv\Scripts\dt.exe index-pdf --source 'standards/source/Rasporyajenies19012026trebovaniya(2).pdf' --output jobs/SYNTH-001/outputs/pdf-index
.venv\Scripts\dt.exe inspect --manifest jobs/SYNTH-001/project.json
```

## Что создаётся

В `jobs/SYNTH-001/outputs/`:

- `npm/`: RGB-атлас 512×512; при Blender — FBX со встроенным PNG и editable blend.
- `vpm/`: две плитки 1001/1002, на каждой Diffuse/ERM/Normal 2048×2048;
  при Blender — FBX без внешних путей текстур и editable blend с геометрией/UV.
  В ВПМ blend карты на этом этапе не подключены: именованные PNG идут отдельно.
- `layout.json`: stable surface IDs, участки атласа, экспортный slot и UDIM.
- `development_bundle.zip`: пакет разработки со снимком задания, картами, UV
  и FBX, если задан DCC. **Не нормативный ZIP для сдачи.**
- `report.json`, `report.html`: технические проверки C001–C004 и явные
  not_run/review для полного списка V001–V017.
- `dcc-roundtrip.json`: фактическое чтение обоих FBX из ZIP, только при Blender.
- `changes.json`: изменённые/неизменные/удалённые компоненты по хешам.
- `pdf-index/`: текст 56 страниц, вложенные изображения, страницы и source hash.

На тестовом кубе: 6 поверхностей, 12 треугольников, 2 материала реестра,
1 экспортный материал на ветку, 1 UV-канал, 2 UDIM-плитки. Все размеры и цвета
явно вымышлены для теста в `fixture-definition.json`. Географические координаты
и отметка нуля не выдумываются: поля остаются неизвестными.

## Архитектура и состояние

- `STATE.md` — точка продолжения и результаты проверок.
- `docs/DIGITAL_TWIN_AI_PROJECT_BRIEF.md` — исходный производственный цикл.
- `standards/` — исходные YAML, PDF, контрольные суммы и `traceability.json`.
- `docs/traceability.html` — 232 строки «правило → страницы/пункт → метод/статус».
- `docs/decisions/` — область примера, 12 расхождений/пробелов, решения контрактов.
- `schemas/` — 7 JSON Schema; модели и межполевые проверки — `src/dt_ai/core/models.py`.
- `src/dt_ai/` — CLI, профили, реестр, индексатор PDF, карты, UV, упаковка, проверки.
- `adapters/` — работающий Blender-мост и описания будущих Max/Revit/CAD адаптеров.
- `tests/` — риски контрактов, ERM/normal, UV/UDIM, изменения материалов, ZIP и DCC.

Изменение только diffuse одного материала сохраняет остальные PNG/UV.
`registry merge` сохраняет утверждённые записи и выделяет конфликтующее предложение:

```powershell
.venv\Scripts\dt.exe registry merge --current current.json --proposal proposed.json --output merged.json
```

Утверждённые входы не перезаписываются генератором. Состав/хеш входов фиксирован
в manifest. Экспорт JSON Schema: `dt schemas`; проверка дрейфа: `dt schemas --check`.

## Границы результата

DT-001 и основа DT-003 реализованы. DT-002: все поля исходных профилей имеют
трассировку, исходник прочитан, пробелы/расхождения записаны; исчерпывающий
нормативный валидатор не готов. DT-010: страницы/текст/изображения, без OCR и
семантики альбомов. DT-011: утверждённый файловый реестр и сохранение конфликтов.
DT-012–014: технический срез карт/UV/FBX и отчёт изменений на синтетическом body.

Следующее после инвентаризации: INT-001 — проверка покрытия существующего
SINTEZ AGR Checker и адаптер findings для DT-020/021. Реализовывать собственные
проверки только для подтверждённых пробелов; спорные нормы остаются открытыми.
[Каталог инструментов](docs/inventory/catalog.html),
[план интеграции](docs/inventory/INTEGRATION_PLAN.md),
[карта НПМ/ВПМ](docs/inventory/NPM_VPM_MAP.md).
Для пилота нужны FBX, альбом фасадов, DWG/СПОЗУ, система координат и отметка нуля,
образец принимаемого GeoJSON/пакета и дополнительное ТЗ заказчика.

Context7 использован для Pydantic v2. Встроенное MCP-подключение текущей задачи
возвращало ошибку старого API-ключа; документация получена прямыми MCP-вызовами
официального `https://mcp.context7.com/mcp` без ключа.
