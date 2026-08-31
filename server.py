import http.server, json, os, time, threading, base64
from urllib.request import urlopen, Request
SUPA_URL=os.environ.get("SUPA_URL", os.environ.get("SUPABASE_URL","https://mdqnedaipzdsivpwgxxn.supabase.co"))
SUPA_KEY=os.environ.get("SUPA_SERVICE_KEY", os.environ.get("SUPA_KEY", os.environ.get("SUPABASE_SERVICE_KEY","__PUT_SUPA_SERVICE_KEY__")))
SUPA_BUCKET="creatorhub"
TOKEN=os.environ.get("TG_TOKEN","__PUT_TG_TOKEN__")
CHAT=os.environ.get("TG_CHAT","__PUT_TG_CHAT__")
PENDING_FILE="pending.json"
BLOCKED_FILE="blocked.json"
OFFSET_FILE="tg_offset.txt"
def load_json(p,d):
    try:
        with open(p,"r",encoding="utf-8") as f: return json.load(f)
    except: return d
def save_json(p,v):
    with open(p,"w",encoding="utf-8") as f: json.dump(v,f)
def supa_get(key,default):
    try:
        req=Request(f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{key}?t={int(time.time()*1000)}", headers={"Cache-Control":"no-cache"})
        with urlopen(req, timeout=10) as r: return json.loads(r.read().decode())
    except:
        try:
            req=Request(f"{SUPA_URL}/storage/v1/object/{SUPA_BUCKET}/{key}", headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Cache-Control":"no-cache"})
            with urlopen(req, timeout=10) as r: return json.loads(r.read().decode())
        except: return load_json(key.split("/")[-1], default)
def supa_put(key,data):
    save_json(key.split("/")[-1], data)
    try:
        raw=json.dumps(data).encode()
        req=Request(f"{SUPA_URL}/storage/v1/object/{SUPA_BUCKET}/{key}", data=raw, headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":"application/json","x-upsert":"true"})
        with urlopen(req, timeout=10): pass
    except Exception as e: print("supa put err",e)
def tg_api(method,data):
    try:
        req=Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
        with urlopen(req, timeout=10) as r: return json.loads(r.read().decode())
    except Exception as e: print("tg err",e); return None
class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/pending"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps(supa_get("meta/pending.json",[])).encode()); return
        if self.path.startswith("/api/blocked"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps(supa_get("meta/blocked.json",[])).encode()); return
        if self.path.startswith("/api/likes"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps({"likes":supa_get("meta/likes.json",{}),"liked":supa_get("meta/liked.json",{})}).encode()); return
        if self.path.startswith("/api/images"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps(supa_get("meta/images.json",[])).encode()); return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    def do_POST(self):
        length=int(self.headers.get('Content-Length',0))
        body=self.rfile.read(length).decode() if length else "{}"
        try: data=json.loads(body)
        except: data={}
        if self.path=="/api/pending":
            pend=supa_get("meta/pending.json",[]); pend.append(data); supa_put("meta/pending.json",pend)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        if self.path=="/api/pending/update":
            pend=supa_get("meta/pending.json",[])
            for p in pend:
                if str(p["id"])==str(data.get("id")):
                    for k,v in data.items():
                        if k!="id": p[k]=v
            supa_put("meta/pending.json",pend)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        if self.path=="/api/block":
            ph=data.get("phone"); blocked=supa_get("meta/blocked.json",[])
            if ph not in blocked: blocked.append(ph)
            supa_put("meta/blocked.json",blocked)
            pend=supa_get("meta/pending.json",[]); pend=[p for p in pend if p["phone"]!=ph]; supa_put("meta/pending.json",pend)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        if self.path=="/api/telegram/send":
            text=data.get("text",""); kb=data.get("reply_markup")
            payload={"chat_id":CHAT,"message_thread_id":2,"text":text,"parse_mode":"HTML"}
            if kb: payload["reply_markup"]=kb
            tg_api("sendMessage",payload)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        if self.path=="/api/likes":
            if "likes" in data: supa_put("meta/likes.json", data["likes"])
            if "liked" in data: supa_put("meta/liked.json", data["liked"])
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        if self.path=="/api/images":
            imgs=data if isinstance(data, list) else data.get("images",[])
            urls=[]
            for i,img in enumerate(imgs):
                if isinstance(img,str) and img.startswith("http"): urls.append(img)
                elif isinstance(img,str) and img.startswith("data:"):
                    try:
                        header,b64=img.split(",",1); ext="jpg"
                        if "png" in header: ext="png"
                        elif "webp" in header: ext="webp"
                        fname=f"{int(time.time()*1000)}_{i}.{ext}"; raw=base64.b64decode(b64)
                        req=Request(f"{SUPA_URL}/storage/v1/object/{SUPA_BUCKET}/{fname}", data=raw, headers={"apikey":SUPA_KEY,"Authorization":f"Bearer {SUPA_KEY}","Content-Type":f"image/{ext}","x-upsert":"true"})
                        with urlopen(req) as r: pass
                        urls.append(f"{SUPA_URL}/storage/v1/object/public/{SUPA_BUCKET}/{fname}")
                    except Exception as e: print("supa upload err",e); urls.append(img)
                else: urls.append(img)
            supa_put("meta/images.json", urls)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(json.dumps({"ok":True,"urls":urls}).encode()); return
        self.send_response(404); self.end_headers()
    def do_OPTIONS(self):
        self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Methods","GET,POST,OPTIONS"); self.send_header("Access-Control-Allow-Headers","Content-Type"); self.end_headers()
def poll_telegram():
    offset=0
    try: offset=int(open(OFFSET_FILE).read().strip())
    except: offset=0
    while True:
        try:
            with urlopen(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset+1}&timeout=5", timeout=15) as r:
                j=json.loads(r.read().decode())
                if j.get("ok"):
                    for u in j.get("result",[]):
                        offset=u["update_id"]; open(OFFSET_FILE,"w").write(str(offset))
                        cb=u.get("callback_query")
                        if not cb: continue
                        data=cb.get("data",""); mid=cb["message"]["message_id"]; chat=cb["message"]["chat"]["id"]
                        try: pid=int(data.split("_")[-1])
                        except: continue
                        pend=supa_get("meta/pending.json",[]); item=next((x for x in pend if str(x["id"])==str(pid)), None)
                        if not item: continue
                        if data.startswith("approve_"):
                            item["status"]="approved"; supa_put("meta/pending.json",pend); tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"✅ Validé"}); tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"✅ Validé: {item['username']} +33 {item['phone']}"})
                        elif data.startswith("reject_"):
                            item["status"]="rejected"; supa_put("meta/pending.json",pend); tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"❌ Refusé"}); tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"❌ Refusé: {item['username']} +33 {item['phone']}"})
                        elif data.startswith("block_"):
                            blocked=supa_get("meta/blocked.json",[]);
                            if item["phone"] not in blocked: blocked.append(item["phone"])
                            supa_put("meta/blocked.json",blocked); pend=[x for x in pend if x["id"]!=pid]; supa_put("meta/pending.json",pend)
                            tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"🚫 Bloqué"}); tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"🚫 Bloqué: {item['username']} +33 {item['phone']}"})
                        elif data.startswith("code_ok_"):
                            item["status"]="approved_final"; supa_put("meta/pending.json",pend); tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"✅ Code OK"}); tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"✅ Code OK: {item['username']} +33 {item['phone']} code {item.get('enteredCode','')}"})
                        elif data.startswith("code_bad_"):
                            item["status"]="rejected"; supa_put("meta/pending.json",pend); tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"❌ Code faux"}); tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"❌ Code faux: {item['username']} +33 {item['phone']} saisi {item.get('enteredCode','')}"})
        except Exception as e: print(e)
        time.sleep(2)
threading.Thread(target=poll_telegram, daemon=True).start()
port=int(os.environ.get("PORT", 8000))
print(f"Server on {port} with Telegram polling")
http.server.test(HandlerClass=Handler, port=port)
