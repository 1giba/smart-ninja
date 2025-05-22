
# SmartNinja - Smartphone Price Tracker Agent

[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/1giba/smart-ninja)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Overview

SmartNinja is an advanced AI-powered smartphone price tracking agent that tracks mobile phone prices globally using web scraping and AI analysis. The application provides real-time insights and analytics for mobile phone pricing trends with a beautiful, responsive UI.

The system features an **Agent-Driven Interface** where each agent's reasoning is transparently visualized in the UI via structured outputs and expandable explanations.

**Live Demo:** [https://smartninja.com.br](https://smartninja.com.br)

## Features

- **Real-time Price Monitoring**: Track prices across multiple global regions
- **LLM-Powered Market Analysis**: Generate market insights using GPT-4 or GPT-3.5-turbo
- **Historical Price Trends**: Visualize price changes over time
- **Global Price Comparison**: Compare across regions and vendors
- **Proactive Alerts**: Notifications for drops or rule-based opportunities
- **Elegant UX**: Responsive dark UI built with Streamlit
- **Pipeline Visualization**: Real-time agent execution timeline in sidebar with detailed tooltips
- **Summary Insights**: AI-generated final recommendations with confidence levels and explanations
- **Explainable AI UX**: Users can see the reasoning, confidence level, and decision criteria behind each recommendation
- **Robust Testing**: 80%+ coverage and CI/CD-ready

## Architecture

SmartNinja is based on a modular agent pipeline, inspired by modern AI orchestration frameworks. It separates concerns into distinct, testable components to ensure flexibility, clarity, and scalability.

### Sequential Agent Pipeline

Each stage of the pipeline is executed by a specialized agent:

1. **PlanningAgent** – determines which sites to target based on device, region, and past performance
2. **ScrapingAgent** – performs concurrent web scraping using asynchronous tooling
3. **AnalysisAgent** – evaluates normalized pricing data using LLMs with fallback logic
4. **RecommendationAgent** – generates user-friendly buying suggestions

#### Benefits
- Modular and extensible
- Transparent reasoning at each stage
- Real-time progress visualization
- Resilient to partial failures
- Follows the Chain of Responsibility design pattern

## Model Context Protocol (MCP) Services

SmartNinja leverages **Model Context Protocol** (MCP) services — modular, distributed components responsible for preparing and enriching the context needed by agents.

### `analyze_prices`
- Analyzes historical data and generates insights using OpenAI models
- Structured prompt generation and fallback to rules if LLM fails
- Components:
  - `PriceFormatter`
  - `PriceAnalysisPromptGenerator`
  - `OpenAIClient`
  - `FallbackAnalyzer`

### `scrape_prices`
- Collects smartphone prices from multiple websites using Bright Data
- Async-enabled for concurrent scraping
- Error-handling with graceful fallback
- Components:
  - `PriceScraper`
  - `ResultNormalizer`
  - `ScrapingErrorHandler`

## Async-First Architecture & AsyncBridge Pattern

SmartNinja implements a **native asynchronous architecture** for I/O operations, which significantly improves performance and user experience.

### Asynchronous Programming Principles

- **Async Interfaces and Implementations**: All methods involving I/O (API calls, scraping, database queries) are defined as `async def` in both interfaces and implementations.
- **CPU-bound vs I/O-bound Differentiation**: CPU-intensive operations are executed in separate threads to avoid blocking the event loop.
- **Concurrent Calls**: MCPs use `asyncio.gather()` to execute operations in parallel when possible.

### AsyncBridge Pattern

To connect Streamlit's synchronous frontend with the asynchronous backend, we implemented the AsyncBridge Adapter pattern:

```python
class AsyncBridge:
    @staticmethod
    def run_async(async_func, *args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
```

This pattern prevents UI blocking while maintaining a clean and consistent internal asynchronous architecture.

### Agent Adapters

Each agent in the pipeline has a corresponding adapter to simplify frontend calls:

- **ScrapingAgentAdapter**: Converts between synchronous UI and asynchronous ScrapingAgent
- **AnalysisAgentAdapter**: Enables data analysis via synchronous interface
- **RecommendationAgentAdapter**: Facilitates recommendation generation for the UI

### Handling CPU-bound Operations

For CPU-intensive operations that shouldn't block the event loop:

```python
async def process_data(data):
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, cpu_intensive_function, data)
```

---

## Tech Stack

- **App**: Streamlit
- **AI & Data**: OpenAI API, Bright Data, Pandas, scikit-learn
- **Infra**: Render.com (CI/CD automated)

## Installation

```bash
git clone https://github.com/1giba/smart-ninja.git
cd smart-ninja
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# configure your .env with API keys
```

## Running the App

```bash
# Start smartninja app
./run.sh app
```

## Testing & Linting

```bash
./run.sh test      # run tests
./run.sh coverage  # with coverage
./run.sh lint      # lint using isort, black, pylint
```

## Project Structure

```
smartninja/
├── app/
│   ├── core/
│   │   ├── agents/         # Sequential agent pipeline
│   │   ├── analyzer/       # Price analysis components
│   │   ├── hooks/          # Callback hooks system
│   │   ├── interfaces/     # Abstract interfaces
│   │   ├── notification/   # Alert and notification services
│   │   ├── scraping/       # Web scrapers
│   │   └── models.py       # Data models
│   ├── api/
│   │   └── models/          # Data models and validation schemas
│   ├── mcp/
│   │   ├── analyze_prices/ # Price analysis MCP service
│   │   ├── scrape_prices/  # Web scraping MCP service
│   │   ├── track_alert_history/ # Alert tracking MCP service
│   │   └── track_price_history/ # Price history MCP service
│   ├── ui/
│   │   ├── pages/          # Streamlit UI pages
│   │   └── timeline_components.py # Agent pipeline visualization
│   └── tests/              # Test suite (pytest-based)
├── app.py                  # Streamlit entrypoint

├── run.sh                  # CLI utility
├── requirements.txt
└── README.md
```

## License

MIT License
