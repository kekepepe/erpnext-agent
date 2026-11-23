"""Reassemble the accepted C0 OCI image from local BuildKit history, verifying every digest."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DIGEST = json.loads((ROOT / "phase0/evidence/c0-validation-20261104.json").read_text())["image_id"]
TAG = "erpnext-phase0-zh:c0-" + DIGEST.split(":")[1][:12]


def recover(ref, archive):
    if archive.exists():
        raise ValueError("镜像归档已存在")
    with tempfile.TemporaryDirectory(dir=archive.parent) as temp:
        folder = Path(temp)
        blobs = folder / "blobs/sha256"
        blobs.mkdir(parents=True)
        def fetch(desc):
            algo, sha = desc["digest"].split(":")
            if algo!="sha256" or len(sha)!=64 or any(c not in "0123456789abcdef" for c in sha):
                raise ValueError("OCI 摘要格式错误")
            path = blobs / sha
            if path.exists():
                return
            with path.open("xb") as f:
                subprocess.run(["docker","buildx","history","inspect","attachment",ref,desc["digest"]],stdout=f,check=True)
            h = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda:stream.read(1024*1024),b""):
                    h.update(chunk)
            if h.hexdigest()!=sha or ("size" in desc and path.stat().st_size!=desc["size"]):
                raise ValueError("缓存镜像层摘要或大小不匹配")
            if desc["mediaType"] == "application/vnd.oci.image.manifest.v1+json":
                obj=json.loads(path.read_bytes())
                for child in obj.get("manifests",[]) + obj.get("layers",[]) + ([obj["config"]] if "config" in obj else []):
                    fetch(child)
        root={"mediaType":"application/vnd.oci.image.index.v1+json","digest":DIGEST}
        fetch(root)
        # Historical BuildKit attestations have independent retention. Select the exact
        # executable platform manifest authenticated by the archived top-level index.
        index=json.loads((blobs/DIGEST.split(":")[1]).read_bytes())
        platform=[entry for entry in index["manifests"] if entry["platform"]=={"os":"linux","architecture":"arm64"}]
        if len(platform)!=1:
            raise ValueError("验收索引未唯一定位 macOS 演练使用的 linux/arm64 镜像")
        root=platform[0].copy()
        fetch(root)
        root["annotations"]={"org.opencontainers.image.ref.name":TAG,"io.containerd.image.name":"docker.io/library/"+TAG}
        (folder/"index.json").write_text(json.dumps({"schemaVersion":2,"manifests":[root]}))
        (folder/"oci-layout").write_text('{"imageLayoutVersion":"1.0.0"}')
        tmp_tar=folder/"image.tar"
        with tarfile.open(tmp_tar,"w") as bundle:
            for name in ("oci-layout","index.json","blobs"):
                bundle.add(folder/name,arcname=name)
        subprocess.run(["docker","image","load","-i",str(tmp_tar)],check=True)
        actual=subprocess.check_output(["docker","image","inspect",TAG,"--format","{{.Id}}"],text=True).strip()
        if actual!=root["digest"]:
            raise ValueError("加载的执行镜像与 C0 索引中的平台清单不符")
        tmp_tar.rename(archive)
        print(f"{TAG} {actual} ; verified {len(list(blobs.iterdir()))} blobs")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_ref")
    parser.add_argument("archive",type=Path)
    args=parser.parse_args()
    if ROOT in args.archive.resolve().parents:
        parser.error("本地镜像归档应在仓库外保存")
    recover(args.build_ref,args.archive)
