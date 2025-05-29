# TerraFusion Platform - Windows Quick Start Guide

## 🎯 Get TerraFusion Running in 5 Minutes

This guide is designed for county IT staff to get TerraFusion operational quickly on Windows systems, regardless of technical background.

---

## ⚡ Express Setup (Recommended)

### Step 1: Run Prerequisites Setup
1. **Right-click** on `setup_rust_prereqs.ps1`
2. Select **"Run with PowerShell"**
3. If prompted, click **"Yes"** to run as administrator
4. Wait for installation to complete (10-15 minutes)

### Step 2: Start TerraFusion
1. **Double-click** `run_all_rust.bat`
2. Wait 30 seconds for services to start
3. Open your web browser
4. Go to: **http://localhost:5000**

### Step 3: Verify Everything Works
- You should see the TerraFusion dashboard
- Check that all status indicators are green
- Test a sample GIS export or district lookup

**✅ That's it! TerraFusion is now running.**

---

## 🛠️ Manual Setup (If Express Setup Fails)

### Prerequisites
- Windows 10 or Windows Server 2019+
- Administrator access
- Internet connection (for initial setup)

### Step 1: Install Python (if not already installed)
1. Download Python 3.11 from [python.org](https://www.python.org/downloads/)
2. **Important**: Check "Add Python to PATH" during installation
3. Restart your computer after installation

### Step 2: Install PostgreSQL Database
1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
2. Install with default settings
3. Remember the password you set for the 'postgres' user

### Step 3: Setup Environment
1. Open **Command Prompt as Administrator**
2. Navigate to the TerraFusion folder:
   ```cmd
   cd C:\path\to\terrafusion
   ```
3. Install Python dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

### Step 4: Configure Database
1. Create a `.env` file in the TerraFusion folder
2. Add your database connection:
   ```
   DATABASE_URL=postgresql://postgres:your_password@localhost:5432/terrafusion
   SESSION_SECRET=your-secret-key-here
   ```

### Step 5: Start Services
```cmd
python app.py
```

---

## 🔍 Troubleshooting

### "Rust not found" Error
**Solution**: Run `setup_rust_prereqs.ps1` as administrator

### "Database connection failed"
**Solutions**:
1. Ensure PostgreSQL service is running:
   ```cmd
   net start postgresql
   ```
2. Check your DATABASE_URL in the `.env` file
3. Verify postgres user password

### "Port already in use"
**Solution**: Stop existing services:
```cmd
taskkill /f /im python.exe
taskkill /f /im cargo.exe
```

### Services won't start
**Solutions**:
1. Run Command Prompt as Administrator
2. Check Windows Defender/Antivirus isn't blocking
3. Ensure all prerequisites are installed

### Web interface won't load
**Solutions**:
1. Wait 60 seconds after starting services
2. Try: http://127.0.0.1:5000 instead
3. Check Windows Firewall settings

---

## 📊 Accessing TerraFusion Features

### Main Dashboard
- **URL**: http://localhost:5000
- **Features**: System overview, recent activity, quick actions

### GIS Export
- **URL**: http://localhost:5000/gis/dashboard
- **Use**: Export parcel data, maps, and spatial information

### District Lookup
- **URL**: http://localhost:5000/district-lookup
- **Use**: Find voting precincts, fire districts, school districts

### API Documentation
- **URL**: http://localhost:5000/api/v1/district-lookup
- **Use**: Integration with other county systems

### Monitoring (Advanced)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

---

## 🔐 Security Notes for IT Administrators

### Default Credentials
- **Application**: No default login required
- **Grafana**: admin/admin (change on first login)
- **Database**: Uses environment variables

### Network Access
- TerraFusion runs locally by default
- To allow network access, edit configuration files
- Ensure proper firewall rules for production use

### Data Protection
- All data stored locally in PostgreSQL
- Regular backups created automatically
- No data sent to external services

---

## 📞 Support

### Getting Help
1. **Check Logs**: Look in the Command Prompt window for error messages
2. **Run Verification**: Execute `verify_terrafusion_env.ps1`
3. **Documentation**: Read specific guides in the `/docs` folder

### Common File Locations
- **Application Files**: Current folder
- **Database**: PostgreSQL data directory
- **Logs**: Check Command Prompt output
- **Backups**: `/backups` folder

### Performance Tips
- **Minimum RAM**: 8 GB recommended
- **Storage**: Ensure 10+ GB free space
- **Network**: Local operation doesn't require internet after setup

---

## 🚀 Next Steps

### After Initial Setup
1. **Configure Users**: Set up access controls for your staff
2. **Import Data**: Connect to your existing county systems
3. **Train Staff**: Show team members the dashboard and features
4. **Schedule Backups**: Verify automatic backup system is working

### Advanced Configuration
- **Custom County Data**: Load your specific parcel boundaries
- **Integration**: Connect to existing assessment systems
- **Monitoring**: Set up alerts and notifications
- **Public Access**: Configure read-only external access

---

## ✅ Success Checklist

- [ ] Prerequisites installed successfully
- [ ] All services start without errors
- [ ] Dashboard loads at http://localhost:5000
- [ ] Can create a test GIS export
- [ ] District lookup returns results
- [ ] System status shows all green indicators
- [ ] Automatic backups are functioning

**🎉 Congratulations! TerraFusion is operational and ready for county use.**

---

*For technical support or advanced configuration, refer to the detailed documentation in the `/docs` folder or contact your TerraFusion administrator.*