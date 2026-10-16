# Проверка NPM Texture Linker, 16.10.2026

Base после fetch: `745bc13634b61c54a30c65e8a3ccf6398f8dbb26`.
Ветка: `codex/max-texture-linker-20261016`, владелец кода/Max — root.
Публикация не запрошена: локальная поставка, без push/PR/merge.

## Критерии

- Один автономный `.ms`, русское небольшое окно выбора папки и применения.
- Рекурсивный полный-name match `SM_<key>` / `<key>` → `T_<key>_[drmon]_<n>`.
- Новый Standard Legacy, включая объекты без материала; только найденные карты.
- Прямые Bitmap, имена по stem файла, Texture + explicit UV channel 1.
- Старые одноимённые материалы заменяются, один новый экземпляр на ключ.
- Отдельный M_Glass_01/02/... на каждый mesh, по естественному порядку имён;
  прочие параметры копируются, все карты отключены, opacity 50.
- Неоднозначности пропускаются, ошибка сканирования блокирует назначения.
- Один Undo для назначений, same-name replacement и стекла.

## Текущие доказательства

Начальный read-only анализ реальной сцены Max 2024.2.5: 16 объектов, 11 основных ОКС,
пять объектов стекла. Рекурсивно распознаны 55 файлов, подготовлены 11 новых
материалов без назначения их пользовательским объектам. Итоговый UI открыт
в рабочем Max, все контролы помещаются в 500×420, Export disabled без JSON
прочитано обратно. Собственная кнопка применения в рабочей сцене не нажималась.
Пользователь сообщил, что сам проверил раннюю версию; новые изменения требуют
его повторного прогона. Drag-and-drop мышью самим агентом не проверен.

Итоговый Python: **329 passed / 3 skipped / 1 expected warning**, 15.91s.
Команда: project venv `python -m pytest -q --basetemp=tmp/pytest-max-texture-linker-complete`,
`PYTHONPATH=<worktree>/src`, вне sandbox для Windows process lifecycle test.
Отдельное независимое подтверждение parser/embedding: **56 passed / 1 skipped**.
Ранний sandbox-прогон: 272 passed / 2 skipped / 1 failed. Единственный failure —
`test_timeout_preserves_partial_stdout_and_stderr`, `taskkill returncode=1`;
отдельный повтор вне sandbox: 1 passed. Итоговые skip — DCC Blender и два
Windows symlink/privilege случая (существующий и новый parser fixture).
Profiles: 3 OK; schemas: 8 OK. Полные логи — local-only
`tmp/max-texture-linker-{complete,pytest,timeout}.log`.

Native fixture запускается в отдельном `3dsmaxbatch.exe`, пользовательская сцена
не сбрасывается и не сохраняется. Ранние ошибки fixture: Dictionary требует Name
ключ; глобалы после fileIn нужно объявить до компиляции; массивы нельзя сравнивать
через `==` как структурные; локальный `copy` окружения вернул OK вместо массива.
Fixture исправлен, тестовые критерии не ослаблены. Native тест обнаружил реальный
дефект: присоединение в Reflection само ставит Environment; исправление — Texture
выставляется **после** подключения, проверяется readback всех пяти Bitmap.

Независимые verifier-ы прочитали актуальные код/требования: прежние замечания о
same-name replacement, дублировании новых материалов и вложенном стекле исправлены.
Дополнительный P1: принудительный MainGlass с общим непрозрачным материалом
глобально заменял соседние opaque назначения. Исправлено: глобально заменяются
только настоящие M_Glass, а для остальных меняется только целевой mesh.
Regression прошёл. Восстановление selection независимо от ошибки PopSettings исправлено.

## Итоговый native gate

**39 PASS / ALL CHECKS PASSED**, отдельный Max 2024.2.5 batch, exit 0:
`3dsmaxbatch.exe technical_library/max_texture_linker/test_native.ms -mxsString fixture:yes`.
Receipt: local-only `tmp/max-texture-linker-native/native-result.txt`; exact run:
`tmp/max-texture-linker-native/run_20261016_160039_362/` (свои PNG/исходный FBX/JSON/
output FBX/export_report и отдельный report). Полный log:
`tmp/max-texture-linker-listener-v10.log`, batch summary рядом.

Подтверждены partial/new/shared materials, direct maps и Texture после Reflection,
естественная уникальная нумерация стекла, вложенное и unassigned стекло,
защита opaque shared material, Undo назначений/редактора/стекла, stale guards.
FBX: embedded Python → disk inventory → clean temporary clones → export →
mesh-set/hash report → native re-import двух мешей с исходными именами/world bounds.
CA node/baseObject/modifier/material/map и User Properties сохранены у source;
у повторно импортированных mesh исходные custom data отсутствуют.
Selection, exporter settings, исходный transform и предыдущая Undo-запись сохранены.

Не проверялась принудительная ошибка в середине export/Cancel. Нет проверки
полного профиля НПМ или AGR Checker; JSON `full_npm_verified=false`, экспортный
`verified` относится к mesh membership. Synthetic roundtrip не заменяет проверку
рабочего пакета пользователя. Hosted CI/push/PR/merge не выполнялись.
Пользовательская визуальная приёмка последней версии — pending.
