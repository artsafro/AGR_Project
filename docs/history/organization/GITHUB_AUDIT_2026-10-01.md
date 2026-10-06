# Аудит GitHub — 01.10.2026

Снимок exact `main` до ремедиации: `a99b8ec`. Репозиторий private; аудит
выполнен через GitHub REST/GraphQL и отдельный checkout.

## Подтверждено

- Новый чистый venv: `pip install -e .[dev]`, `pip check`, CLI, profiles3,
  schemas8 и pytest156passed/1skipped/1expected warning — OK.
- `pip-audit` для прямых и разрешённых транзитивных зависимостей: известных
  уязвимостей не найдено.
- Высокоточные шаблоны токенов/private keys в текущем tree и Git history: 0.
- Из16 PR слиты15; единственный открытый PR #18 отложен пользователем.

## Найдено

1. Последние100 Actions runs завершились `startup_failure` до jobs: hosted CI
   отсутствует, хотя локальная чистая установка проходит.
2. `main` не защищён; ruleset/protection API недоступен для текущего аккаунта.
3. Actions разрешены без ограничения, SHA pinning не требовался, workflow
   создавал дублирующие push/pull_request runs.
4. GitHub community health28%: отсутствовали SECURITY/CONTRIBUTING/license,
   CODEOWNERS, шаблоны и Dependabot config.
5. Все16 PR имели0 reviews,0 review threads и0 labels.
6. После15 merge head-ветки сохранялись; `delete_branch_on_merge=false`.
7. `PROJECT_MAP` и `SCRIPT_LIBRARY` отстали от `main`; TASK_CONTEXT и
   AGENT_WORKFLOW отсутствовали; четыре ссылки вели в ignored outputs.
8. Security alerts API не дал доказательства: Dependabot/code scanning —403,
   secret scanning —404. Это не интерпретируется как ноль alerts.
9. Один нормативный PDF занимает24 861 066 из27 161 682 tracked bytes; LFS не
   используется. Пятнадцать tracked-файлов содержат персональные абсолютные пути.

## Ремедиация этого этапа

- workflow ограничен `main` push и PR, получил concurrency, read-only permission,
  timeout, pip cache/check и pin официальных Actions по exact SHA;
- добавлены governance/security/templates/dependabot и маршруты агента;
- актуализированы карта и библиотека операций, исправлены ссылки на outputs;
- настройки GitHub, labels, branch cleanup и фактический run проверяются после
  слияния PR с этой правкой.

Native DCC, модели и PR #18 этим аудитом не изменяются. Local QA, hosted CI,
пользовательская приёмка и delivery остаются отдельными статусами.
