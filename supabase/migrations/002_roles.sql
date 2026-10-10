-- Least-privilege role for n8n. Run as the database owner.
--
-- FIX: the previous version set the password with
--        alter role n8n_app password :app_password;
--      `:app_password` is a *psql variable* — psql substitutes it client-side
--      before the SQL is ever sent. Any client that does not perform that
--      substitution (the Supabase SQL editor, `supabase db push`, migration
--      runners, pgAdmin, any driver) sends the literal text ":app_password"
--      and the script dies on the very first statement after the DO block:
--        ERROR:  syntax error at or near ":"
--        LINE 1: alter role n8n_app password :app_password;
--      ...which aborts the run before any ALTER FUNCTION / REVOKE / GRANT
--      below it is applied, leaving n8n_app created but completely unprivileged.
--
--      The password is now handled in plain SQL that every client understands.
--
-- USAGE
--   1. Paste the strong password from your secret manager into `app_password`.
--   2. Run this file in any client: Supabase SQL editor, psql, supabase db push.
--
-- If you would rather keep the secret out of the file entirely, leave
-- `app_password` as the CHANGE_ME sentinel: the role and every grant below are
-- still applied, the password step is skipped with a warning, and you can set
-- it out-of-band without the value ever landing in git:
--     psql "$DATABASE_URL" -c "\password n8n_app"

do $$
declare
  -- Paste the strong password from your secret manager between the quotes.
  app_password text := 'CHANGE_ME';
begin
  if not exists (select 1 from pg_roles where rolname = 'n8n_app') then
    create role n8n_app login;
  end if;

  if app_password = 'CHANGE_ME' then
    raise warning
      'n8n_app password not set (app_password is still the CHANGE_ME sentinel). '
      'Role and grants were applied, but n8n cannot authenticate until you run: '
      'psql "$DATABASE_URL" -c "\password n8n_app"';
  else
    -- format(%L) quotes the value as a literal, so quotes and backslashes in
    -- the password cannot break out of the statement.
    execute format('alter role n8n_app password %L', app_password);
  end if;
end $$;

-- Core write paths run with the owner's rights, so n8n never touches stock tables directly.
alter function post_stock_movement(text,bigint,bigint,int,text,text,text,text,boolean) security definer set search_path = public;
alter function post_transfer(text,bigint,bigint,bigint,int,text,text)                 security definer set search_path = public;
alter function record_platform_lines(text,jsonb,bigint,text,text)                      security definer set search_path = public;
alter function trg_enqueue_sync()                                                      security definer set search_path = public;
alter function claim_sync_batch(int)                                                   security definer set search_path = public;
alter function complete_sync(bigint,boolean,text)                                      security definer set search_path = public;
alter function claim_events(int)                                                       security definer set search_path = public;
alter function finish_event(bigint,text,text)                                          security definer set search_path = public;
alter function requeue_stuck_events(int)                                               security definer set search_path = public;

revoke all on all tables in schema public from public;
revoke execute on all functions in schema public from public;

grant usage on schema public to n8n_app;
grant select on products, variants, locations, stock_levels, variant_platform_map,
               platform_connections, v_stock_total, v_low_stock, v_oversold, v_drift to n8n_app;
grant select, insert on platform_events, platform_stock_snapshots to n8n_app;
grant usage on sequence platform_events_id_seq, platform_stock_snapshots_id_seq to n8n_app;
grant execute on function
  post_stock_movement(text,bigint,bigint,int,text,text,text,text,boolean),
  post_transfer(text,bigint,bigint,bigint,int,text,text),
  record_platform_lines(text,jsonb,bigint,text,text),
  claim_sync_batch(int), complete_sync(bigint,boolean,text),
  claim_events(int), finish_event(bigint,text,text), requeue_stuck_events(int)
to n8n_app;
