"""
AI Agent for processing scraped data using AWS Bedrock Claude
"""
import os
from typing import Dict, Any, List
import boto3
from langchain_community.chat_models import BedrockChat
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated

class AgentState(TypedDict):
    """State for the AI agent graph"""
    input: str
    context: List[str]
    question: str
    answer: str
    metadata: Dict[str, Any]

class AIAgent:
    """Class for AI agent operations using AWS Bedrock Claude"""
    
    def __init__(self, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """
        Initialize the AI agent
        
        Args:
            model_id: Bedrock model ID
        """
        self.model_id = model_id
        self.bedrock_client = boto3.client('bedrock-runtime')
        self.llm = BedrockChat(
            client=self.bedrock_client,
            model_id=self.model_id,
            model_kwargs={
                "temperature": 0.0,
                "max_tokens": 4096
            }
        )
    
    def process_text(self, text: str, query: str) -> str:
        """
        Process text with the AI model
        
        Args:
            text: Text to process
            query: Query to ask about the text
            
        Returns:
            AI response
        """
        messages = [
            SystemMessage(content="You are an AI assistant that helps extract and analyze information from documents."),
            HumanMessage(content=f"Here is a document excerpt:\n\n{text}\n\nQuestion: {query}")
        ]
        
        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            raise Exception(f"Error processing text with AI: {str(e)}")
    
    def create_agent_graph(self) -> StateGraph:
        """
        Create a LangGraph for the agent workflow
        
        Returns:
            StateGraph instance
        """
        # Define the nodes in our graph
        def extract_question(state: AgentState) -> AgentState:
            """Extract the main question from the input"""
            state["question"] = state["input"]
            return state
        
        def retrieve_context(state: AgentState) -> AgentState:
            """Retrieve relevant context for the question"""
            # In a real implementation, this would query the vector database
            # For now, we'll just use the context that was passed in
            return state
        
        def generate_answer(state: AgentState) -> AgentState:
            """Generate an answer based on the question and context"""
            context_text = "\n\n".join(state["context"])
            question = state["question"]
            
            # Get source file names from metadata
            source_files = []
            if "source_metadatas" in state["metadata"]:
                for metadata in state["metadata"]["source_metadatas"]:
                    if "file_name" in metadata:
                        source_files.append(metadata["file_name"])
                    elif "source" in metadata:
                        source_files.append(os.path.basename(metadata["source"]))
            
            source_files = list(set(source_files))  # Remove duplicates
            source_info = "Sources: " + ", ".join(source_files) if source_files else ""
            
            messages = [
                SystemMessage(content="You are an AI assistant that helps extract and analyze information from documents. Include the source file names in your response."),
                HumanMessage(content=f"Here is the context information:\n\n{context_text}\n\nSource files: {', '.join(source_files)}\n\nQuestion: {question}\n\nMake sure to mention which source files contain the information you're using in your answer.")
            ]
            
            try:
                response = self.llm.invoke(messages)
                state["answer"] = response.content
                
                # Add source information if not already included in the response
                if source_info and source_info.lower() not in state["answer"].lower():
                    state["answer"] += f"\n\n{source_info}"
            except Exception as e:
                state["answer"] = f"Error generating answer: {str(e)}"
            
            return state
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("extract_question", extract_question)
        workflow.add_node("retrieve_context", retrieve_context)
        workflow.add_node("generate_answer", generate_answer)
        
        # Add edges
        workflow.add_edge("extract_question", "retrieve_context")
        workflow.add_edge("retrieve_context", "generate_answer")
        workflow.add_edge("generate_answer", END)
        
        # Set the entry point
        workflow.set_entry_point("extract_question")
        
        return workflow.compile()