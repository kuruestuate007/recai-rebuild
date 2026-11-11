import re
import subprocess
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

S = Path(r"C:/Users/kikunal/AppData/Local/Temp/claude/4d737c2ba2bc1703/42329f66-8444-456f-8fe0-f3742cabc90c/scratchpad")
OUTDOC = Path(r"D:/2026-estuate/Anthropic-app-publishing/Citation_generator/docs/deliverables/RecAI-Rebuild-Understanding-Architecture-Cost.docx")
NAVY, GREY = RGBColor(0x1F, 0x38, 0x64), RGBColor(0x59, 0x59, 0x59)

doc = Document()
s = doc.sections[0]
s.page_width, s.page_height = Inches(8.5), Inches(11)
s.left_margin = s.right_margin = Inches(0.8)
s.top_margin = s.bottom_margin = Inches(0.7)
st = doc.styles["Normal"]
st.font.name = "Arial"
st.font.size = Pt(10)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
st.paragraph_format.space_after = Pt(4)


def run(p, t, b=False, c=None, sz=None):
    r = p.add_run(t)
    r.bold = b
    r.font.name = "Arial"
    if c:
        r.font.color.rgb = c
    if sz:
        r.font.size = Pt(sz)


def para(t, c=None, sz=None):
    p = doc.add_paragraph()
    run(p, t, c=c, sz=sz)
    return p


def head(t):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.keep_with_next = True
    run(p, t, True, NAVY, 13)


def bl(lead, rest=""):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    if lead:
        run(p, lead, True)
    run(p, rest)


def shade(c, f):
    tc = c._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), f)
    tc.append(sh)


def tbl(w, rows, bold_rows=()):
    t = doc.add_table(rows=len(rows), cols=len(w))
    t.style = "Table Grid"
    t.autofit = False
    for ri, row in enumerate(rows):
        for ci, x in enumerate(row):
            c = t.cell(ri, ci)
            c.width = Inches(w[ci])
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.space_before = Pt(1)
            h = ri == 0
            run(p, x, b=h or ri in bold_rows, c=RGBColor(255, 255, 255) if h else None, sz=9)
            if h:
                shade(c, "1F3864")
            elif ri in bold_rows:
                shade(c, "E8EEF7")
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def pic(name, width=6.9):
    doc.add_picture(str(S / name), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


p = doc.add_paragraph()
run(p, "RecAI Rebuild: Understanding, Architecture and Cost", True, NAVY, 18)
p.paragraph_format.space_after = Pt(0)
para("Working document for the owner and the CEO story  |  5 November 2026  |  Estimates only: nothing here has been built or measured on AWS yet. Prices were read from AWS's public price list (Ohio) and Anthropic's model table on 5 November 2026.", GREY, 9)

head("1. The short version")
bl("Where we picked it up: ", "RecAI works for Estuate's recruiters, but it runs on one always-on server, keeps tokens in memory, and had five security flaws we reproduced on a test copy (anyone could read screening data through the Claude connector in its default setting; users could read each other's reports and chats and overwrite each other's files). Cost today: about $73/month for the server plus about $84/month for AI services, about $157/month.")
bl("What we already did: ", "closed those flaws on the current code with 26 automated checks that prove both the refusal and the legitimate user's access (26 of 26 pass), and rebuilt the database definition from the real production structure. Nothing was pushed or deployed.")
bl("The proposal: ", "rebuild as pay-per-use services on AWS, so nothing runs (or bills) while nobody is using it. Estimated idle infrastructure is about $3 to 4 a month, against $73 today. The real cost is then the Claude calls, which we control by model choice, batching and caching: about $10 to 16 a month lean, $20 to 40 balanced, up to about $70 to 150 if Sonnet is used for everything.")
bl("The honest caveats: ", "it is a rewrite (weeks, not days), it relies on newer AWS services we must test first, and the lean cost assumes Haiku 5.5 is good enough at screening, which only a test on labelled resumes can show. We recommend a one to two week prototype before committing.")

head("2. What RecAI is for")
para("Recruiters upload resumes and then (a) search and chat over them and get the exact passage as evidence, (b) screen many resumes against a job description and get a report, (c) convert resumes to the Estuate template, (d) track job requisitions, and (e) do all of that from Claude through a connector. A video interview module exists only on paper.")
tbl([1.3, 3.0, 2.6], [
    ["Feature", "Plan", "Why"],
    ["Search with citations (Claude connector and portal)", "Keep. First public release, free, read-only", "Core value; no Claude call needed on our side, so near-zero cost per search"],
    ["Screening against a job description", "Keep, internal only, human reviews every result", "Anthropic's policy (12 Nov 2026) treats candidate screening and ranking as high-risk: qualified human review and disclosure"],
    ["Resume conversion to the Estuate template", "Keep, internal, later", "Useful, not part of the public release; was missing from the AI cost estimate"],
    ["Job requisitions, admin", "Keep, simplified (admin via sign-in groups)", "Less custom code to secure"],
    ["Video interviews", "Defer", "Not built; biometric and employment-decision risk"],
    ["Web search inside chat", "Drop for now", "Extra attack surface (outside requests, injected text)"],
], bold_rows=())

head("3. Today, and what it costs")
pic("diagram1_today.png")
para("One server does everything, so it is paid for around the clock, a failure takes everything down, and sign-in tokens vanish on every restart. Four outside services are billed even when nobody uses them (Pinecone alone has a $50 monthly minimum on its standard plan).")

head("4. Proposed design")
pic("diagram2_proposed.png")
bl("Sign-in and checks first: ", "Cognito handles users and tokens; API Gateway rejects a bad token before any of our code runs. This replaces the hand-written sign-in that caused the worst flaw.")
bl("Separate roles per function: ", "the Claude connector can only search; the parser can only read one file and has no internet; only the screening worker can call Claude. A mistake in one place cannot reach the rest.")
bl("Data: ", "DynamoDB for records, private encrypted S3 for files, S3 Vectors for the search index (about $0.06 per GB-month, replacing Pinecone), Bedrock Titan for embeddings ($0.02 per million tokens).")
bl("Background work: ", "uploads and screening go through a queue, with retries and a dead-letter queue, so one big batch cannot freeze the app.")
bl("No NAT gateway, no database server, no public IP: ", "each is a common hidden monthly cost ($30 and up) that this design avoids.")
pic("diagram3_search.png")

head("5. Cost, old against new, same workload")
para("Workload used (Akshay's low-end figures): 2,000 to 5,000 resumes and screenings a month, 1,000 to 3,000 chat queries, about 500 conversions (not in his estimate). Token sizes are assumptions: 3,000-token resume, 1,000-token job description, 700-token structured answer.")
tbl([2.2, 1.6, 1.6, 1.5], [
    ["Per month", "Lean", "Balanced", "Premium"],
    ["How the AI is used", "Haiku 5.5 first, Sonnet only for the top 20%, batch + cached prompts", "Sonnet 5.5 for screening with batch + cache; Haiku for chat and conversion", "Sonnet 5.5 for everything, on demand"],
    ["Idle infrastructure (S3, DynamoDB, logs)", "$3 to 4", "$3 to 4", "$3 to 4"],
    ["Embeddings and search index", "under $1", "under $1", "under $1"],
    ["Screening", "$3 to 9", "$13 to 33", "$32 to 80"],
    ["Chat and conversion", "$2 to 3", "$2 to 3", "$33 to 63"],
    ["Total (rebuild)", "about $10 to 16", "about $20 to 40", "about $70 to 150"],
    ["Today (server + outside services)", "about $157", "about $157", "about $157"],
], bold_rows=(6,))
para("The $25 stretch goal is reachable in the lean and the low end of the balanced case. The $125 permission covers even most of the premium case. Optional extras not included: a web firewall (about $6 to 8 a month) and tax. Everything depends on the quality test in section 7: if Haiku is not accurate enough, the lean column does not apply.", GREY, 9)

head("6. Three ways to build it (infrastructure only, per month)")
tbl([2.0, 1.0, 3.9], [
    ["Option", "Idle cost", "In plain words"],
    ["A. Serverless: DynamoDB + S3 Vectors (recommended)", "$3 to 4", "Cheapest, strongest separation, nothing to patch. Most rewrite; newer AWS services to prove."],
    ["C. Serverless + small PostgreSQL (pgvector)", "about $17", "Keeps SQL and the team's skills. A database server runs all day (db.t4g.micro $11.68 plus storage)."],
    ["B. One small server with PostgreSQL", "about $21 to 33", "Fastest to port. Always on, one failure point, patching is ours."],
    ["Today", "about $73", "For comparison."],
], bold_rows=(1,))

head("7. What we must prove first (1 to 2 weeks, synthetic data only, our AWS account)")
bl("Claude can sign in through Cognito ", "(the plan uses Anthropic-held client credentials; works for claude.ai and Desktop, Claude Code needs separate checking).")
bl("Search quality: ", "S3 Vectors against exact and alias search, PostgreSQL pgvector and today's Pinecone plus Cohere, on the 60-profile labelled benchmark ChatGPT built (today's simple baseline gets 31.8% citation precision).")
bl("Screening quality: ", "Haiku 5.5 against Sonnet 5.5 on a labelled sample, including when it should say there is no evidence.")
bl("Speed: ", "cold-start and total time for one search inside Claude's tool timeout.")
bl("The parser: ", "LibreOffice and OCR in an isolated worker; and a decision on the PDF library (PyMuPDF is AGPL or commercial; pypdf is the candidate).")
bl("The thin slice: ", "upload a synthetic resume, find the passage through Claude, prove a second user cannot see it, delete it and prove it is gone from search and storage.")

head("8. Decisions needed")
bl("Go ahead with the prototype ", "in your AWS account (Ohio, synthetic data only, with a budget cap)?")
bl("Public scope: ", "agree that release one is free evidence search only, with screening and ranking kept internal?")
bl("Legal and policy: ", "PyMuPDF terms, and the Estuate privacy policy (still the blocker for any public listing).")
bl("Akshay: ", "which build and hostname are live, where the unpublished connector code is (the production database has a token table no repository branch uses).")
doc.save(OUTDOC)
print("saved", OUTDOC)
