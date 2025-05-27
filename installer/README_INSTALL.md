# 🏛️ TerraFusion Platform - Windows Installation Guide

**One-Click County GIS Platform Deployment**

This installer creates a complete, production-ready TerraFusion environment on Windows systems for county government use.

---

## 🎯 What Gets Installed

The TerraFusion installer provides:

- **🖥️ Complete Platform**: API Gateway, Sync Service, GIS Export Engine
- **🤖 AI Assistant**: NarratorAI with local Ollama runtime (optional)
- **💾 Database**: Embedded PostgreSQL or connection to existing server
- **🔧 Windows Services**: Auto-start background services
- **📊 Sample Data**: Test parcels and zoning data (optional)
- **🎛️ Desktop Integration**: Start menu shortcuts and system tray

---

## 🚀 Installation Steps

### 1. Download and Run Installer

1. Download `TerraFusion-2.1.0-Setup.exe`
2. Right-click and select **"Run as administrator"**
3. Follow the installation wizard

### 2. Configuration Options

During installation, you'll configure:

| Option | Recommendation | Purpose |
|--------|----------------|---------|
| **County Name** | Enter your county | Customizes interface and file naming |
| **Database** | Embedded PostgreSQL | Simplest setup, no existing server needed |
| **AI Features** | Enable | Provides intelligent data analysis |
| **Auto-Start Services** | Enable | Services start with Windows |
| **Sample Data** | Enable for testing | Provides data for training and validation |

### 3. Post-Installation

After installation completes:

1. **Validation**: Run the validation script from Start Menu
2. **Access Platform**: Open browser to `http://localhost:5000`
3. **Desktop Shortcut**: Use the TerraFusion Platform icon

---

## 🔧 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10 (64-bit) or Windows Server 2019 |
| **RAM** | 8 GB |
| **Storage** | 10 GB available space |
| **Network** | Internet connection for AI model download |
| **Permissions** | Administrator rights for installation |

### Recommended Specifications

| Component | Recommendation |
|-----------|----------------|
| **OS** | Windows 11 or Windows Server 2022 |
| **RAM** | 16 GB or more |
| **Storage** | 50 GB SSD storage |
| **CPU** | 4+ cores, 2.5 GHz |
| **Network** | 100 Mbps or faster |

---

## 🛠️ Installation Components

### Core Platform (Required)
- **TerraFusion API Gateway**: Web interface and REST API
- **Sync Service**: Data synchronization engine
- **Configuration Files**: County-specific settings

### GIS Export Engine (Recommended)
- **Advanced Export Formats**: Shapefile, GeoJSON, KML, CSV, GeoPackage
- **GDAL Libraries**: Industry-standard geospatial processing
- **Format Validation**: Ensures data integrity

### NarratorAI Assistant (Optional)
- **Ollama Runtime**: Local AI processing (no cloud required)
- **AI Model**: Llama 3.2 (3B parameters)
- **Analysis Features**: Intelligent insights about GIS data

### Database Options

**Embedded PostgreSQL (Recommended):**
- Complete database server included
- No additional setup required
- Optimized for TerraFusion

**External PostgreSQL:**
- Connect to existing county database server
- Requires manual configuration
- Better for enterprise environments

### Windows Services Integration
- **Automatic Startup**: Services start with Windows
- **Background Operation**: No user login required
- **Service Management**: Standard Windows service controls

---

## 🎛️ Using TerraFusion

### First-Time Access

1. Open web browser
2. Navigate to `http://localhost:5000`
3. You'll see the TerraFusion dashboard

### Main Features

**🗺️ GIS Export Dashboard (`/gis/dashboard`):**
- Export parcel, zoning, and property data
- Multiple format options with guidance
- Real-time export progress

**🔍 District Lookup (`/district-lookup/dashboard`):**
- Find districts by address or coordinates
- Voting precincts, fire districts, school districts
- Instant lookup results

**🤖 AI Analysis:**
- Automatically available after GIS exports
- Provides insights about data patterns
- User-friendly summaries and recommendations

### API Access

**Health Check:** `http://localhost:5000/api/status`
**Available Formats:** `http://localhost:5000/api/formats`
**Help Documentation:** `http://localhost:5000/api/help`

---

## 🔒 Security and Access

### Default Security Settings

- **Local Access Only**: Platform accessible only from the installed computer
- **No Authentication Required**: Suitable for internal county use
- **Data Protection**: Exports are temporary and auto-cleaned

### Network Access (Optional)

To allow network access from other county computers:

1. Open Windows Firewall
2. Add inbound rule for port 5000
3. Update county.env: `ALLOW_NETWORK_ACCESS=true`
4. Restart TerraFusion services

### User Identification

- Staff enter their county email for tracking
- All export operations are logged with user information
- No passwords required for read operations

---

## 🔧 Maintenance and Support

### Daily Operations

**Check System Health:**
- Visit `http://localhost:5000/api/status`
- Verify all components show "healthy"

**View Logs:**
- Start Menu → TerraFusion Platform → Logs
- Check for any error messages

### Service Management

**Start/Stop Services:**
```cmd
net start "TerraFusion Gateway"
net stop "TerraFusion Gateway"
net start "TerraFusion Sync"
net stop "TerraFusion Sync"
```

**Service Status:**
```cmd
sc query "TerraFusion Gateway"
sc query "TerraFusion Sync"
```

### Backup and Recovery

**Automatic Backups:**
- Database backed up hourly
- Stored in `C:\ProgramData\TerraFusion\backups\`
- 7 days retention

**Manual Backup:**
- Start Menu → TerraFusion Platform → Configuration
- Run county_setup.bat for backup options

---

## 🚨 Troubleshooting

### Common Issues

**"Platform not accessible" (404 error):**
1. Check if services are running: `sc query "TerraFusion Gateway"`
2. Restart services if needed: `net start "TerraFusion Gateway"`
3. Check firewall settings
4. Verify port 5000 is not blocked

**"AI features not working":**
1. Ensure Ollama service is running
2. Run AI setup: Start Menu → TerraFusion Platform → Configuration
3. Check internet connection for model download

**"Export jobs failing":**
1. Verify database connection: `http://localhost:5000/api/status`
2. Check available disk space
3. Review logs for specific error messages

**"Services won't start":**
1. Check Windows Event Viewer
2. Verify file permissions in installation directory
3. Run as administrator: `net start "TerraFusion Gateway"`

### Getting Help

**Built-in Help:**
- Platform Help: `http://localhost:5000/api/help`
- Start Menu → TerraFusion Platform → User Guide

**Log Files:**
- Gateway: `C:\Program Files\TerraFusion\logs\gateway.log`
- Sync Service: `C:\Program Files\TerraFusion\logs\sync.log`

**Support Contacts:**
- County IT Help Desk (for user questions)
- System Administrator (for technical issues)
- Vendor Support (for platform bugs)

---

## 🎯 Success Checklist

After installation, verify these items work:

- [ ] **Web Access**: `http://localhost:5000` loads successfully
- [ ] **Health Check**: `/api/status` shows all services healthy
- [ ] **GIS Export**: Can create a test export job
- [ ] **District Lookup**: Can search by address or coordinates
- [ ] **Services Running**: Both TerraFusion services show as "Running"
- [ ] **Desktop Shortcuts**: Start menu items work correctly

---

## 📋 Uninstallation

To remove TerraFusion:

1. **Add/Remove Programs**: Control Panel → Programs → TerraFusion Platform
2. **OR Start Menu**: TerraFusion Platform → Uninstall
3. **Services**: Automatically stopped and removed
4. **Data**: Optionally preserve data in `C:\ProgramData\TerraFusion\`

---

Your TerraFusion Platform is now ready to modernize your county's GIS operations with professional-grade tools and AI-powered insights! 🎉

For additional support and updates, visit your county IT department or system administrator.