import {DatabaseSync} from 'node:sqlite';
import {getMigrations} from 'better-auth/db/migration';
import {writeFile} from 'node:fs/promises';
import {authOptions} from './auth.js';
const database=new DatabaseSync(':memory:');
const migration=await getMigrations({...authOptions({LIBRARY:database,AUTH_SECRET:'schema-generation-only-not-a-live-secret',PUBLIC_ORIGIN:'http://localhost:8789'}),database});
await writeFile(new URL('./auth-schema.sql',import.meta.url),await migration.compileMigrations());
database.close();
