-- Add source metadata: access date and original source images
-- For web/youtube: stores when the URL was accessed
-- For photos: stores URLs to the original uploaded images in Supabase Storage

alter table recipes add column if not exists source_accessed_at timestamptz;
alter table recipes add column if not exists source_image_urls text[] default '{}';

-- Create storage bucket for source images (original photos used for ingestion)
insert into storage.buckets (id, name, public)
values ('source-images', 'source-images', true)
on conflict (id) do nothing;

-- Allow authenticated users to upload/read source images
create policy "Allow authenticated upload to source-images"
  on storage.objects for insert
  to authenticated
  with check (bucket_id = 'source-images');

create policy "Allow public read of source-images"
  on storage.objects for select
  to public
  using (bucket_id = 'source-images');
