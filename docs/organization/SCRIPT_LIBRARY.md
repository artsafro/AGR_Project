# Каталог сценариев

## Декор трубы: воспроизведение решётки

[Node.js сценарий](../../technical_library/mesh_audit/pipe_lattice/README.md):
один проверяемый вход → профиль/рисунок → квады → сравнение с reference.
[Кейс и приёмка](../case_studies/PIPE_DECOR_LATTICE.md): принята сборка со стойками,
но исходник генератора стоек ещё не найден. Не распространять приёмку на текстуру.

Полная навигация по компактным пакетам: [техническая библиотека](../../technical_library/README.md).
Сначала выбирайте существующую операцию; временные версии и модели в этот каталог не входят.

## NPM: материалы Max и FBX по исходному составу

[NPM Texture Linker](../../technical_library/max_texture_linker/README.md) — один
автономный MAXScript для подключения найденных T_ карт, новых Standard Legacy,
отдельных M_Glass и экспорта по проверенному source-FBX JSON. Python reader и
embed builder оставлены для разработки; отдельный runtime Python не требуется.

[Область проверки и ограничения](../../technical_library/max_texture_linker/QA.md) ·
[Кейс и точная пользовательская оценка](../case_studies/NPM_MAX_MATERIAL_FBX_LINKER.md).
Один реальный кейс и синтетический roundtrip не доказывают универсальность или
полную приёмку НПМ. Актуальная сцена пользователя не запускается при переносе.

## Blender4.4: Sharp и Smooth by Angle

[Сценарий в mesh_audit](../../technical_library/mesh_audit/SMOOTHING.md):
один CLI, защита входов, проверка saved output и исторического reference.
Один16mesh-кейс; visual/user/fullAGR остаются pending.
