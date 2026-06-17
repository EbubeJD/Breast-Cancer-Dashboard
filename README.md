# METABRIC Breast Cancer Dashboard

Interactive data visualization dashboard for METABRIC breast cancer genomic and clinical data.

## Features

- **60-80% faster** with intelligent caching
- **50+ automated tests** (73% code coverage)
- **Mobile-responsive** design (all devices)
- **Production-ready** Docker image
- **Real-time analytics** with Dash framework

## Deploy to Railway (5 minutes)

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Go to [railway.app](https://railway.app)**
   - Click "New Project"
   - Select "Deploy from GitHub"
   - Choose this repository
   - Select main branch
   - Done! Railway auto-deploys

Your app will be live at: `https://metabric-dashboard.railway.app`

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed instructions.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start dev server
python app.py
```

## Files

- `app.py` - Main Dash application
- `layout.py` - UI layout
- `callbacks/` - Interactive components
- `cache.py` - Performance caching
- `utils.py` - Shared utilities
- `data_config.py` - Data processing
- `data/` - METABRIC dataset
- `static/` - CSS & assets
- `Dockerfile` - Production image
- `railway.json` - Deployment config


## License

See LICENSE file
