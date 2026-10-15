## Document Size Rule

Use one Mongo document for bounded domain artifacts:

- One combat finalization document.
- One generated monster profile document.
- One simulation run result document.

Use separate Mongo documents for unbounded streams:

- Chat messages.
- Long audit logs.
- World activity feeds.
- Very long event streams.

Do not store an indefinitely growing message list as one array inside a single
thread document. MongoDB documents have a hard size limit, and growing arrays
become hard to query and update.

## Chat Pattern

PostgreSQL should own the thread record and membership indexes.

MongoDB should own message bodies and flexible message metadata.

PostgreSQL example:

```text
chat_thread_id
thread_type
created_at
last_message_at
membership rows
mongo_status
```

Mongo examples:

```json
{
  "thread_id": "thread_1",
  "document_kind": "chat_thread_meta",
  "schema_version": 1,
  "settings": {
    "private": true
  }
}
```

```json
{
  "thread_id": "thread_1",
  "message_id": "msg_100",
  "document_kind": "chat_message",
  "schema_version": 1,
  "sender_id": "user_1",
  "created_at": "2026-06-04T10:00:00Z",
  "body": "message text",
  "attachments": []
}
```

## Combat Analytics Direction

For combat analytics, move heavy JSONB payloads out of PostgreSQL and into
MongoDB:

- `combat_finalizations.finalization`
- `combat_finalizations.analytics`
- large `report` payloads
- large `reward_hooks` payloads when they are not needed for game truth
- runtime/debug traces

Keep or add PostgreSQL columns for:

- fast filtering and list pages
- combat result truth
- reward processing truth
- Mongo document reference and write status
- small summaries required by UI or workers

`combat_exchange_facts` and `combat_balance_rollups` may remain PostgreSQL
read models when they serve fast dashboard queries. Treat them as derived
analytics projections, not as primary raw analytics storage.

## Write Flow

Prefer this flow:

1. Write the official fact to PostgreSQL.
2. Write or enqueue the Mongo document.
3. Record Mongo write status in PostgreSQL.
4. Let retry/backfill repair failed Mongo writes.

If MongoDB is temporarily unavailable, game-critical state must not be lost.
The PostgreSQL row should expose enough status for a retry worker or admin
repair command.

## Repository Boundaries

Put low-level Mongo access under:

```text
src/backend/infrastructure/<domain>/repositories/
```

or shared Mongo connection code under:

```text
src/backend/infrastructure/mongo/
```

Feature services must use feature `integrations/` for semantic operations when
crossing infrastructure boundaries. Do not let runtime services build Mongo
queries or collection names directly.

## Versioning

Every Mongo document needs `schema_version`. Readers must handle known versions
explicitly. Do not add broad fallback behavior that silently hides invalid or
unknown document shapes.
