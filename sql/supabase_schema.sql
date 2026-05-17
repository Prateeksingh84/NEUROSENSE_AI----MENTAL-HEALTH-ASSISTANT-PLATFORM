-- ============================================================================
-- NeuroSense AI — Supabase Main Schema
-- ============================================================================

create extension if not exists "pgcrypto";

-- ============================================================================
-- USER PROFILES
-- ============================================================================

create table if not exists public.user_profiles (

    id uuid primary key references auth.users(id) on delete cascade,

    full_name text,

    email text unique,

    phone text,

    avatar_url text,

    role text default 'user'
    check (role in ('admin', 'user')),

    account_status text default 'active'
    check (
        account_status in (
            'active',
            'disabled',
            'deleted'
        )
    ),

    preferred_language text default 'en',

    emergency_contact_name text,

    emergency_contact_phone text,

    wellness_notes text,

    last_login timestamptz,

    created_at timestamptz default now(),

    updated_at timestamptz default now()
);

-- ============================================================================
-- USER USAGE TRACKING
-- ============================================================================

create table if not exists public.usage_limits (

    id uuid primary key default gen_random_uuid(),

    user_id uuid references public.user_profiles(id)
    on delete cascade,

    usage_date date default current_date,

    daily_messages int default 0,

    monthly_messages int default 0,

    daily_limit int default 100,

    monthly_limit int default 2000,

    reports_generated int default 0,

    voice_minutes int default 0,

    sign_sessions int default 0,

    image_uploads int default 0,

    created_at timestamptz default now(),

    updated_at timestamptz default now(),

    unique(user_id, usage_date)
);

-- ============================================================================
-- CHAT SESSIONS
-- ============================================================================

create table if not exists public.chat_sessions (

    id uuid primary key default gen_random_uuid(),

    user_id uuid references public.user_profiles(id)
    on delete cascade,

    session_type text default 'normal'
    check (
        session_type in (
            'normal',
            'voice',
            'sign'
        )
    ),

    dominant_emotion text,

    average_mood_score numeric(4,2),

    summary text,

    started_at timestamptz default now(),

    ended_at timestamptz,

    created_at timestamptz default now()
);

-- ============================================================================
-- CHAT MESSAGES
-- ============================================================================

create table if not exists public.chat_messages (

    id uuid primary key default gen_random_uuid(),

    session_id uuid references public.chat_sessions(id)
    on delete cascade,

    sender text
    check (
        sender in (
            'user',
            'assistant'
        )
    ),

    message text,

    translated_message text,

    emotion text,

    mood_score numeric(4,2),

    created_at timestamptz default now()
);

-- ============================================================================
-- EMOTION LOGS
-- ============================================================================

create table if not exists public.emotion_logs (

    id uuid primary key default gen_random_uuid(),

    user_id uuid references public.user_profiles(id)
    on delete cascade,

    session_id uuid references public.chat_sessions(id)
    on delete cascade,

    emotion text,

    confidence numeric(5,2),

    source_type text
    check (
        source_type in (
            'camera',
            'voice',
            'text',
            'sign'
        )
    ),

    detected_at timestamptz default now()
);

-- ============================================================================
-- GENERATED REPORTS
-- ============================================================================

create table if not exists public.generated_reports (

    id uuid primary key default gen_random_uuid(),

    user_id uuid references public.user_profiles(id)
    on delete cascade,

    session_id uuid references public.chat_sessions(id)
    on delete set null,

    report_type text
    check (
        report_type in (
            'pdf',
            'csv'
        )
    ),

    report_title text,

    file_url text,

    created_at timestamptz default now()
);

-- ============================================================================
-- AI SETTINGS
-- ============================================================================

create table if not exists public.user_settings (

    id uuid primary key default gen_random_uuid(),

    user_id uuid unique references public.user_profiles(id)
    on delete cascade,

    emotion_detection boolean default true,

    voice_enabled boolean default true,

    analytics_enabled boolean default true,

    sign_language_enabled boolean default false,

    anonymous_reports boolean default false,

    auto_delete_sessions boolean default false,

    theme text default 'dark',

    created_at timestamptz default now(),

    updated_at timestamptz default now()
);

-- ============================================================================
-- ADMIN ACTIVITY LOGS
-- ============================================================================

create table if not exists public.admin_logs (

    id uuid primary key default gen_random_uuid(),

    admin_id uuid references public.user_profiles(id)
    on delete set null,

    action text,

    target_user uuid references public.user_profiles(id)
    on delete set null,

    metadata jsonb,

    created_at timestamptz default now()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

create index if not exists idx_sessions_user
on public.chat_sessions(user_id);

create index if not exists idx_messages_session
on public.chat_messages(session_id);

create index if not exists idx_reports_user
on public.generated_reports(user_id);

create index if not exists idx_emotions_user
on public.emotion_logs(user_id);

create index if not exists idx_usage_user
on public.usage_limits(user_id);