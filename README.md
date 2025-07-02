# Weekly Market Research Agent 🔍

💡 **Inspiration**

While working at my current company, I noticed a recurring pattern: executives constantly share competitor news — new product launches, partnerships, acquisitions — in a WhatsApp group. These updates often create urgency and anxiety, but there's no structured way to track, verify, or act on them.

This inspired me to build a tool that delivers **weekly market intelligence reports** focused on competitors and sector trends — enabling leadership to stay ahead with **accurate, relevant, and actionable insights**.

## Why This Product?

Companies often lack a systematic way to monitor competitor moves and industry shifts. This leads to delayed reactions and missed opportunities. This project provides a solution:

- **Automated competitor tracking**
- **Summarized weekly reports**
- **Market trends without noise**
- **Optional alerts for major announcements**

## User Flow

1. **Quick setup**: Simple onboarding form to define the company's domain and competitors.
2. **Competitor curation**: Extracted from company website, editable by user (fast and no waiting).
3. **Weekly briefing**: Concise market updates focused solely on competitors and trends — no internal data.
4. _(Optional)_ **Push notifications** for major news.

---

This project demonstrates how Tavily's data can power strategic decision-making with minimal effort from end users.

⚠️ Challenges & Lessons Learned
Throughout the development of this tool, several real-world challenges surfaced — especially when attempting to make it production-grade:

1. Identifying Actual Competitors
   This turned out to be the hardest problem.

I initially tried straightforward queries like “Tavily competitors” or “Tavily alternatives” — but results were often unreliable, vague, or outdated.

I tested multiple approaches and found that a more effective method was to first gather contextual information about the company (services, customer types, industry focus, etc.), and then use that data to generate dynamic search queries for discovering relevant competitors.

While this improves precision, it's still an imperfect solution and remains an open challenge — especially for niche or stealthy companies.

2. Gathering Relevant News & Trends
   Even once competitors are identified, surfacing only high-value updates (e.g., product launches, M&A, partnerships) is tricky.

A lot of online content is noisy: blog posts, hiring announcements, and minor updates clutter the feed.

I use structured prompts and search instructions to narrow the scope — but ensuring relevance and accuracy without human feedback remains an ongoing tradeoff.

## ✨ Features

- **🤖 Multi-Agent AI Research**: Specialized AI agents for different aspects of company research
- **🏢 Competitor Discovery**: Automated identification and analysis of competitors
- **📊 Market Intelligence**: Sector trends, client analysis, and competitive positioning
- **⚡ Real-time Updates**: Live progress tracking via WebSocket connections
- **📄 PDF Report Generation**: Professional reports with comprehensive insights
- **🔄 Interactive Review**: Human-in-the-loop competitor validation and modification
- **🌐 Modern UI**: React-based interface with real-time collaboration features

## 🏗️ Architecture

### Backend (Python + FastAPI + LangGraph)

- **FastAPI**: High-performance API server with WebSocket support
- **LangGraph**: Orchestrates multi-agent AI workflows
- **MongoDB**: Persistent storage for research data and job tracking
- **PDF Generation**: Automated report creation with ReportLab

### Frontend (React + TypeScript + Vite)

- **React 18**: Modern component-based UI
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Framer Motion**: Smooth animations and transitions
- **React Router**: Client-side routing

### AI Agents

1. **Research Intent Planner**: Analyzes research requirements
2. **User Profile Enrichment Agent**: Enhances user context and preferences
3. **Competitor Discovery Agent**: Identifies relevant competitors using AI-powered search
4. **Competitor Analyst Agent**: Deep-dive analysis of discovered competitors
5. **Sector Trend Agent**: Industry and market trend analysis
6. **Client Trend Agent**: Customer behavior and market dynamics
7. **Comprehensive Report Generator**: Synthesizes all research into final reports

## 🚀 Quick Start

### Prerequisites

- **Node.js** >= 14.x
- **Python** >= 3.8
- **MongoDB** instance (local or MongoDB Atlas)
- **API Keys**:
  - OpenAI API key
  - Tavily API key (for web search)

### 1. Clone Repository

```bash
git clone <repository-url>
cd company-research-agent
```

### 2. Environment Setup

Copy the environment template and configure your API keys:

```bash
cp env_template.txt .env
```

Edit `.env` with your actual values:

```bash
# API Keys
TAVILY_API_KEY=your_tavily_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database
MONGODB_URI=mongodb://localhost:27017/tavily_research

# Application
PORT=8000
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
python application.py
```

The backend will be available at `http://localhost:8000`

### 4. Frontend Setup

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🐳 Docker Deployment

### Local Development

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Production Deployment

```bash
# Build Docker image
docker build -t company-research-agent .

# Run container
docker run -p 8000:8000 --env-file .env company-research-agent
```

## ☁️ AWS Deployment

Deploy to AWS Elastic Beanstalk using the provided configuration:

1. **Prepare Docker image for ECR**:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker build -t company-research-agent .
docker tag company-research-agent:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/company-research-agent:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/company-research-agent:latest
```

2. **Deploy via Elastic Beanstalk Console**:
   - Upload `Dockerrun.aws.json`
   - Configure environment variables
   - Deploy application

See [`guides/AWS_DEPLOYMENT_GUIDE.md`](guides/AWS_DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## 📖 Usage

### Basic Research Workflow

1. **Start Research**:

   - Enter company name (required)
   - Add company website (optional)
   - Specify your role (optional)
   - Click "Start Analysis"

2. **Competitor Discovery**:

   - System automatically discovers competitors (2-3 minutes)
   - Real-time progress updates via WebSocket

3. **Competitor Review**:

   - Review discovered competitors
   - Remove irrelevant competitors
   - Add additional competitors if needed
   - Confirm and continue

4. **Comprehensive Analysis**:

   - AI agents analyze competitors, trends, and market dynamics
   - Progress tracked in real-time (5-10 minutes)

5. **Report Generation**:
   - Download PDF report
   - View interactive web report
   - Share insights with team

See [`guides/USER_GUIDE.md`](guides/USER_GUIDE.md) for detailed usage instructions.

## 🛠️ Development

### Project Structure

```
company-research-agent/
├── backend/                 # Python FastAPI backend
│   ├── agents/             # Base agent classes
│   ├── classes/            # State management and data models
│   ├── nodes/              # Individual AI agent implementations
│   ├── services/           # External services (MongoDB, PDF, WebSocket)
│   ├── utils/              # Utility functions
│   └── workflow.py         # LangGraph workflow orchestration
├── ui/                     # React TypeScript frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── types/          # TypeScript type definitions
│   │   ├── utils/          # Frontend utilities
│   │   └── styles/         # Styling and themes
│   └── public/             # Static assets
├── guides/                 # Documentation and guides
└── reports/                # Generated report storage
```

### Running Tests

```bash
# Backend tests
python -m pytest

# Frontend tests
cd ui && npm test
```

### Building for Production

```bash
# Build frontend
cd ui && npm run build

# Build Docker image
docker build -t company-research-agent .
```

## 🔧 Configuration

### Environment Variables

| Variable         | Description                                 | Required |
| ---------------- | ------------------------------------------- | -------- |
| `TAVILY_API_KEY` | Tavily API key for web search               | Yes      |
| `OPENAI_API_KEY` | OpenAI API key for AI agents                | Yes      |
| `MONGODB_URI`    | MongoDB connection string                   | Yes      |
| `PORT`           | Server port (default: 8000)                 | No       |
| `ENVIRONMENT`    | Environment mode (development/production)   | No       |
| `LOG_LEVEL`      | Logging level (INFO, DEBUG, WARNING, ERROR) | No       |

### API Endpoints

- `POST /research` - Start research job
- `GET /research/{job_id}` - Get research status
- `GET /research/{job_id}/report` - Get final report
- `POST /generate-pdf` - Generate PDF report
- `POST /research/competitors/modify` - Modify competitor list
- `WS /research/ws/{job_id}` - WebSocket for real-time updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the [User Guide](guides/USER_GUIDE.md)
2. Review the [AWS Deployment Guide](guides/AWS_DEPLOYMENT_GUIDE.md)
3. Open an issue in the GitHub repository

## 🙏 Acknowledgments

- **OpenAI** for GPT models powering the AI agents
- **Tavily** for comprehensive web search capabilities
- **LangGraph** for agent workflow orchestration
- **FastAPI** for the high-performance backend framework
- **React** and **TypeScript** for the modern frontend experience
