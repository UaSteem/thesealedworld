# Integrations

Frontend/site взаимодействует с game backend через typed HTTP clients under:

```text
src/frontend/integrations/backend_api/
```

Frontend code не импортирует backend feature internals напрямую.

## Site-To-Game Calls

Site-owned routes и game-facing frontend features используют backend API clients
для game-backed данных и действий.

Правила:

- outbound requests к backend/game добавляют configured internal service key;
- game lobby bootstrap/select/create/release/delete проходят через backend API;
- game-token cookies используются для game action routes;
- site auth не проксируется в backend как site-auth API;
- game-backed UI должен уметь показать unavailable/maintenance state, если
  backend недоступен.

## Game Tokens

Frontend хранит game token state отдельно от site auth token state:

```text
tbmmorpg_game_access_token
tbmmorpg_game_refresh_token
```

Game-token flow используется после выбора или создания персонажа. Backend
проверяет `character_id` scope на игровых action routes.

## Combat report in the persistent chat area

`GET /game/combat/report?char_id=…&page=…` authenticates the frontend user and
reads a typed `CombatLogDTO` through `BackendCombatApi.logs`, using the game
access token. Page size is fixed at eight exchange groups. Backend character
ownership authorization remains mandatory.

The persistent overlay owns a separate battle report model, outside chat
channels, sending, message history and storage. Session fragments expose the
current battle ID and active state on `game-session-root`. A replaced fragment
updates lifecycle without replacing the overlay or its WebSocket. Active
battles refresh an authoritative page every three seconds; network reconnect
and realtime reconnect reconcile it again. Responses are guarded by character,
battle ID and request generation. Snapshots replace a page, never append page 1.

The selected chat tab is preserved. Only the battle tab hides message input.
The final report stays available during subsequent screens until the next
battle or character context change; it is in-memory and does not survive reload.
Pagination preserves the selected page and scroll on refresh, with automatic
scroll only when already at the bottom. The report renders text through
`x-text` from typed facts for both live and historical pages. Historical
narrative is excluded; absent historical facts cannot be recovered from text.

## Library And Public Game Data

Library/cabinet/ranking pages may read game data through backend APIs or future
site-owned projections. До отдельного решения такие страницы должны оставаться
за integration boundary и не импортировать backend internals.
