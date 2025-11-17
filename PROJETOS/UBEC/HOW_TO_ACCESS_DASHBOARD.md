# 🌐 How to Access Your Dashboard

## 🚀 Quick Access

### Dashboard URL:
```
http://localhost:1880/ui
```

Just open your web browser and go to that address!

---

## 📋 Step-by-Step Instructions

### 1️⃣ Import the Dashboard Workflow

1. **Open Node-RED** in your browser:
   ```
   http://localhost:1880
   ```

2. **Import the new workflow:**
   - Click the **☰ menu** (top right)
   - Select **Import**
   - Click **select a file to import**
   - Browse to: `/home/gabriel/Downloads/mtzview/PROJETOS/UBEC/nodered-with-dashboard-ui.json`
   - Click **Import**
   - Click anywhere on canvas to place

3. **Deploy:**
   - Click the red **Deploy** button (top right)
   - Wait for "Successfully deployed"

### 2️⃣ Access the Dashboard

Open your browser and go to:
```
http://localhost:1880/ui
```

**That's it!** 🎉

---

## 🎨 What You'll See on the Dashboard

### 🌡️ Temperature Section
**4 Beautiful Gauges:**
- 🌡️ **Ambiente** (Ambient) - Blue gauge, 0-60°C
- ⚡ **Quadro Elétrico** (Electrical Panel) - 0-80°C
- ☀️ **Módulo FV** (PV Module) - 0-90°C
- 🔌 **Transformador** (Transformer) - 0-120°C

**Plus a Live Chart:**
- 📈 **Temperature Trends** - Last 10 minutes of history

### 🔴 Outputs Status (LED Indicators)
**10 LED indicators showing:**
- ✅ Comunicação OK (green when active)
- ✅ Usina Gerando (green when active)
- 🔴 Falha (RED when active - system fault!)
- 🟠 Alarme (orange when active)
- 🔴 Emergência (RED when active - emergency!)
- 🔵 Reset Rasp
- 🔵 Reset 3G
- ⚪ Reserva 1, 2, 3

### 🔵 Inputs Status (LED Indicators)
**14 LED indicators showing:**
- 🟠 DJ Geral Aberto (orange when open)
- ✅ DJ Geral Fechado (green when closed)
- ⚪ Reserva I02-I09 (grey when active)
- ✅ Serviço Auxiliar (green when OK)
- 🔵 Botão Close (blue when pressed)
- 🟠 Botão Trip (orange when pressed)
- 🔴 **EMERGÊNCIA** (RED when pressed!)

### 🚨 Alerts Section
- Shows active alerts in real-time
- Color-coded by severity:
  - 🔴 **RED** = High severity (fault, emergency)
  - 🟠 **ORANGE** = Medium severity (alarm)
  - 🟡 **YELLOW** = Low severity
- ✅ Shows "Sistema Operacional" when no alerts

### 📊 System Statistics
- **Total Collections** - Number of data collections
- **Success Rate** - Gauge showing % success (0-100%)
- **System Uptime** - How long the system has been running

---

## 🎯 Live Dashboard Features

### Real-Time Updates
- Data updates **every 30 seconds** automatically
- No need to refresh the page!
- LEDs light up/turn off instantly
- Gauges animate smoothly
- Chart plots new points in real-time

### Color Coding
- 🟢 **Green** = Good/OK/Active (normal)
- 🔵 **Blue** = Information/Button pressed
- 🟠 **Orange** = Warning/Caution
- 🔴 **Red** = Alert/Fault/Emergency
- ⚪ **Grey** = Inactive/Reserved

### Responsive Design
- Works on desktop, tablet, and mobile
- Automatically adjusts layout
- Touch-friendly on mobile devices

---

## 🖥️ Desktop vs Mobile

### Desktop View (Recommended)
- Full width layout
- All sections visible at once
- Best for monitoring

### Mobile View
- Sections stack vertically
- Scroll to see all data
- Touch-friendly buttons
- Works great for checking status on-the-go!

---

## 📱 Access from Other Devices

### Same Network
If you want to access the dashboard from another computer/phone on the same network:

1. **Find your computer's IP address:**
   ```bash
   hostname -I
   ```
   Example output: `192.168.1.100`

2. **On the other device, go to:**
   ```
   http://192.168.1.100:1880/ui
   ```
   (Replace `192.168.1.100` with your actual IP)

### Different Network
If you need remote access, you'll need to set up:
- Port forwarding on your router, OR
- VPN access, OR  
- Reverse proxy (like ngrok)

---

## 🔧 Customization

### Change Update Interval
1. In Node-RED editor, find **⏰ Auto Collect (30s)** node
2. Double-click it
3. Change **Repeat** field (default: 30 seconds)
4. Click **Done** and **Deploy**

### Change Color Themes
1. Double-click any gauge or LED node
2. Edit the **Colors** section
3. Click **Done** and **Deploy**

### Rearrange Dashboard
1. Click **☰ menu** → **Dashboard**
2. In the sidebar, use **Layout** tab
3. Drag and drop groups to reorder
4. Click **Deploy**

---

## 🐛 Troubleshooting

### Dashboard Not Loading?

**1. Check Node-RED is running:**
   ```bash
   # If you started it manually:
   node-red
   
   # If it's a service:
   sudo systemctl status nodered
   ```

**2. Verify the URL:**
   - Should be: `http://localhost:1880/ui`
   - NOT: `http://localhost:1880` (that's the editor)

**3. Check browser console:**
   - Press `F12` to open developer tools
   - Look for errors in the Console tab

**4. Try another browser:**
   - Chrome, Firefox, Edge all work great

### Dashboard Shows "No Data"?

**Wait 30 seconds** - The first collection happens 3 seconds after startup, then every 30 seconds.

### Gauges Not Moving?

1. Check debug panel in Node-RED editor
2. Look for Modbus errors
3. Verify PLC connection (IP: 192.168.10.1)

### LEDs All Grey?

This is normal if no inputs/outputs are active. Try clicking the **👆 Manual Trigger** in Node-RED to force a collection.

---

## 📸 Screenshot Reference

When working correctly, you should see:

```
╔══════════════════════════════════════════════════════════════╗
║           UBEC Solar Plant - Dashboard                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🌡️ Temperatures                                             ║
║  ┌──────────┬──────────┬──────────┬──────────┐             ║
║  │ Ambiente │  Quadro  │ Módulo FV│  Trafo   │             ║
║  │  23.5°C  │  31.2°C  │  45.6°C  │  67.8°C  │             ║
║  │    🌡️    │    ⚡    │    ☀️    │    🔌    │             ║
║  └──────────┴──────────┴──────────┴──────────┘             ║
║                                                              ║
║  📈 Temperature Trends                                       ║
║  ┌─────────────────────────────────────────────────────────┐║
║  │  [Live chart showing 4 lines for each temperature]     │║
║  └─────────────────────────────────────────────────────────┘║
║                                                              ║
║  🔴 Outputs Status        │  🔵 Inputs Status              ║
║  ─────────────────────────┼──────────────────────────────  ║
║  ✅ Comunicação OK        │  🟠 DJ Aberto                  ║
║  ✅ Usina Gerando         │  ✅ DJ Fechado                 ║
║  ⚪ Falha                 │  ⚪ Reserva I02                ║
║  ⚪ Alarme                │  ⚪ Reserva I03                ║
║  ⚪ Emergência            │  ... (more inputs)             ║
║                                                              ║
║  🚨 Alertas Ativos                                          ║
║  ┌─────────────────────────────────────────────────────────┐║
║  │  ✓ Sistema Operacional                                 │║
║  └─────────────────────────────────────────────────────────┘║
║                                                              ║
║  📊 System Statistics                                       ║
║  ┌──────────┬──────────────┬────────────────┐              ║
║  │   150    │   Success    │   Uptime       │              ║
║  │Collections│   98.5%     │   3600 s       │              ║
║  └──────────┴──────────────┴────────────────┘              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 🎉 Enjoy Your Dashboard!

Your solar plant monitoring system is now **fully visual** with:

✅ **Live temperature gauges** with color warnings
✅ **LED status indicators** for all I/O
✅ **Real-time chart** showing temperature trends
✅ **Alert display** for critical conditions
✅ **System statistics** for monitoring health
✅ **Auto-updating** every 30 seconds
✅ **Mobile-friendly** responsive design

**Access it anytime at:** `http://localhost:1880/ui` 🌞⚡

---

## 📚 Additional Resources

- **Node-RED Editor:** `http://localhost:1880` (for configuration)
- **Debug Console:** Click the 🐛 tab in Node-RED editor
- **Backup Data:** `/home/gabriel/clp_data_backup.jsonl`
- **Documentation:** See `README_NODERED_VISUAL.md` and `QUICK_START.md`

---

**Questions? Check the debug panel in Node-RED - it shows everything!** 🔍

