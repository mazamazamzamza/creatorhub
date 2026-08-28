Config Telegram temporaire
1. @BotFather -> /newbot -> récupère TOKEN
2. Envoie un message à ton bot, puis https://api.telegram.org/botTOKEN/getUpdates -> chat.id
3. Dans app.js remplace __PUT_TG_TOKEN_HERE__ et __PUT_TG_CHAT_ID_HERE__
4. NE PAS commit le token : gitignore déjà prêt

Envoi se fait côté client (visible) - OK pour test temporaire. Pour prod, passe par un backend.
