-- ============================================================================
-- NeuroSense AI — Seed Admin User
-- ============================================================================

-- IMPORTANT:
-- Replace UUID below with your actual auth.users id
-- Replace email/name accordingly

insert into public.user_profiles (

    id,
    full_name,
    email,
    role,
    account_status,
    preferred_language,
    created_at,
    updated_at

)
values
(
    '11111111-1111-1111-1111-111111111111',

    'Prateek Singh',

    'prathamgsingh@gmail.com',

    'admin',

    'active',

    'en',

    now(),

    now()
)

on conflict (id)
do update set
role = 'admin';


-- ============================================================================
-- DEFAULT ADMIN SETTINGS
-- ============================================================================

insert into public.user_settings (

    user_id,
    emotion_detection,
    voice_enabled,
    analytics_enabled,
    sign_language_enabled,
    anonymous_reports,
    auto_delete_sessions,
    theme,
    created_at,
    updated_at

)
values
(
    '11111111-1111-1111-1111-111111111111',

    true,

    true,

    true,

    true,

    false,

    false,

    'dark',

    now(),

    now()
)

on conflict (user_id)
do nothing;