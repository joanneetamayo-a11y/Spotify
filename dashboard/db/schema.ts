import { text, sqliteTable } from 'drizzle-orm/sqlite-core';
export const snapshots = sqliteTable('snapshots', {
  id: text('id').primaryKey(),
  payload: text('payload').notNull(),
  sourceHash: text('source_hash').notNull(),
  updatedAt: text('updated_at').notNull(),
});
