# 🚀 QUICK START - UBEC Visual Node-RED Workflow

## ⚡ 3-Minute Setup

### Step 1: Import the Workflow (1 min)

1. Open Node-RED: `http://localhost:1880`
2. Click menu (☰) → **Import**
3. Click **select a file to import**
4. Browse to: `/home/gabriel/Downloads/mtzview/PROJETOS/UBEC/nodered-visual-complete.json`
5. Click **Import**
6. Click anywhere on the canvas to place the flow

### Step 2: Verify Modbus Settings (30 sec)

The workflow is pre-configured for:
- **IP:** 192.168.10.1
- **Port:** 502

**If your PLC has different settings:**
1. Double-click any **🌡️/🔴/🔵** Modbus node
2. Click the pencil ✏️ icon next to "Server"
3. Update IP address if needed
4. Click **Update**, then **Done**

### Step 3: Deploy! (30 sec)

1. Click the red **Deploy** button (top right)
2. Wait for "Successfully deployed" message
3. Done! ✅

### Step 4: Watch It Work! (1 min)

1. Click the **debug** tab (🐛 icon) in the right sidebar
2. You'll immediately see:
   ```
   🚀 System initialized
   ⏰ Auto collection starting in 3 seconds...
   ```
3. After 3 seconds, watch the magic happen:
   ```
   🎬 Starting collection...
   🌡️ Temperature data received
   🔴 Output data received
   🔵 Input data received
   📦 Data aggregated
   📡 Sent to API
   ✅ Success!
   ```

## 👀 What You'll See

### In Debug Panel (Right Sidebar)

Real-time messages with emojis:

```
[info] 🚀 System Ready
[info] 🎬 Collection started
[msg] 🔍 Req Temps: {fc:3, address:36, quantity:4}
[msg] 🔍 Raw Temps: [235, 312, 456, 678]
[msg] 🔍 Proc Temps: {ambiente: 23.5, quadro: 31.2, ...}
[msg] 🔍 Aggregated: {device_id: "CLP...", timestamp: "..."}
[msg] ✅ API Success: {status: 200}
```

### On Node Status (Below Each Node)

Live status indicators:

- **🚀 Initialize System:** `🟢 System Ready`
- **🎬 Start Collection:** `🔵 Collecting data...`
- **🌡️ Process Temperatures:** `🟢 23.5°C / 31.2°C / 45.6°C / 67.8°C`
- **🔴 Process Outputs:** `🟢 3/10 active`
- **🔵 Process Inputs:** `🟡 5/14 active`
- **📡 POST to API:** `🟢 HTTP 200`

### In Console (If Running Node-RED from Terminal)

Beautiful formatted output with box drawings:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 STARTING NEW DATA COLLECTION CYCLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Timestamp: 2025-11-17T10:30:45.123Z
📊 Target data:
   🌡️  Temperatures (4 sensors)
   🔴 Outputs (10 channels)
   🔵 Inputs (14 channels)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🎮 Interactive Controls

### Manual Trigger

Click the button on the **👆 Manual Trigger** node to force an immediate collection.

### Stop Auto Collection

1. Double-click **⏰ Auto Collect (30s)**
2. Uncheck **Inject once after**
3. Uncheck **Repeat**
4. Click **Done** and **Deploy**

Now only manual triggers will work.

### Change Collection Interval

1. Double-click **⏰ Auto Collect (30s)**
2. Change **Repeat** to your desired seconds (e.g., `60` for 1 minute)
3. Click **Done** and **Deploy**

## 📊 Understanding the Visual Flow

### Left to Right Data Flow

```
Trigger → Collection → Modbus → Processing → Aggregation → API
   ⏰         🎬         📡          ⚙️           📦          📡
```

### Color Coding

- **Red/Orange nodes** = Temperatures 🌡️
- **Red nodes** = Outputs 🔴
- **Blue/Cyan nodes** = Inputs 🔵
- **Green nodes** = Success ✅
- **Red nodes** = Errors ❌
- **Purple nodes** = Dashboard 📊

### Debug Nodes (Green)

Every green **🔍** node shows you data. Click to expand!

## 🔍 Troubleshooting in 30 Seconds

### Problem: No Data Showing

**Check:**
1. Is PLC powered on? ⚡
2. Is IP address correct in Modbus config? 🌐
3. Look at **🔍 Errors** debug node - any red messages? 🔴

### Problem: Collection Stuck

**Fix:**
1. Click **👆 Manual Trigger** to force new collection
2. System has 15s timeout - will auto-reset

### Problem: API Errors

**Check:**
1. Look at **🔍 API Error** debug node
2. Is API server running at `http://localhost:3001`?
3. Try accessing API in browser: `http://localhost:3001/api/health`

### Problem: Too Many Debug Messages

**Fix:**
1. Use the filter in debug panel (funnel icon 🔽)
2. Type keywords like `🌡️` or `Error` to filter
3. Or disable debug nodes you don't need:
   - Double-click debug node
   - Uncheck **Enabled**
   - Click **Done** and **Deploy**

## 💡 Pro Tips

### Tip 1: Search Debug Messages

In debug panel, use filter to search for:
- `🌡️` - Only temperatures
- `🔴` - Only outputs
- `🔵` - Only inputs
- `Error` - Only errors
- `Success` - Only successes

### Tip 2: Expand Messages

Click any message in debug to expand and see full JSON structure.

### Tip 3: Copy Data

Click message → Click copy icon → Paste anywhere

### Tip 4: Clear Debug Panel

Click the trash icon 🗑️ in debug panel to clear old messages.

### Tip 5: Watch Node Status

Hover over any node to see its current status text!

## 📁 Files Created

The workflow automatically creates:

### Backup File

```
/home/gabriel/clp_data_backup.jsonl
```

One JSON line per collection:
```json
{"device_id":"CLP_SCHNEIDER_TM200CE24R","timestamp":"2025-11-17T10:30:45.123Z",...}
{"device_id":"CLP_SCHNEIDER_TM200CE24R","timestamp":"2025-11-17T10:31:15.456Z",...}
```

View it:
```bash
tail -f /home/gabriel/clp_data_backup.jsonl
# or
cat /home/gabriel/clp_data_backup.jsonl | jq
```

## 🎯 What Gets Collected?

### Every 30 Seconds:

✅ **4 Temperature Readings**
- Ambiente (ambient)
- Quadro Elétrico (electrical panel)
- Módulo FV (PV module)
- Transformador (transformer)

✅ **10 Output States**
- Comunicação OK, Usina Gerando, Falha, Alarme, etc.

✅ **14 Input States**
- DJ Geral, Serviço Auxiliar, Botões, etc.

✅ **Automatic Alerts**
- High temperature warnings
- System fault alerts
- Emergency conditions

## 🚀 Next Level

### Add a Dashboard

```bash
cd ~/.node-red
npm install node-red-dashboard
```

Then drag dashboard nodes (gauge, chart, text, LED) onto the canvas and connect to the **📊 Dashboard** output nodes!

### View Statistics

Every 5 minutes, check **🔍 Statistics** debug node to see:
- Total collections
- Success rate
- Memory usage
- System uptime

## 🎉 You're All Set!

The workflow is now:
- ✅ Collecting data every 30 seconds
- ✅ Showing debug messages
- ✅ Displaying status indicators
- ✅ Backing up to file
- ✅ Sending to API
- ✅ Generating alerts
- ✅ Tracking statistics

**Just watch the debug panel and enjoy the show!** 🌞⚡

---

**Need more details?** Read `README_NODERED_VISUAL.md`

**Having issues?** All debug nodes are your friends - they show everything! 🔍

