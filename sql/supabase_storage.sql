-- ============================================================================
-- NeuroSense AI — Storage Buckets
-- ============================================================================

insert into storage.buckets (
    id,
    name,
    public
)
values
(
    'avatars',
    'avatars',
    true
)
on conflict (id) do nothing;

insert into storage.buckets (
    id,
    name,
    public
)
values
(
    'reports',
    'reports',
    true
)
on conflict (id) do nothing;

insert into storage.buckets (
    id,
    name,
    public
)
values
(
    'voice-recordings',
    'voice-recordings',
    false
)
on conflict (id) do nothing;

insert into storage.buckets (
    id,
    name,
    public
)
values
(
    'emotion-snapshots',
    'emotion-snapshots',
    false
)
on conflict (id) do nothing;