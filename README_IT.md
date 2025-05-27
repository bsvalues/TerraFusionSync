# 🏛️ TerraFusion Platform - County IT Guide

**Enterprise GIS Data Management & AI Analysis Platform**

This guide helps county IT staff deploy, configure, and maintain the TerraFusion platform for reliable geospatial data processing and analysis.

---

## 🎯 What TerraFusion Does

TerraFusion provides county staff with:

- **📊 GIS Data Export**: Convert parcel, zoning, and property data to various formats (CSV, GeoJSON, Shapefile, KML)
- **🤖 AI-Powered Analysis**: Intelligent insights about property data and sync operations  
- **🗺️ District Lookup**: Find voting precincts, fire districts, and school districts by address or coordinates
- **📈 Real-Time Monitoring**: Performance dashboards and health checks
- **🔄 Automated Sync**: Keep county data synchronized across systems

---

## 🚀 Quick Start for County IT

### 1. System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Operating System** | Windows 10/Server 2019, Ubuntu 18.04+ | Windows 11/Server 2022, Ubuntu 22.04+ |
| **Memory (RAM)** | 8 GB | 16 GB+ |
| **Storage** | 50 GB free | 200 GB+ SSD |
| **Database** | PostgreSQL 12+ | PostgreSQL 15+ |
| **Network** | 100 Mbps | 1 Gbps |

### 2. Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/your-county/terrafusion-platform.git
cd terrafusion-platform

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Validate configuration
python config_validator.py

# 4. Start the services
python main.py                          # API Gateway (port 5000)
python run_syncservice_workflow_8080.py # Sync Service (port 8080)
```

### 3. Configuration

Create `.env` file with your county settings:

```bash
# Generate template
python config_validator.py --template

# Edit the .env file
DATABASE_URL=postgresql://user:password@localhost:5432/county_gis
SESSION_SECRET=your-secure-random-key-here
NARRATOR_AI_URL=http://localhost:11434
```

---

## 🔧 Daily Operations

### Health Monitoring

**Check System Status:**
```bash
# Visit in web browser:
http://localhost:5000/api/status

# Or use curl:
curl http://localhost:5000/api/status
```

**View Performance Dashboard:**
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

### User Support

**Common Staff Questions:**

| Question | Answer |
|----------|---------|
| "How do I export parcel data?" | Visit `/gis/dashboard` and fill out the export form |
| "What formats are supported?" | Check `/api/formats` for complete list with recommendations |
| "Why is my export taking so long?" | Large datasets (>10K records) may take 2-5 minutes |
| "Can I get AI analysis?" | Yes, use `/api/v1/ai/analyze/gis-export` after export completes |

### Troubleshooting

**Service Won't Start:**
1. Check configuration: `python config_validator.py`
2. Verify database connection: `psql $DATABASE_URL`
3. Check port availability: `netstat -an | grep :5000`

**Slow Performance:**
1. Check system resources: `/api/status`
2. Review Grafana dashboards for bottlenecks
3. Consider increasing server memory

**Export Failures:**
1. Verify data exists in target area
2. Check available disk space
3. Review error logs in application output

---

## 🔒 Security & Access Control

### User Authentication

TerraFusion uses email-based identification:
- Staff enter their county email (e.g., `staff@countygov.us`)
- No passwords required for read operations
- Export jobs are tagged with user email for tracking

### Data Protection

- **Database**: Uses PostgreSQL with connection encryption
- **File Exports**: Stored temporarily, auto-cleaned after download
- **API Access**: Rate-limited to prevent abuse
- **Logs**: Rotated automatically, no sensitive data stored

### Network Security

**Required Ports:**
- 5000: API Gateway (staff access)
- 8080: Sync Service (internal only)
- 5432: PostgreSQL (database access)
- 3000: Grafana (monitoring, optional)
- 9090: Prometheus (metrics, optional)

**Firewall Recommendations:**
```bash
# Allow staff access to main application
ufw allow from county-network to any port 5000

# Block external access to internal services
ufw deny from any to any port 8080
ufw deny from any to any port 5432
```

---

## 🗄️ Database Management

### Backup Procedures

**Automated Backups:**
- Runs hourly during business hours
- Stores 7 days of backups
- Location: `backups/` directory

**Manual Backup:**
```bash
# Create immediate backup
python backup_utilities.py --create

# List available backups
python backup_utilities.py --list

# Restore from backup
python backup_utilities.py --restore backup_file.sql
```

### Data Maintenance

**Regular Tasks:**
- Weekly: Review sync operation logs
- Monthly: Archive old export files
- Quarterly: Update AI models if available

**Storage Monitoring:**
```bash
# Check database size
SELECT pg_size_pretty(pg_database_size('county_gis'));

# Monitor export directory
du -sh exports/
```

---

## 📊 Performance Monitoring

### Key Metrics to Watch

| Metric | Normal Range | Action Required |
|--------|--------------|----------------|
| **CPU Usage** | < 70% | Above 80%: investigate |
| **Memory Usage** | < 80% | Above 90%: restart services |
| **Export Success Rate** | > 95% | Below 90%: check data quality |
| **Response Time** | < 5 seconds | Above 10s: performance tuning |

### Grafana Dashboard

**Pre-configured Panels:**
- GIS Export job success/failure rates
- AI analysis response times
- System resource utilization
- Database connection health

**Setting Up Alerts:**
1. Open Grafana (`http://localhost:3000`)
2. Import dashboard: `grafana/terrafusion_monitoring.json`
3. Configure notification channels (email, Slack)
4. Set thresholds for critical metrics

---

## 🔧 Maintenance Procedures

### Weekly Maintenance

**Every Monday:**
```bash
# Check system health
curl http://localhost:5000/api/status

# Review backup status
ls -la backups/

# Check disk space
df -h

# Restart services if memory usage high
systemctl restart terrafusion-api
systemctl restart terrafusion-sync
```

### Monthly Maintenance

**First Friday of each month:**
```bash
# Update system packages
apt update && apt upgrade

# Clean old export files
find exports/ -mtime +30 -delete

# Vacuum database
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# Update AI models (if available)
# Contact vendor for latest model updates
```

### Emergency Procedures

**Service Down:**
1. Check `/api/status` for error details
2. Review application logs
3. Restart affected services
4. Contact development team if issues persist

**Data Corruption:**
1. Stop all services immediately
2. Restore from most recent backup
3. Investigate root cause
4. Document incident for future prevention

---

## 📞 Support Contacts

### Internal Support

| Issue Type | Contact | Response Time |
|------------|---------|---------------|
| **User Training** | County IT Help Desk | Same day |
| **Configuration** | Database Administrator | 1-2 hours |
| **Performance** | System Administrator | 4 hours |
| **Data Issues** | GIS Coordinator | Next business day |

### Vendor Support

| Component | Vendor | Support Level |
|-----------|--------|---------------|
| **TerraFusion Platform** | Development Team | Priority support |
| **PostgreSQL** | Community/Enterprise | Standard |
| **AI Services** | Ollama/OpenAI | Per contract |

---

## 📚 Additional Resources

### Documentation

- **User Guide**: `README.md` - End user instructions
- **API Documentation**: `/api/help` - Complete API reference
- **Monitoring Setup**: `README_GRAFANA.md` - Dashboard configuration
- **Performance Testing**: `benchmark/README.md` - Performance validation

### Training Materials

- **Staff Training**: 2-hour session covering basic operations
- **Admin Training**: 4-hour session covering maintenance and troubleshooting
- **Video Guides**: Available on county intranet

### Compliance

- **Data Retention**: Follows county data retention policies
- **Audit Logging**: All export operations logged with user identification
- **Privacy**: No personal data exposed in logs or monitoring

---

## 🎯 Success Metrics

**For County Leadership:**
- **95%+ export success rate** - Reliable data access for staff
- **<5 second response times** - Fast user experience
- **99%+ uptime** - Always available when needed
- **Zero data security incidents** - Maintains public trust

**For IT Department:**
- **<2 hours/week maintenance** - Minimal administrative overhead
- **<1 support ticket/week** - Self-service capabilities
- **Automated monitoring alerts** - Proactive issue detection
- **Clear documentation** - Easy knowledge transfer

---

Your TerraFusion platform is designed for reliable, low-maintenance operation that empowers county staff with powerful GIS and AI capabilities while keeping IT overhead minimal. 🎉