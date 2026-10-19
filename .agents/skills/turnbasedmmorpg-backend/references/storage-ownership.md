# TurnBasedMMORPG Hybrid Persistence

Use this skill before changing persistence boundaries between PostgreSQL and
MongoDB.

## Core Rule

PostgreSQL remains the source of truth. MongoDB stores heavy, flexible,
document-shaped data that must evolve without repeated SQL migrations.

Do not make MongoDB the authority for game-critical facts such as account
ownership, character ownership, inventory, currency, rewards, combat result,
progression, permissions, or membership.

## Authority, Checkpoint & Rebuild Matrix (SG10-K3)

| Storage Layer | Authority & Lifecycle Role | Checkpoint & Rebuild Behavior |
| --- | --- | --- |
| **PostgreSQL (`tbmmorpg_game`)** | **Durable Authority** for characters, inventory items, progression, economy, and combat finalization metadata. | Permanent source of truth. Checkpoints hot runtime state; target of rehydration and restore drills. |
| **RedisJSON (`game:ac:*`, `combat:rbc:*`)** | **Hot Runtime Authority** during active gameplay sessions and live combat. | Mutations to `game:ac:*` must call `mark_dirty(char_id, reason=..., paths=...)`, which updates and tracks `sync_dirty.generation`. `ActiveCharacterDirtySyncMiddleware` and ARQ sync tasks flush dirty state to PostgreSQL and clear `sync_dirty` only when `generation` matches. On crash/reconnect, active session is rehydrated from PostgreSQL. |
| **MongoDB (`tbmmorpg_analytics`)** | **Durable Document Store** for combat finalization payloads, battle logs, simulation traces, and chat message buckets. | Use stable IDs/pointers such as `combat_id` or `mongo_document_id` according to the owning document contract. Version new persisted payload contracts explicitly; inspect existing schemas rather than assuming every document already has a `schema_version`. |

## PostgreSQL Owns

Keep stable facts, relationships, and fast indexes in PostgreSQL:

- Entity ids and ownership.
- Access control and memberships.
- Short list/search fields.
- Foreign-key-like relationships.
- Lifecycle status.
- Processing status for Mongo writes.
- Timestamps used for ordering.
- Pointers to Mongo documents.
- Small summaries needed by pages, dashboards, and workers.

Examples:

```text
combat_id
status
battle_type
location_id
winner_team
participant_char_ids
started_at
finished_at
mongo_document_id
mongo_status
mongo_stored_at
schema_version
```

## MongoDB Owns

Put heavy, flexible, nested, or high-variance payloads in MongoDB:

- Combat full analytics documents.
- Combat runtime/debug traces.
- Chat message bodies and long history.
- Generated content payloads.
- Simulation result documents.
- Dynamic monster configuration documents.
- Audit/event bodies when the event stream is large or schema-changing.

Mongo documents must include:

```text
schema_version
document_kind
stable foreign id from PostgreSQL, such as combat_id or thread_id
created_at / updated_at where relevant
```

## Avoid Repeated Metadata

Do not copy the same metadata into every nested event or message when it can
live once at document or thread level.

Use semantic local keys inside Mongo documents. Keep full participant metadata
once, then refer to it from nested events by compact keys.

Correct combat shape:

```json
{
  "combat_id": "combat_1",
  "document_kind": "combat_battle_log",
  "schema_version": 1,
  "meta": {
    "battle_type": "rift",
    "location_id": "forest_01"
  },
  "participants": {
    "p1": {
      "actor_id": "123",
      "type": "player",
      "team": "players"
    },
    "m1": {
      "actor_id": "wolf_7",
      "type": "monster",
      "team": "enemies"
    }
  },
  "events": [
    {
      "t": 1,
      "seq": 1,
      "s": "p1",
      "d": "m1",
      "a": "slash",
      "o": "hit",
      "dmg": 10
    }
  ]
}
```

Avoid this shape:

```json
{
  "events": [
    {
      "combat_id": "combat_1",
      "battle_type": "rift",
      "location_id": "forest_01",
      "source_actor_id": "123",
      "source_actor_type": "player",
      "source_actor_team": "players",
      "target_actor_id": "wolf_7",
      "target_actor_type": "monster",
      "target_actor_team": "enemies",
      "damage": 10
    }
  ]
}
```
