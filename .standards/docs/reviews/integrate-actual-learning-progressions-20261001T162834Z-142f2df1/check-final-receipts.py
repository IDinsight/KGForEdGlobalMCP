import hashlib,json
from pathlib import Path
c="integrate-actual-learning-progressions-20261001T162834Z-142f2df1";root=Path.cwd();e=root/"data/source_artifacts/learning_progressions/tester"/c/"reverify"
names=["fixture-relocation-suite","fixture-relocation-black-final","fixture-relocation-isort","fixture-relocation-ruff-final","fixture-relocation-mypy","fixture-relocation-pylint-final","fixture-relocation-interrogate","packages","stdio","stage","distribution","stage-regression"]
out=[];count=0
for name in names:
 p=e/(name+".command.json");d=json.loads(p.read_text())
 for k,v in d.get("logs",{}).items():
  q=Path(v["path"]);q=q if q.is_absolute() else root/q
  assert hashlib.sha256(q.read_bytes()).hexdigest()==v["sha256"].removeprefix("sha256:"),(name,k)
  count+=1
 out.append({"receipt":str(p.relative_to(root)),"exitCode":d.get("exitCode"),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
print(json.dumps({"checkedLogs":count,"receipts":out}))
