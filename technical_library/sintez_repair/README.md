# SINTEZ: исправление пакета Гарибальди

Один case adapter объединяет собственные `repair.py`, `native_qa.py` и `finish.py`
от 13.10.2026 в два этапа: **repair → отдельный readback**. Это конкретный сохранённый
Garibaldi_22, не общий исправитель моделей. Код не содержит SINTEZ addon, моделей,
текстур, ZIP и временных вариантов.

`garibaldi.json` отделяет объектные имена, ожидаемые 6 mesh signatures, 17 текстур,
3 FBX, 44 native группы, исходный SHA256 и pin установленного addon. Код района0707
обоснован native district check именно этого объекта; это не новая норма для других
объектов. Геометрия, UV, material slots и матрицы не меняются. Перегенерируются FBX
и имена коллекций/пакета; сохранённый .blend остаётся новым файлом.

## Зависимости и запуск

Проверено Blender **4.4.0**, SINTEZ AGR Checker **1.6.1**. Установите addon и его
зависимости штатным способом отдельно, укажите каталог `sintez_agr_checker` и
каталог dependencies `site-packages`. Пакет ничего не устанавливает и не меняет
настройки Blender. Pin охватывает относительные пути и SHA256 `.py`, `.csv`,
`.toml`, `.json`, `.geojson`; несовпадение требует отдельной проверки версии и
явного нового конфига. Не подменяйте pin только ради прохождения.

Каждая команда запускает **новый background процесс** с factory startup. Используется
минимальная регистрация восьми property classes addon, не UI register. Активная
пользовательская сцена не затрагивается. Input — сохранённый `source_snapshot.blend`
с SHA256 из JSON; отсутствующий исторический ZIP для этого маршрута не требуется.
Пути задаёт вызывающий агент. Например, в PowerShell:

```powershell
$blender = '<Blender 4.4>/blender.exe'
$addon = '<installed extension>/sintez_agr_checker'
$deps = '<installed extension dependencies>/site-packages'
$config = 'technical_library/sintez_repair/garibaldi.json'
$script = 'technical_library/sintez_repair/repair.py'
& $blender --background --factory-startup --python-exit-code 1 --python $script -- repair --config $config --input '<local source_snapshot.blend>' --output '<new local repair directory>' --addon $addon --dependencies $deps
& $blender --background --factory-startup --python-exit-code 1 --python $script -- readback --config $config --input '<new local repair directory>/repaired.blend' --package-root '<new local repair directory>' --output '<new local QA directory>' --addon $addon --dependencies $deps
```

Каталоги output должны **не существовать**; существующие результаты и пересечения
с входами отклоняются. При неудаче частичный новый output остаётся для диагностики;
повтор запускайте в следующем новом каталоге. Удаление/перезапись не выполняется.
Все проверки используют явные исключения, работающие и при `python -O`.
`readback` пишет только в производный package-root (распаковка/checker logs) и новый
QA output. Не направляйте его в approved каталог. ZIP содержит 3 FBX, папка `maps`
рядом с ZIP обязательна для native импорта; один ZIP не является self-contained delivery.

## Текущее расхождение и подтверждение

Исторический source ZIP теперь доступен по сохранённому пути: SHA256 и CRC
совпадают с исходным receipt. Corrected ZIP по сохранённому пути по-прежнему
отсутствует. Прежняя недоступность source ZIP оказалась ошибкой чтения UTF-8
манифеста через системную cp1251: получался другой кириллический путь. Всегда
используйте `read_text(encoding="utf8")`. Причина отсутствия corrected ZIP неизвестна.
Исторический final `.blend` совпадает с сохранённым SHA256, snapshot и извлечённые
FBX/maps сохранены. Архив восстановлен **новым экспортом** из pinned snapshot;
это новый производный пакет, не побайтно восстановленный исторический ZIP.

15.10.2026 отдельно запущены repair и native readback. Сохранённый blend и повторно
импортированный ZIP дали те же 6 signatures (координаты/топология/material indices/
UV/matrix/material slots), что исторический маршрут, и те же17 packed texture hashes.
Полный native checker вернул44 группы без errors. Компактные hashes — `QA.json`;
подробные локальные логи/модели сохранены в task evidence и не публикуются.
Эти gates не доказывают эквивалентность всех настроек/рендера сцены.

**Отдельно остаются:**28 manual checks, УКЭП, пользовательская визуальная приёмка
и полная сдача. Исторические44/44 auto checks не превращаются в72/72. UI stale
texture_sets обновлялся в исходной операции; новый маршрут выполняет полный native
import/check, не переносит stale UI counters. Addon рекомендуется УКЭП; код не
подписывает пакет и не снимает рекомендацию. Универсальность на втором объекте
не проверена. Исходный ZIP заново прочитан без изменения.
