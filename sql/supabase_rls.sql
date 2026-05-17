-- ============================================================================
-- NeuroSense AI — Row Level Security
-- ============================================================================

alter table public.user_profiles
enable row level security;

alter table public.usage_limits
enable row level security;

alter table public.chat_sessions
enable row level security;

alter table public.chat_messages
enable row level security;

alter table public.generated_reports
enable row level security;

alter table public.emotion_logs
enable row level security;

alter table public.user_settings
enable row level security;

alter table public.admin_logs
enable row level security;

-- ============================================================================
-- USER PROFILE POLICIES
-- ============================================================================

create policy "Users can view own profile"
on public.user_profiles
for select
using (
    auth.uid() = id
);

create policy "Users can update own profile"
on public.user_profiles
for update
using (
    auth.uid() = id
);

create policy "Users can insert own profile"
on public.user_profiles
for insert
with check (
    auth.uid() = id
);

-- ============================================================================
-- USAGE LIMITS
-- ============================================================================

create policy "Users can view own usage"
on public.usage_limits
for select
using (
    auth.uid() = user_id
);

create policy "Users can insert own usage"
on public.usage_limits
for insert
with check (
    auth.uid() = user_id
);

create policy "Users can update own usage"
on public.usage_limits
for update
using (
    auth.uid() = user_id
);

-- ============================================================================
-- CHAT SESSIONS
-- ============================================================================

create policy "Users can view own sessions"
on public.chat_sessions
for select
using (
    auth.uid() = user_id
);

create policy "Users can insert own sessions"
on public.chat_sessions
for insert
with check (
    auth.uid() = user_id
);

create policy "Users can update own sessions"
on public.chat_sessions
for update
using (
    auth.uid() = user_id
);

-- ============================================================================
-- CHAT MESSAGES
-- ============================================================================

create policy "Users can view own messages"
on public.chat_messages
for select
using (
    exists (
        select 1
        from public.chat_sessions s
        where s.id = session_id
        and s.user_id = auth.uid()
    )
);

create policy "Users can insert own messages"
on public.chat_messages
for insert
with check (
    exists (
        select 1
        from public.chat_sessions s
        where s.id = session_id
        and s.user_id = auth.uid()
    )
);

-- ============================================================================
-- GENERATED REPORTS
-- ============================================================================

create policy "Users can view own reports"
on public.generated_reports
for select
using (
    auth.uid() = user_id
);

create policy "Users can insert own reports"
on public.generated_reports
for insert
with check (
    auth.uid() = user_id
);

-- ============================================================================
-- EMOTION LOGS
-- ============================================================================

create policy "Users can view own emotions"
on public.emotion_logs
for select
using (
    auth.uid() = user_id
);

create policy "Users can insert own emotions"
on public.emotion_logs
for insert
with check (
    auth.uid() = user_id
);

-- ============================================================================
-- USER SETTINGS
-- ============================================================================

create policy "Users can manage own settings"
on public.user_settings
for all
using (
    auth.uid() = user_id
);

-- ============================================================================
-- ADMIN LOGS
-- ============================================================================

create policy "Admins can view logs"
on public.admin_logs
for select
using (
    exists (
        select 1
        from public.user_profiles p
        where p.id = auth.uid()
        and p.role = 'admin'
    )
);