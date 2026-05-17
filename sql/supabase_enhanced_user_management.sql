-- ============================================================
-- NeuroSense AI — Supabase Enhanced User Management
-- Run this in Supabase SQL Editor
-- ============================================================

-- Required extension for UUID generation
create extension if not exists pgcrypto;

-- ── USER PROFILES ───────────────────────────────────────────
create table if not exists public.user_profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null default 'User',
  email text unique,
  phone text,
  avatar_url text,
  preferred_language text not null default 'en',
  role text not null default 'user' check (role in ('admin', 'user')),
  account_status text not null default 'active' check (account_status in ('active', 'disabled', 'deleted')),
  emergency_contact_name text,
  emergency_contact_phone text,
  daily_limit integer not null default 100,
  monthly_limit integer not null default 2000,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  last_active timestamptz
);

-- ── USAGE LIMITS / TRACKING ─────────────────────────────────
create table if not exists public.usage_limits (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.user_profiles(id) on delete cascade,
  usage_date date not null default current_date,
  month_key text not null default to_char(current_date, 'YYYY-MM'),
  daily_messages integer not null default 0,
  monthly_messages integer not null default 0,
  daily_limit integer not null default 100,
  monthly_limit integer not null default 2000,
  reports_generated integer not null default 0,
  voice_minutes integer not null default 0,
  sign_sessions integer not null default 0,
  updated_at timestamptz not null default now(),
  unique(user_id, usage_date)
);

-- ── INDEXES ─────────────────────────────────────────────────
create index if not exists idx_user_profiles_email on public.user_profiles(email);
create index if not exists idx_user_profiles_role on public.user_profiles(role);
create index if not exists idx_usage_limits_user_date on public.usage_limits(user_id, usage_date desc);
create index if not exists idx_usage_limits_month on public.usage_limits(user_id, month_key);

-- ── STORAGE BUCKET FOR AVATARS ──────────────────────────────
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do nothing;

-- ── ENABLE RLS ──────────────────────────────────────────────
alter table public.user_profiles enable row level security;
alter table public.usage_limits enable row level security;

-- ── USER PROFILE POLICIES ───────────────────────────────────
drop policy if exists "Users can view own profile" on public.user_profiles;
create policy "Users can view own profile"
on public.user_profiles
for select
using (auth.uid() = id);

drop policy if exists "Users can update own profile" on public.user_profiles;
create policy "Users can update own profile"
on public.user_profiles
for update
using (auth.uid() = id)
with check (auth.uid() = id);

-- ── USAGE POLICIES ──────────────────────────────────────────
drop policy if exists "Users can view own usage" on public.usage_limits;
create policy "Users can view own usage"
on public.usage_limits
for select
using (auth.uid() = user_id);

-- Service role bypasses RLS automatically. Flask backend uses service role.

-- ── STORAGE POLICIES ────────────────────────────────────────
drop policy if exists "Avatar images are publicly readable" on storage.objects;
create policy "Avatar images are publicly readable"
on storage.objects
for select
using (bucket_id = 'avatars');

drop policy if exists "Users can upload own avatar" on storage.objects;
create policy "Users can upload own avatar"
on storage.objects
for insert
with check (
  bucket_id = 'avatars'
  and auth.uid()::text = (storage.foldername(name))[1]
);

drop policy if exists "Users can update own avatar" on storage.objects;
create policy "Users can update own avatar"
on storage.objects
for update
using (
  bucket_id = 'avatars'
  and auth.uid()::text = (storage.foldername(name))[1]
)
with check (
  bucket_id = 'avatars'
  and auth.uid()::text = (storage.foldername(name))[1]
);

-- ── OPTIONAL: make first user admin manually after signup ─────
-- update public.user_profiles set role = 'admin' where email = 'your-email@example.com';
