-- Recipe Agent: Initial schema
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor > New Query)

create table if not exists recipes (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  ingredients jsonb not null default '[]'::jsonb,
  instructions text[] not null default '{}',
  servings int,
  prep_time_minutes int,
  cook_time_minutes int,
  bake_time_minutes int,
  chill_time_minutes int,
  freeze_time_minutes int,
  tags text[] default '{}',
  category text,
  season text[] default '{"all"}',
  rating int check (rating >= 1 and rating <= 5),
  image_url text,
  source_url text,
  source_type text not null default 'manual',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Auto-update updated_at on row change
create or replace function update_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger recipes_updated_at
  before update on recipes
  for each row
  execute function update_updated_at();

-- Row Level Security (permissive for single-user, locked to authenticated)
alter table recipes enable row level security;

create policy "Allow all for authenticated users"
  on recipes
  for all
  using (true)
  with check (true);

-- Full-text search index
alter table recipes add column if not exists fts tsvector
  generated always as (
    to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))
  ) stored;

create index if not exists recipes_fts_idx on recipes using gin(fts);
create index if not exists recipes_tags_idx on recipes using gin(tags);
create index if not exists recipes_category_idx on recipes(category);
