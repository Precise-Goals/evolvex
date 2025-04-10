import os
import sys
import requests
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.tools import BaseTool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_community.document_loaders import TextLoader, DirectoryLoader, CSVLoader, PyPDFLoader

# Set the API key from environment variables
os.environ["TOGETHER_API_KEY"] = str(os.getenv("TOGETHER_API"))
print(os.environ["TOGETHER_API_KEY"])

# Initialize Flask app
app = Flask(__name__)
# Restrict CORS to your frontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173/evolvex-code-agentic-ai",
            "http://localhost:5173",
            "https://evolvexai.vercel.app"
        ]
    }
})


class SimpleTracer:
    def __init__(self, project_name="agent_system_project"):
        self.project_name = project_name

    def trace(self, run_type="", name="", extra=None):
        class TracerContext:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return TracerContext()


tracer = SimpleTracer(project_name="agent_system_project")


class CustomTogetherLLM:
    def __init__(self, model="mistralai/Mixtral-8x7B-Instruct-v0.1", temperature=0.7, max_tokens=2048):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = os.environ.get("TOGETHER_API_KEY")

    def _call_api(self, prompt):
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        API_ENDPOINT = "https://api.together.xyz/v1/completions"
        data = {"model": self.model, "prompt": prompt, "max_tokens": self.max_tokens,
                "temperature": self.temperature, "top_p": 0.95, "stop": ["<|endoftext|>"]}
        response = requests.post(
            API_ENDPOINT, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            return result.get("choices", [{}])[0].get("text", "")
        else:
            return f"Error from Together AI API: {response.status_code} - {response.text}"

    def __call__(self, prompt, *args, **kwargs):
        return self._call_api(prompt)


def get_llm(temperature=0.7, model="mistralai/Mixtral-8x7B-Instruct-v0.1"):
    return CustomTogetherLLM(model=model, temperature=temperature, max_tokens=2048)


class SimpleEmbeddings:
    def __init__(self, model="togethercomputer/m2-bert-80M-8k-retrieval"):
        self.model = model
        self.api_key = os.environ.get("TOGETHER_API_KEY")

    def embed_documents(self, texts):
        import numpy as np
        return [np.random.rand(384) for _ in texts]

    def embed_query(self, text):
        import numpy as np
        return np.random.rand(384)


embeddings = SimpleEmbeddings(
    model="togethercomputer/m2-bert-80M-8k-retrieval")


class RAGSystem:
    def __init__(self, docs_dir="./knowledge_base"):
        self.docs_dir = docs_dir
        self.vectorstore = None
        self.retriever = None
        self.llm = get_llm(temperature=0.1)

    def load_documents(self):
        try:
            loaders = []
            if os.path.exists(f"{self.docs_dir}/text"):
                loaders.append(DirectoryLoader(
                    f"{self.docs_dir}/text", loader_cls=TextLoader))
            if os.path.exists(f"{self.docs_dir}/csv"):
                loaders.append(DirectoryLoader(
                    f"{self.docs_dir}/csv", loader_cls=CSVLoader))
            if os.path.exists(f"{self.docs_dir}/pdf"):
                loaders.append(DirectoryLoader(
                    f"{self.docs_dir}/pdf", loader_cls=PyPDFLoader))
            documents = []
            for loader in loaders:
                documents.extend(loader.load())
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(documents)
            self.vectorstore = Chroma.from_documents(
                documents=splits, embedding=embeddings)
            base_retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 5})
            compressor = LLMChainExtractor.from_llm(self.llm)
            self.retriever = ContextualCompressionRetriever(
                base_compressor=compressor, base_retriever=base_retriever)
            return f"Successfully loaded {len(splits)} document chunks into the RAG system."
        except Exception as e:
            return f"Error loading documents: {str(e)}"

    def query(self, question, num_results=3):
        if not self.retriever:
            return "RAG system not initialized. Please load documents first."
        docs = self.retriever.get_relevant_documents(question)[:num_results]
        context = "\n\n".join([doc.page_content for doc in docs])
        template = """
        Use the following context to answer the question. If the answer is not in the context, say "I don't have enough information to answer this question."
        Context:
        {context}
        Question:
        {question}
        Answer:
        """
        prompt = PromptTemplate(template=template, input_variables=[
                                "context", "question"])
        chain = LLMChain(llm=self.llm, prompt=prompt)
        response = chain.run(context=context, question=question)
        return {"answer": response, "sources": [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]}


class RAGLoader(BaseTool):
    name: str = "rag_loader"
    description: str = "Loads documents into the RAG system"

    def __init__(self, rag_system):
        super().__init__()
        self._rag_system = rag_system

    def _run(self, docs_dir: str = "") -> str:
        if docs_dir:
            self._rag_system.docs_dir = docs_dir
        return self._rag_system.load_documents()

    def _arun(self, docs_dir: str):
        raise NotImplementedError("RAGLoader does not support async")


class RAGQueryTool(BaseTool):
    name: str = "rag_query"
    description: str = "Queries the RAG system for information based on a question"

    def __init__(self, rag_system):
        super().__init__()
        self._rag_system = rag_system

    def _run(self, query: str) -> str:
        result = self._rag_system.query(query)
        return f"Answer: {result['answer']}\nSources: {result['sources']}"

    def _arun(self, query: str):
        raise NotImplementedError("RAGQueryTool does not support async")


class StarCodeCompletion(BaseTool):
    name: str = "star_code_completion"
    description: str = "Uses Together AI StarCoder API to complete code with higher accuracy"

    def _run(self, code_context: str) -> str:
        headers = {
            "Authorization": f"Bearer {os.environ.get('TOGETHER_API_KEY')}", "Content-Type": "application/json"}
        STARCODER_API_ENDPOINT = "https://api.together.xyz/v1/completions"
        data = {"model": "togethercomputer/StarCoder", "prompt": code_context,
                "max_tokens": 500, "temperature": 0.3, "top_p": 0.95, "stop": ["<|endoftext|>"]}
        response = requests.post(
            STARCODER_API_ENDPOINT, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            completion = result.get("choices", [{}])[0].get("text", "")
            return f"StarCoder suggested completion:\n{completion}"
        else:
            return f"Error from Together AI API: {response.status_code} - {response.text}"

    def _arun(self, code_context: str):
        raise NotImplementedError("StarCodeCompletion does not support async")


class StarBugDetection(BaseTool):
    name: str = "star_bug_detection"
    description: str = "Uses Together AI StarCoder to detect bugs and provide fixes with higher accuracy"

    def _run(self, code: str) -> str:
        headers = {
            "Authorization": f"Bearer {os.environ.get('TOGETHER_API_KEY')}", "Content-Type": "application/json"}
        STARCODER_API_ENDPOINT = "https://api.together.xyz/v1/completions"
        prompt = f"""
        Analyze the following code for bugs and issues:
        Identify any:
        1. Syntax errors
        2. Logic errors
        3. Performance issues
        4. Security vulnerabilities
        5. Suggested fixes
        Analysis:
        """
        data = {"model": "togethercomputer/StarCoder", "prompt": prompt,
                "max_tokens": 700, "temperature": 0.2, "top_p": 0.95, "stop": ["<|endoftext|>"]}
        response = requests.post(
            STARCODER_API_ENDPOINT, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            analysis = result.get("choices", [{}])[0].get("text", "")
            return f"StarCoder bug analysis:\n{analysis}"
        else:
            return f"Error from Together AI API: {response.status_code} - {response.text}"

    def _arun(self, code: str):
        raise NotImplementedError("StarBugDetection does not support async")


class StarCodeTesting(BaseTool):
    name: str = "star_code_testing"
    description: str = "Uses Together AI StarCoder API to generate test cases for the provided code"

    def _run(self, code: str) -> str:
        headers = {
            "Authorization": f"Bearer {os.environ.get('TOGETHER_API_KEY')}", "Content-Type": "application/json"}
        STARCODER_API_ENDPOINT = "https://api.together.xyz/v1/completions"
        language = self._detect_language(code)
        prompt = f"""
        Generate comprehensive test cases for the following {language} code:
        Write unit tests that cover:
        1. Normal expected behavior
        2. Edge cases
        3. Error handling
        Test code:
        """
        data = {"model": "togethercomputer/StarCoder", "prompt": prompt,
                "max_tokens": 800, "temperature": 0.2, "top_p": 0.95, "stop": ["<|endoftext|>"]}
        response = requests.post(
            STARCODER_API_ENDPOINT, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            result = response.json()
            test_code = result.get("choices", [{}])[0].get("text", "")
            return f"Generated test cases:\n{test_code}"
        else:
            return f"Error from Together AI API: {response.status_code} - {response.text}"

    def _detect_language(self, code: str) -> str:
        if "def " in code or "import " in code or "class " in code and ":" in code:
            return "Python"
        elif "function " in code or "const " in code or "let " in code or "var " in code:
            return "JavaScript"
        elif "func " in code or "package " in code:
            return "Go"
        elif "#include" in code or "int main" in code:
            return "C++"
        elif "public class" in code or "import java" in code:
            return "Java"
        else:
            return "Python"

    def _arun(self, code: str):
        raise NotImplementedError("StarCodeTesting does not support async")


class DocStringGenerator(BaseTool):
    name: str = "docstring_generator"
    description: str = "Generates docstrings for functions and classes"

    def _run(self, code: str) -> str:
        llm = get_llm(temperature=0.1)
        template = """Generate a comprehensive docstring for the following code using the appropriate format for the language. Include:
        - Brief description
        - Parameters with types and descriptions
        - Return values with types and descriptions
        - Examples if helpful
        CODE:
        {code}
        DOCSTRING:"""
        prompt = PromptTemplate(template=template, input_variables=["code"])
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run(code=code)

    def _arun(self, code: str):
        raise NotImplementedError("DocStringGenerator does not support async")


class ReadmeGenerator(BaseTool):
    name: str = "readme_generator"
    description: str = "Generates README files for projects"

    def _run(self, project_info: str) -> str:
        llm = get_llm(temperature=0.2)
        template = """Generate a comprehensive README.md file for the following project. Include:
        - Project title and description
        - Installation instructions
        - Usage examples
        - Main features
        - Dependencies
        - Contribution guidelines if applicable
        PROJECT INFO:
        {project_info}
        README.md:"""
        prompt = PromptTemplate(
            template=template, input_variables=["project_info"])
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run(project_info=project_info)

    def _arun(self, project_info: str):
        raise NotImplementedError("ReadmeGenerator does not support async")


class BugDetector(BaseTool):
    name: str = "bug_detector"
    description: str = "Detects potential bugs in code"

    def _run(self, code: str) -> str:
        llm = get_llm(temperature=0.1)
        template = """Analyze the following code for potential bugs, errors, or code smells. Include:
        - Syntax errors
        - Logical errors
        - Performance issues
        - Security vulnerabilities
        - Best practice violations
        CODE:
        {code}
        BUGS AND ISSUES:"""
        prompt = PromptTemplate(template=template, input_variables=["code"])
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run(code=code)

    def _arun(self, code: str):
        raise NotImplementedError("BugDetector does not support async")


class CodeFixer(BaseTool):
    name: str = "code_fixer"
    description: str = "Fixes bugs in code"

    def _run(self, code_and_bugs: str) -> str:
        llm = get_llm(temperature=0.2)
        template = """Fix the following code based on the identified bugs and issues. Provide:
        - Fixed code
        - Explanation of changes made
        CODE AND BUGS:
        {code_and_bugs}
        FIXED CODE:"""
        prompt = PromptTemplate(
            template=template, input_variables=["code_and_bugs"])
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run(code_and_bugs=code_and_bugs)

    def _arun(self, code_and_bugs: str):
        raise NotImplementedError("CodeFixer does not support async")


class CodeCompleter(BaseTool):
    name: str = "code_completer"
    description: str = "Completes code based on context"

    def _run(self, code_context: str) -> str:
        llm = get_llm(temperature=0.3,
                      model="togethercomputer/CodeLlama-34b-Instruct")
        template = """Complete the following code based on the context. Provide a full implementation that follows best practices.
        CODE CONTEXT:
        {code_context}
        COMPLETED CODE:"""
        prompt = PromptTemplate(
            template=template, input_variables=["code_context"])
        chain = LLMChain(llm=llm, prompt=prompt)
        return chain.run(code_context=code_context)

    def _arun(self, code_context: str):
        raise NotImplementedError("CodeCompleter does not support async")


def initialize_documentation_agent():
    llm = get_llm(temperature=0.2)
    tools = [DocStringGenerator(), ReadmeGenerator()]
    return initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, handle_parsing_errors=True)


def initialize_bug_detection_agent():
    llm = get_llm(temperature=0.1)
    tools = [BugDetector(), CodeFixer(), StarBugDetection(), StarCodeTesting()]
    return initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, handle_parsing_errors=True)


def initialize_code_completion_agent():
    llm = get_llm(temperature=0.3,
                  model="togethercomputer/CodeLlama-34b-Instruct")
    tools = [CodeCompleter(), StarCodeCompletion()]
    return initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, handle_parsing_errors=True)


def initialize_rag_agent(rag_system):
    llm = get_llm(temperature=0.2)
    tools = [RAGQueryTool(rag_system), RAGLoader(rag_system)]
    return initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, handle_parsing_errors=True)


class SimpleAgent:
    def __init__(self, name, system_message, all_agents=None):
        self.name = name
        self.system_message = system_message
        self.tools = []
        self.llm = get_llm(temperature=0.3)
        self.all_agents = all_agents or {}

    def register_tool(self, tool):
        self.tools.append(tool)
        return self

    def run(self, message, history=None):
        if history is None:
            history = []
        history.append(f"User: {message}")

        if self.name == "Manager":
            return self._manager_run(message, history)
        else:
            return self._specialized_run(message, history)

    def _manager_run(self, message, history):
        if " and " in message.lower() or "multiple" in message.lower():
            prompt = f"""
            System: {self.system_message}
            Available agents:
            - CodeCompleter: Handles code generation and completion
            - BugDetector: Finds and fixes bugs in code
            - DocumentationAgent: Creates documentation
            - RAGAgent: Handles knowledge base queries
            
            Message: {message}
            Respond with only: [DELEGATE:AgentName] (choose the most appropriate agent)
            """
            response = self.llm(prompt).strip()
            agent_name = "code_completer"  # Default to correct key
            agent_name_raw = agent_name  # Default raw name for output

            if response.startswith("[DELEGATE:") and response.endswith("]"):
                agent_name_raw = response[10:-1].strip()
                agent_name = agent_name_raw.lower().replace("completer", "completer")

            if agent_name in self.all_agents and agent_name != "manager":
                delegated_response = self.all_agents[agent_name].run(
                    message, history)
                return f"Manager: Delegated to {agent_name_raw}\n{delegated_response}"
            else:
                return f"Manager: Invalid agent '{agent_name_raw}', handling directly\n{self._execute_simple_task(message, history)}"
        else:
            return self._execute_simple_task(message, history)

    def _execute_simple_task(self, message, history):
        prompt = f"""
        System: I am the Manager agent with basic coding capabilities.
        Message: {message}
        Provide a concise response with code if requested, no extra commentary.
        """
        return self.llm(prompt).strip()

    def _specialized_run(self, message, history):
        prompt = f"""
        System: {self.system_message}
        Message: {message}
        Provide a concise response with code if requested, no extra commentary.
        """
        return self.llm(prompt).strip()


class SimpleUserAgent:
    def __init__(self, name="User"):
        self.name = name

    def initiate_chat(self, agent, message):
        response = agent.run(message)
        print(f"User: {message}")
        print(f"{agent.name}'s Response:\n{response}")
        return response


def setup_simple_agents():
    agents = {}
    agents["manager"] = SimpleAgent(
        name="Manager", system_message="You are the Managerial Agent that coordinates tasks or executes simple ones directly.")
    agents["code_completer"] = SimpleAgent(
        name="CodeCompleter", system_message="You are the Code Completion Agent for generating code snippets.")
    agents["bug_detector"] = SimpleAgent(
        name="BugDetector", system_message="You are the Bug Detection Agent for finding and fixing code issues.")
    agents["documentation_agent"] = SimpleAgent(
        name="DocumentationAgent", system_message="You are the Documentation Agent for creating documentation.")
    agents["rag_agent"] = SimpleAgent(
        name="RAGAgent", system_message="You are the RAG Agent for knowledge base queries.")

    for agent in agents.values():
        agent.all_agents = agents

    agents["user_proxy"] = SimpleUserAgent(name="User")
    return agents


def integrate_tools(agents):
    star_completion_tool = {"name": "star_code_completion",
                            "description": "Get code completion suggestions from Together AI StarCoder API", "func": StarCodeCompletion()._run}
    star_bug_detection_tool = {"name": "star_bug_detection",
                               "description": "Analyze code for bugs using Together AI StarCoder API", "func": StarBugDetection()._run}
    star_testing_tool = {"name": "star_code_testing",
                         "description": "Generate test cases using Together AI StarCoder API", "func": StarCodeTesting()._run}
    agents["code_completer"].register_tool(star_completion_tool)
    agents["bug_detector"].register_tool(star_bug_detection_tool)
    agents["bug_detector"].register_tool(star_testing_tool)
    return agents


# Initialize agents globally
agents = setup_simple_agents()
agents = integrate_tools(agents)
manager = agents["manager"]

# Flask API Routes


@app.route('/api/code', methods=['POST'])
def process_code():
    try:
        data = request.get_json()
        user_input = data.get('input', '')
        if not user_input:
            return jsonify({'error': 'No input provided'}), 400

        response = manager.run(user_input)
        return jsonify({'output': response, 'status': 'success'}), 200

    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'message': 'Server is running', 'status': 'ok'}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
