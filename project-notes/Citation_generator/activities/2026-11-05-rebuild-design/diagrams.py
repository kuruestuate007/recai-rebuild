from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

OUT = Path(r"C:/Users/kikunal/AppData/Local/Temp/claude/4d737c2ba2bc1703/42329f66-8444-456f-8fe0-f3742cabc90c/scratchpad")
F = lambda sz, bold=False: ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", sz)
NAVY, BLUE, GREEN, ORANGE, GREY, RED = "#1F3864", "#2E75B6", "#548235", "#C55A11", "#6B6B6B", "#C00000"
FILLS = {"user": "#E8EEF7", "edge": "#DDEBF7", "compute": "#E2F0D9", "data": "#FFF2CC", "ext": "#F2F2F2", "bad": "#FBE5D6", "auth": "#EADCF4"}


class Canvas:
    def __init__(self, w, h, title, subtitle=""):
        self.img = Image.new("RGB", (w, h), "white")
        self.d = ImageDraw.Draw(self.img)
        self.d.text((30, 18), title, font=F(34, True), fill=NAVY)
        if subtitle:
            self.d.text((30, 62), subtitle, font=F(21), fill=GREY)
        self.boxes = {}

    def box(self, key, x, y, w, h, text, kind="edge", bold_first=True, size=21, border=None):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=14, fill=FILLS[kind], outline=border or NAVY, width=2)
        lines = text.split("\n")
        total = len(lines) * (size + 6)
        ty = y + (h - total) / 2
        for i, line in enumerate(lines):
            f = F(size, bold=(i == 0 and bold_first))
            tw = self.d.textlength(line, font=f)
            self.d.text((x + (w - tw) / 2, ty), line, font=f, fill="#222222" if i else NAVY)
            ty += size + 6
        self.boxes[key] = (x, y, w, h)

    def label(self, x, y, text, color=GREY, size=20, bold=False):
        self.d.text((x, y), text, font=F(size, bold), fill=color)

    def band(self, x, y, w, h, text, color="#F7F7F7"):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=color, outline="#BBBBBB", width=2)
        self.d.text((x + 16, y + 10), text, font=F(21, True), fill=GREY)

    def _edge(self, key, toward):
        x, y, w, h = self.boxes[key]
        cx, cy = x + w / 2, y + h / 2
        tx, ty = toward
        dx, dy = tx - cx, ty - cy
        if dx == 0 and dy == 0:
            return cx, cy
        sx = (w / 2) / abs(dx) if dx else 1e9
        sy = (h / 2) / abs(dy) if dy else 1e9
        s = min(sx, sy)
        return cx + dx * s, cy + dy * s

    def arrow(self, a, b, color=NAVY, width=3, text=None, both=False, dash=False, tx=0, ty=0):
        ax, ay, aw, ah = self.boxes[a]
        bx, by, bw, bh = self.boxes[b]
        ca = (ax + aw / 2, ay + ah / 2)
        cb = (bx + bw / 2, by + bh / 2)
        p1, p2 = self._edge(a, cb), self._edge(b, ca)
        if dash:
            n = int(math.dist(p1, p2) // 16)
            for i in range(0, n, 2):
                s = (p1[0] + (p2[0] - p1[0]) * i / n, p1[1] + (p2[1] - p1[1]) * i / n)
                e = (p1[0] + (p2[0] - p1[0]) * (i + 1) / n, p1[1] + (p2[1] - p1[1]) * (i + 1) / n)
                self.d.line([s, e], fill=color, width=width)
        else:
            self.d.line([p1, p2], fill=color, width=width)
        self._head(p1, p2, color)
        if both:
            self._head(p2, p1, color)
        if text:
            mx, my = (p1[0] + p2[0]) / 2 + tx, (p1[1] + p2[1]) / 2 + ty
            tw = self.d.textlength(text, font=F(18))
            self.d.rectangle([mx - tw / 2 - 4, my - 12, mx + tw / 2 + 4, my + 12], fill="white")
            self.d.text((mx - tw / 2, my - 11), text, font=F(18), fill=color)

    def _head(self, p1, p2, color):
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        L = 16
        pts = [p2, (p2[0] - L * math.cos(ang - 0.4), p2[1] - L * math.sin(ang - 0.4)),
               (p2[0] - L * math.cos(ang + 0.4), p2[1] - L * math.sin(ang + 0.4))]
        self.d.polygon(pts, fill=color)

    def save(self, name):
        self.img.save(OUT / name)
        print("saved", name, self.img.size)


# ---------------------------------------------------------------- 1. today
c = Canvas(1800, 900, "Today: everything runs on one always-on server",
           "One AWS server (t3-class) does the website, login, files, AI calls, database and the Claude connector. Cost: about $73/month hosting + about $84/month AI services.")
c.box("br", 40, 180, 300, 90, "Recruiter\n(web browser)", "user")
c.box("cl", 40, 420, 300, 90, "Claude\n(claude.ai / Desktop)", "user")
c.band(420, 130, 760, 700, "ONE SERVER  (always on, you pay 24 hours a day)", "#FDF2E9")
c.box("ng", 460, 190, 320, 80, "nginx\nweb server", "edge")
c.box("api", 460, 330, 320, 170, "RecAI app (FastAPI)\nlogin, uploads, chat,\nscreening, reports,\nMCP connector + its own OAuth", "compute", size=20)
c.box("pg", 830, 190, 310, 90, "PostgreSQL database\n(on the same disk)", "data")
c.box("disk", 830, 330, 310, 90, "Local disk\nresumes, Excel reports", "data")
c.box("lo", 830, 470, 310, 90, "LibreOffice, OCR\n(document converters)", "ext")
c.box("pc", 1330, 160, 400, 80, "Pinecone  ~$15 (min. $50 on Standard)", "ext", bold_first=False, size=20)
c.box("co", 1330, 270, 400, 80, "Cohere rerank  ~$3", "ext", bold_first=False, size=20)
c.box("oa", 1330, 380, 400, 80, "OpenAI embeddings  ~$1", "ext", bold_first=False, size=20)
c.box("cc", 1330, 490, 400, 100, "Claude Sonnet (screening + chat)\n~$65", "ext", bold_first=False, size=20)
c.arrow("br", "ng", text="HTTPS")
c.arrow("cl", "api", text="/mcp")
c.arrow("ng", "api")
c.arrow("api", "pg")
c.arrow("api", "disk")
c.arrow("api", "lo")
for k in ("pc", "co", "oa", "cc"):
    c.arrow("api", k, dash=True, color=GREY)
c.label(440, 850, "Weak points: one server = one failure point; sign-in tokens held in memory; patching is our job; every external service is billed even when idle.", RED, 20)
c.save("diagram1_today.png")

# ---------------------------------------------------------------- 2. proposed
c = Canvas(1800, 1120, "Proposed: pay-per-use on AWS, nothing running while idle",
           "Each box below costs nothing when nobody is using it, except storage (cents). Estimated infrastructure when idle: about $3-4/month.")
c.box("br", 40, 150, 300, 90, "Recruiter\n(web browser)", "user")
c.box("cl", 40, 330, 300, 90, "Claude\n(claude.ai / Desktop)", "user")
c.box("cf", 440, 130, 330, 90, "CloudFront + S3\nthe web app (static)", "edge")
c.box("gw", 440, 300, 330, 110, "API Gateway\nchecks the sign-in token\nbefore anything runs", "edge", size=20)
c.box("cg", 440, 480, 330, 100, "Cognito\nsign-in, users, tokens", "auth")
c.box("la", 900, 190, 320, 90, "Lambda: web API\n(uploads, chat, reports)", "compute", size=20)
c.box("lm", 900, 340, 320, 100, "Lambda: Claude tools\n(search, get citation)", "compute", size=20)
c.box("db", 1340, 130, 400, 80, "DynamoDB\nusers, jobs, results, chats", "data", size=20)
c.box("s3", 1340, 230, 400, 80, "S3 (private, encrypted)\nresumes and reports", "data", size=20)
c.box("sv", 1340, 330, 400, 80, "S3 Vectors\nsearch index, per tenant", "data", size=20)
c.band(400, 640, 1380, 440, "BACKGROUND WORK  (starts only when a file or a job arrives)")
c.box("q", 440, 720, 260, 90, "SQS queue\n(jobs wait here)", "edge", size=20)
c.box("lp", 800, 700, 330, 110, "Lambda: document parser\nno internet access,\nsees one file only", "compute", size=19)
c.box("tt", 1260, 700, 330, 100, "Bedrock Titan\nembeddings  $0.02 / M tokens", "ext", size=19)
c.box("lw", 800, 880, 330, 100, "Lambda: screening worker\n(Estuate recruiters only)", "compute", size=19)
c.box("ai", 1260, 870, 480, 120, "Claude API\nHaiku 5.5 first, Sonnet 5.5 when needed\nbatch + cached prompts (about half price)", "ext", size=19)
c.arrow("br", "cf")
c.arrow("br", "gw", text="login + API")
c.arrow("cl", "gw", text="MCP")
c.arrow("gw", "cg", both=True)
c.arrow("gw", "la")
c.arrow("gw", "lm")
c.arrow("la", "db")
c.arrow("la", "s3")
c.arrow("lm", "sv")
c.arrow("la", "q", dash=True, color=GREEN)
c.arrow("q", "lp")
c.arrow("lp", "tt")
c.arrow("q", "lw")
c.arrow("lw", "ai")
c.label(420, 1085, "Green dashed = triggers background work.  Not shown: CloudWatch alarms, AWS Budgets kill switch, secrets in Parameter Store.", GREY, 18)
c.save("diagram2_proposed.png")

# ---------------------------------------------------------------- 3. one search
c = Canvas(1800, 620, "One search, step by step (the Claude connector)",
           "Our side makes no Claude call and holds no server: the user's own Claude writes the answer from our evidence.")
steps = [
    ("1", "User asks Claude\n\"find senior Spark\nengineers\"", "user"),
    ("2", "Claude calls our\nconnector over HTTPS\nwith the user's token", "user"),
    ("3", "API Gateway checks\nthe token (Cognito)\nbad token = stop", "edge"),
    ("4", "Lambda turns the\nquestion into numbers\n(Titan, $0.00002/1K)", "compute"),
    ("5", "S3 Vectors finds the\nclosest resume parts,\nonly this tenant's", "data"),
    ("6", "Lambda returns\nsnippets + citations\n(file, page)", "compute"),
]
x = 40
for i, (n, t, kind) in enumerate(steps):
    c.box(f"s{i}", x, 170, 255, 170, f"{n}\n{t}", kind, size=19)
    if i:
        c.arrow(f"s{i-1}", f"s{i}")
    x += 285
c.box("fin", 40, 420, 1700, 110, "7  Claude reads the evidence and writes the answer with sources.  Cost to Estuate for the whole request: a fraction of a cent.\nTenant and permissions are decided by the token, never by anything the caller types.", "user", size=21, bold_first=False)
c.arrow("s5", "fin", color=GREEN)
c.save("diagram3_search.png")
