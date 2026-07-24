# QA Device Farm — MVP

Plataforma de automação e orquestração de testes Android multi-dispositivo.
Escopo: automação de **aplicações próprias/autorizadas** para fins de QA — não
inclui (e não deve incluir) automação de interação com apps de terceiros
(ex.: redes sociais) fora do controle de quem está testando.

## Requisitos

- Docker e Docker Compose
- Dispositivos Android com **Depuração USB** habilitada, ou emuladores
  rodando com ADB acessível (`adb devices` deve listá-los no host)
- Para reconhecimento de botões por imagem: capturas de referência (templates)
  dos elementos de UI que você quer localizar

## Subindo o ambiente

```bash
docker compose up --build
```

A API sobe em `http://localhost:8000` (docs interativas em `/docs`).

> Observação: por padrão o `docker-compose.yml` roda os containers `api` e
> `worker` em modo `privileged` com acesso a `/dev/bus/usb`, para o ADB do
> container enxergar dispositivos USB do host. Em ambiente de produção, o mais
> comum é rodar o worker **fora de container**, direto no host que tem os
> cabos/dispositivos conectados, e usar rede/cloud phones (`adb connect`) para
> o resto da fila.

## Fluxo de uso básico

1. **Listar dispositivos conectados**
   ```bash
   curl http://localhost:8000/devices
   ```

2. **Cadastrar um fluxo de teste** (veja `examples/flow_login.json`)
   ```bash
   curl -X POST http://localhost:8000/flows \
     -H "Content-Type: application/json" \
     -d @examples/flow_login.json
   ```

3. **Disparar a execução em vários dispositivos ao mesmo tempo**
   ```bash
   curl -X POST http://localhost:8000/runs \
     -H "Content-Type: application/json" \
     -d '{"flow_id": 1, "device_serials": ["emulator-5554", "R58N30XXXX"]}'
   ```

4. **Consultar o resultado**
   ```bash
   curl http://localhost:8000/runs?flow_id=1
   ```

## Estrutura do projeto

```
app/
  devices.py     -> Gerenciador de dispositivos (ADB)
  vision.py      -> OCR (Tesseract) e template matching (OpenCV)
  executor.py    -> Interpreta e executa um fluxo passo a passo
  tasks.py       -> Orquestração multi-dispositivo via Celery (execução paralela)
  models/db.py   -> Modelos SQLAlchemy (Flow, FlowRun)
  main.py        -> API FastAPI
examples/
  flow_login.json -> Exemplo de fluxo de teste
```

## Blocos de fluxo suportados no MVP

| Ação | Parâmetros | Descrição |
|---|---|---|
| `open_app` | `activity` (opcional) | Abre o app sob teste |
| `wait` | `seconds` | Aguarda N segundos |
| `tap` | `x`, `y` | Toque em coordenada fixa |
| `swipe` | `x1,y1,x2,y2`, `duration_ms` | Gesto de arraste |
| `input_text` | `text` | Digita texto no campo focado |
| `assert_text` | `expected`, `lang` | Valida texto na tela via OCR |
| `find_and_tap` | `template`, `threshold` | Localiza um botão por imagem (OpenCV) e toca nele |
| `screenshot` | — | Captura e salva print da tela |
| `loop` | `times`, `steps` | Repete uma sublista de passos |

## Próximos passos (fora do escopo do MVP)

- Frontend com editor visual (drag-and-drop) dos fluxos
- Uso de modelo de IA para localizar elementos por descrição textual
  ("encontre o botão Continuar"), reduzindo dependência de templates/coordenadas
- Dashboard com métricas agregadas (CPU/RAM dos workers, taxa de sucesso por app)
- Suporte a iOS (via `WebDriverAgent`)
