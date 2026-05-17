-- Supabase Storage bucket must be created from dashboard:
-- Storage > New Bucket > name: avatars > Public bucket: ON

-- If you want to create bucket by SQL:
insert into storage.buckets (id, name, public)
values ('avatars', 'avatars', true)
on conflict (id) do nothing;

-- Public read policy for avatars bucket
create policy if not exists "Avatar images are publicly readable"
on storage.objects
for select
using (bucket_id = 'avatars');

-- Authenticated upload policy
create policy if not exists "Users can upload own avatar"
on storage.objects
for insert
with check (bucket_id = 'avatars');

-- Authenticated update policy
create policy if not exists "Users can update own avatar"
on storage.objects
for update
using (bucket_id = 'avatars');
