# Карта AGR — 06.10.2026

Начало: [STATE](../../STATE.md) → [восемь направлений](TASK_BOARD.md) → один job/операция.
Это карта работы; статус сдачи берётся из job evidence и manual gates.

## Версии

- Published default branch после fetch: `origin/main@7c418f34b74c3669d03ce6a530c366d6894d7a2f`.
- Этот worktree: `codex/project-hygiene-20261006`, та же base; local docs change.
- Primary: `feature/revit-typical-floor@d7ecdfda5f83d0c0ad672a65fc954031fca0cfbc`,
  dirty и активно используется КПП1. Не переносить незавершённые файлы blanket staging.
- Bootstrap docs: `026b1474d314098104a5f3b0592d87dbaeda2f81`, локально.
- Harness: `c4f2f095b1166d9f1d3c78e0de6fa615e7e1c54b`, локально.
- Run evidence: `06ecba51b30be4d23bb0016ed77d77d0349add11`, open PR31.
  Local monitor/global skills не объявляются включёнными в published main.

## Файлы и действия

- [TASK_CONTEXT](../TASK_CONTEXT.md): конкретный маршрут к правилам, коду и QA.
- [Каталог операций](SCRIPT_LIBRARY.md) и [technical library](../../technical_library/GROUP_REVIEW.md).
- [Кейсы](../case_studies/README.md): точная область успеха/неудач/приёмки.
- [Аудит гигиены](HYGIENE_AUDIT_2026-10-06.md) и [chat manifest](CHAT_RETIREMENT_2026-10-06.json).
- [Исторический реестр чатов](CHAT_REGISTER.md), снимки CHAT_AUDIT от29.09/02.10;
  не использовать их старые P-очереди без сверки.
- [GitHub lifecycle](GITHUB_CODEX_WORKFLOW.md): проверки, publication и merge.

## GitHub: проверено native search 06.10

Открыты [PR31](https://github.com/artsafro/AGR_Project/pull/31) и
[PR18](https://github.com/artsafro/AGR_Project/pull/18). PR18 отложен: не review/QA/merge.
PR31 — перенос inspector; его QA не переносится на другой head, merge не выполнен.
Issues [6](https://github.com/artsafro/AGR_Project/issues/6),
[7](https://github.com/artsafro/AGR_Project/issues/7),
[10](https://github.com/artsafro/AGR_Project/issues/10),
[11](https://github.com/artsafro/AGR_Project/issues/11),
[12](https://github.com/artsafro/AGR_Project/issues/12),
[13](https://github.com/artsafro/AGR_Project/issues/13),
[14](https://github.com/artsafro/AGR_Project/issues/14) открыты.
Hosted CI и billing в этом аудите заново не проверялись. `gh` CLI вернул401;
native connector дал список PR/Issues. Никаких remote writes в этом этапе.

## Сохранность

Ignored blend/FBX/PNG не восстанавливаются из Git. Issue6 сохраняет запрет загрузки
около4ГБ outputs в GitHub. Архивы и recovery receipts03.10 остаются локально;
текущий аудит не повторяет cleanup. Original/approved/unknown/active retain.
Исходная карта доступна как `7c418f34b74c3669d03ce6a530c366d6894d7a2f:docs/organization/PROJECT_MAP.md`,
blob `cd25ef40a98b2fcf632a2d46f27328978c49cc64`; это история, а не текущая очередь.
