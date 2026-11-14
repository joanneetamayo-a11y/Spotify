CREATE TABLE `snapshots` (
	`id` text PRIMARY KEY NOT NULL,
	`payload` text NOT NULL,
	`source_hash` text NOT NULL,
	`updated_at` text NOT NULL
);
