# Edurite - The ReAct AI Agent Framework

A modular framework for building AI agents that can read documents from various sources, reason about their contents, and act upon queries based on that information.

## 🌟 Features

- **Document Processing**: Read and extract information from various sources (PDFs, text files, web pages, YouTube videos)
- **Knowledge Base**: Store and index document contents for efficient retrieval
- **LLM Integration**: Use large language models for reasoning and generating responses
- **ReAct Pattern**: Implements the Reasoning + Acting pattern for more effective AI interactions
- **Modular Design**: Easily extend with new document processors or capabilities

## 🔧 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/thekakodkar/edurite.git
   cd edurite
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 📋 Usage

### Basic Usage

```python
from my_agent.main import AIAgent

# Initialize the agent with your config
agent = AIAgent("config/config.yaml")
agent.initialize()

# Ask a question
result = agent.query("What are the key concepts in the documentation?")
print(result["answer"])

# Add a new document
agent.add_document("path/to/new_document.pdf")
```

### Running the CLI Interface

```bash
python run.py
```

## 🧩 Project Structure

```
Edurite/
├── config/                 # Configuration files
│   └── config.yaml         # Main configuration
├── my_agent/               # Agent implementation
│   ├── __init__.py
│   └── main.py             # Core agent code
├── documents/              # Your document collection
├── .env                    # Environment variables (API keys)
├── requirements.txt        # Project dependencies
└── run.py                  # CLI entry point
```

## ⚙️ Configuration

Create a `config/config.yaml` file with your configuration:

```yaml
agent:
  name: "Edurite"
  version: "1.0.0"

document_sources:
  sources:
    - type: "folder"
      path: "./documents"
      extensions: ["pdf", "txt", "md"]
    - type: "website"
      path: "https://example.com/documentation"
    - type: "youtube"
      path: "https://www.youtube.com/watch?v=your_video_id"

knowledge_base:
  storage_type: "memory"

connections:
  list:
    openai:
      type: "api"
      api_key_env: "OPENAI_API_KEY"
      endpoint: "https://api.openai.com/v1"

query_processing:
  model: "gpt-4"
  temperature: 0.7
  max_tokens: 1000
```

## 🔍 How It Works

1. **Document Processing**: The agent reads documents from configured sources and extracts their content.
2. **Knowledge Storage**: Document contents are stored in a knowledge base for efficient retrieval.
3. **Query Processing**: When a question is asked, the agent:
   - Searches for relevant documents
   - Creates a context with the most relevant content
   - Uses an LLM to reason about the information and generate a response
   - Returns the answer along with source citations

## 📚 ReAct Pattern Implementation

This framework implements the ReAct (Reasoning + Acting) pattern:

- **Reasoning**: The LLM analyzes document content and reasons about the best response
- **Acting**: The agent retrieves documents, processes them, and generates answers

## 🛠️ Extending the Framework

### Adding a New Document Processor

```python
from my_agent.main import DocumentProcessor

class ExcelProcessor(DocumentProcessor):
    """Process Excel spreadsheets"""
    def process_document(self, document_path: str) -> Dict[str, Any]:
        # Your implementation here
        pass

# Add to your agent
agent.source_manager.processors["excel"] = ExcelProcessor()
```

### Using Vector Embeddings for Search

For more advanced semantic search, you can enhance the KnowledgeBase class with vector embeddings.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🙏 Acknowledgements

- OpenAI for the LLM API https://platform.openai.com/docs/api-reference
- ReAct pattern from Princeton/Google researchers https://arxiv.org/pdf/2210.03629
- All open-source libraries used in this project