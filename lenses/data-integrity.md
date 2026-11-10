# Data-integrity lens

Review the diff for ways stored or exchanged data can become wrong, lost or inconsistent.

## Look for

- Migrations: irreversible or destructive steps, missing backfill, locking a large table, new NOT NULL column without a default, dropped column still read by code.
- Partial writes: multi-step updates without a transaction, writes to two stores that can diverge, work done before validation.
- Transactions: wrong isolation or scope, commit before all steps succeed, missing rollback on error, non-idempotent retries creating duplicates.
- Nullability and constraints: code assuming non-null where the schema allows null (or the reverse), missing unique or foreign-key constraints for invariants the code relies on.
- Serialization contracts: JSON, protobuf, CSV or file formats whose field names, types, units, enums or date formats changed without updating readers, writers or stored data.
- Lossy conversions: truncation, float for money, time zone loss, encoding changes, silent default fill.
- Cache or derived data not invalidated when its source changes.

## How to check

- Compare the schema change against every reader and writer of the affected fields.
- Ask what state remains if the process dies halfway through.

## Ignore

- Read-only code paths with no stored state.
- Performance of migrations unless they risk long locks or outages.
- Naming or formatting of schema files.

## Category

Emits `data-integrity`. Typical severity: P0 for data loss or corruption, P1 for wrong or inconsistent data and broken serialization contracts.
