import os
import logging
import yaml
import json
import openai
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv

load_dotenv()


class DocumentProcessor:
    """Base document processor"""

    def process_document(self, document_path: str) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement process_document")


class TextProcessor(DocumentProcessor):
    """Process text documents"""

    def process_document(self, document_path: str) -> Dict[str, Any]:
        try:
            with open(document_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return {
                "content": content,
                "metadata": {
                    "path": document_path,
                    "type": "text"
                }
            }
        except Exception as e:
            logger.error(f"Error processing text document {document_path}: {str(e)}")
            return {"content": "", "metadata": {"error": str(e)}}


class PDFProcessor(DocumentProcessor):
    """Process PDF documents"""

    def process_document(self, document_path: str) -> Dict[str, Any]:
        try:
            from pypdf import PdfReader
            reader = PdfReader(document_path)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"

            return {
                "content": content,
                "metadata": {
                    "path": document_path,
                    "type": "pdf",
                    "pages": len(reader.pages)
                }
            }
        except Exception as e:
            logger.error(f"Error processing PDF document {document_path}: {str(e)}")
            return {"content": "", "metadata": {"error": str(e)}}


class WebPageProcessor(DocumentProcessor):
    """Process web pages"""

    def process_document(self, url: str) -> Dict[str, Any]:
        try:
            import requests
            from bs4 import BeautifulSoup

            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract text from the main content areas
            main_content = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            content = "\n".join([tag.get_text() for tag in main_content])

            return {
                "content": content,
                "metadata": {
                    "url": url,
                    "type": "webpage",
                    "title": soup.title.string if soup.title else url
                }
            }
        except Exception as e:
            logger.error(f"Error processing web page {url}: {str(e)}")
            return {"content": "", "metadata": {"error": str(e), "url": url}}


class YouTubeProcessor(DocumentProcessor):
    """Process YouTube videos"""

    def process_document(self, video_url: str) -> Dict[str, Any]:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi

            # Extract video ID from URL
            video_id = video_url.split("v=")[1].split("&")[0]

            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([item['text'] for item in transcript_list])

            return {
                "content": transcript_text,
                "metadata": {
                    "url": video_url,
                    "type": "youtube",
                    "video_id": video_id
                }
            }
        except Exception as e:
            logger.error(f"Error processing YouTube video {video_url}: {str(e)}")
            return {"content": "", "metadata": {"error": str(e), "url": video_url}}


class KnowledgeBase:
    """Simple in-memory knowledge base"""

    def __init__(self):
        self.documents = []

    def add_document(self, document: Dict[str, Any]) -> None:
        """Add a document to the knowledge base"""
        if document and document.get("content"):
            self.documents.append(document)
            logger.info(
                f"Added document to knowledge base: {document['metadata'].get('path', document['metadata'].get('url', 'unknown'))}")

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Simple keyword search"""
        results = []
        for doc in self.documents:
            if query.lower() in doc.get('content', '').lower():
                results.append(doc)
        return results


class DocumentSourceManager:
    """Manages document sources"""

    def __init__(self, config: Dict[str, Any], knowledge_base: KnowledgeBase):
        self.config = config
        self.knowledge_base = knowledge_base
        self.processors = {
            "text": TextProcessor(),
            "pdf": PDFProcessor(),
            "webpage": WebPageProcessor(),
            "youtube": YouTubeProcessor()
        }

    def process_source(self, source: Dict[str, Any]) -> None:
        """Process a single source based on its configuration"""
        source_type = source.get("type")
        path = source.get("path")

        if source_type == "folder":
            self._process_folder(path, source.get("extensions", []))
        elif source_type == "website":
            self._process_website(path)
        elif source_type == "youtube":
            self._process_youtube(path)
        elif source_type == "file":
            self._process_file(path)

    def _process_folder(self, folder_path: str, extensions: List[str]) -> None:
        """Process all files in a folder"""
        if not os.path.exists(folder_path):
            logger.error(f"Folder does not exist: {folder_path}")
            return

        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                self._process_file(file_path)

    def _process_file(self, file_path: str) -> None:
        """Process a single file"""
        extension = os.path.splitext(file_path)[1].lower()[1:]

        if extension == "pdf":
            document = self.processors["pdf"].process_document(file_path)
        elif extension in ["txt", "md", "json", "yaml", "csv"]:
            document = self.processors["text"].process_document(file_path)
        else:
            logger.warning(f"Unsupported file extension: {extension}")
            return

        self.knowledge_base.add_document(document)

    def _process_website(self, url: str) -> None:
        """Process a website URL"""
        document = self.processors["webpage"].process_document(url)
        self.knowledge_base.add_document(document)

    def _process_youtube(self, url: str) -> None:
        """Process a YouTube video"""
        document = self.processors["youtube"].process_document(url)
        self.knowledge_base.add_document(document)


class QueryProcessor:
    """Process queries using an LLM"""

    def __init__(self, config: Dict[str, Any], knowledge_base: KnowledgeBase):
        self.config = config
        self.knowledge_base = knowledge_base
        self.model = config.get("model", "gpt-4")
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)

        # Set up OpenAI
        openai.api_key = os.getenv(self.config.get("api_key_env", "OPENAI_API_KEY"))

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query using the knowledge base and LLM"""
        # 1. Search the knowledge base
        relevant_docs = self.knowledge_base.search(query)

        if not relevant_docs:
            return {
                "answer": "I don't have enough information to answer that question.",
                "sources": []
            }

        # 2. Prepare context for the LLM
        context = self._prepare_context(relevant_docs, query)

        # 3. Generate response using LLM
        response = self._generate_response(context, query)

        # 4. Extract sources for citation
        sources = []
        for doc in relevant_docs:
            metadata = doc.get("metadata", {})
            source_info = {
                "type": metadata.get("type", "unknown"),
            }
            if "path" in metadata:
                source_info["path"] = metadata["path"]
            if "url" in metadata:
                source_info["url"] = metadata["url"]
            sources.append(source_info)

        return {
            "answer": response,
            "sources": sources
        }

    def _prepare_context(self, documents: List[Dict[str, Any]], query: str) -> str:
        """Prepare context from relevant documents"""
        context = f"Answer the question based on the following information:\n\n"

        # Add content from each document
        for i, doc in enumerate(documents):
            metadata = doc.get("metadata", {})
            source_type = metadata.get("type", "unknown")
            source_id = metadata.get("path", metadata.get("url", f"Source {i + 1}"))

            # Add source information
            context += f"SOURCE {i + 1} ({source_type}): {source_id}\n"

            # Add document content (truncate if too long)
            content = doc.get("content", "")
            if len(content) > 1000:  # Truncate long documents
                content = content[:1000] + "..."
            context += f"{content}\n\n"

        return context

    def _generate_response(self, context: str, query: str) -> str:
        """Generate a response using the OpenAI API"""
        try:
            prompt = f"{context}\n\nQuestion: {query}\n\nAnswer:"

            response = openai.Completion.create(
                model=self.model,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            return response.choices[0].text.strip()
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return f"I encountered an error when trying to generate a response: {str(e)}"


class AIAgent:
    """Main AI agent class"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.knowledge_base = KnowledgeBase()
        self.source_manager = DocumentSourceManager(
            self.config.get("document_sources", {}),
            self.knowledge_base
        )
        self.query_processor = QueryProcessor(
            self.config.get("query_processing", {}),
            self.knowledge_base
        )

        logger.info("AI Agent initialized")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return {}

    def initialize(self) -> None:
        """Initialize by processing all sources"""
        logger.info("Processing document sources...")

        for source in self.config.get("document_sources", {}).get("sources", []):
            self.source_manager.process_source(source)

        doc_count = len(self.knowledge_base.documents)
        logger.info(f"Initialization complete. Processed {doc_count} documents.")

    def query(self, question: str) -> Dict[str, Any]:
        """Process a user query"""
        logger.info(f"Processing query: {question}")
        return self.query_processor.process_query(question)

    def add_document(self, document_path: str) -> None:
        """Add a document to the knowledge base"""
        self.source_manager.process_source({
            "type": "file",
            "path": document_path
        })