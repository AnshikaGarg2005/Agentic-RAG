from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output"; DOCX = OUT / "docx" / "Research_Paper.docx"; FIG = OUT / "Figures"; REF = OUT / "References"
for p in (DOCX.parent, OUT / "pdf", FIG, REF): p.mkdir(parents=True, exist_ok=True)

def pil_font(size, bold=False):
    paths = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"]
    for x in paths:
        try: return ImageFont.truetype(x, size)
        except OSError: pass
    return ImageFont.load_default()

def wrap(d, text, f, width):
    lines=[]; line=""
    for word in text.split():
        c=(line+" "+word).strip()
        if d.textbbox((0,0),c,font=f)[2] <= width: line=c
        else: lines.append(line); line=word
    return lines+[line]

def fig(path, title, boxes, arrows, note):
    im=Image.new("RGB",(1500,820),"white"); d=ImageDraw.Draw(im); navy="#183A63"; f=pil_font(29,True)
    d.text((750,22),title,anchor="ma",font=pil_font(36,True),fill=navy)
    for x1,y1,x2,y2,label,color in boxes:
        d.rounded_rectangle((x1,y1,x2,y2),radius=18,fill=color,outline=navy,width=3)
        lines=wrap(d,label,f,x2-x1-24); y=(y1+y2-(len(lines)*34))/2
        for line in lines:
            d.text(((x1+x2)/2,y),line,anchor="ma",font=f,fill="white"); y+=34
    for a,b in arrows:
        d.line([a,b],fill=navy,width=4); x,y=b; px,py=a
        if abs(x-px)>abs(y-py): d.polygon([(x,y),(x-15 if x>px else x+15,y-8),(x-15 if x>px else x+15,y+8)],fill=navy)
        else: d.polygon([(x,y),(x-8,y-15 if y>py else y+15),(x+8,y-15 if y>py else y+15)],fill=navy)
    d.text((750,780),note,anchor="ma",font=pil_font(19),fill="#404040"); im.save(path)

arch=FIG/"Figure_1_System_Architecture.png"
fig(arch,"Agentic RAG System Architecture",[(50,160,285,280,"Files and URLs","#4F81BD"),(350,160,585,280,"Load and chunk","#70AD47"),(650,160,890,280,"NVIDIA embeddings","#70AD47"),(955,160,1195,280,"ChromaDB context","#70AD47"),(1260,160,1450,280,"Retrieve","#F4B183"),(50,510,285,630,"Question","#5B9BD5"),(350,510,585,630,"Context available?","#A5A5A5"),(650,430,890,550,"Grade relevance","#F4B183"),(650,640,890,760,"Tavily search","#8064A2"),(955,510,1195,630,"Generate","#ED7D31"),(1260,510,1450,630,"Grounding and usefulness","#ED7D31")], [((285,220),(350,220)),((585,220),(650,220)),((890,220),(955,220)),((1195,220),(1260,220)),((285,570),(350,570)),((585,550),(650,490)),((585,590),(650,700)),((890,490),(955,550)),((890,700),(955,590)),((1195,570),(1260,570))],"A local-source miss returns a safe not-found answer; web search is used only without indexed context.")
flow=FIG/"Figure_2_Agent_Workflow.png"
fig(flow,"Implemented LangGraph Question Answering Workflow",[(50,160,285,290,"User question","#5B9BD5"),(360,160,620,290,"Route by indexed context","#A5A5A5"),(700,75,970,205,"Retrieve semantic chunks","#F4B183"),(700,300,970,430,"Tavily web search","#8064A2"),(1050,75,1320,205,"Relevance grading","#F4B183"),(1050,300,1320,430,"Generate answer","#ED7D31"),(1050,540,1320,670,"Grounding and answer checks","#ED7D31"),(360,540,620,670,"Safe not-found response","#C55A11"),(1050,710,1320,800,"Final answer","#70AD47")], [((285,225),(360,225)),((620,190),(700,140)),((620,255),(700,365)),((970,140),(1050,140)),((970,365),(1050,365)),((1185,205),(1185,300)),((1185,430),(1185,540)),((1185,670),(1185,710)),((1050,140),(620,605))],"The graph retries unsupported generations within a configured recursion limit.")
evalfig=FIG/"Figure_3_Evaluation_Protocol.png"
fig(evalfig,"Proposed Reproducible Evaluation Protocol",[(65,230,315,365,"Held-out source corpus","#4F81BD"),(390,230,640,365,"Questions with gold answers and evidence spans","#5B9BD5"),(715,115,965,250,"Retrieval metrics: Recall@K and MRR","#70AD47"),(715,350,965,485,"Generation: correctness and faithfulness","#ED7D31"),(1040,115,1290,250,"Safe failure: abstention precision","#C55A11"),(1040,350,1290,485,"Operational: latency per stage","#8064A2")], [((315,295),(390,295)),((640,270),(715,185)),((640,320),(715,415)),((965,185),(1040,185)),((965,415),(1040,415))],"This protocol is proposed for future measurement; the current repository has no benchmark results to report.")

def cols(s):
    c=s._sectPr.first_child_found_in("w:cols"); c.set(qn("w:num"),"2"); c.set(qn("w:space"),"270"); c.set(qn("w:equalWidth"),"1")
def cell(c, fill=None, header=False):
    p=c._tc.get_or_add_tcPr(); b=OxmlElement("w:tcBorders")
    for e in ("top","left","bottom","right"):
        x=OxmlElement(f"w:{e}"); x.set(qn("w:val"),"single"); x.set(qn("w:sz"),"6"); x.set(qn("w:color"),"D9D9D9"); b.append(x)
    p.append(b)
    if fill: x=OxmlElement("w:shd"); x.set(qn("w:fill"),fill); p.append(x)
    for pp in c.paragraphs:
        pp.paragraph_format.space_after=Pt(0)
        for r in pp.runs:
            r.font.name="Times New Roman"; r.font.size=Pt(8)
            if header: r.bold=True; r.font.color.rgb=RGBColor(255,255,255)
def page_no(p):
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(); a=OxmlElement("w:fldChar");a.set(qn("w:fldCharType"),"begin");i=OxmlElement("w:instrText");i.text="PAGE";z=OxmlElement("w:fldChar");z.set(qn("w:fldCharType"),"end");r._r.extend((a,i,z))

d=Document(); s=d.sections[0]; s.page_width=Inches(8.27);s.page_height=Inches(11.69);s.top_margin=s.bottom_margin=Inches(.55);s.left_margin=s.right_margin=Inches(.6);page_no(s.footer.paragraphs[0])
n=d.styles["Normal"];n.font.name="Times New Roman";n._element.rPr.rFonts.set(qn("w:eastAsia"),"Times New Roman");n.font.size=Pt(10.5);n.paragraph_format.space_after=Pt(3);n.paragraph_format.line_spacing=1.0
t=d.styles["Title"];t.font.name="Times New Roman";t.font.size=Pt(20);t.font.color.rgb=RGBColor(0,0,0);t.font.bold=False
def para(x,label=None):
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.0
    if label: r=p.add_run(label);r.bold=True
    p.add_run(x)
def head(i,x):
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_before=Pt(7);p.paragraph_format.space_after=Pt(3);r=p.add_run(f"{i + '. ' if i else ''}{x.upper()}");r.font.name="Times New Roman";r.font.size=Pt(10.2)
def sub(i,x):
    p=d.add_paragraph();p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(2);r=p.add_run(f"{i}. {x}");r.bold=True;r.font.name="Times New Roman";r.font.size=Pt(9.4)
def caption(x):
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(4);r=p.add_run(x);r.italic=True;r.font.name="Times New Roman";r.font.size=Pt(8.2)
def picture(path,cap):
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run().add_picture(str(path),width=Inches(3.27));caption(cap)
def table(title,heads,rows):
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;r=p.add_run(title);r.bold=True;r.font.name="Times New Roman";r.font.size=Pt(8.2)
    q=d.add_table(rows=1,cols=2);q.alignment=WD_TABLE_ALIGNMENT.CENTER;q.autofit=False
    q.columns[0].width=Inches(1.05);q.columns[1].width=Inches(2.12)
    for c,x,w in zip(q.rows[0].cells,heads,(1.05,2.12)):
        c.text=x;c.width=Inches(w);cell(c,"183A63",True)
    for k,row in enumerate(rows):
        for c,x,w in zip(q.add_row().cells,row,(1.05,2.12)):
            c.text=x;c.width=Inches(w);cell(c,"EEF4FA" if k%2==0 else None)

p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(5)
r=p.add_run("Agentic Retrieval Augmented Generation for Source Grounded Document and Web Question Answering");r.font.name="Times New Roman";r.font.size=Pt(20)
for x,it,sz in [("Anshika Garg, Namita Mishra, Mohit Shukla",False,11),("School of Computer Science, UPES, Dehradun",True,9.5),("Emails: Anshika.120611@stu.upes.ac.in, Namita.122800@stu.upes.ac.in, Mohit.123427@stu.upes.ac.in",False,8.3)]:
    p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.paragraph_format.space_after=Pt(1);r=p.add_run(x);r.font.name="Times New Roman";r.font.size=Pt(sz);r.italic=it
b=d.add_section(WD_SECTION.CONTINUOUS);b.top_margin=s.top_margin;b.bottom_margin=s.bottom_margin;b.left_margin=s.left_margin;b.right_margin=s.right_margin;cols(b)
para("Large language models can provide fluent answers but may not know private documents and can produce unsupported content. This paper presents an Agentic Retrieval Augmented Generation prototype for source-grounded question answering over PDFs, text files, Markdown files, CSV files, and webpage URLs. The system chunks source text, creates NVIDIA embeddings, stores representations in ChromaDB, retrieves semantic evidence, and generates answers using NVIDIA Nemotron. A LangGraph workflow performs source-aware routing, relevance grading, generation, grounding assessment, and answer usefulness assessment. Tavily web search is used only when no indexed context exists. If indexed sources do not contain evidence, the system returns an explicit not-found response rather than unrelated web content. Repository inspection confirms functional integration tests but finds no benchmark dataset, model checkpoints, training logs, or numerical evaluation artifacts; therefore, the paper reports verified functional results and a reproducible evaluation protocol without fabricated metrics.","Abstract—")
para("agentic RAG, retrieval augmented generation, semantic retrieval, source grounding, ChromaDB, LangGraph, NVIDIA NIM","Index Terms—")

head("I","Introduction")
sub("A","Problem statement and motivation")
para("Large language models are useful conversational interfaces, but model knowledge alone is insufficient for questions about private, current, or domain-specific material. Retrieval-Augmented Generation supplements a language model with retrieved external evidence before generation [1]. This is relevant to resumes, academic material, technical documentation, and policy repositories where users expect answers tied to an identifiable source.")
para("The project addresses how a conversational application can answer from user-provided files and webpages, filter weak retrieval, and avoid representing a general web response as a fact found in a selected document. The active local application is a Streamlit frontend built around a LangGraph workflow and NVIDIA-hosted model endpoints.")
sub("B","Objectives and contributions")
para("The objectives are to ingest heterogeneous sources, build a session-specific semantic index, retrieve evidence for a question, generate concise context-conditioned answers, grade relevance and grounding, use web search only without local context, and abstain when selected sources are insufficient. The contribution is an implementation-focused source-boundary policy: once a user context exists, an unsupported question returns a safe local-source miss instead of automatic unrelated web fallback.")

head("II","Literature Review")
sub("A","RAG and semantic retrieval")
para("RAG combines parametric generation with non-parametric retrieved memory for knowledge-intensive tasks [1]. Dense passage retrieval uses a shared vector space for questions and passages and has proven effective for open-domain question answering [2]. Sentence-BERT demonstrated efficient semantically meaningful embeddings for similarity tasks [3]. The proposed system follows this retrieval pattern, using passage-mode embeddings for chunks and query-mode embeddings for questions.")
sub("B","Corrective and agentic RAG")
para("Retrieved evidence may be weak or irrelevant. Corrective RAG assesses retrieval quality and can take alternative retrieval actions [4]. Self-RAG integrates retrieval and critique mechanisms to improve factuality [5]. The project does not train a corrective model; it applies these ideas as an execution graph with relevance, grounding, and usefulness graders. LangGraph supports the graph-based orchestration of deterministic and model-driven steps [7].")
sub("C","Research gap")
para("Benchmark studies evaluate retrieval and generation over fixed corpora, while user-facing systems also need clear provenance rules. This work prioritises user-indexed context over live web results. The policy improves interpretability, although it requires an explicit future Web Only or Hybrid mode for questions unrelated to an active local corpus.")

head("III","Methodology")
sub("A","System architecture")
para("Figure 1 shows two linked paths. The knowledge-base path accepts files or URLs, loads text with format-specific loaders, recursively splits text, produces NVIDIA embeddings, and stores chunks in a session-specific ChromaDB collection. The question path chooses local retrieval if context exists, or Tavily search only if it does not. The resulting evidence conditions answer generation and checking.")
picture(arch,"Fig. 1. Source-grounded architecture derived from the active repository implementation.")
sub("B","Ingestion and representation")
para("The repository supports PDF through PyPDFLoader, TXT and Markdown through TextLoader, CSV through CSVLoader, and webpages through WebBaseLoader. RecursiveCharacterTextSplitter uses a default chunk size of 250 tokens and overlap of zero. The NVIDIA embedding client sends source chunks with input_type passage and questions with input_type query. Let q denote a question and d_i a chunk. The embeddings are e_q and e_i, and retrieval ranks chunks by semantic similarity.")
p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run("e_q = E_query(q),       e_i = E_passage(d_i)                                      (1)").font.name="Times New Roman"
p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER;p.add_run("R(q) = TopK_i sim(e_q, e_i)                                                   (2)").font.name="Times New Roman"
sub("C","Agent workflow")
para("Figure 2 maps the graph in compile.py and graph.py. If context exists, the graph retrieves candidates and grades each chunk. If no chunk survives, it returns a predefined not-found message. Without local context, TavilySearchResults returns up to TAVILY_K results, which defaults to three. The generator uses retrieved context, after which grounding and answer graders determine whether the response is accepted, retried, or redirected. A recursion limit of 10 bounds graph execution in the Streamlit frontend.")
picture(flow,"Fig. 2. Implemented state graph for source-aware routing, retrieval, generation, and validation.")
table("TABLE I: IMPLEMENTED CONFIGURATION",["Component","Repository-supported configuration"],[
("Sources","PDF, TXT, Markdown, CSV, and webpage URLs."),("Chunking","Recursive splitter; 250 token default; zero overlap."),("Embeddings","nvidia/nemotron-3-embed-1b; passage and query modes."),("Vector store","ChromaDB via langchain-chroma; session-specific collection."),("Generation and graders","nvidia/nemotron-3.5-lightning-30b-a3b through NVIDIA endpoint."),("Web fallback","TavilySearchResults; default maximum result count 3."),("Execution bound","Streamlit invokes graph with recursion_limit=10.")])
sub("D","Prompting, output parsing, and failure handling")
para("The generator prompt asks the hosted model to use retrieved context, to state that it does not know when evidence is unavailable, and to remain concise. The relevance, grounding, and usefulness prompts request binary decisions. Although the templates request JSON, the implementation uses a regular-expression parser that accepts both structured output and bare yes or no responses. If the parser cannot identify a binary score, it fails closed to no. This prevents a malformed grader output from being interpreted as evidence for a document-grounded answer.")
para("The system separates operational failures from answer-level abstention. Invalid URLs and loader failures are skipped during source ingestion; a context is only marked ready after embedding and ChromaDB storage succeed. Tavily exceptions are surfaced to the Streamlit user as a configuration or web-search failure. A graph recursion error returns a user-facing retry-limit message. These paths do not establish correctness of every answer, but they make failure modes explicit instead of silently returning an arbitrary response.")
sub("E","Privacy and operational considerations")
para("Uploaded files are written under a collection-specific directory and indexed into a collection whose name is derived from a per-session UUID. This reduces accidental mixing of temporary contexts within the application, but it is not a substitute for persistent identity, access control, encryption, or a retention policy. API keys are loaded through environment variables using python-dotenv rather than embedded in source code. For production use, document storage, provider data handling, audit logging, secret rotation, rate limits, and authorisation must be designed separately.")
sub("F","Runtime lifecycle")
para("At application startup, the Streamlit frontend loads environment variables, creates session state, and displays whether the NVIDIA and Tavily credentials are available. A new session receives a unique ChromaDB collection name. When a user selects files, the frontend writes them into a collection-specific upload directory, rejects already processed file-name and size pairs, and invokes the file-ingestion pipeline. For a URL list, the frontend splits lines, validates URL structure, attempts to load each page, and indexes only usable content. The knowledge-base status changes to context ready only when indexing returns successfully.")
para("At query time, the user question and the active collection name are placed in the LangGraph state together with model identifiers and prompt templates. The graph stream emits updates from individual nodes; the frontend collects the final generation and renders it in the chat view. Clear context deletes the active collection, resets source state, and restores web-search fallback. This lifecycle makes context state explicit, which is important because the answer route depends on whether indexed content currently exists.")
sub("G","Why chunking and session isolation matter")
para("Embedding an entire long document as one record would make retrieval coarse and would force the generator to receive excessive context. Recursive chunking creates smaller units that can be independently compared with the question. The selected chunk size is a configurable engineering parameter rather than a universal optimum: larger chunks may retain more context but can introduce unrelated text, whereas smaller chunks can improve focus but fragment evidence. The current default of 250 tokens with zero overlap is a repository configuration and should be treated as a value for evaluation, not as a claimed optimum.")
para("Similarly, a single shared collection could cause a later question to retrieve material from a previous unrelated upload. The session-specific naming strategy reduces this risk in the local prototype. It does not by itself establish long-term privacy because persisted data still requires retention controls. In a multi-user deployment, collection ownership, access checks, encryption, audit records, and a deletion mechanism must be added around the vector store and upload directories.")
sub("H","User interaction and source state")
para("The Streamlit interface deliberately separates source preparation from question answering. A user may enter webpage URLs one per line or choose supported local files. The interface retains the selected sources, exposes an index action, and identifies the resulting indexed sources after successful processing. This interaction model prevents a user from assuming that merely selecting a file makes it available to retrieval. It also makes the source-boundary policy visible: the status panel distinguishes web-search fallback from a context-ready collection.")
para("The query field is shared by both routes, but its semantics depend on the active context. With no collection, the same question is treated as a web-search question. With an active collection, it is treated as a request for evidence from the selected sources. This is an important interface-level constraint rather than an incidental implementation detail. A production interface should make the selected mode explicit before submission and should provide controls to inspect, remove, or reorder individual sources.")

head("IV","Experimental Setup and Validation")
sub("A","Scope of evidence")
para("This is an inference-time application, not a model-training repository. No labelled benchmark, train-validation split, checkpoints, loss curves, confusion matrices, ROC curves, hardware logs, or measured accuracy outputs were found during the repository audit. Consequently, it would be invalid to report accuracy, precision, recall, F1, AUC, Dice, IoU, latency, cost, or percentage improvements. The present evaluation instead records completed functional checks from the verified project workflow.")
sub("B","Functional validation")
table("TABLE II: VERIFIED FUNCTIONAL RESULTS",["Test","Observed result"],[
("Syntax and dependencies","Python compilation passed for active application, graph, database, and prompt modules."),("NVIDIA connectivity","Hosted chat and nvidia/nemotron-3-embed-1b embedding requests passed with valid Build inference access."),("Indexing and retrieval","ChromaDB indexing and semantic retrieval passed for uploaded content."),("Web fallback","Tavily request and complete web-search workflow passed when no context existed."),("Grounded document path","Retrieval, relevance grading, generation, grounding, and answer grading completed for a relevant question."),("Unsupported local question","Returns an indexed-source not-found response instead of unrelated web content."),("Output parsing","Plain yes/no and JSON-like grader result handling passed.")])
sub("C","Reproducible quantitative protocol")
para("A future controlled evaluation should define a held-out corpus, questions with gold answers and source spans, and a reproducible environment. Retrieval evaluation should report Recall@K and Mean Reciprocal Rank. Generation evaluation should report human-scored correctness and faithfulness plus context precision, context recall, and answer relevance using a documented framework such as RAGAS [6]. A deliberately unanswerable subset should report abstention precision and false-answer rate. Timing should separately measure indexing, retrieval, web search, generation, and end-to-end latency.")
picture(evalfig,"Fig. 3. Proposed protocol for future quantitative evaluation of the repository implementation.")
sub("D","Metric definitions and experimental controls")
para("For a test set of N questions, Recall@K is the fraction for which at least one supporting chunk appears among the K retrieved chunks. Mean Reciprocal Rank averages the inverse rank of the first supporting chunk. Faithfulness should be assessed against the specific evidence passed to generation rather than only against a reference answer. The unanswerable subset must contain questions whose answers are demonstrably absent from the indexed source, so that abstention can be evaluated as a first-class system behaviour. Every run should record the model identifiers, prompt versions, chunk size, overlap, TAVILY_K value, recursion limit, source corpus version, and execution timestamp.")
para("Comparisons must hold the corpus and question set fixed. Suitable ablations include removing relevance grading, replacing the source-priority policy with hybrid fallback, altering chunk size and overlap, and comparing dense-only retrieval with hybrid retrieval. Human evaluators should be blinded to the evaluated configuration where possible, and disagreements should be reported rather than collapsed into a single unverified score. The current paper does not claim the outcome of these ablations because the repository does not contain the required experiment records.")
sub("E","Validation procedure and traceability")
para("The completed checks should be repeatable with a configured NVIDIA Build endpoint and Tavily API key. First, compile the active Python modules to detect import and syntax failures. Next, start the Streamlit application and confirm service readiness. Index a small supported document and verify that a source-specific question completes retrieval, relevance grading, generation, grounding assessment, and answer-quality assessment. Ask a question whose answer is absent from that document and verify the explicit not-found response. Clear context, ask a general question, and verify the Tavily branch. These tests check transitions and failure boundaries; they are not substitutes for a held-out benchmark.")
para("For every validation run, an evaluator should retain a minimal trace containing the selected source list, indexing status, query, chosen route, accepted or rejected chunks, grader decisions, final response, model names, and any error message. The current graphical interface displays chat-level outputs but does not export such a trace. Recording it in a future version would allow regressions to be detected when prompts, loaders, dependencies, or hosted-model behaviour change.")

head("V","Results and Discussion")
sub("A","Findings")
para("The functional results establish that the prototype executes each designed branch: it constructs a session-local knowledge base, retrieves evidence for source questions, generates and grades answers, searches the web without local context, and abstains for unsupported local questions. The last behaviour directly addresses the project objective of maintaining a distinction between missing source evidence and absence of a source collection.")
para("The implementation also reveals an important distinction between source indexing and live web search. A URL entered by the user is first downloaded, chunked, embedded, and stored as part of the local knowledge base. It is then queried through ChromaDB like any uploaded document. Tavily, in contrast, is invoked only when the collection has no indexed content. Therefore, a question about a current event will not automatically use Tavily if an unrelated resume, PDF, or URL is still indexed. This behaviour is not a search failure; it follows the source-priority policy encoded in the route_question and decide_to_generate transitions.")
sub("B","Evidence trace for representative scenarios")
para("For a representative document-grounded scenario, the sequence is: select a supported file, extract its text, split and embed chunks, persist the chunks to the session collection, ask a question, retrieve semantically similar chunks, grade the chunks, generate from accepted evidence, and assess the answer. For a representative web-only scenario, no collection context exists, so the router invokes Tavily and generation receives the returned web text. For an unsupported local question, retrieval can return candidates but the relevance grader removes them; this leads to the safe not-found node instead of a web search. These three branches are the core behaviours verified in the project validation record.")
para("The generated response is intentionally concise because the generator prompt specifies a maximum of five sentences. Concision reduces the opportunity for unsupported elaboration but does not replace evidence citations. An improvement would attach the filenames, URLs, page numbers, and chunk excerpts that contributed to a response. Such provenance would make human review possible and would enable a more rigorous faithfulness evaluation than the current binary grader alone.")
sub("C","Comparison and limitations")
table("TABLE III: DESIGN COMPARISON",["Pattern","Evidence policy"],[
("Direct LLM prompting","No external source boundary; private documents are unavailable unless manually placed in the prompt."),("Basic local RAG","Retrieves local chunks but can generate from weak retrieval without explicit quality checks."),("Unconstrained local plus web RAG","Can increase coverage but may obscure whether an answer was found locally or online."),("Proposed agentic RAG","Source-aware routing, relevance filtering, grounding and usefulness checks, and safe not-found path.")])
para("The system does not display passage-level citations or page references with each answer. Extraction quality is limited for scanned PDFs because OCR is absent. URL ingestion depends on readable webpages. LLM grading can vary with prompts and model behaviour; it is a control mechanism, not formal verification. The local-source priority policy also makes unrelated current-affairs questions return not-found while context remains active. Authentication, role-based access, source retention, deletion policy, and security evaluation are not implemented.")
sub("D","Error modes and mitigation")
para("The principal error modes occur at source loading, retrieval, grading, generation, and user interpretation. A URL can be syntactically valid but fail to expose usable text; a PDF can contain a scanned page without extractable text; semantically similar chunks can still omit the answer; and a generated statement can be unsupported despite contextual prompting. The current system mitigates some of these risks with loader error handling, relevance filtering, a safe not-found branch, grounding assessment, and bounded retries. It does not yet expose retrieved chunks or citations to the user, so a user cannot independently inspect the exact evidence within the interface.")
para("The system also has a design tension between recall and provenance. Permitting web fallback whenever a local retrieval fails can improve coverage, but it can conceal the fact that an answer was not found in the user-selected source. Blocking fallback preserves provenance but can be overly restrictive. The present prototype selects the latter behaviour. A user-controlled retrieval mode is the recommended resolution because it exposes this trade-off as an explicit product decision rather than an implicit agent action.")
sub("E","Practical deployment considerations")
para("The prototype is suitable for local demonstrations and controlled evaluation, but hosted deployment changes the threat model. Uploaded files may contain sensitive personal or organisational information, and web pages may change after indexing. A deployment should define an allowed-file policy, virus scanning, storage encryption, isolation between users, retention periods, deletion workflows, and monitoring for provider errors. API credentials must remain server-side and should be rotated according to the provider policy. These measures sit outside the current codebase and should not be inferred from the use of environment variables alone.")
para("Operational quality also depends on observability. Useful production telemetry would include indexing duration, chunk count, retrieval depth, rejected-chunk rate, route selection, retry count, and user feedback. These values should be collected without logging source text or secrets unnecessarily. Such instrumentation would make it possible to distinguish a loader issue, an embedding issue, an empty retrieval result, a grader rejection, and a hosted-model failure when a user reports an unsatisfactory response.")
sub("F","Design trade-offs and interpretability")
para("The main architectural trade-off is between broad answer coverage and a clear provenance boundary. A conventional assistant may search the web whenever it cannot answer from a file, which can be convenient but may lead a user to believe that the answer came from the selected file. The present prototype instead treats the presence of an indexed collection as an instruction to remain within that collection. It may therefore return a not-found response more often, but the response has a simpler interpretation: the requested evidence was not retrieved from the currently selected sources.")
para("The grading stages introduce a second trade-off. Relevance filtering prevents clearly unrelated chunks from reaching generation, while grounding and usefulness checks can trigger another attempt. These controls can reduce unsupported answers, but they also add model calls, latency, and dependence on prompt interpretation. The repository handles malformed binary-grader output conservatively, treating it as negative rather than accepting it as evidence. This is preferable for a source-grounded prototype, although a full evaluation is needed to quantify how often valid answers are incorrectly rejected.")
para("Interpretability is consequently more than a visual feature. The system should tell the user whether the response was derived from indexed files, an indexed URL, or web search; which chunks were used; and why a source was rejected. The current application exposes the high-level knowledge-base state and chat response, but not this detailed provenance. Adding a compact evidence panel would help users verify answers, help developers diagnose retrieval errors, and make the claimed source boundary observable rather than implicit.")
sub("G","Component interactions and data flow")
para("The data flow is intentionally modular. Loaders produce LangChain documents with source metadata, the splitter produces chunks, the embedding client transforms chunks into vectors, and ChromaDB stores vectors with their associated text. The graph does not need to know how a PDF or webpage was loaded; it receives a collection name and a question. This separation allows a loader or the embedding provider to be replaced without changing the high-level routing logic. Conversely, changes to metadata, chunking, or collection naming can affect retrieval quality even when the graph itself remains unchanged.")
para("During indexed retrieval, the vector store returns semantically similar candidates rather than a definitive answer. The relevance grader is therefore applied to candidate text, not to a completed response. The generator is only called after this filtering stage chooses context to pass downstream. Grounding and usefulness assessment occur after generation and operate on the generated answer in relation to the retrieved evidence and user question. Keeping these responsibilities separate makes the workflow easier to reason about: retrieval selects evidence, generation writes an answer, and graders decide whether the evidence or answer should be accepted.")
para("The web path follows a parallel route. TavilySearchResults returns web material when no local collection is available. The workflow applies contextual generation and checking, but the provenance is online search rather than a user-indexed artifact. A future implementation should preserve result URLs and retrieval timestamps because online content is mutable.")
sub("H","Failure semantics and user expectations")
para("A reliable interface should distinguish a system failure from an information failure. A system failure includes an invalid API key, an unreachable provider, a parsing error, an unsupported file, a webpage with no usable text, or a recursion limit reached by the graph. An information failure means that the system ran normally but the requested evidence was not present in the indexed sources. The prototype represents the latter with a safe not-found message. Treating these outcomes separately prevents an unavailable answer from being mistaken for a successful but empty search.")
para("This distinction also guides user feedback. A message about missing indexed evidence should recommend a more specific question or another source. A configuration or provider failure should identify the affected service and support a safe retry. Future versions can represent error categories as structured events and provide targeted recovery actions such as reindexing, clearing context, checking credentials, or switching retrieval mode.")
sub("I","Future work")
para("Future work should add clickable citations, source filtering, OCR, hybrid sparse-dense retrieval, reranking, explicit Document Only/Web Only/Hybrid controls, authentication, lifecycle controls for uploads, and an evaluation corpus. A subsequent study can compare the current source-priority policy with hybrid retrieval under answerable and unanswerable questions using documented retrieval, faithfulness, abstention, and latency metrics.")

head("VI","Conclusion and Future Work")
para("This paper presented a source-grounded Agentic RAG system for questions over uploaded files and indexed webpages. The implementation combines multi-format ingestion, chunking, NVIDIA embeddings, ChromaDB retrieval, NVIDIA-hosted generation, LangGraph control flow, relevance grading, grounding assessment, and answer usefulness assessment. Its distinctive design choice is to avoid replacing missing evidence in an active user knowledge base with unrelated web content. Verified integration tests confirm the main functional paths. Quantitative claims are intentionally reserved for future benchmarked evaluation, providing a technically honest foundation for continued research on trustworthy conversational retrieval systems.")

head("","References")
refs=[
"[1] P. Lewis et al., ‘Retrieval-augmented generation for knowledge-intensive NLP tasks,’ Advances in Neural Information Processing Systems, vol. 33, pp. 9459-9474, 2020. https://proceedings.neurips.cc/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf",
"[2] V. Karpukhin et al., ‘Dense passage retrieval for open-domain question answering,’ Proc. EMNLP, 2020, pp. 6769-6781, doi: 10.18653/v1/2020.emnlp-main.550.",
"[3] N. Reimers and I. Gurevych, ‘Sentence-BERT: Sentence embeddings using Siamese BERT-networks,’ Proc. EMNLP-IJCNLP, 2019, pp. 3982-3992, doi: 10.18653/v1/D19-1410.",
"[4] S.-Q. Yan, J.-C. Gu, Y. Zhu, and Z.-H. Ling, ‘Corrective retrieval augmented generation,’ arXiv:2401.15884, 2024. https://arxiv.org/abs/2401.15884",
"[5] A. Asai et al., ‘Self-RAG: Learning to retrieve, generate, and critique through self-reflection,’ Proc. ICLR, 2024. https://proceedings.iclr.cc/paper_files/paper/2024/file/25f7be9694d7b32d5cc670927b8091e1-Paper-Conference.pdf",
"[6] S. Es et al., ‘RAGAS: Automated evaluation of retrieval augmented generation,’ arXiv:2309.15217, 2023. https://arxiv.org/abs/2309.15217",
"[7] LangChain, ‘LangGraph documentation,’ 2026. https://langchain-ai.github.io/langgraph/",
"[8] Chroma, ‘Chroma documentation,’ 2026. https://docs.trychroma.com/",
"[9] NVIDIA, ‘NVIDIA NIM API reference,’ 2026. https://docs.api.nvidia.com/nim/",
"[10] Streamlit, ‘Streamlit documentation,’ 2026. https://docs.streamlit.io/",
"[11] Tavily, ‘Tavily Search API documentation,’ 2026. https://docs.tavily.com/",
]
for x in refs:
    p=d.add_paragraph();p.paragraph_format.left_indent=Inches(.14);p.paragraph_format.first_line_indent=Inches(-.14);p.paragraph_format.space_after=Pt(2);r=p.add_run(x);r.font.name="Times New Roman";r.font.size=Pt(8.1)
d.core_properties.title="Agentic Retrieval Augmented Generation for Source Grounded Document and Web Question Answering";d.core_properties.author="Anshika Garg, Namita Mishra, Mohit Shukla";d.save(DOCX)
(REF/"Verified_Bibliography.txt").write_text("\n\n".join(refs)+"\n",encoding="utf-8")
(REF/"Repository_Evidence.txt").write_text("Active entry point: app.py\nGraph: code/chatui/utils/compile.py and graph.py\nIngestion: code/chatui/utils/database.py\nPrompts: code/chatui/prompts/prompts_nemotron.py\n\nAudit finding: no labelled benchmark dataset, model checkpoints, training logs, loss curves, confusion matrices, ROC curves, or quantitative evaluation outputs were found. The paper therefore makes no unsupported metric claims.\n",encoding="utf-8")
print(DOCX)
