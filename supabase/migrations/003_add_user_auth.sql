-- Add user ownership and visibility to recipes
-- Enables multi-user with per-user isolation and public sharing

-- Add user_id column (references Supabase auth.users)
alter table recipes add column if not exists user_id uuid references auth.users(id);

-- Add visibility column: 'private' (owner only) or 'public' (all users)
alter table recipes add column if not exists visibility text not null default 'public'
  check (visibility in ('private', 'public'));

-- Assign all existing recipes to the initial user
update recipes set user_id = '21b428a1-1199-449b-9ecb-07d1489b685b' where user_id is null;

-- Make user_id required for future inserts
alter table recipes alter column user_id set not null;

-- Drop the old permissive policy
drop policy if exists "Allow all for authenticated users" on recipes;

-- New RLS policies: user sees own recipes + public recipes from others
create policy "Users can view own recipes"
  on recipes for select
  to authenticated
  using (user_id = auth.uid());

create policy "Users can view public recipes"
  on recipes for select
  to authenticated
  using (visibility = 'public');

create policy "Users can insert own recipes"
  on recipes for insert
  to authenticated
  with check (user_id = auth.uid());

create policy "Users can update own recipes"
  on recipes for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "Users can delete own recipes"
  on recipes for delete
  to authenticated
  using (user_id = auth.uid());
