-- OpenClaw Persistence Layer (Postgres/Supabase)

create extension if not exists pgcrypto;

create table if not exists agent_profiles (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null unique,
  goals jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists user_preferences (
  id uuid primary key default gen_random_uuid(),
  user_key text not null,
  pref_key text not null,
  pref_value jsonb not null default 'null'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_key, pref_key)
);

create table if not exists projects (
  id uuid primary key default gen_random_uuid(),
  project_key text not null unique,
  title text not null,
  status text not null default 'active',
  summary text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists tasks (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references projects(id) on delete set null,
  title text not null,
  details text,
  task_type text not null default 'one_time', -- one_time|recurring|blocking|dependent
  status text not null default 'open', -- open|in_progress|blocked|done|cancelled
  priority int not null default 3,
  due_at timestamptz,
  recurrence text, -- cron|daily|weekly|custom
  next_run_at timestamptz,
  depends_on_task_id uuid references tasks(id) on delete set null,
  resurfacing_count int not null default 0,
  last_resurfaced_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists idx_tasks_status_due on tasks(status, due_at);
create index if not exists idx_tasks_next_run on tasks(next_run_at);

create table if not exists working_memory_buffers (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  current_sprint jsonb not null default '{}'::jsonb,
  today_tasks jsonb not null default '[]'::jsonb,
  blocking_issues jsonb not null default '[]'::jsonb,
  open_loops jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(agent_name)
);

create table if not exists infrastructure_state (
  id uuid primary key default gen_random_uuid(),
  system_key text not null unique,
  status text not null default 'unknown',
  details jsonb not null default '{}'::jsonb,
  last_checked_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists memory_entries (
  id uuid primary key default gen_random_uuid(),
  scope text not null, -- long_term|session|runbook
  topic text,
  content text not null,
  source_path text,
  source_ref text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_memory_scope_topic on memory_entries(scope, topic);

create table if not exists execution_steps (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  step_type text not null, -- boot|significant_step|shutdown
  summary text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
create index if not exists idx_execution_steps_agent_created on execution_steps(agent_name, created_at desc);

create table if not exists reflections (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  period_type text not null, -- daily|weekly
  period_key text not null,
  wins text,
  misses text,
  carry_forward jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  unique(agent_name, period_type, period_key)
);

create table if not exists self_improvement_log (
  id uuid primary key default gen_random_uuid(),
  agent_name text not null,
  failure text not null,
  lesson text not null,
  upgrade_applied text,
  created_at timestamptz not null default now()
);

create or replace function touch_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end; $$;

drop trigger if exists trg_tasks_updated_at on tasks;
create trigger trg_tasks_updated_at before update on tasks for each row execute function touch_updated_at();

drop trigger if exists trg_projects_updated_at on projects;
create trigger trg_projects_updated_at before update on projects for each row execute function touch_updated_at();

drop trigger if exists trg_prefs_updated_at on user_preferences;
create trigger trg_prefs_updated_at before update on user_preferences for each row execute function touch_updated_at();

drop trigger if exists trg_profiles_updated_at on agent_profiles;
create trigger trg_profiles_updated_at before update on agent_profiles for each row execute function touch_updated_at();

drop trigger if exists trg_buffers_updated_at on working_memory_buffers;
create trigger trg_buffers_updated_at before update on working_memory_buffers for each row execute function touch_updated_at();

drop trigger if exists trg_infra_updated_at on infrastructure_state;
create trigger trg_infra_updated_at before update on infrastructure_state for each row execute function touch_updated_at();
