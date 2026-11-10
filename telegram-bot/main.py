import os, logging, uuid
from datetime import datetime, timezone
from urllib.parse import quote
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters, ConversationHandler

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"), format="%(asctime)s %(levelname)s %(message)s")
log=logging.getLogger("fadstore")
BOT_TOKEN=os.environ["BOT_TOKEN"]
ADMIN_ID=int(os.getenv("ADMIN_TELEGRAM_ID","7460223477"))
SUPABASE_URL=os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY=os.environ["SUPABASE_SERVICE_ROLE_KEY"]
BUCKET=os.getenv("SUPABASE_STORAGE_BUCKET","product-images")
API=SUPABASE_URL+"/rest/v1"
H={"apikey":SUPABASE_KEY,"Authorization":"Bearer "+SUPABASE_KEY,"Content-Type":"application/json"}
NAME,GAME,PRICE,STOCK,RANK,LEVEL,ITEMS,PHOTO=range(8)
SETTING=20
OC,OP,OA,OS,ON=range(30,35)

def money(n):
    try: return "Rp"+f"{int(float(n)):,.0f}".replace(",",".")
    except (ValueError,TypeError): return "Rp0"
def admin(u):
    return bool(u.effective_user and u.effective_user.id==ADMIN_ID)
async def req(method,path,params=None,json=None,headers=None,content=None):
    h=dict(H); h.update(headers or {})
    async with httpx.AsyncClient(timeout=45) as c:
        r=await c.request(method,API+"/"+path,params=params,json=json,headers=h,content=content)
        if r.is_error: raise RuntimeError(f"Supabase {r.status_code}: {r.text[:400]}")
        return r.json() if r.content else None
async def rows(table,select="*",limit=100):
    return await req("GET",table,{"select":select,"limit":limit,"order":"created_at.desc"})
async def product(pid):
    a=await req("GET","products",{"select":"*","id":"eq."+str(pid),"limit":1})
    return a[0] if a else None
async def upload(data,ctype):
    ext={"image/jpeg":"jpg","image/png":"png","image/webp":"webp"}.get(ctype,"jpg")
    path=f"telegram/{datetime.now(timezone.utc):%Y%m%d}/{uuid.uuid4().hex}.{ext}"
    h={"apikey":SUPABASE_KEY,"Authorization":"Bearer "+SUPABASE_KEY,"Content-Type":ctype or "image/jpeg","x-upsert":"false"}
    async with httpx.AsyncClient(timeout=60) as c:
        r=await c.post(f"{SUPABASE_URL}/storage/v1/object/{quote(BUCKET)}/{quote(path,safe='/')}",content=data,headers=h)
        if r.is_error: raise RuntimeError("Upload foto gagal: "+r.text[:300])
    return f"{SUPABASE_URL}/storage/v1/object/public/{quote(BUCKET)}/{quote(path,safe='/')}"
def menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📦 Stok",callback_data="products"),InlineKeyboardButton("➕ Tambah",callback_data="add")],[InlineKeyboardButton("🧾 Pesanan",callback_data="orders"),InlineKeyboardButton("📊 Ringkasan",callback_data="stats")],[InlineKeyboardButton("⚙️ Pengaturan",callback_data="settings")]])
async def edit(q,text,kb=None,mode=None):
    try: await q.edit_message_text(text,reply_markup=kb,parse_mode=mode)
    except Exception: await q.message.reply_text(text,reply_markup=kb,parse_mode=mode)
async def start(u:Update,c:ContextTypes.DEFAULT_TYPE):
    if not admin(u): return await u.message.reply_text("⛔ Bot khusus admin FadStore.")
    await u.message.reply_text("🏪 FadStore Admin Bot\nKelola stok dan pesanan website dari Telegram.",reply_markup=menu())
async def actions(u:Update,c:ContextTypes.DEFAULT_TYPE):
    q=u.callback_query; await q.answer()
    if not admin(u): return
    a=q.data
    try:
        if a=="home": await edit(q,"🏪 Menu Admin FadStore",menu())
        elif a=="products":
            ps=await rows("products","id,game,name,price,stock,rank,level,image",100)
            if not ps: return await edit(q,"Belum ada stok.",InlineKeyboardMarkup([[InlineKeyboardButton("➕ Tambah stok",callback_data="add")],[InlineKeyboardButton("Menu",callback_data="home")]]))
            lines=["📦 DAFTAR STOK"]; kb=[]
            for p in ps[:30]:
                lines.append(f"• {p.get('name')} | {p.get('game')} | {money(p.get('price'))} | {'READY' if p.get('stock') else 'TERJUAL'}")
                kb.append([InlineKeyboardButton(("🟢 " if p.get("stock") else "🔴 ")+str(p.get("name","Produk"))[:35],callback_data="p:"+str(p["id"]))])
            kb.extend([[InlineKeyboardButton("➕ Tambah stok",callback_data="add")],[InlineKeyboardButton("⬅️ Menu",callback_data="home")]])
            await edit(q,"\n".join(lines),InlineKeyboardMarkup(kb))
        elif a.startswith("p:"):
            pid=a.split(":",1)[1]; p=await product(pid)
            if not p: return await edit(q,"Produk tidak ditemukan.",menu())
            c.user_data["pid"]=pid
            msg=(f"{p.get('name')}\nGame: {p.get('game')}\nHarga: {money(p.get('price'))}\nStok: {'READY' if p.get('stock') else 'TERJUAL'}\nRank: {p.get('rank') or '-'}\nLevel: {p.get('level') or '-'}\nDetail: {p.get('items') or '-'}\nFoto: {'Ada' if p.get('image') else 'Belum ada'}")
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("✏️ Edit detail",callback_data="edit")],[InlineKeyboardButton("📷 Ganti foto",callback_data="editphoto"),InlineKeyboardButton("🔄 READY/TERJUAL",callback_data="toggle")],[InlineKeyboardButton("🗑 Hapus",callback_data="delete")],[InlineKeyboardButton("⬅️ Daftar stok",callback_data="products")]])
            await edit(q,msg,kb)
        elif a=="stats":
            ps=await rows("products","id,stock",1000); os_=await rows("orders","id",1000); ready=sum(bool(x.get("stock")) for x in ps)
            await edit(q,f"📊 RINGKASAN\nTotal produk: {len(ps)}\nREADY: {ready}\nTERJUAL: {len(ps)-ready}\nTotal pesanan: {len(os_)}",InlineKeyboardMarkup([[InlineKeyboardButton("Menu",callback_data="home")]]))
        elif a=="orders":
            os_=await rows("orders","id,customer_name,product_name,amount,status,created_at",40)
            if not os_: return await edit(q,"Belum ada pesanan.",InlineKeyboardMarkup([[InlineKeyboardButton("➕ Catat pesanan",callback_data="addorder")],[InlineKeyboardButton("Menu",callback_data="home")]]))
            lines=["🧾 PESANAN TERBARU"]; kb=[]
            for o in os_[:25]:
                lines.append(f"• {o.get('customer_name')} — {o.get('product_name')} | {money(o.get('amount'))} | {o.get('status')}")
                kb.append([InlineKeyboardButton(f"{str(o.get('customer_name','Pelanggan'))[:22]} · {o.get('status','')}",callback_data="o:"+str(o["id"]))])
            kb.extend([[InlineKeyboardButton("➕ Catat pesanan",callback_data="addorder")],[InlineKeyboardButton("Menu",callback_data="home")]])
            await edit(q,"\n".join(lines),InlineKeyboardMarkup(kb))
        elif a.startswith("o:"):
            c.user_data["oid"]=a.split(":",1)[1]
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("Menunggu",callback_data="os:Menunggu"),InlineKeyboardButton("Diproses",callback_data="os:Diproses")],[InlineKeyboardButton("Selesai",callback_data="os:Selesai"),InlineKeyboardButton("Dibatalkan",callback_data="os:Dibatalkan")],[InlineKeyboardButton("🗑 Hapus pesanan",callback_data="odel")],[InlineKeyboardButton("Kembali",callback_data="orders")]])
            await edit(q,"Pilih status atau hapus pesanan ini:",kb)
        elif a.startswith("os:"):
            await req("PATCH","orders",{"id":"eq."+c.user_data["oid"]},{"status":a.split(":",1)[1]})
            await edit(q,"✅ Status pesanan diperbarui.",InlineKeyboardMarkup([[InlineKeyboardButton("Pesanan",callback_data="orders")]]))
        elif a=="odel":
            await req("DELETE","orders",{"id":"eq."+c.user_data["oid"]})
            await edit(q,"🗑 Pesanan dihapus.",InlineKeyboardMarkup([[InlineKeyboardButton("Pesanan",callback_data="orders")]]))
        elif a=="toggle":
            p=await product(c.user_data["pid"])
            if p: await req("PATCH","products",{"id":"eq."+c.user_data["pid"]},{"stock":not bool(p.get("stock"))})
            await edit(q,"✅ Status stok diperbarui.",InlineKeyboardMarkup([[InlineKeyboardButton("Daftar stok",callback_data="products")]]))
        elif a=="delete":
            await req("DELETE","products",{"id":"eq."+c.user_data["pid"]})
            await edit(q,"🗑 Produk dihapus.",InlineKeyboardMarkup([[InlineKeyboardButton("Daftar stok",callback_data="products")]]))
        elif a in ("add","edit"):
            if a=="add": c.user_data["prod"]={}; c.user_data.pop("editing",None)
            else:
                p=await product(c.user_data.get("pid"))
                if not p: return await edit(q,"Produk tidak ditemukan.")
                c.user_data["prod"]={k:p.get(k) for k in ("name","game","price","stock","rank","level","items","image")}
                c.user_data["editing"]=True
            await edit(q,"Kirim nama akun/produk:")
            return NAME
        elif a=="editphoto":
            c.user_data["photo_only"]=True
            await edit(q,"Kirim foto baru sebagai Photo Telegram. /skip untuk batal.")
            return PHOTO
        elif a=="settings":
            ss=await rows("store_settings","key,value",50); c.user_data["settings"]={x["key"]:x["value"] for x in ss}
            kb=InlineKeyboardMarkup([[InlineKeyboardButton("Nama toko",callback_data="s:store_name")],[InlineKeyboardButton("WhatsApp",callback_data="s:whatsapp")],[InlineKeyboardButton("Telegram",callback_data="s:telegram")],[InlineKeyboardButton("Menu",callback_data="home")]])
            await edit(q,"⚙️ Pilih pengaturan yang ingin diubah:",kb)
        elif a.startswith("s:"):
            c.user_data["setting_key"]=a.split(":",1)[1]
            await edit(q,"Kirim nilai baru untuk "+c.user_data["setting_key"]+":")
            return SETTING
        elif a=="addorder":
            c.user_data["order"]={}
            await edit(q,"Nama pelanggan:")
            return OC
    except Exception as e:
        log.exception("Callback error")
        await edit(q,"❌ "+str(e)[:700],menu())
    return

async def name_step(u,c):
    c.user_data["prod"]["name"]=u.message.text.strip()
    await u.message.reply_text("Pilih game:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Free Fire",callback_data="g:Free Fire")],[InlineKeyboardButton("Mobile Legends",callback_data="g:Mobile Legends")],[InlineKeyboardButton("Roblox",callback_data="g:Roblox")]]))
    return GAME
async def game_step(u,c):
    q=u.callback_query; await q.answer()
    if not admin(u): return ConversationHandler.END
    c.user_data["prod"]["game"]=q.data.split(":",1)[1]
    await q.message.reply_text("Harga dalam Rupiah (angka saja):")
    return PRICE
async def price_step(u,c):
    try: c.user_data["prod"]["price"]=int(u.message.text.replace(".","").replace(",","").strip())
    except ValueError:
        await u.message.reply_text("Harga harus angka. Coba lagi:"); return PRICE
    await u.message.reply_text("Pilih status stok:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("READY",callback_data="st:true"),InlineKeyboardButton("TERJUAL",callback_data="st:false")]]))
    return STOCK
async def stock_step(u,c):
    q=u.callback_query; await q.answer()
    if not admin(u): return ConversationHandler.END
    c.user_data["prod"]["stock"]=q.data.endswith("true")
    await q.message.reply_text("Rank akun (atau - jika kosong):"); return RANK
async def rank_step(u,c):
    t=u.message.text.strip(); c.user_data["prod"]["rank"]="" if t=="-" else t
    await u.message.reply_text("Level akun (atau - jika kosong):"); return LEVEL
async def level_step(u,c):
    t=u.message.text.strip(); c.user_data["prod"]["level"]="" if t=="-" else t
    await u.message.reply_text("Detail item/skin (atau - jika kosong):"); return ITEMS
async def items_step(u,c):
    t=u.message.text.strip(); c.user_data["prod"]["items"]="" if t=="-" else t
    await u.message.reply_text("Kirim foto produk atau /skip jika tanpa foto."); return PHOTO
async def save_product(u,c):
    p=c.user_data["prod"]; payload={k:p.get(k) for k in ("name","game","price","stock","rank","level","items","image")}
    try:
        if c.user_data.get("editing"): await req("PATCH","products",{"id":"eq."+str(c.user_data["pid"])},payload)
        else: await req("POST","products",json=payload)
        c.user_data.pop("editing",None); c.user_data.pop("prod",None)
        await u.message.reply_text("✅ Produk tersimpan. Katalog website ikut diperbarui.",reply_markup=menu())
    except Exception as e: await u.message.reply_text("❌ Gagal menyimpan: "+str(e)[:500],reply_markup=menu())
    return ConversationHandler.END
async def photo_step(u,c):
    if not admin(u): return ConversationHandler.END
    try:
        f=await c.bot.get_file(u.message.photo[-1].file_id); data=bytes(await f.download_as_bytearray())
        url=await upload(data,"image/jpeg")
        if c.user_data.get("photo_only"):
            await req("PATCH","products",{"id":"eq."+str(c.user_data["pid"])},{"image":url})
            c.user_data.pop("photo_only",None)
            await u.message.reply_text("✅ Foto produk diperbarui.",reply_markup=menu()); return ConversationHandler.END
        c.user_data["prod"]["image"]=url
        return await save_product(u,c)
    except Exception as e:
        log.exception("Photo upload")
        await u.message.reply_text("❌ Foto gagal diunggah: "+str(e)[:400]+"\nKirim ulang atau /skip.")
        return PHOTO
async def skip_photo(u,c):
    if c.user_data.get("photo_only"):
        c.user_data.pop("photo_only",None)
        await u.message.reply_text("Perubahan foto dibatalkan.",reply_markup=menu()); return ConversationHandler.END
    c.user_data["prod"]["image"]=c.user_data["prod"].get("image")
    return await save_product(u,c)
async def setting_step(u,c):
    key=c.user_data.get("setting_key")
    if key not in ("store_name","whatsapp","telegram"): return ConversationHandler.END
    await req("POST","store_settings",{"on_conflict":"key"},{"key":key,"value":u.message.text.strip()},{"Prefer":"resolution=merge-duplicates,return=minimal"})
    await u.message.reply_text("✅ Pengaturan toko disimpan.",reply_markup=menu()); return ConversationHandler.END
async def order_customer(u,c):
    c.user_data["order"]={"customer_name":u.message.text.strip()}
    await u.message.reply_text("Nama produk/akun:"); return OP
async def order_product(u,c):
    c.user_data["order"]["product_name"]=u.message.text.strip()
    await u.message.reply_text("Nominal Rupiah (angka saja):"); return OA
async def order_amount(u,c):
    try: c.user_data["order"]["amount"]=int(u.message.text.replace(".","").replace(",","").strip())
    except ValueError:
        await u.message.reply_text("Masukkan angka saja:"); return OA
    await u.message.reply_text("Pilih status:",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Menunggu",callback_data="new:Menunggu"),InlineKeyboardButton("Diproses",callback_data="new:Diproses")],[InlineKeyboardButton("Selesai",callback_data="new:Selesai"),InlineKeyboardButton("Dibatalkan",callback_data="new:Dibatalkan")]]))
    return OS
async def order_status(u,c):
    q=u.callback_query; await q.answer()
    if not admin(u): return ConversationHandler.END
    c.user_data["order"]["status"]=q.data.split(":",1)[1]
    await q.message.reply_text("Catatan (atau - jika kosong):"); return ON
async def order_note(u,c):
    d=c.user_data["order"]; t=u.message.text.strip(); d["note"]="" if t=="-" else t
    try:
        await req("POST","orders",json=d)
        await u.message.reply_text("✅ Pesanan dicatat.",reply_markup=menu())
    except Exception as e: await u.message.reply_text("❌ Gagal: "+str(e)[:400],reply_markup=menu())
    return ConversationHandler.END
async def cancel(u,c):
    c.user_data.clear(); await u.message.reply_text("Dibatalkan.",reply_markup=menu()); return ConversationHandler.END
async def err(u,c): log.exception("Unhandled bot exception",exc_info=c.error)

def build():
    app=Application.builder().token(BOT_TOKEN).build()
    product_flow=ConversationHandler(entry_points=[CallbackQueryHandler(actions,pattern="^(add|edit)$")],states={
        NAME:[MessageHandler(filters.TEXT & ~filters.COMMAND,name_step)],GAME:[CallbackQueryHandler(game_step,pattern="^g:")],
        PRICE:[MessageHandler(filters.TEXT & ~filters.COMMAND,price_step)],STOCK:[CallbackQueryHandler(stock_step,pattern="^st:")],
        RANK:[MessageHandler(filters.TEXT & ~filters.COMMAND,rank_step)],LEVEL:[MessageHandler(filters.TEXT & ~filters.COMMAND,level_step)],
        ITEMS:[MessageHandler(filters.TEXT & ~filters.COMMAND,items_step)],PHOTO:[MessageHandler(filters.PHOTO,photo_step),CommandHandler("skip",skip_photo)]
    },fallbacks=[CommandHandler("cancel",cancel)],allow_reentry=True)
    photo_flow=ConversationHandler(entry_points=[CallbackQueryHandler(actions,pattern="^editphoto$")],states={PHOTO:[MessageHandler(filters.PHOTO,photo_step),CommandHandler("skip",skip_photo)]},fallbacks=[CommandHandler("cancel",cancel)],allow_reentry=True)
    setting_flow=ConversationHandler(entry_points=[CallbackQueryHandler(actions,pattern="^s:")],states={SETTING:[MessageHandler(filters.TEXT & ~filters.COMMAND,setting_step)]},fallbacks=[CommandHandler("cancel",cancel)],allow_reentry=True)
    order_flow=ConversationHandler(entry_points=[CallbackQueryHandler(actions,pattern="^addorder$")],states={
        OC:[MessageHandler(filters.TEXT & ~filters.COMMAND,order_customer)],OP:[MessageHandler(filters.TEXT & ~filters.COMMAND,order_product)],
        OA:[MessageHandler(filters.TEXT & ~filters.COMMAND,order_amount)],OS:[CallbackQueryHandler(order_status,pattern="^new:")],
        ON:[MessageHandler(filters.TEXT & ~filters.COMMAND,order_note)]
    },fallbacks=[CommandHandler("cancel",cancel)],allow_reentry=True)
    app.add_handler(CommandHandler("start",start))
    app.add_handler(product_flow); app.add_handler(photo_flow); app.add_handler(setting_flow); app.add_handler(order_flow)
    app.add_handler(CallbackQueryHandler(actions))
    app.add_error_handler(err)
    return app
if __name__=="__main__":
    missing=[x for x in ("BOT_TOKEN","SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY") if not os.getenv(x)]
    if missing: raise SystemExit("Isi Railway Variables: "+", ".join(missing))
    log.info("FadStore bot starting; admin ID %s",ADMIN_ID)
    build().run_polling(allowed_updates=Update.ALL_TYPES)
