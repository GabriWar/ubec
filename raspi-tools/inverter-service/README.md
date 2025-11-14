# MTZ View - Huawei Inverter Service

Serviço modular Python para integração de inversores Huawei SUN2000 com o sistema MTZ View.

## Características

- Suporte completo à linha Huawei SUN2000 (3KTL até 100KTL e superiores)
- Conexão via Modbus RTU (USB/RS485) ou Modbus TCP
- Totalmente configurável via argumentos de linha de comando
- Leitura automática de todos os parâmetros importantes
- Envio de dados para backend MTZ View
- Retry automático em caso de falhas
- Logging colorido e detalhado
- Pronto para rodar como serviço systemd na Raspberry Pi

## Modelos Suportados

Todos os inversores da linha SUN2000:
- SUN2000-3KTL-M0/M1
- SUN2000-4KTL-M0/M1
- SUN2000-5KTL-M0/M1
- SUN2000-6KTL-M0/M1
- SUN2000-8KTL-M0/M1
- SUN2000-10KTL-M0/M1
- SUN2000-12KTL-M0/M1
- SUN2000-15KTL-M0/M1
- SUN2000-17KTL-M0/M1
- SUN2000-20KTL-M0/M1
- SUN2000-25KTL-M3
- SUN2000-30KTL-M3
- SUN2000-36KTL-M3
- SUN2000-40KTL-M3
- SUN2000-50KTL-M3
- SUN2000-60KTL-M3/M6
- SUN2000-75KTL-M6
- SUN2000-90KTL-M6
- SUN2000-100KTL-M1/M6
- SUN2000-110KTL-M6
- SUN2000-125KTL-M6

## Instalação

### Pré-requisitos

```bash
# Raspberry Pi / Debian / Ubuntu
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv git

# Arch Linux
sudo pacman -S python python-pip git
```

### Instalação do Serviço

```bash
cd /home/gabriel/Downloads/mtzview/inverter-service

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## Uso

### Conexão USB/RS485 (Padrão)

```bash
# Básico - usa defaults (/dev/ttyUSB0, 9600 baud)
python3 main.py

# Especificando porta serial
python3 main.py --serial-port /dev/ttyUSB0

# Com todas as opções
python3 main.py \
  --serial-port /dev/ttyUSB0 \
  --baudrate 9600 \
  --slave-id 1 \
  --poll-interval 30 \
  --backend-url http://localhost:3001 \
  --log-level INFO
```

### Conexão TCP/IP

```bash
# Via rede (SDongle, WiFi-AP, etc)
python3 main.py \
  --tcp-host 192.168.1.100 \
  --tcp-port 502 \
  --poll-interval 30
```

### Opções de Linha de Comando

```
Inverter Connection:
  -t, --connection-type {rtu,tcp}
                        Connection type (default: rtu for USB/RS485)

RTU/Serial Connection (USB/RS485):
  -p, --serial-port     Serial port device (default: /dev/ttyUSB0)
  -b, --baudrate        Serial baudrate (default: 9600)
  -s, --slave-id        Modbus slave ID (default: 1)

TCP Connection (Network):
  --tcp-host            TCP host/IP address (auto-enables TCP mode)
  --tcp-port            TCP port (default: 502)

Polling Configuration:
  -i, --poll-interval   Polling interval in seconds (default: 30)

Backend Configuration:
  -u, --backend-url     Backend API URL (default: http://localhost:3001)
  --backend-timeout     Backend request timeout in seconds (default: 10)

Logging:
  -l, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: INFO)

Utility:
  -v, --version         Show version
  --show-config         Show current configuration and exit
  -h, --help            Show help message
```

### Verificar Configuração

```bash
python3 main.py --show-config
```

### Exemplos Completos

**Raspberry Pi com USB:**
```bash
python3 main.py \
  --serial-port /dev/ttyUSB0 \
  --baudrate 9600 \
  --poll-interval 30 \
  --backend-url http://localhost:3001
```

**Rede TCP com polling a cada 1 minuto:**
```bash
python3 main.py \
  --tcp-host 192.168.200.1 \
  --tcp-port 502 \
  --poll-interval 60 \
  --log-level DEBUG
```

**Modo debug com backend remoto:**
```bash
python3 main.py \
  --serial-port /dev/ttyUSB0 \
  --backend-url http://192.168.1.50:3001 \
  --log-level DEBUG
```

## Dados Coletados

O serviço coleta automaticamente:

### Potência
- Potência de entrada DC
- Potência ativa AC
- Potência reativa
- Fator de potência

### Tensão e Corrente
- Tensões de linha (AB, BC, CA)
- Tensões de fase (A, B, C)
- Correntes de fase (A, B, C)

### Energia
- Energia gerada diária
- Energia total acumulada

### Temperatura
- Temperatura interna do inversor

### Grid
- Frequência da rede

### Status
- Status do dispositivo
- Alarmes (3 registros)

### Strings PV
- Tensão e corrente de até 4 strings PV

## Configuração como Serviço Systemd

Para rodar automaticamente na Raspberry Pi:

```bash
# Copiar arquivo de serviço
sudo cp systemd/huawei-inverter.service /etc/systemd/system/

# Editar o arquivo para ajustar caminhos e argumentos
sudo nano /etc/systemd/system/huawei-inverter.service

# Recarregar systemd
sudo systemctl daemon-reload

# Habilitar serviço
sudo systemctl enable huawei-inverter

# Iniciar serviço
sudo systemctl start huawei-inverter

# Ver status
sudo systemctl status huawei-inverter

# Ver logs
sudo journalctl -u huawei-inverter -f
```

## Troubleshooting

### Porta serial não encontrada

```bash
# Listar portas seriais disponíveis
ls -l /dev/ttyUSB*
ls -l /dev/ttyACM*

# Dar permissão ao usuário
sudo usermod -a -G dialout $USER
# Fazer logout e login novamente

# Verificar permissões
ls -l /dev/ttyUSB0
```

### Inversor não responde

1. Verificar conexão física (cabo USB/RS485)
2. Verificar baudrate correto (geralmente 9600)
3. Verificar slave ID (geralmente 1)
4. Tentar modo debug: `--log-level DEBUG`
5. Verificar se apenas uma conexão está ativa (inversores Huawei aceitam apenas 1 conexão simultânea)

### Backend não recebe dados

```bash
# Verificar se backend está rodando
curl http://localhost:3001/health

# Verificar conectividade
ping <backend-ip>

# Testar com backend local primeiro
python3 main.py --backend-url http://localhost:3001
```

### Erros de importação

```bash
# Reinstalar dependências
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

## Estrutura Modular

```
inverter-service/
├── main.py                    # Entry point com CLI
├── requirements.txt           # Dependências Python
├── config/
│   ├── __init__.py
│   └── config.py             # Configuração centralizada
├── modules/
│   ├── __init__.py
│   ├── inverter_client.py    # Cliente Modbus do inversor
│   └── backend_client.py     # Cliente HTTP para backend
├── utils/
│   ├── __init__.py
│   └── logger.py             # Logging configurável
└── systemd/
    └── huawei-inverter.service  # Serviço systemd
```

## Desenvolvimento

### Adicionar novos registros

Editar `modules/inverter_client.py` e adicionar registros às listas:
- `POWER_REGISTERS`
- `VOLTAGE_CURRENT_REGISTERS`
- `ENERGY_REGISTERS`
- etc.

Todos os registros disponíveis estão em `huawei_solar.register_names`.

### Modificar formatação de dados

Editar método `_format_results()` em `InverterClient`.

### Adicionar novo backend

Criar novo client em `modules/` seguindo o padrão de `backend_client.py`.

## API Backend Esperada

O serviço envia dados via POST para `/api/inverter/telemetry`:

```json
{
  "device_id": "SUN2000-100KTL-M1",
  "timestamp": "2025-11-14T10:30:00",
  "power": {
    "input_power": {"value": 98500, "unit": "W"},
    "active_power": {"value": 97200, "unit": "W"},
    ...
  },
  "voltage_current": {...},
  "energy": {...},
  "temperature": {...},
  "grid": {...},
  "status": {...},
  "pv_strings": {...},
  "metadata": {
    "connection_type": "rtu",
    "data_quality": "good",
    "read_timestamp": "2025-11-14T10:30:00"
  }
}
```

## Licença

Propriedade de UBEC Automação

## Suporte

Para problemas, consulte os logs detalhados:

```bash
# Modo debug
python3 main.py --log-level DEBUG

# Via systemd
sudo journalctl -u huawei-inverter -n 100 --no-pager
```
