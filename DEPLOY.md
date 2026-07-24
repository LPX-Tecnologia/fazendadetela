# Guia de Deploy — QA Device Farm

Este guia assume zero conhecimento prévio de deploy. São dois pedaços pra colocar no ar:
o **backend** (API + banco + fila) e o **frontend** (a tela, `index.html`).

⚠️ **Antes de tudo — leia isto:** um dispositivo Android físico só é enxergado pelo ADB
se estiver conectado (USB ou rede) na **mesma máquina** onde o worker está rodando.
Ou seja, "tudo 100% online" funciona perfeitamente para gerenciar fluxos, banco de dados
e disparar execuções — mas se você quiser usar celulares físicos, o worker precisa estar
rodando numa máquina (PC, servidor, VPS) que esteja fisicamente conectada a eles, ou
usar emuladores/"cloud phones" que já estejam acessíveis em rede via `adb connect`.
Isso é uma limitação de hardware, não do software.

---

## Parte 1 — Backend (API)

### Opção A: Render.com (mais simples, tem plano grátis)

1. Crie uma conta em [render.com](https://render.com) e conecte seu GitHub.
2. Suba a pasta `mvp/` (deste pacote) para um repositório novo no seu GitHub.
3. No Render, clique **New > Blueprint**, aponte para esse repositório —
   ele vai ler o arquivo `render.yaml` incluído e criar o serviço web e o banco automaticamente.
4. Crie um Redis gratuito separado (ex: [Upstash](https://upstash.com), tem free tier) e
   cole a URL de conexão na variável de ambiente `REDIS_URL` do serviço no painel do Render.
5. Aguarde o build. Quando terminar, você terá uma URL tipo
   `https://qa-device-farm-api.onrender.com` — essa é a URL que vai no frontend.

> No plano gratuito do Render o serviço "dorme" após inatividade e demora uns segundos
> para acordar na primeira chamada — normal, não é erro.

### Opção B: Railway.app

1. Crie conta em [railway.app](https://railway.app).
2. **New Project > Deploy from GitHub repo**, aponte pra pasta `mvp/`.
3. Adicione os plugins **PostgreSQL** e **Redis** pelo botão "+ New" dentro do projeto —
   o Railway já injeta `DATABASE_URL` e `REDIS_URL` automaticamente nas variáveis de ambiente.
4. O `Procfile` incluído já diz ao Railway como rodar o `web` (API) e o `worker` (Celery).
5. Copie a URL pública gerada pelo Railway para o serviço `web`.

### Opção C: Sua própria máquina/VPS (necessário se for usar celular físico)

```bash
cd mvp
docker compose up --build -d
```

Isso já sobe API, worker, Postgres e Redis juntos. Se a máquina tiver IP público
(ou você usar um túnel como `ngrok` ou `cloudflared`), a API fica acessível de fora
também — assim seu frontend hospedado no GitHub Pages consegue chamá-la.

---

## Parte 2 — Frontend (a tela)

O arquivo `index.html` (nesta mesma pasta) não precisa de build nem de `npm install` —
é só subir ele pronto.

### Opção mais simples: GitHub Pages (você já tem o repositório)

1. Copie `index.html` para dentro do repositório `fazendadetela` que você já publicou.
2. Commit e push. O GitHub Pages atualiza sozinho em 1-2 minutos.
3. Abra `https://lpx-tecnologia.github.io/fazendadetela/`, cole a URL do seu backend
   (da Parte 1) no campo do topo da tela, e pronto — a interface já fala com a API.

### Alternativas igualmente simples

- **Netlify Drop**: arraste o arquivo `index.html` em [app.netlify.com/drop](https://app.netlify.com/drop) — fica no ar em segundos, sem conta nem git.
- **Vercel**: `vercel deploy` na pasta que contém o `index.html`.

---

## Checklist final

- [ ] Backend no ar (Render/Railway/VPS) e respondendo em `SUA_URL/docs`
- [ ] `REDIS_URL` e `DATABASE_URL` configurados no backend
- [ ] Frontend publicado (GitHub Pages/Netlify/Vercel)
- [ ] Campo de URL da API no topo do frontend apontando pra URL do backend
- [ ] Se for usar dispositivo físico: worker rodando numa máquina com o celular conectado
