import hashlib,json,zipfile
from pathlib import Path
c="integrate-actual-learning-progressions-20261001T162834Z-142f2df1";e=Path("data/source_artifacts/learning_progressions/tester")/c/"reverify";stage=Path("data/source_artifacts/learning_progressions/recovery-dev022/bundle")
a=stage.parent/"kgfegmcp-0.3.1-recovery.mcpb"
def sha(b):return hashlib.sha256(b).hexdigest()
d=json.loads((e/"distribution.json").read_text()); bad=[]; old=[]
with zipfile.ZipFile(a) as z:
 assert len(z.namelist())==len(set(z.namelist()))==650
 for n,h in d["sourceStageArchiveIdentities"].items():
  b=z.read(n);assert sha(b)==h and sha((stage/n).read_bytes())==h,n
  src=Path("backend")/n if n.startswith("src/") or n in ["README.md","pyproject.toml","uv.lock","fastmcp.json"] else Path("packaging/mcpb/manifest.json") if n=="manifest.json" else Path(n)
  if sha(src.read_bytes())!=h:bad.append({"archiveMember":n,"source":str(src),"recordedSha256":h,"currentSha256":sha(src.read_bytes())})
 for i,line in enumerate(z.read("README.md").decode().splitlines(),1):
  if any(w in line for w in ["13 tools","12 resource templates","7 prompts","13/1/12/7",'"promptCount": 7','"resourceTemplateCount": 12','"toolCount": 13',"progression-evidence","kgfegmcp-0.1.0"]):old.append({"line":i,"text":line})
print(json.dumps({"archiveSha256":sha(a.read_bytes()),"members":len(d["sourceStageArchiveIdentities"]),"archiveStageReceiptMatch":True,"currentSourceDifferences":bad,"staleReadmeLines":old},indent=2))
