# Точное увеличение ×2 и TIFF

Сценарий сохраняет выполненную операцию ImageMagick: `-filter Lanczos -resize
200% -compress LZW`. Это обычная интерполяция, без нейросетевой дорисовки.
Он не использует растеризацию материалов/атласов соседних модулей: входом служат
целые изображения, выходом — TIFF и локальный отчёт проверки.

Зависимости: Python 3.11+, Pillow из зависимостей проекта, установленный ImageMagick.
Проверенный исполнитель — ImageMagick 7.1.2-31 Q16-HDRI x64. Сценарий ограничен
однокадровыми RGB 8-bit sRGB JPG/PNG/TIFF; альфа, CMYK, 16-bit и многокадровые
файлы не поддерживаются. Исходники с такими свойствами отклоняются до записи.

```powershell
python technical_library/texture_tiles/resize_tiff.py --source <absolute-input-directory> --output <absolute-new-directory> --magick <absolute-magick.exe> --reference <absolute-historical-TIFF-directory>
```

Родитель output должен существовать; output должен быть новым, вне source и
reference, без компонента пути `approved`. Существующие файлы не перезаписываются.
Обход только верхнего уровня и разрешённых расширений; ZIP не является входом.
Столкновения имён без учёта регистра, symbolic links и неподдерживаемые режимы входа
отклоняются. Каждому имени соответствует `<stem>_x2.tiff`.

Все входы/эталоны читаются до создания output. После конвертации ImageMagick и
Pillow независимо читают размеры, режим/глубину и TIFF/LZW; SHA256 исходников и
эталонов проверяются до/после всего пакета. ICC profile сохраняется побайтно.
При `--reference` сравниваются все декодированные RGB-пиксели и ICC profile.
Байты TIFF могут отличаться из-за metadata; pixel equality не доказывает визуальную
приёмку, цветиметрическую точность или восстановление потерянных деталей.

Без `--reference` выполняется конвертация/readback, но `reference_replay_passed`
равен `null`. Указанный недоступный эталон — ошибка, не пропуск проверки.
`delivery_passed=false` всегда. Ошибка может оставить новую частичную папку без
успешного `report.json`; не принимать её и не повторять запуск в той же папке.
Локальный отчёт содержит имена/хеши; изображения и отчёт с частными именами
не включать в Git. [Компактный replay QA](RESIZE_TIFF_QA.json).

```powershell
python -m pytest -q tests/test_resize_tiff.py
$env:AGR_TIFF_SOURCE = '<absolute-private-input-directory>'
$env:AGR_TIFF_REFERENCE = '<absolute-private-reference-directory>'
$env:AGR_MAGICK = '<absolute-magick.exe>'
python -m pytest -q tests/test_resize_tiff.py
```

Private replay явно пропускается без локальных входов; это не доказательство
проверки на другом компьютере. Проверен один восьмифайловый пакет, универсальность
на других профилях/битности не заявляется. Пользователь выбрал точное ×2;
последующей визуальной/финальной приёмки в исходном чате нет.
