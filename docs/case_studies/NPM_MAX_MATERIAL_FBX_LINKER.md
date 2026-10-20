# NPM: Blender FBX → Standard Legacy в 3ds Max

## Оценка и область

16.10.2026 пользователь: «Вроде скрипт работает, я затестил».
Это частичное подтверждение ранней версии на его открытой сцене, с прямо
указанными недостатками Metallic/Environment и повторяющихся M_Glass_01.
Хеш запущенного пользователем экземпляра не зафиксирован; полная приёмка,
последующий FBX pipeline и последняя версия UI этим высказыванием не подтверждены.

## Задача и входы

11 основных ОКС и пять glass mesh, Blender FBX в Max 2024.2.5. Пользователь
попросил самостоятельный drag-and-drop `.ms`: рекурсивные T_ наборы по имени
объекта, новые Standard Legacy, direct Bitmap, правильные имена/Texture mode,
отдельная нумерация glass mesh, затем source FBX inventory JSON и обратный экспорт.
Итоговый код/запуск: [NPM Texture Linker](../../technical_library/max_texture_linker/README.md).
Источники FBX логики прочитаны в Заводе, не изменены. Нормы и geometry не менялись.

## Что сработало и исправления

- Полный ключ объекта защищает от смешивания соседних ОКС. Неоднозначный канал
  пропускает объект, отсутствующий канал остаётся пустым; source mesh не меняется.
- Standard Legacy создаётся заново, старые настройки не переносятся. На один
  непрозрачный ключ один новый material; старые одноимённые refs заменяются.
- Max автоматически ставит Environment при подключении Reflection. Поэтому
  Texture нужно выставлять **после** подключения; native readback обязателен.
- Пользователь изменил исходное glass правило: вместо сохранения общего материала
  нужны отдельные M_Glass_01/02/... по natural object-name order. Другие параметры
  копируются, maps отключаются, opacity50. Обычный shared material нельзя
  заменять глобально из-за одного mesh MainGlass.
- Из Завода перенесена идея FBX→JSON membership, а не destructive prepare/weld.
  Встроенный stdlib reader исключает внешний Python launcher/quoting и line JSON parser.
  Новая папка для JSON+FBX сохраняет originals; source SHA и strict matching защищают
  от устаревшего состава и частичного экспорта. Cleanup только на временных копиях.

## Проверки и доказательства

[QA](../../technical_library/max_texture_linker/QA.md): 329 Python tests passed,
3 skipped; 39 native assertions passed, включая Undo, glass shared-material regression,
FBX export/native import/world bounds, source CA и настройки/selection.
Все private/full receipts остаются в local-only `tmp/max-texture-linker-*`.
Ранние fixture ошибки сохранены в log; после roundtrip fixture надо создавать
в новом run-folder, иначе extracted .fbm загрязняет повторный texture scan.

Это один реальный пользовательский кейс и синтетические контрпримеры, не
второй проект и не доказательство полной сдачи НПМ. Проверка кандидатов JSON
охватывает binary7400/naming; triangle budget, UV и координаты отдельно.
Последний рабочий пакет/полный AGR Checker и пользовательская финальная приёмка pending.

## Повторение и сохранение

Runtime — один `.ms`, embedded Python не требует внешних файлов. Разработчику
оставлены reader, embed builder и тесты; все находятся в технической библиотеке.
Воспроизведение и native команда — в README/QA. Повторять в новой output папке;
originals не перезаписывать. Сохранено как scoped script, новый Skill не создавался.
Git: local branch `codex/max-texture-linker-20261016`, исходные commits `59fbef2` / `9a4e3c2`;
исходный этап локальный. Перенос 17.10 в отдельный draft PR разрешён общим
chat-learning loop; новая ветка `codex/chat-learning-linker-20261017`. Merge не выполняется.
Свежие хеши/QA: [TRANSFER_QA.json](../../technical_library/max_texture_linker/TRANSFER_QA.json).
