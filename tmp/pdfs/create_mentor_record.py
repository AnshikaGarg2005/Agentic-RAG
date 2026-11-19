from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "pdf" / "mentor_meeting_record_midsem.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

BLUE = colors.HexColor("#163F8C")
LIGHT_BLUE = colors.HexColor("#EAF2FF")
GREY = colors.HexColor("#5B6573")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="RecordTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=18, leading=22, textColor=BLUE, spaceAfter=6, alignment=1,
))
styles.add(ParagraphStyle(
    name="RecordSub", parent=styles["Normal"], fontName="Helvetica",
    fontSize=9.5, leading=13, textColor=GREY, alignment=1, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="MeetingTitle", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12, leading=15, textColor=BLUE, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="BodySmall", parent=styles["Normal"], fontName="Helvetica",
    fontSize=9.3, leading=12.5, textColor=colors.HexColor("#202938"),
))
styles.add(ParagraphStyle(
    name="Label", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=8.7, leading=11, textColor=BLUE,
))


def p(text, style="BodySmall"):
    return Paragraph(text, styles[style])


def meeting_block(number, focus, discussion, progress, next_steps):
    header = Table(
        [[p(f"MEETING {number}: {focus}", "MeetingTitle"), p("Date: __________________", "Label")]],
        colWidths=[13.2 * cm, 4.2 * cm],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#B7CBEF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    rows = [
        [p("Discussion / agenda", "Label"), p(discussion)],
        [p("Progress / outcome", "Label"), p(progress)],
        [p("Action items before next meeting", "Label"), p(next_steps)],
        [p("Signatures", "Label"), p("Student: ____________________________&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Mentor: ____________________________")],
    ]
    details = Table(rows, colWidths=[4.2 * cm, 13.2 * cm])
    details.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D4E8")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F6F9FF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return KeepTogether([header, details, Spacer(1, 0.45 * cm)])


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B7CBEF"))
    canvas.line(1.5 * cm, 1.25 * cm, A4[0] - 1.5 * cm, 1.25 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(1.5 * cm, 0.85 * cm, "Mentor Meeting Record - Agentic RAG with AI Agent")
    canvas.drawRightString(A4[0] - 1.5 * cm, 0.85 * cm, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    rightMargin=1.5 * cm, leftMargin=1.5 * cm,
    topMargin=1.35 * cm, bottomMargin=1.7 * cm,
)

story = [
    p("MENTOR MEETING RECORD", "RecordTitle"),
    p("Major Project: Agentic RAG with AI Agent | Record up to Mid-Semester", "RecordSub"),
]

student_info = [
    [p("Student Name", "Label"), p("____________________________________________"), p("SAP ID", "Label"), p("________________________")],
    [p("Programme / Semester", "Label"), p("____________________________________________"), p("Mentor Name", "Label"), p("________________________")],
    [p("Department", "Label"), p("Computer Science and Engineering"), p("Academic Session", "Label"), p("________________________")],
]
info = Table(student_info, colWidths=[3.0 * cm, 7.0 * cm, 3.0 * cm, 4.4 * cm])
info.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D4E8")),
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F6F9FF")),
    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F6F9FF")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story += [info, Spacer(1, 0.5 * cm)]

meetings = [
    (
        "Project Topic Finalization and Problem Identification",
        "Discussed the project topic, Agentic RAG with AI Agent. Identified the limitation of conventional chatbots: they may hallucinate and cannot reliably answer from user-specific documents.",
        "Finalized the problem statement and the main goal: develop a source-grounded assistant for uploaded documents and webpages.",
        "Study Retrieval-Augmented Generation, vector databases, embeddings, and LLM-based question answering.",
    ),
    (
        "Literature Review and Technology Selection",
        "Reviewed the concepts of RAG, document chunking, semantic embeddings, vector search, and agent-based validation. Discussed possible technology choices.",
        "Selected Python, Streamlit, LangChain, LangGraph, ChromaDB, NVIDIA APIs, and Tavily Search for the prototype.",
        "Prepare the preliminary system architecture and identify supported source formats.",
    ),
    (
        "Architecture and Data Ingestion Design",
        "Designed the high-level pipeline: source upload or URL input, text extraction, chunking, embeddings, vector storage, retrieval, answer generation, and validation.",
        "Defined support for PDF, TXT, Markdown, CSV, and webpage URLs. Chose ChromaDB as the local vector store.",
        "Implement document loaders, text splitting, and source indexing workflow.",
    ),
    (
        "Embedding and Vector Retrieval Module",
        "Discussed semantic retrieval and the difference between keyword search and vector similarity search. Reviewed passage embeddings for source chunks and query embeddings for questions.",
        "Implemented NVIDIA embedding integration and ChromaDB storage. Verified that relevant document chunks can be retrieved for a query.",
        "Integrate the retrieval module with the language-model answer generation step.",
    ),
    (
        "Agent Workflow and Answer Validation",
        "Discussed routing between indexed sources and web search, relevance grading of retrieved chunks, grounding checks, and answer-quality evaluation.",
        "Created the LangGraph workflow for retrieval, generation, relevance grading, hallucination checking, and safe not-found responses.",
        "Connect the workflow to the Streamlit interface and test source-grounded question answering.",
    ),
    (
        "Mid-Semester Progress Review",
        "Demonstrated the prototype with document upload, URL indexing, semantic retrieval, NVIDIA LLM-based answer generation, and validation stages. Discussed current limitations and improvements after mid-semester.",
        "Mid-semester deliverable completed: working Agentic RAG prototype with a Streamlit interface, ChromaDB knowledge base, and web-search fallback when no source context exists.",
        "Post-mid-semester scope: add citations, improve document handling, conduct formal evaluation, and prepare final deployment/documentation.",
    ),
]

for index, meeting in enumerate(meetings, start=1):
    # Keep the final two meetings together on a fresh page instead of allowing
    # a meeting header to land at the very top of a continuation page.
    if index == 5:
        story.append(PageBreak())
    story.append(meeting_block(index, *meeting))

doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
