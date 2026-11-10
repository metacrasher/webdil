const CFG=window.FADSTORE_CONFIG||{};
const CONFIGURED=CFG.SUPABASE_URL&&CFG.SUPABASE_ANON_KEY&&!CFG.SUPABASE_URL.includes("ISI_")&&!CFG.SUPABASE_ANON_KEY.includes("ISI_");
let db=null,products=[],orders=[],settings={store_name:"FadStore",whatsapp:"6285273114090",telegram:"@fadstore"},adminSession=false;
const $=id=>document.getElementById(id);
const money=n=>new Intl.NumberFormat("id-ID",{style:"currency",currency:"IDR",maximumFractionDigits:0}).format(Number(n)||0);
function toast(s){const t=$("toast");t.textContent=s;t.classList.add("show");setTimeout(()=>t.classList.remove("show"),3000)}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function showLogin(){adminSession=false;$("store-access-label").textContent="Login Admin";$("store-view").hidden=false;$("app-view").hidden=true;$("admin-login-panel").classList.remove("open");loadPublicCatalog()}
function showApp(){adminSession=true;$("store-access-label").textContent="Kembali Dashboard";$("store-view").hidden=true;$("app-view").hidden=false;$("admin-login-panel").classList.remove("open");loadAll()}
function showStorePreview(){if(!adminSession)return;$("app-view").hidden=true;$("store-view").hidden=false;$("admin-login-panel").classList.remove("open");$("store-access-label").textContent="Kembali Dashboard";loadPublicCatalog()}
function openAdminLogin(){if(adminSession){showApp();return}$("login-error").textContent="";$("admin-login-panel").classList.add("open");setTimeout(()=>$("login-email").focus(),180)}
document.querySelectorAll("[data-close-login]").forEach(b=>b.addEventListener("click",()=>$("admin-login-panel").classList.remove("open")));
$("open-admin-login").addEventListener("click",openAdminLogin);
$("preview-store").addEventListener("click",showStorePreview);

function needConfig(){if(!CONFIGURED){$("login-error").textContent="Layanan admin belum dikonfigurasi. Silakan hubungi pengelola toko.";return true}return false}
let publicProducts=[];
function gameMark(game){return game==="Free Fire"?"FF":game==="Mobile Legends"?"ML":"R"}
function contactIcon(type){
 if(type==="wa")return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 3.5A11.8 11.8 0 0 0 2 17.7L.5 23.5l6-1.6A11.8 11.8 0 0 0 20.5 3.5ZM12 21a9 9 0 0 1-4.6-1.3l-.3-.2-3.5.9.9-3.4-.2-.4A9 9 0 1 1 12 21Zm5-6.7c-.3-.2-1.7-.9-2-.9s-.5-.2-.7.2-.8.9-1 1.1-.4.2-.7.1a7.4 7.4 0 0 1-2.2-1.4 8.2 8.2 0 0 1-1.5-1.9c-.2-.3 0-.5.2-.7l.5-.6c.2-.2.2-.4.3-.6.1-.2 0-.4 0-.6l-.9-2c-.2-.5-.5-.4-.7-.4h-.6c-.2 0-.6.1-.9.4s-1.2 1.2-1.2 2.8 1.2 3.2 1.4 3.4a10.7 10.7 0 0 0 4.1 3.6c.6.3 1.1.5 1.5.6.6.2 1.2.2 1.7.1.5-.1 1.7-.7 1.9-1.4.2-.7.2-1.3.1-1.4s-.2-.2-.5-.4Z"/></svg>';
 return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21.8 3.2 18.5 20c-.2 1.2-.9 1.5-1.8.9l-5-3.7-2.4 2.3c-.3.3-.5.5-1 .5l.4-5.1 9.3-8.4c.4-.4-.1-.6-.6-.2L5.9 13.5 1 12c-1.1-.3-1.1-1 .2-1.5L20.3 3c.9-.3 1.7.2 1.5.2Z"/></svg>';
}
function imageUrl(raw){
 const value=String(raw||"").trim();
 const drive=value.match(/drive\.google\.com\/(?:file\/d\/|open\?|uc\?)[^#]*?(?:id=)?([a-zA-Z0-9_-]{15,})/);
 if(drive)return "https://drive.google.com/uc?export=view&id="+drive[1];
 if(value.includes("dropbox.com/"))return value.replace("www.dropbox.com","dl.dropboxusercontent.com").replace(/[?&]dl=0/,"?raw=1");
 return value;
}
function renderPublicCatalog(){
 const q=$("public-search").value.toLowerCase(),g=$("public-game-filter").value;
 const list=publicProducts.filter(p=>((""+p.name+" "+p.game+" "+(p.rank||"")+" "+(p.items||"")).toLowerCase().includes(q))&&(g==="all"||p.game===g));
 $("public-stock-count").textContent=publicProducts.length+" akun ready";
 if(!list.length){$("public-products").innerHTML='<div class="catalog-empty">Belum ada akun yang ready untuk kategori ini. Coba cek kembali nanti, ya.</div>';return}
 $("public-products").innerHTML=list.map(p=>{
  const src=imageUrl(p.image);
  const image=src?'<img src="'+esc(src)+'" alt="'+esc(p.name)+'" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentElement.classList.add(\'image-failed\');this.remove()">':'<div class="product-placeholder"><span>'+esc(p.game)+'</span><b>'+gameMark(p.game)+'</b></div>';
  const message=encodeURIComponent("Halo FadStore, saya tertarik membeli akun: "+p.name+" ("+p.game+") dengan harga "+money(p.price)+". Apakah masih tersedia?");
  const tgUser=(settings.telegram||"@fadstore").replace(/^@/,"");
  return '<article class="public-product-card"><div class="public-product-image">'+image+'<span class="ready-pill"><i></i> READY</span></div><div class="public-product-info"><span class="game-label">'+esc(p.game)+'</span><h3>'+esc(p.name)+'</h3><p>'+esc([p.rank,p.level,p.items].filter(Boolean).join(" • ")||"Detail akun dapat ditanyakan ke admin")+'</p><div class="public-product-bottom"><b>'+money(p.price)+'</b><div class="product-contact-actions"><a class="contact-btn wa-btn" href="https://wa.me/'+esc((settings.whatsapp||"6285273114090").replace(/\\D/g,""))+'?text='+message+'" target="_blank" rel="noopener">'+contactIcon("wa")+' WhatsApp</a><a class="contact-btn tg-btn" href="https://t.me/'+encodeURIComponent(tgUser)+'?text='+message+'" target="_blank" rel="noopener">'+contactIcon("tg")+' Telegram</a></div></div></div></article>';
 }).join("");
}
async function loadPublicCatalog(){
 if(!db){$("public-stock-count").textContent="Katalog FadStore";$("public-products").innerHTML='<div class="catalog-empty">Katalog sedang disiapkan. Silakan hubungi admin melalui Telegram @fadstore.</div>';return}
 const {data,error}=await db.from("products").select("id,game,name,price,stock,rank,level,items,image").eq("stock",true).order("created_at",{ascending:false});
 if(error){$("public-stock-count").textContent="Stok belum dapat dimuat";$("public-products").innerHTML='<div class="catalog-empty">Katalog belum dapat dimuat. Pengelola perlu mengaktifkan akses baca katalog publik di database.</div>';return}
 publicProducts=data||[];renderPublicCatalog();
}
$("public-search").addEventListener("input",renderPublicCatalog);
$("public-game-filter").addEventListener("change",renderPublicCatalog);
$("login-form").addEventListener("submit",async e=>{e.preventDefault();$("login-error").textContent="";if(needConfig())return;const {data,error}=await db.auth.signInWithPassword({email:$("login-email").value.trim(),password:$("login-password").value});if(error){$("login-error").textContent=error.message;return}showApp()});
$("logout").addEventListener("click",async()=>{await db.auth.signOut();showLogin()});
function navigate(page){document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));$("page-"+page).classList.add("active");document.querySelectorAll(".side-link").forEach(b=>b.classList.toggle("active",b.dataset.page===page));$("page-name").textContent=({overview:"Ringkasan",products:"Produk & Stok",orders:"Riwayat Pesanan",settings:"Pengaturan Toko"})[page];$("sidebar").classList.remove("open")}
document.querySelectorAll("[data-page]").forEach(b=>b.addEventListener("click",()=>navigate(b.dataset.page)));
document.querySelectorAll("[data-go]").forEach(b=>b.addEventListener("click",()=>navigate(b.dataset.go)));
$("mobile-menu").addEventListener("click",()=>$("sidebar").classList.toggle("open"));
function modal(id,open){$(id).classList.toggle("open",open)}
document.querySelectorAll("[data-close]").forEach(b=>b.addEventListener("click",()=>modal(b.dataset.close,false)));
async function loadAll(){if(!db)return;const [pr,or,se]=await Promise.all([db.from("products").select("*").order("created_at",{ascending:false}),db.from("orders").select("*").order("created_at",{ascending:false}),db.from("store_settings").select("*")]);if(pr.error||or.error||se.error){toast((pr.error||or.error||se.error).message);return}products=pr.data||[];orders=or.data||[];for(const s of se.data||[])settings[s.key]=s.value;renderAll()}
function renderAll(){ $("stat-products").textContent=products.length;$("stat-stock").textContent=products.filter(p=>p.stock).length;$("stat-sold").textContent=products.filter(p=>!p.stock).length;$("stat-orders").textContent=orders.length;renderProducts();renderOrders();renderRecent();$("setting-name").value=settings.store_name||"FadStore";$("setting-wa").value=settings.whatsapp||"6285273114090";$("setting-telegram").value=settings.telegram||"@fadstore"}
function statusBadge(p){return `<span class="badge ${p.stock?"":"sold"}">${p.stock?"Tersedia":"Terjual"}</span>`}
function productRows(list){if(!list.length)return '<p class="muted-note">Belum ada produk. Klik Tambah Produk untuk mulai mengisi katalog.</p>';return `<table><thead><tr><th>PRODUK</th><th>GAME</th><th>HARGA</th><th>STOK</th><th>AKSI</th></tr></thead><tbody>${list.map(p=>`<tr><td><b>${esc(p.name)}</b><small>${esc(p.rank||"-")} · ${esc(p.level||"-")}</small></td><td>${esc(p.game)}</td><td>${money(p.price)}</td><td>${statusBadge(p)}</td><td><div class="row-actions"><button class="mini-btn" onclick="editProduct('${p.id}')">Edit</button><button class="mini-btn danger" onclick="deleteProduct('${p.id}')">Hapus</button></div></td></tr>`).join("")}</tbody></table>`}
function renderProducts(){const q=$("product-search").value.toLowerCase(),st=$("product-filter").value,g=$("game-filter").value;let list=products.filter(p=>(`${p.name} ${p.game}`.toLowerCase().includes(q))&&(st==="all"||(st==="available"?p.stock:!p.stock))&&(g==="all"||p.game===g));$("products-table").innerHTML=productRows(list)}
function renderRecent(){$("recent-products").innerHTML=productRows(products.slice(0,5))}
["product-search","product-filter","game-filter"].forEach(id=>$(id).addEventListener("input",renderProducts));
$("add-product").addEventListener("click",()=>{ $("product-form").reset();$("p-id").value="";$("product-modal-title").textContent="Tambah Produk";$("p-stock").value="true";modal("product-modal",true)});
window.editProduct=id=>{const p=products.find(x=>String(x.id)===String(id));if(!p)return;$("p-id").value=p.id;$("p-game").value=p.game;$("p-name").value=p.name;$("p-price").value=p.price;$("p-stock").value=String(p.stock);$("p-rank").value=p.rank||"";$("p-level").value=p.level||"";$("p-items").value=p.items||"";$("p-image").value=p.image||"";$("product-modal-title").textContent="Edit Produk";modal("product-modal",true)};
$("product-form").addEventListener("submit",async e=>{e.preventDefault();const id=$("p-id").value;const row={game:$("p-game").value,name:$("p-name").value.trim(),price:Number($("p-price").value),stock:$("p-stock").value==="true",rank:$("p-rank").value.trim(),level:$("p-level").value.trim(),items:$("p-items").value.trim(),image:$("p-image").value.trim()||null};const result=id?await db.from("products").update(row).eq("id",id):await db.from("products").insert(row);if(result.error){$("product-error").textContent=result.error.message;return}modal("product-modal",false);toast("Produk berhasil disimpan");await loadAll()});
window.deleteProduct=async id=>{if(!confirm("Hapus produk ini secara permanen?"))return;const {error}=await db.from("products").delete().eq("id",id);if(error){toast(error.message);return}toast("Produk dihapus");loadAll()};
$("add-order").addEventListener("click",()=>{$("order-form").reset();modal("order-modal",true)});
$("order-form").addEventListener("submit",async e=>{e.preventDefault();const row={customer_name:$("o-customer").value.trim(),product_name:$("o-product").value.trim(),amount:Number($("o-price").value),status:$("o-status").value,note:$("o-note").value.trim()};const {error}=await db.from("orders").insert(row);if(error){toast(error.message);return}modal("order-modal",false);toast("Pesanan dicatat");loadAll()});
function renderOrders(){const q=$("order-search").value.toLowerCase(),st=$("order-status-filter").value,list=orders.filter(o=>(`${o.customer_name} ${o.product_name}`.toLowerCase().includes(q))&&(st==="all"||o.status===st));if(!list.length){$("orders-table").innerHTML='<p class="muted-note">Belum ada pesanan yang cocok. Catat pesanan setelah pelanggan menghubungi admin.</p>';return}$("orders-table").innerHTML=`<table><thead><tr><th>PELANGGAN</th><th>PRODUK</th><th>NOMINAL</th><th>TANGGAL</th><th>STATUS</th><th>AKSI</th></tr></thead><tbody>${list.map(o=>`<tr><td><b>${esc(o.customer_name)}</b></td><td>${esc(o.product_name)}<small>${esc(o.note||"")}</small></td><td>${money(o.amount)}</td><td>${new Date(o.created_at).toLocaleDateString("id-ID")}</td><td><span class="badge ${o.status==="Selesai"?"":o.status==="Dibatalkan"?"cancel":o.status==="Menunggu"?"pending":"process"}">${esc(o.status)}</span></td><td><div class="row-actions"><select aria-label="Ubah status pesanan" onchange="updateOrder('${o.id}',this.value)"><option ${o.status==="Menunggu"?"selected":""}>Menunggu</option><option ${o.status==="Diproses"?"selected":""}>Diproses</option><option ${o.status==="Selesai"?"selected":""}>Selesai</option><option ${o.status==="Dibatalkan"?"selected":""}>Dibatalkan</option></select><button class="mini-btn danger" onclick="deleteOrder('${o.id}')">Hapus</button></div></td></tr>`).join("")}</tbody></table>`}
$("order-search").addEventListener("input",renderOrders);$("order-status-filter").addEventListener("change",renderOrders);
window.updateOrder=async(id,status)=>{const {error}=await db.from("orders").update({status}).eq("id",id);if(error){toast(error.message);return}toast("Status pesanan diperbarui");loadAll()};
window.deleteOrder=async id=>{if(!confirm("Hapus catatan pesanan?"))return;const {error}=await db.from("orders").delete().eq("id",id);if(error){toast(error.message);return}loadAll()};
$("settings-form").addEventListener("submit",async e=>{e.preventDefault();const rows=[{key:"store_name",value:$("setting-name").value.trim()},{key:"whatsapp",value:$("setting-wa").value.trim()},{key:"telegram",value:$("setting-telegram").value.trim()}];const {error}=await db.from("store_settings").upsert(rows);if(error){toast(error.message);return}toast("Pengaturan toko disimpan");loadAll()});
async function init(){
 if(!window.supabase){$("public-products").innerHTML='<div class="catalog-empty">Koneksi katalog gagal dimuat. Periksa koneksi internet.</div>';return}
 if(CONFIGURED)db=window.supabase.createClient(CFG.SUPABASE_URL,CFG.SUPABASE_ANON_KEY);
 if(!db){showLogin();return}
 await loadPublicCatalog();
 const {data:{session}}=await db.auth.getSession();
 if(session)showApp();else showLogin();
 db.auth.onAuthStateChange((_event,session)=>{if(session)showApp();else showLogin()});
}
init();
