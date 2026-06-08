"""
IAS Report Generator
Generates DOCX reports in Empower Professional format.
"""
import json, os, re, subprocess
from pathlib import Path
from datetime import date

BASE    = Path(__file__).parent.parent
OUT_DIR = BASE / "output"


def _safe(text: str) -> str:
    """Sanitise text for embedding in JS string literals.
    Strips non-BMP characters (emoji, etc.) that render as ?? on Windows."""
    if not isinstance(text, str):
        text = str(text)
    # Remove surrogates and non-BMP chars (codepoint > U+FFFF) that cause ??
    text = "".join(c for c in text if ord(c) < 0xFFFF and not (0xD800 <= ord(c) <= 0xDFFF))
    # Encode/decode to clean any remaining surrogates
    text = text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return (text
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("'", "\\'")
            .replace("\n", " ")
            .replace("\r", " ")
            .replace("`", "\\`")
            .strip())


def _stars_spaced(n: int) -> str:
    parts = []
    for i in range(5):
        parts.append("\\u2605" if i < n else "\\u2606")
    return "  ".join(parts)


def _find_docx_pkg() -> str:
    candidates = [
        OUT_DIR / "node_modules" / "docx",
        Path("C:/temp/node_modules/docx"),
        Path.home() / "node_modules" / "docx",
    ]
    for c in candidates:
        if (c / "package.json").exists():
            return str(c).replace("\\", "/")
    # Auto-install
    OUT_DIR.mkdir(exist_ok=True)
    subprocess.run(["npm","init","-y"], cwd=str(OUT_DIR), capture_output=True, timeout=30)
    subprocess.run(["npm","install","docx"], cwd=str(OUT_DIR), capture_output=True, timeout=120)
    pkg = OUT_DIR / "node_modules" / "docx"
    if (pkg / "package.json").exists():
        return str(pkg).replace("\\", "/")
    raise RuntimeError("docx npm package not found. Run: cd output && npm install docx")


def _run_js(js: str, out_file: str) -> tuple:
    OUT_DIR.mkdir(exist_ok=True)
    pkg   = _find_docx_pkg()
    js    = js.replace("require('docx')", f"require('{pkg}')")
    js    = js.replace('require("docx")', f'require("{pkg}")')
    # Replace star chars with unicode escapes
    js    = js.replace("\u2605", "\\u2605").replace("\u2606", "\\u2606")

    js_path = OUT_DIR / "ias_report.js"
    js_path.write_text(js, encoding="utf-8", errors="replace")

    result = subprocess.run(
        ["node", str(js_path)],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0 and Path(out_file).exists():
        return out_file, ""
    return None, (result.stderr or result.stdout or "Unknown error").strip()


def generate_empower_report(data: dict) -> tuple:
    """
    Generate Empower Professional DOCX report.
    Returns (file_path, error_message).
    """
    OUT_DIR.mkdir(exist_ok=True)

    cand   = _safe(data.get("candidate", "Candidate"))
    title  = _safe(data.get("role", "Role")[:80])
    v      = data.get("verdict", "SELECTED").upper()
    o      = float(data.get("overall_score", 3.0))
    sm     = _safe(data.get("overall_summary", ""))
    today  = _safe(data.get("date", date.today().strftime("%d-%b-%Y")))
    vc     = "00B050" if "SELECT" in v else "CC0000"

    # Safe filename
    safe_name = re.sub(r'[^\w\-]', '_', data.get("candidate","Candidate"))
    out_file  = str(OUT_DIR / f"Empower_{safe_name}_{v}.docx").replace("\\", "/")

    sc = data.get("scores", [])
    ss = data.get("skill_scores", {})

    # Build domain groups from scores
    from collections import OrderedDict
    domains = OrderedDict()
    for s in sc:
        skill = _safe(s.get("skill", "General"))
        if skill not in domains:
            domains[skill] = []
        raw_code   = s.get("code", "") or ""
        code_lines = [_safe(ln) for ln in raw_code.replace("\r\n","\n").split("\n")] if raw_code.strip() else []
        domains[skill].append({
            "num":       s.get("q_num", 0),
            "question":  _safe(s.get("question", "")),
            "response":  _safe(s.get("summary", "")),
            "codeLines": code_lines
        })

    first_score = list(ss.values())[0].get("competency", 5) if ss else 5
    proj_stars  = min(5, first_score)
    proj_fb     = _safe(sm)
    domains_js  = json.dumps(list(domains.items()))

    js = f"""
const {{Document,Packer,Paragraph,TextRun,Table,TableRow,TableCell,
        AlignmentType,BorderStyle,WidthType,ShadingType}}=require('docx');
const fs=require('fs');

const NAVY="1F3864",ORANGE="FF6600",MGRAY="404040",GREEN="00B050";

function starsSpaced(n){{
  const f="\\u2605",e="\\u2606";
  let a=[];
  for(let i=0;i<5;i++) a.push(i<n?f:e);
  return a.join("  ");
}}

function p(ch,bef=0,aft=140){{
  return new Paragraph({{spacing:{{before:bef,after:aft}},children:ch}});
}}

function r(tx,{{bold=false,sz=20,col="000000",it=false}}={{}}){{
  return new TextRun({{text:tx,bold,size:sz,color:col,italics:it,font:"Calibri"}});
}}

function blank(){{
  return new Paragraph({{spacing:{{before:0,after:100}},children:[]}});
}}

function codeBlock(lines){{
  const brd={{style:BorderStyle.SINGLE,size:4,color:"CCCCCC"}};
  return new Table({{
    width:{{size:9200,type:WidthType.DXA}},columnWidths:[9200],
    rows:[new TableRow({{children:[new TableCell({{
      borders:{{top:brd,bottom:brd,left:brd,right:brd}},
      shading:{{fill:"F5F5F5",type:ShadingType.CLEAR}},
      margins:{{top:80,bottom:80,left:160,right:160}},
      children:lines.map(l=>new Paragraph({{
        spacing:{{before:0,after:0}},
        children:[new TextRun({{text:l||" ",size:16,font:"Courier New",color:"222222"}})]
      }}))
    }})]}})]
  }});
}}

const DOMAINS={domains_js};
const C=[];

// TITLE
C.push(p([r("Feedback for Candidate: : {cand} - {title}",{{bold:true,sz:24,col:NAVY}})],0,180));

// OVERALL RATING
C.push(p([r("Overall Rating :  ",{{bold:true,sz:22,col:NAVY}}),r(starsSpaced(Math.round({o})),{{sz:22,col:ORANGE,bold:true}})],0,60));
C.push(blank());

// VERDICT
C.push(p([r("Verdict : ",{{bold:true,sz:22,col:NAVY}}),r("{v}",{{bold:true,sz:22,col:"{vc}"}})],0,180));

// PHOTO ID
C.push(p([r("1. Photo ID  ",{{bold:true,sz:20,col:NAVY}}),r(starsSpaced(5),{{sz:20,col:ORANGE,bold:true}}),r("  Checked",{{sz:20,col:MGRAY}})],0,100));

// PROJECT DISCUSSION
C.push(blank());
C.push(p([r("2. Project Discussion  ",{{bold:true,sz:20,col:NAVY}}),r(starsSpaced({proj_stars}),{{sz:20,col:ORANGE,bold:true}})],0,60));
C.push(p([r("{proj_fb}",{{sz:19,col:MGRAY}})],0,140));

// Q&A DOMAINS
DOMAINS.forEach(([domain,questions])=>{{
  C.push(blank());
  C.push(p([r(">> "+domain,{{bold:true,sz:20,col:NAVY}})],0,60));
  questions.forEach(q=>{{
    C.push(p([
      r("Q"+q.num+".  ",{{bold:true,sz:19,col:NAVY}}),
      r(q.question,{{sz:19,col:MGRAY,it:true}})
    ],0,0));
    C.push(p([
      r("Candidate Response:  ",{{bold:true,sz:19,col:NAVY}}),
      r(q.response,{{sz:19,col:MGRAY}})
    ],0,q.codeLines&&q.codeLines.length?60:120));
    if(q.codeLines&&q.codeLines.length){{
      C.push(p([r("Code Written Below:",{{bold:true,sz:19,col:NAVY}})],0,40));
      C.push(codeBlock(q.codeLines));
      C.push(blank());
    }}
  }});
}});

// OVERALL FEEDBACK
C.push(blank());
C.push(p([r("Overall Feedback: ",{{bold:true,sz:22,col:NAVY}})],60,60));
C.push(p([r("{sm}",{{sz:19,col:MGRAY}})],0,0));

const doc=new Document({{
  styles:{{default:{{document:{{run:{{font:"Calibri",size:20}}}}}}}},
  sections:[{{
    properties:{{page:{{
      size:{{width:12240,height:15840}},
      margin:{{top:900,right:1080,bottom:900,left:1080}}
    }}}},
    children:C
  }}]
}});
Packer.toBuffer(doc)
  .then(buf=>{{fs.writeFileSync("{out_file}",buf);console.log("OK:{out_file}");  }})
  .catch(e=>{{console.error("ERR:"+e.message);process.exit(1);}});
"""
    return _run_js(js, out_file)
