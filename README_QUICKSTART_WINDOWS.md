# TerraFusion Platform - Windows Quick Start Guide

## 🚀 3-Click Setup for County IT Staff

This guide gets TerraFusion running on Windows in 3 simple steps. No technical expertise required!

---

## Step 1: Download & Extract
1. Download the TerraFusion package to your computer
2. Extract all files to `C:\TerraFusion` (or your preferred location)
3. Open the extracted folder

## Step 2: Install Prerequisites
1. **Right-click** on `setup_rust_prereqs.ps1`
2. Select **"Run with PowerShell"**
3. If prompted, click **"Yes"** to allow the script to run
4. Wait for installation to complete (10-15 minutes)

## Step 3: Start TerraFusion
1. **Double-click** `run_all_rust.bat`
2. Wait for services to start (30-60 seconds)
3. Your browser will open automatically to the dashboard

---

## 🎯 That's It! You're Ready

### Access Your Platform:
- **Main Dashboard**: http://localhost:5000/dashboard
- **GIS Export Tool**: http://localhost:5000/gis-dashboard
- **District Lookup**: http://localhost:5000/district-lookup-dashboard
- **System Health**: http://localhost:5000/health

### Verify Everything Works:
✅ Dashboard loads and shows county data  
✅ GIS Export creates sample exports  
✅ District lookup finds locations  
✅ Health check shows all green  

---

## 🔧 Quick Configuration

### Database Setup (Optional)
If you have an existing PostgreSQL database:
1. Open `.env` file in Notepad
2. Update `DATABASE_URL` with your database connection
3. Restart by running `run_all_rust.bat` again

### County Configuration
1. Navigate to `county_configs` folder
2. Copy your county's configuration files here
3. Restart the platform

---

## 📞 Getting Help

### Common Issues:

**Port Already in Use Error**
- Close any existing TerraFusion windows
- Wait 30 seconds, then run `run_all_rust.bat` again

**Python Not Found Error**
- Re-run `setup_rust_prereqs.ps1` as Administrator
- Restart your computer after installation

**Dashboard Won't Load**
- Wait 2-3 minutes after starting services
- Check Windows Firewall isn't blocking ports 5000-8081

### Support Contacts:
- Technical Support: [Your support email]
- Documentation: Check the `docs` folder
- Emergency: [Emergency contact]

---

## 🛠️ Advanced Operations

### Stop All Services:
Close all TerraFusion command windows that opened

### Restart Services:
Double-click `run_all_rust.bat` again

### Clean Uninstall:
1. Close all TerraFusion windows
2. Delete the TerraFusion folder
3. Optionally remove Python/Rust if not needed elsewhere

### Update TerraFusion:
1. Stop all services
2. Extract new version over existing files
3. Run `run_all_rust.bat`

---

## 📊 System Requirements

### Minimum:
- Windows 10 or Server 2016+
- 4GB RAM
- 2GB disk space
- Internet connection (for initial setup)

### Recommended:
- Windows 11 or Server 2022
- 8GB RAM
- 10GB disk space
- SSD storage

---

## 🔒 Security Notes

- TerraFusion runs on localhost by default (secure)
- No external network access required after setup
- All data stays on your local system
- Regular backups are automatically created

---

## 🎉 Success Checklist

After setup, verify these work:

□ Dashboard loads at http://localhost:5000/dashboard  
□ Can create a test GIS export  
□ District lookup returns results  
□ Health check shows all systems green  
□ County-specific data displays correctly  

**Congratulations! TerraFusion is ready for county operations.**