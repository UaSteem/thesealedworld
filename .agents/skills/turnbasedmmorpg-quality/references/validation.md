# TurnBasedMMORPG Quality Gate

Read [check commands](check-commands.md) for available commands. Choose checks by changed behavior and risk; report exact commands and results. Start with focused tests, and use the broader gate when required or proportionate. Documentation-only skill changes need structural and link checks.

`tools/dev/check.py` delegates its base checks to `codex_core.dev.check_runner.BaseCheckRunner` and adds fixture validation and a MkDocs build. The current script references a machine-specific external `codex-core` path. Do not assert the base runner's exact steps or a successful full gate without inspecting that dependency in the active environment and executing the command.

Do not invent flags or claim a skipped check passed. If a command cannot run, report the reason and the focused checks that did run.
