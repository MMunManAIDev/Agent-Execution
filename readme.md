# AgentExecutive

Een krachtige tool voor het automatiseren van webtaken met behulp van Large Language Models (LLMs).

## 📋 Features

- **LLM-Gestuurde Automatisering**: Gebruikt OpenAI's GPT modellen voor intelligente webautomatisering
- **Multi-Tab Interface**: Beheer meerdere automatiseringstaken tegelijk
- **Uitgebreide Logging**: Gedetailleerde logging van alle acties en beslissingen
- **Flexibele Configuratie**: Aanpasbare rollen en doelen voor verschillende use cases
- **Veilige Uitvoering**: Robuuste error handling en timeout management
- **Screenshot Ondersteuning**: Visuele weergave van automatiseringsvoortgang

## 🚀 Quick Start

### Prerequisites

- Python 3.8 of hoger
- Chrome browser
- OpenAI API key

### Installatie

1. Clone de repository:
```bash
git clone https://github.com/yourusername/agent-executive.git
cd agent-executive
```

2. Installeer dependencies:
```bash
pip install -r requirements.txt
```

3. Configureer je OpenAI API key:
```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_api_key_here
```

### Gebruik

Start de applicatie:
```bash
python -m agent_executive.src.main
```

## 🔧 Configuratie

De applicatie kan geconfigureerd worden via `config.py`. Belangrijke instellingen zijn:

- `WINDOW_SIZE`: Formaat van het hoofdvenster
- `CHROME_OPTIONS`: Selenium Chrome driver opties
- `LOG_LEVEL`: Logging detail niveau
- `SCREENSHOT_DIR`: Directory voor screenshots
- `LOG_DIR`: Directory voor log files

## 💻 Development

### Project Structuur
```
agent_executive/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── llm_handler.py
│   │   └── web_handler.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── tab.py
│   │   └── widgets.py
│   └── utils/
│       ├── __init__.py
│       ├── url_utils.py
│       ├── threading.py
│       └── logging.py
├── tests/
│   ├── __init__.py
│   ├── test_url_utils.py
│   ├── test_threading.py
│   └── test_logging.py
├── requirements.txt
└── README.md
```

### Tests Uitvoeren

Run alle tests:
```bash
pytest tests/
```

Met coverage report:
```bash
pytest --cov=agent_executive tests/
```

### Code Style

Dit project volgt de PEP 8 style guide. Format je code met:
```bash
black src/ tests/
```

### Type Checking

Run type checking met:
```bash
mypy src/
```

## 🤝 Contributing

1. Fork de repository
2. Maak een feature branch (`git checkout -b feature/amazing-feature`)
3. Commit je changes (`git commit -m 'Add amazing feature'`)
4. Push naar de branch (`git push origin feature/amazing-feature`)
5. Open een Pull Request

## 📝 License

Dit project is gelicenseerd onder de MIT License - zie het [LICENSE](LICENSE) bestand voor details.

## ✨ Acknowledgments

- OpenAI voor de GPT modellen
- Selenium voor web automatisering
- De Python community voor geweldige libraries

## 📧 Contact

Mike van Munster - Mantjes - mikemantjes@live.nl

Project Link: [https://github.com/yourusername/agent-executive](https://github.com/yourusername/agent-executive)