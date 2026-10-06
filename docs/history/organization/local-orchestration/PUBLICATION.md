## Исправления ревью PR28 — 01.10.2026

Все пять замечаний c61dd0b исправлены; критерии и фактическая QA —
[PR28_FIX_QA.json](../../../organization/local-orchestration/PR28_FIX_QA.json). Nonfinite XYZ/UV отклоняются, matching
ищет полное соответствие, renderer использует selected_mesh_names с одной
камерой/масштабом и сохраняет hidden parent/constraint dependencies. Устранено
обрезание projected bounds и нормализован pixel aspect. Cursor v2 summary
проверяет authoritative ledger/input fingerprint/output hashes; failed/legacy
отказывается до записи. Version probe тоже RunRecord-owned с timeout/treecleanup.
213passed/1skipped/1expectedwarning; profiles3/schemas8OK; SYNTH DCC passed
development only. Actual golden FBX:46objects/5206tris, native readback passed.
Synthetic native render: selected cube, hiddenfar mesh и parent Camera;
четыре actualPNG, scope/camera/scale согласованы, source SHA не изменён.
Independent matching:300 brute-force cases без расхождений; final code gate
без blockers. Native render/real FBX проверил ведущий. Новый real Cursor не
вызывался, legacy004 summaries сохранены. Context7 tools недоступны этой сессии.
Пользователь явно разрешил публикацию исправлений в PR; merge отдельно. Hosted CI остаётся отдельным
статусом; полная сдача модели не заявлена. Следующие сведения исторические.

# Публикация настройки оркестрации — 01.10.2026

Изолированная ветка codex/local-orchestration от main fc48f1a.
Результат: постоянный цикл Codex в AGENTS/AGENT_WORKFLOW, маршруты TASK_CONTEXT,
read-only dt-verifier, протокол RunRecord, узкие local CLI/DCC wrappers и evidence.
Полная сдача модели не является критерием этой настройки.

QA publishing checkout (существующий project venv, PYTHONPATH=this checkout/src):
- pytest178passed/1skipped/1expectedwarning,exit0,14.89s;
- profiles3/sourcehash/traceabilityOK,schemas8OK;
- SYNTH-001 Blender4.4 build/readback exit0,development=true,delivery=false;
- gitdiffcheck,Pythoncompile и JSON readbackOK.
Первый pytest запуск дал49setuperrors из-за отсутствующего tmp parent; родитель
создан, второй запуск прошёл. Первый -m dt_ai.cli был неправильной entrypoint;
фактические успешные profile/schema/build команды использовали -m dt_ai.cli.main.

Реальный OBR22 pilot и Cursor004 были выполнены ранее в основном checkout;
их code/tool/input hashes и области приведены в execution-evidence.json,
cursor-cli-evidence.json, EXECUTION.md и CURSOR_CLI.md. Новая публикационная QA
не считается повторной сертификацией real scene или fulldelivery.

Models/approved scenes/atlases/ZIPs/raw transcripts/session logs находятся только
локально. jobs/*/runs и jobs/*/cli-runs игнорируются Git; compact JSON proofs
публикуются отдельно. Для нового DCC pilot требуются локальные approved inputs,
перечисленные в spec/APPROVED_VERSIONS; свежий Git clone не содержит эти assets.
Логи CLI не восстанавливаются из compact SHA summary. Нормы и approved решения
не менялись; чужие dirty изменения основного checkout не включены. PR18 не затронут.

GitHub publication и hosted CI — отдельные статусы. PR сохранит изменения в
GitHub; включение в main требует merge. Исторический Issue7 фиксирует блокировку
hosted Actions; результаты текущего PR сообщаются отдельно от local QA.

Опубликовано: https://github.com/artsafro/AGR_Project/pull/28 (open, не merged).
Implementation head db371f854e02f1b0885c8b0361fdddc6237705f2 проверен на remote.
Hosted Actions run213 (36882627185) завершился startup_failure до jobs;
это не результат тестов. LocalQA выше пройден. PR18 сохранён без изменений.
