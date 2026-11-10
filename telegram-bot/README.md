# FadStore Telegram Admin Bot

Bot admin Telegram untuk mengelola data website FadStore secara langsung.

## Fitur
- Daftar produk dan ringkasan READY/TERJUAL.
- Tambah produk beserta foto, game, harga, rank, level, dan detail item.
- Edit detail produk, ganti foto, ubah status stok, dan hapus produk.
- Lihat pesanan, ubah status, hapus, dan catat pesanan manual.
- Ubah nama toko, WhatsApp, dan Telegram.

## Deploy Railway
1. Buat project baru → Deploy from GitHub Repo → pilih `metacrasher/webdil`.
2. Atur Root Directory menjadi `/telegram-bot`.
3. Tambahkan Variables berikut di Railway:
   - `BOT_TOKEN` = token baru dari BotFather.
   - `ADMIN_TELEGRAM_ID` = `7460223477`
   - `SUPABASE_URL` = `https://qdfrdxsqkufytssjinrv.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY` = service role/secret key dari Supabase Project Settings → API.
   - `SUPABASE_STORAGE_BUCKET` = `product-images` (opsional).
4. Deploy, lalu buka bot Telegram dan kirim `/start`.

## Keamanan
Jangan pernah menaruh BOT_TOKEN atau SUPABASE_SERVICE_ROLE_KEY di GitHub, file kode, atau frontend. Bot hanya menerima perintah dari ADMIN_TELEGRAM_ID. Jika token pernah dibagikan, cabut lewat BotFather dan pakai token pengganti.

Bot menggunakan tabel `products`, `orders`, `store_settings`, dan bucket Storage `product-images` milik website. Service role key diperlukan agar bot dapat mengelola data tanpa mengubah kebijakan akses publik website.
