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
