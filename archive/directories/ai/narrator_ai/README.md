# NarratorAI - AI-Powered Text Processing for TerraFusion

🤖 **NarratorAI** is a high-performance Rust microservice that provides intelligent natural language processing for property assessment data using local Ollama models.

## Features

- **Property Summarization** - Convert complex property data into clear summaries
- **Property Classification** - Automatically categorize properties by type
- **Data Explanation** - Translate technical assessment data into plain language
- **Local AI Processing** - Uses Ollama for offline, secure AI capabilities
- **Prometheus Metrics** - Full observability and monitoring
- **High Performance** - Built in Rust for maximum speed and efficiency

## Quick Start

### 1. Install Dependencies

Make sure you have Rust installed:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### 2. Install Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull llama2
```

### 3. Run NarratorAI

```bash
cd ai/narrator_ai
cargo run
```

The service will start on `http://localhost:7100`

## API Endpoints

### Health Check
```bash
curl http://localhost:7100/api/v1/health
```

### Summarize Property Data
```bash
curl -X POST http://localhost:7100/api/v1/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Property ID: 12345. This is a 2-story single-family residential home built in 1995. Located in tax district 503. Total square footage: 2,400. Lot size: 0.25 acres. Assessed value: $485,000. Last sale: $420,000 in 2019.",
    "model": "llama2",
    "max_tokens": 500,
    "temperature": 0.7
  }'
```

### Classify Property Type
```bash
curl -X POST http://localhost:7100/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Multi-unit apartment complex with 24 units, commercial laundry facility, and retail space on ground floor"
  }'
```

### Explain Assessment Data
```bash
curl -X POST http://localhost:7100/api/v1/explain \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Mill rate: 1.2%, Assessed value: $485,000, Market value: $520,000, Exemptions: Homestead $50,000"
  }'
```

### View Metrics
```bash
curl http://localhost:7100/api/v1/metrics
```

## Configuration

Configure via environment variables in `.env`:

```env
OLLAMA_URL=http://localhost:11434
AI_MODEL_NAME=llama2
NARRATOR_AI_PORT=7100
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.7
AI_TIMEOUT_SECONDS=30
RUST_LOG=info
```

## Integration with TerraFusion

Add these endpoints to your main application:

```python
# Example Python integration
import requests

def get_property_summary(property_data):
    response = requests.post(
        "http://localhost:7100/api/v1/summarize",
        json={"text": property_data}
    )
    return response.json()["result"]
```

## Performance

- **Sub-second response times** for most queries
- **Concurrent request handling** with Actix-web
- **Memory efficient** Rust implementation
- **Prometheus metrics** for monitoring and alerting

## Supported Models

Any Ollama-compatible model:
- `llama2` (recommended for general use)
- `mistral` (faster, good for summaries)
- `phi3` (smaller, good for classification)
- `codellama` (good for technical explanations)

## Monitoring

Access Prometheus metrics at `/api/v1/metrics`:
- `narrator_ai_tasks_total` - Total tasks processed
- `narrator_ai_latency_seconds` - Processing latency
- `narrator_ai_errors_total` - Error counts
- `ollama_health_status` - Ollama service health

Perfect for integration with Grafana dashboards!