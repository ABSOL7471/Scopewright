"""
Scopewright - paste messy job-walk notes, get a client-ready Scope of Work.

Local-first: your notes and your scopes never leave this machine. The model
is whatever Ollama has installed; the validation, repair, and rendering are
all code in this folder.

    python scopewright_server.py      ->  http://localhost:8431

Routes:
    GET  /              the app UI
    GET  /api/status    {ollama, model} - the UI's capability gate
    POST /api/generate  {notes} -> {scope, repairs, model}
    POST /api/transcribe {image: base64} -> {text, model}  (vision-gated)
    POST /api/render    {scope} -> standalone printable HTML proposal

The render layer is deliberately model-free: the proposal a client receives
is assembled by code from validated JSON, with every string HTML-escaped.
The model proposes; it never writes HTML.
"""

import datetime
import html
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import llm

HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.environ.get("SCOPEWRIGHT_HOST", "127.0.0.1")
PORT = int(os.environ.get("SCOPEWRIGHT_PORT", "8431"))

MAX_NOTES = 20000  # characters; a job walk is not a novel
MAX_IMAGE_B64 = 14_000_000  # ~10 MB image as base64; a phone photo fits


def load_company():
    """Optional company.json beside this file puts your letterhead on the
    proposal: {"name", "license", "phone", "email", "location"} - all keys
    optional. Ships absent (generic proposals); see company.example.json.
    The file is gitignored so your details stay local."""
    path = os.path.join(HERE, "company.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------- rendering

PROPOSAL_CSS = """
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Georgia, 'Times New Roman', serif; color: #26221c;
         background: #e8e5df; line-height: 1.55; }
  .sheet { max-width: 7.6in; margin: 24px auto; background: #fdfcf9;
           padding: 0.9in 0.85in; box-shadow: 0 2px 14px rgba(0,0,0,.14); }
  .company { font-size: 13px; margin-bottom: 14px; letter-spacing: .02em; }
  .company-meta { color: #6b6353; font-size: 11px; }
  header { border-bottom: 3px double #8a7d66; padding-bottom: 14px;
           margin-bottom: 22px; }
  .kicker { font-family: Arial, Helvetica, sans-serif; font-size: 11px;
            letter-spacing: .22em; text-transform: uppercase; color: #8a7d66; }
  h1 { font-size: 26px; font-weight: normal; margin-top: 6px; }
  .meta { font-family: Arial, Helvetica, sans-serif; font-size: 11px;
          color: #6b6357; margin-top: 8px; }
  .summary { font-size: 15px; font-style: italic; color: #3d382f;
             margin-bottom: 24px; }
  h2 { font-family: Arial, Helvetica, sans-serif; font-size: 12px;
       letter-spacing: .14em; text-transform: uppercase; color: #6b6357;
       border-bottom: 1px solid #d8d2c6; padding-bottom: 5px;
       margin: 26px 0 10px; }
  h3 { font-size: 15px; margin: 16px 0 6px; }
  table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
  th { font-family: Arial, Helvetica, sans-serif; font-size: 10px;
       letter-spacing: .1em; text-transform: uppercase; color: #8a8071;
       text-align: left; padding: 4px 8px 4px 0; }
  td { padding: 5px 8px 5px 0; border-top: 1px solid #eee9df;
       vertical-align: top; }
  td.qty { white-space: nowrap; color: #4b4437; width: 90px; }
  td.notes { color: #6b6357; font-style: italic; width: 30%; }
  ul { margin: 4px 0 0 20px; font-size: 13.5px; }
  li { margin-bottom: 4px; }
  .allow td { border-top: 1px solid #eee9df; }
  .allow .an { color: #6b6357; font-style: italic; }
  .terms { font-size: 13px; }
  .oq { background: #f6f2e8; border: 1px solid #e2d9c4; padding: 12px 16px;
        margin-top: 10px; }
  .oq p { font-family: Arial, Helvetica, sans-serif; font-size: 11px;
          color: #7d6f52; margin-bottom: 6px; }
  .sig { margin-top: 44px; display: flex; gap: 40px; }
  .sig div { flex: 1; border-top: 1px solid #26221c; padding-top: 6px;
             font-family: Arial, Helvetica, sans-serif; font-size: 11px;
             color: #6b6357; }
  footer { margin-top: 30px; font-family: Arial, Helvetica, sans-serif;
           font-size: 10px; color: #a29a8b; }
  @media print {
    body { background: #fff; }
    .sheet { box-shadow: none; margin: 0; max-width: none; padding: 0; }
    .oq { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""


def render_proposal(scope):
    """Validated scope JSON -> standalone printable HTML. Pure code, pure
    escaping - the model never touches this layer."""
    e = html.escape
    today = datetime.date.today().strftime("%B %d, %Y")
    out = []
    w = out.append

    w("<!DOCTYPE html><html><head><meta charset='utf-8'>")
    w("<title>Scope of Work — %s</title>" % e(scope.get("project_title", "")))
    w("<style>%s</style></head><body><div class='sheet'>" % PROPOSAL_CSS)

    company = load_company()
    w("<header>")
    if company.get("name"):
        line2 = " · ".join(
            e(str(company[k])) for k in ("license", "phone", "email", "location")
            if company.get(k))
        w("<div class='company'><strong>%s</strong>%s</div>"
          % (e(str(company["name"])),
             ("<br><span class='company-meta'>%s</span>" % line2) if line2 else ""))
    w("<div class='kicker'>Scope of Work</div>")
    w("<h1>%s</h1>" % e(scope.get("project_title", "")))
    w("<div class='meta'>Prepared %s &nbsp;·&nbsp; Draft for review — "
      "not a contract until signed</div></header>" % e(today))

    if scope.get("client_summary"):
        w("<p class='summary'>%s</p>" % e(scope["client_summary"]))

    w("<h2>Work Included</h2>")
    for sec in scope.get("sections", []):
        w("<h3>%s</h3>" % e(sec.get("name", "")))
        w("<table><tr><th>Item</th><th>Qty</th><th>Notes</th></tr>")
        for item in sec.get("items", []):
            qty = " ".join(x for x in (item.get("quantity"),
                                       item.get("unit")) if x)
            w("<tr><td>%s</td><td class='qty'>%s</td>"
              "<td class='notes'>%s</td></tr>"
              % (e(item.get("description", "")), e(qty or "—"),
                 e(item.get("notes") or "")))
        w("</table>")

    if scope.get("exclusions"):
        w("<h2>Not Included</h2><ul>")
        for x in scope["exclusions"]:
            w("<li>%s</li>" % e(x))
        w("</ul>")

    if scope.get("allowances"):
        w("<h2>Allowances</h2><table class='allow'>")
        for a in scope["allowances"]:
            w("<tr><td>%s</td><td class='an'>%s</td></tr>"
              % (e(a.get("description", "")), e(a.get("amount_note", ""))))
        w("</table>")

    if scope.get("assumptions"):
        w("<h2>Assumptions</h2><ul>")
        for a in scope["assumptions"]:
            w("<li>%s</li>" % e(a))
        w("</ul>")

    if scope.get("change_order_terms"):
        w("<h2>Change Orders</h2><p class='terms'>%s</p>"
          % e(scope["change_order_terms"]))

    if scope.get("open_questions"):
        w("<h2>Open Questions</h2><div class='oq'>")
        w("<p>These items were not answered by the job-walk notes. They "
          "need answers before this scope is final — they are listed here "
          "instead of guessed at.</p><ul>")
        for q in scope["open_questions"]:
            w("<li>%s</li>" % e(q))
        w("</ul></div>")

    w("<div class='sig'><div>Contractor signature / date</div>"
      "<div>Client signature / date</div></div>")
    w("<footer>Generated with Scopewright — reviewed and approved by the "
      "contractor before signing.</footer>")
    w("</div></body></html>")
    return "".join(out)


# ------------------------------------------------------------------ server

class Handler(BaseHTTPRequestHandler):
    server_version = "Scopewright/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/":
            with open(os.path.join(HERE, "scopewright.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if path == "/api/status":
            return self._send(200, llm.status())
        return self._send(404, {"error": "no such route"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        body = self._body()

        if path == "/api/generate":
            notes = body.get("notes")
            if not isinstance(notes, str) or not notes.strip():
                return self._send(400, {"error": "notes must be a"
                                        " non-empty string"})
            if len(notes) > MAX_NOTES:
                return self._send(400, {"error": "notes too long (%d chars,"
                                        " max %d)" % (len(notes), MAX_NOTES)})
            try:
                scope, repairs, model = llm.generate_scope(notes)
            except llm.OllamaDown as e:
                return self._send(503, {"error": str(e), "ollama": False})
            except llm.GenerationError as e:
                return self._send(502, {"error": str(e), "ollama": True})
            return self._send(200, {"scope": scope, "repairs": repairs,
                                    "model": model})

        if path == "/api/transcribe":
            image = body.get("image")
            if not isinstance(image, str) or not image.strip():
                return self._send(400, {"error": "image must be a base64"
                                        " string (no data: prefix)"})
            if len(image) > MAX_IMAGE_B64:
                return self._send(400, {"error": "image too large"
                                        " (max ~10 MB)"})
            try:
                text, model = llm.transcribe_image(image.strip())
            except llm.OllamaDown as e:
                return self._send(503, {"error": str(e), "ollama": False})
            except llm.GenerationError as e:
                return self._send(502, {"error": str(e), "ollama": True})
            return self._send(200, {"text": text, "model": model})

        if path == "/api/render":
            scope = body.get("scope")
            if not isinstance(scope, dict):
                return self._send(400, {"error": "scope must be an object"})
            return self._send(200, render_proposal(scope),
                              "text/html; charset=utf-8")

        return self._send(404, {"error": "no such route"})


def main():
    st = llm.status()
    print("[scopewright] http://localhost:%d" % PORT)
    if st["ollama"]:
        print("[scopewright] ollama up, model: %s" % st["model"])
    else:
        print("[scopewright] ollama NOT detected - UI will say so"
              " (start Ollama, then reload the page)")
    srv = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[scopewright] stopped")


if __name__ == "__main__":
    main()
