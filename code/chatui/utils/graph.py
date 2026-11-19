# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re

from typing_extensions import TypedDict
from typing import List, Optional

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

from chatui.utils import database, nim


# Tavily related parameters and exceptions
DEFAULT_TAVILY_K = 3
TAVILY_K = int(os.getenv("TAVILY_K", DEFAULT_TAVILY_K)) 

class TavilyAPIError(Exception):
    """Raised when Tavily returns invalid or unauthorized results."""
    pass


# Nemotron 3 API models generate a reasoning ("thinking") trace by default. Every
# component in this workflow expects a direct completion -- the graders parse bare
# JSON from the response -- so thinking is disabled on each hosted-endpoint call.
NEMOTRON_NO_THINK = {"chat_template_kwargs": {"enable_thinking": False}}
NVIDIA_API_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")


def hosted_chat_model(model: str, temperature: float):
    """Create an NVIDIA hosted model through its OpenAI-compatible API."""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=os.getenv("NVIDIA_API_KEY"),
        base_url=NVIDIA_API_BASE,
        extra_body=NEMOTRON_NO_THINK,
    )


def _binary_score(response) -> str:
    """Read a yes/no grader result without assuming one exact JSON key casing."""
    if isinstance(response, dict):
        for key in ("score", "grade", "verdict", "answer", "relevance", "grounded", "useful"):
            if key in response:
                response = response[key]
                break
        else:
            response = " ".join(str(value) for value in response.values())

    match = re.search(r"\b(yes|no)\b", str(response).lower())
    if match:
        return match.group(1)
    # Failing closed prevents unsupported document content becoming an answer.
    return "no"



### State

class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: question
        generation: LLM generation
        web_search: whether to add search
        documents: list of documents
    """

    question: str
    generation: str
    web_search: str
    documents: List[str]
    generator_model_id: str
    router_model_id: str
    retrieval_model_id: str
    hallucination_model_id: str
    answer_model_id: str
    prompt_generator: str
    prompt_router: str
    prompt_retrieval: str
    prompt_hallucination: str
    prompt_answer: str
    router_use_nim: bool
    retrieval_use_nim: bool
    generator_use_nim: bool
    hallucination_use_nim: bool
    answer_use_nim: bool
    collection_name: str
    nim_generator_ip: str
    nim_router_ip: str
    nim_retrieval_ip: str
    nim_hallucination_ip: str
    nim_answer_ip: str
    nim_generator_port: str
    nim_router_port: str
    nim_retrieval_port: str
    nim_hallucination_port: str
    nim_answer_port: str
    nim_generator_id: str
    nim_router_id: str
    nim_retrieval_id: str
    nim_hallucination_id: str
    nim_answer_id: str
    nim_generator_gpu_type: Optional[str]
    nim_generator_gpu_count: Optional[str]
    nim_router_gpu_type: Optional[str]
    nim_router_gpu_count: Optional[str]
    nim_retrieval_gpu_type: Optional[str]
    nim_retrieval_gpu_count: Optional[str]
    nim_hallucination_gpu_type: Optional[str]
    nim_hallucination_gpu_count: Optional[str]
    nim_answer_gpu_type: Optional[str]
    nim_answer_gpu_count: Optional[str]


from langchain.schema import Document


def _model_desc(state, component):
    """Human-readable description of the endpoint serving a component, for the Actions Console."""
    if state[f"{component}_use_nim"]:
        model_name = state[f"nim_{component}_id"] or "meta/llama-3.1-8b-instruct"
        return f"{model_name} (self-hosted endpoint)"
    return f"{state[f'{component}_model_id']} (NVIDIA API endpoint)"


### Nodes


def retrieve(state):
    """
    Retrieve documents from vectorstore

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, documents, that contains retrieved documents
    """
    print("[Retriever] Searching the vector database for relevant chunks...")
    question = state["question"]

    # Retrieval
    retriever = database.get_retriever(state["collection_name"])
    documents = retriever.invoke(question)
    print(f"[Retriever] Retrieved {len(documents)} chunk(s) from the vector database")
    return {"documents": documents, "question": question}


def generate(state):
    """
    Generate answer using RAG on retrieved documents

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation, that contains LLM generation
    """
    question = state["question"]
    documents = state["documents"]
    print(f"[Generator] Generating an answer from {len(documents)} context document(s) using {_model_desc(state, 'generator')}...")

    # RAG generation
    prompt = PromptTemplate(
        template=state["prompt_generator"],
        input_variables=["question", "context"],
    )
    llm = nim.CustomChatOpenAI(custom_endpoint=state["nim_generator_ip"], 
                               port=state["nim_generator_port"] if len(state["nim_generator_port"]) > 0 else "8000",
                               model_name=state["nim_generator_id"] if len(state["nim_generator_id"]) > 0 else "meta/llama-3.1-8b-instruct",
                               gpu_type=state["nim_generator_gpu_type"] if "nim_generator_gpu_type" in state else None,
                               gpu_count=state["nim_generator_gpu_count"] if "nim_generator_gpu_count" in state else None,
                               temperature=0.7) if state["generator_use_nim"] else hosted_chat_model(state["generator_model_id"], 0.7)
    rag_chain = prompt | llm | StrOutputParser()
    context = "\n\n".join(document.page_content for document in documents)
    generation = rag_chain.invoke({"context": context, "question": question})
    print(f"[Generator] ✓ Draft answer generated ({len(generation)} characters)")
    return {"documents": documents, "question": question, "generation": generation}


def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question
    If any document is not relevant, we will set a flag to run web search

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Filtered out irrelevant documents and updated web_search state
    """

    question = state["question"]
    documents = state["documents"]
    print(f"[Retrieval Grader] Grading {len(documents)} retrieved chunk(s) for relevance using {_model_desc(state, 'retrieval')}...")

    # Score each doc
    filtered_docs = []
    web_search = "No"
    prompt = PromptTemplate(
        template=state["prompt_retrieval"],
        input_variables=["question", "document"],
    )
    llm = nim.CustomChatOpenAI(custom_endpoint=state["nim_retrieval_ip"], 
                               port=state["nim_retrieval_port"] if len(state["nim_retrieval_port"]) > 0 else "8000",
                               model_name=state["nim_retrieval_id"] if len(state["nim_retrieval_id"]) > 0 else "meta/llama-3.1-8b-instruct",
                               gpu_type=state["nim_retrieval_gpu_type"] if "nim_retrieval_gpu_type" in state else None,
                               gpu_count=state["nim_retrieval_gpu_count"] if "nim_retrieval_gpu_count" in state else None,
                               temperature=0.7) if state["retrieval_use_nim"] else hosted_chat_model(state["retrieval_model_id"], 0)
    retrieval_grader = prompt | llm | StrOutputParser()
    for i, d in enumerate(documents):
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = _binary_score(score)
        # Document relevant
        if grade.lower() == "yes":
            print(f"[Retrieval Grader] Chunk {i + 1} of {len(documents)}: ✓ relevant")
            filtered_docs.append(d)
        # Document not relevant
        else:
            print(f"[Retrieval Grader] Chunk {i + 1} of {len(documents)}: ✗ not relevant — discarded")
            # We do not include the document in filtered_docs
            continue
    # We set a flag to indicate that we want to run web search if insufficient relevant docs found
    web_search = "Yes" if len(filtered_docs) < 1 else "No"
    print(f"[Retrieval Grader] Kept {len(filtered_docs)} of {len(documents)} chunk(s)")
    return {"documents": filtered_docs, "question": question, "web_search": web_search}


def web_search(state):
    """
    Web search based based on the question

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): Appended web results to documents
    """

    question = state["question"]
    documents = state.get("documents", [])
    print(f'[Web Search] Searching the web with Tavily (top {TAVILY_K} results): "{question}"')

    web_search_tool = TavilySearchResults(max_results=TAVILY_K)

    # Web search
    try:
        docs = web_search_tool.invoke({"query": question})

        # Manually validate Tavily returned what we expect
        if not isinstance(docs, list) or not all(isinstance(d, dict) and "content" in d for d in docs):
            raise TavilyAPIError(f"Invalid response from Tavily: {docs}")

        web_results = "\n".join([d["content"] for d in docs])
        web_results = Document(page_content=web_results)
        documents.append(web_results)
        print(f"[Web Search] ✓ Added {len(docs)} web result(s) to the context")

        return {"documents": documents, "question": question}

    except Exception as e:
        print(f"[Web Search] ✗ Web search failed: {e}")
        raise TavilyAPIError(f"Tavily web search failed: {e}")
    # if documents is not None:
    #     documents.append(web_results)
    # else:
    #     documents = [web_results]



### Conditional edge


def route_question(state):
    """
    Route question to web search or RAG.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """

    if database.has_context(state["collection_name"]):
        print("[Router] → A document context is available — searching the vector database first")
        return "vectorstore"
    print("[Router] → No document context is available — routing to web search")
    return "websearch"


def decide_to_generate(state):
    """
    Determines whether to generate an answer, or add web search

    Args:
        state (dict): The current graph state

    Returns:
        str: Binary decision for next node to call
    """

    question = state["question"]
    web_search = state["web_search"]
    filtered_documents = state["documents"]

    if web_search == "Yes":
        # A document collection was deliberately supplied by the user. Do not
        # replace an unsupported document answer with an unrelated web result.
        print("[Agent] No relevant document chunks survived grading — returning a grounded not-found response")
        return "not_found"
    else:
        # We have relevant documents, so generate answer
        print(f"[Agent] {len(filtered_documents)} relevant chunk(s) in hand — proceeding to answer generation")
        return "generate"


def no_answer(state):
    """Return a safe response when the indexed sources do not answer a question."""
    return {
        "documents": state.get("documents", []),
        "question": state["question"],
        "generation": "I couldn't find that information in the indexed sources. Try a more specific question or add another source.",
    }


### Conditional edge


def grade_generation_v_documents_and_question(state):
    """
    Determines whether the generation is grounded in the document and answers question.

    Args:
        state (dict): The current graph state

    Returns:
        str: Decision for next node to call
    """

    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]
    print(f"[Hallucination Grader] Checking the answer is grounded in the context using {_model_desc(state, 'hallucination')}...")

    prompt = PromptTemplate(
        template=state["prompt_hallucination"],
        input_variables=["generation", "documents"],
    )
    llm = nim.CustomChatOpenAI(custom_endpoint=state["nim_hallucination_ip"], 
                               port=state["nim_hallucination_port"] if len(state["nim_hallucination_port"]) > 0 else "8000",
                               model_name=state["nim_hallucination_id"] if len(state["nim_hallucination_id"]) > 0 else "meta/llama-3.1-8b-instruct",
                               gpu_type=state["nim_hallucination_gpu_type"] if "nim_hallucination_gpu_type" in state else None,
                               gpu_count=state["nim_hallucination_gpu_count"] if "nim_hallucination_gpu_count" in state else None,
                               temperature=0.7) if state["hallucination_use_nim"] else hosted_chat_model(state["hallucination_model_id"], 0)
    hallucination_grader = prompt | llm | StrOutputParser()

    score = hallucination_grader.invoke(
        {"documents": documents, "generation": generation}
    )
    grade = _binary_score(score)

    # Check hallucination
    prompt = PromptTemplate(
        template=state["prompt_answer"],
        input_variables=["generation", "question"],
    )
    llm = nim.CustomChatOpenAI(custom_endpoint=state["nim_answer_ip"], 
                               port=state["nim_answer_port"] if len(state["nim_answer_port"]) > 0 else "8000",
                               model_name=state["nim_answer_id"] if len(state["nim_answer_id"]) > 0 else "meta/llama-3.1-8b-instruct",
                               gpu_type=state["nim_answer_gpu_type"] if "nim_answer_gpu_type" in state else None,
                               gpu_count=state["nim_answer_gpu_count"] if "nim_answer_gpu_count" in state else None,
                               temperature=0.7) if state["answer_use_nim"] else hosted_chat_model(state["answer_model_id"], 0)
    answer_grader = prompt | llm | StrOutputParser()
    
    if grade == "yes":
        print("[Hallucination Grader] ✓ Answer is grounded in the retrieved context")
        # Check question-answering
        print(f"[Answer Grader] Checking the answer addresses the question using {_model_desc(state, 'answer')}...")
        score = answer_grader.invoke({"question": question, "generation": generation})
        grade = _binary_score(score)
        if grade == "yes":
            print("[Answer Grader] ✓ Answer addresses the question")
            return "useful"
        else:
            print("[Answer Grader] ✗ Answer does not address the question — retrying with web search")
            return "not useful"
    else:
        print("[Hallucination Grader] ✗ Answer is not grounded in the context — regenerating")
        return "not supported"
