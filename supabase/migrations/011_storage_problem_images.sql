-- Create a public storage bucket for problem images.
-- Images are uploaded by parsers and referenced in problems.problem_images.

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'problem-images',
  'problem-images',
  true,
  5242880,  -- 5 MB max per file
  ARRAY['image/png', 'image/jpeg', 'image/gif', 'image/svg+xml', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

-- Allow public read access to all images in the bucket
CREATE POLICY "Public read access for problem images"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'problem-images');

-- Allow authenticated service role to upload/update/delete images
CREATE POLICY "Service role can manage problem images"
ON storage.objects FOR ALL
TO service_role
USING (bucket_id = 'problem-images')
WITH CHECK (bucket_id = 'problem-images');
