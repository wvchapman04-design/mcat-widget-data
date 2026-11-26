# mcat-widget-data

Stats feed for a personal study widget. `status.json` is refreshed hourly from the MCAT Mastery game by a scheduled task: streak, mastery % per section, next topic. It holds aggregate numbers only.

- `gen.py` builds `status.json` from a saved game state.
- `topics.json` maps topic ids to names.
