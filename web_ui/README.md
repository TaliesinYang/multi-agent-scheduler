# Web UI for Multi-Agent Scheduler

Modern web interface for monitoring and managing the Multi-Agent Scheduler.

## Features

- **Dashboard** - Real-time system status and metrics
- **Task Management** - View and manage tasks
- **Workflow Visualization** - Monitor workflow executions
- **Monitoring Integration** - Links to Jaeger, Prometheus, Grafana

## Quick Start

### Install Dependencies

```bash
pip install fastapi uvicorn jinja2 python-multipart
```

### Run the Web UI

```bash
# Development mode
python web_ui/app.py

# Or with uvicorn
uvicorn web_ui.app:app --host 0.0.0.0 --port 8080 --reload
```

### Access the UI

Open your browser and navigate to:
- http://localhost:8080

## Pages

### Dashboard (/)
- System health status
- Active tasks count
- Error metrics
- Service status
- Quick actions

### Tasks (/tasks)
- Task list
- Task creation
- Task details
- Status tracking

### Workflows (/workflows)
- Workflow management
- Execution history
- Visualization

### Monitoring (/monitoring)
- Links to external monitoring tools
- Metrics summary
- Real-time updates

## API Endpoints

- `GET /` - Dashboard page
- `GET /tasks` - Tasks page
- `GET /workflows` - Workflows page
- `GET /monitoring` - Monitoring page
- `GET /api/health` - Health check API
- `GET /api/tasks` - Tasks list API
- `GET /api/metrics` - Metrics API

## Architecture

```
web_ui/
├── app.py                  # FastAPI application
├── templates/              # Jinja2 templates
│   ├── base.html          # Base template
│   ├── dashboard.html     # Dashboard page
│   ├── tasks.html         # Tasks page
│   ├── workflows.html     # Workflows page
│   └── monitoring.html    # Monitoring page
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   └── js/
│       └── main.js        # JavaScript utilities
└── README.md              # This file
```

## Development

### Adding New Pages

1. Create template in `templates/`
2. Add route in `app.py`
3. Update navigation in `base.html`

### Styling

Edit `static/css/style.css` to customize the appearance.

### JavaScript

Add interactivity in `static/js/main.js`.

## Deployment

### With Docker

The Web UI is included in the main `docker-compose.yml`:

```yaml
services:
  webui:
    build: .
    command: uvicorn web_ui.app:app --host 0.0.0.0 --port 8080
    ports:
      - "8080:8080"
```

### Production Mode

```bash
uvicorn web_ui.app:app --host 0.0.0.0 --port 8080 --workers 4
```

## Features Roadmap

### Completed ✅
- Dashboard with health metrics
- Task list page
- Workflow page
- Monitoring integration
- Responsive design
- Auto-refresh

### Planned 🔮
- Real-time WebSocket updates
- Task creation form
- Workflow editor
- Log viewer
- User authentication
- Dark mode toggle

## Technology Stack

- **Backend**: FastAPI
- **Templates**: Jinja2
- **Styling**: Pure CSS (no frameworks)
- **JavaScript**: Vanilla JS
- **Server**: Uvicorn (ASGI)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

When adding new features:
1. Follow the existing code style
2. Update templates as needed
3. Add API endpoints in `app.py`
4. Document new features

## License

Same as main project (MIT).
