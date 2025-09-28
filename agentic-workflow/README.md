# Zippy-Archon Platform 🚀

A comprehensive AI-powered platform for requirements engineering, A/B testing, and marketplace trading with ZippyTrust validation and ZippyCoin integration.

## ✨ Features

### 🤖 **Multi-Provider AI Integration**
- **Grok AI (xAI)** - Real-time AI generation with fallback
- **OpenAI GPT-4/3.5** - Industry-standard AI models
- **Anthropic Claude** - Advanced reasoning capabilities
- **Zippy AI** - Custom models with trust validation
- Automatic fallback and cost optimization

### 🔒 **ZippyTrust Validation**
- Content quality assessment
- Security vulnerability detection
- Code quality analysis
- Documentation evaluation
- Community trust scoring
- Real-time validation feedback

### 📊 **Enhanced A/B Testing**
- Multi-version prompt comparison
- Statistical significance testing
- Cost-effectiveness analysis
- Winner determination algorithms
- Results export and sharing
- Marketplace integration

### 🏪 **ZippyCoin Marketplace**
- Trade spec templates and A/B test results
- Trust-based pricing
- Secure transaction processing
- User reputation system
- Content discovery and search
- Revenue sharing model

### 🎯 **Enhanced Rubric Scoring**
- VoidSpec metrics integration
- EARS compliance checking
- Testability assessment
- Clarity and structure evaluation
- Automated improvement suggestions
- Trust insights generation

### 🗄️ **Supabase Database Integration**
- Real-time data synchronization
- User authentication and management
- Transaction history tracking
- Analytics and reporting
- Scalable cloud storage
- Automatic backups

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Supabase account
- AI provider API keys (at least one)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-org/zippy-archon.git
cd zippy-archon/agentic-workflow
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp env.example .env
# Edit .env with your API keys and configuration
```

4. **Set up database**
```bash
# Run the migration script
psql -h your-supabase-host -U your-user -d your-db -f database/migrations/001_initial_schema.sql
```

5. **Start the platform**
```bash
python start_server.py
```

### Environment Configuration

Required environment variables:

```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# AI Providers (at least one required)
XAI_API_KEY=your_grok_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
ZIPPY_API_KEY=your_zippy_api_key

# Security
JWT_SECRET_KEY=your_jwt_secret_key
```

## 📖 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Key Endpoints

#### Requirements Generation
```bash
POST /api/v1/specs/generate
{
  "prompt": "Create a user authentication system",
  "provider": "grok",
  "version": "v1",
  "reviewer_pass": true
}
```

#### A/B Testing
```bash
POST /api/v1/ab-test/run
{
  "prompt": "Design a payment processing system",
  "versions": ["v1", "v1b", "enhanced"],
  "provider": "grok",
  "num_runs": 3
}
```

#### Marketplace
```bash
POST /api/v1/marketplace/listings
{
  "title": "E-commerce Requirements Template",
  "description": "Complete requirements for e-commerce platform",
  "content": {...},
  "category": "spec_template",
  "pricing": {"price": 50, "currency": "ZIPPY"}
}
```

#### Trust Validation
```bash
POST /api/v1/trust/validate
{
  "content": "WHEN user logs in THE SYSTEM SHALL authenticate credentials",
  "content_type": "requirements"
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   Supabase      │    │   AI Providers  │
│   Server        │◄──►│   Database      │    │   (Grok/OpenAI) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ZippyTrust    │    │   Marketplace   │    │   A/B Testing   │
│   Validation    │    │   (ZippyCoin)   │    │   System        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Development

### Project Structure
```
agentic-workflow/
├── api/                    # FastAPI server and endpoints
├── ai/                     # Multi-provider AI integration
├── database/               # Supabase client and migrations
├── plugins/                # ZippyTrust and marketplace
├── testing/                # A/B testing and rubric scoring
├── specs/                  # Requirements management
├── logs/                   # Application logs
├── data/                   # Data storage
├── requirements.txt        # Python dependencies
├── env.example            # Environment configuration
└── start_server.py        # Startup script
```

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t zippy-archon .

# Run container
docker run -p 8000:8000 --env-file .env zippy-archon
```

### Production Considerations
- Set `ENVIRONMENT=production`
- Configure proper CORS origins
- Set up monitoring (Sentry)
- Enable rate limiting
- Configure SSL/TLS
- Set up automated backups

## 📊 Monitoring and Analytics

The platform includes comprehensive monitoring:

- **Health checks**: `/health` endpoint
- **Usage statistics**: `/api/v1/analytics/stats`
- **AI usage tracking**: `/api/v1/analytics/ai-usage`
- **User statistics**: Database views
- **Error tracking**: Sentry integration

## 🔐 Security Features

- JWT-based authentication
- API key management
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection
- CORS configuration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.zippy-archon.com](https://docs.zippy-archon.com)
- **Issues**: [GitHub Issues](https://github.com/your-org/zippy-archon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/zippy-archon/discussions)

## 🎯 Roadmap

- [ ] **VS Code Extension Enhancement**
  - Real-time collaboration
- [ ] **Advanced Analytics**
  - Machine learning insights
- [ ] **Mobile App**
  - iOS and Android support
- [ ] **Enterprise Features**
  - SSO integration
  - Advanced permissions
- [ ] **AI Model Training**
  - Custom model fine-tuning
- [ ] **Blockchain Integration**
  - Smart contracts for marketplace
  - Decentralized governance

---

**Built with ❤️ by the Zippy-Archon Team**
