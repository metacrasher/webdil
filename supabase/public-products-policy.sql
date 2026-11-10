-- FadStore: allow everyone to READ the public product catalog.
-- This does NOT grant permission to insert, update, or delete products.
grant select on table public.products to anon, authenticated;

drop policy if exists "Public can view product catalog" on public.products;

create policy "Public can view product catalog"
on public.products
for select
to anon, authenticated
using (true);

-- Product images are intended to be visible in the public storefront.
-- Enable public reads only for objects in the product-images bucket.
drop policy if exists "Public can view product images" on storage.objects;

create policy "Public can view product images"
on storage.objects
for select
to anon, authenticated
using (bucket_id = 'product-images');
