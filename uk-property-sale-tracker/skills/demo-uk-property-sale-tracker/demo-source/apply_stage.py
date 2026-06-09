#!/usr/bin/env python3
"""Staging engine for the demo-uk-property-sale-tracker run skill.

Applies ONE stage of demo-script.json to a live deal folder:
  1. (stage 0 only) create the deal folder tree and install the workbook + templates
  2. pull the stage's inbound / produced documents into the deal folder
  3. merge the stage's tracker patch into tracker.json
  4. run the plugin's refresh_tracker.py so mandate-tracker.xlsx + snapshot stay in sync
  5. log the documents pulled to correspondence-log.md
  6. print a JSON summary (narration, copied files, simulated schedules, status)

Usage:
  python apply_stage.py <deal-folder> <stage-id>     # one stage
  python apply_stage.py <deal-folder> all            # every stage in order
  python apply_stage.py --list                       # list stage ids

Source prefixes inside demo-script.json "copies":
  inbox/...    -> demo-source/_inbox/...
  produced/... -> demo-source/_produced/...
  asset/...    -> <plugin-root>/assets/...
"""
import json, os, sys, shutil, subprocess, datetime

HERE = os.path.dirname(os.path.abspath(__file__))               # .../demo-source
SCRIPT = os.path.join(HERE, "demo-script.json")
INBOX = os.path.join(HERE, "_inbox")
PRODUCED = os.path.join(HERE, "_produced")

def plugin_root():
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env and os.path.isdir(os.path.join(env, "shared")):
        return env
    # .../<root>/skills/demo-uk-property-sale-tracker/demo-source/apply_stage.py
    p = HERE
    for _ in range(3):
        p = os.path.dirname(p)
    return p

ROOT = plugin_root()
ASSETS = os.path.join(ROOT, "assets")
REFRESH = os.path.join(ROOT, "shared", "refresh_tracker.py")

TREE = ["00-mandate", "01-dataroom/title", "01-dataroom/leases", "01-dataroom/financial",
        "01-dataroom/compliance", "01-dataroom/planning", "01-dataroom/management",
        "01-dataroom/diligence", "02-marketing", "nda/signed", "03-buyers",
        "bids/round-1", "bids/round-2", "04-legals", "05-reporting"]

EMPTY_TRACKER = {"deal": {}, "buyers": [], "bids": [], "dataroom": [], "tasks": [],
                 "legals": [], "reporting": [], "preferred_bidder": {}}

def load_script():
    with open(SCRIPT) as f:
        return json.load(f)

def resolve(src):
    if src.startswith("inbox/"):
        return os.path.join(INBOX, src[len("inbox/"):])
    if src.startswith("produced/"):
        return os.path.join(PRODUCED, src[len("produced/"):])
    if src.startswith("asset/"):
        return os.path.join(ASSETS, src[len("asset/"):])
    raise ValueError("unknown source prefix: " + src)

def copy_one(src, dest_dir, deal_folder):
    s = resolve(src)
    dest_dir_abs = os.path.join(deal_folder, dest_dir)
    os.makedirs(dest_dir_abs, exist_ok=True)
    out = []
    if os.path.isdir(s):
        for fn in sorted(os.listdir(s)):
            sp = os.path.join(s, fn)
            if os.path.isfile(sp):
                shutil.copy2(sp, os.path.join(dest_dir_abs, fn))
                out.append(os.path.join(dest_dir, fn))
    else:
        shutil.copy2(s, os.path.join(dest_dir_abs, os.path.basename(s)))
        out.append(os.path.join(dest_dir, os.path.basename(s)))
    return out

def merge_list(existing, patches, key):
    by = {e.get(key): e for e in existing}
    for p in patches:
        k = p.get(key)
        if k in by:
            by[k].update(p)
        else:
            existing.append(p)
            by[k] = p

def apply_patch(tracker, patch):
    if "deal" in patch:
        tracker["deal"].update(patch["deal"])
    if "buyers" in patch:
        merge_list(tracker["buyers"], patch["buyers"], "slug")
    if "bids" in patch:
        tracker["bids"].extend(patch["bids"])
    if "dataroom" in patch:
        tracker["dataroom"].extend(patch["dataroom"])
    if "tasks" in patch:
        merge_list(tracker["tasks"], patch["tasks"], "task")
    if "legals" in patch:
        merge_list(tracker["legals"], patch["legals"], "milestone")
    if "reporting" in patch:
        tracker["reporting"].extend(patch["reporting"])
    if "preferred_bidder" in patch:
        tracker["preferred_bidder"].update(patch["preferred_bidder"])

def write_snapshot(deal_folder, tracker):
    d = tracker["deal"]
    buyers = tracker["buyers"]
    signed = sum(1 for b in buyers if b.get("nda_status") == "signed")
    qual = sum(1 for b in buyers if b.get("aml_status") == "clear" and b.get("pof_status") == "verified")
    lines = [f"# {d.get('name','')}, tracker snapshot", "",
             f"- Stage: **{d.get('current_stage','')}**  |  Round: {d.get('current_round',0)}",
             f"- Client: {d.get('client','')}  |  Quoting: {d.get('quoting_price','')}",
             f"- Buyers: {len(buyers)}  |  NDAs signed: {signed}  |  Qualified: {qual}  |  Bids logged: {len(tracker['bids'])}",
             f"- Target exchange: {d.get('target_exchange','')}  |  Completion: {d.get('target_completion','')}"
             + (f"  |  Actual completion: {d['actual_completion']}" if d.get('actual_completion') else ""), ""]
    if tracker["preferred_bidder"].get("buyer"):
        pb = tracker["preferred_bidder"]
        lines.append(f"- Preferred bidder: **{pb['buyer']}** at £{pb.get('price',0):,.0f}, {pb.get('hot_status','')}")
        lines.append("")
    lines.append("| Buyer | Company | NDA | AML | PoF | R1 | R2 |")
    lines.append("|---|---|---|---|---|---|---|")
    for b in buyers:
        lines.append("| {name} | {company} | {nda_status} | {aml_status} | {pof_status} | {r1} | {r2} |".format(
            name=b.get("name",""), company=b.get("company",""), nda_status=b.get("nda_status",""),
            aml_status=b.get("aml_status",""), pof_status=b.get("pof_status",""),
            r1=b.get("bid_status_round_1",""), r2=b.get("bid_status_round_2","")))
    with open(os.path.join(deal_folder, "tracker-snapshot.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

def log_correspondence(deal_folder, stage, copied):
    path = os.path.join(deal_folder, "correspondence-log.md")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("# Correspondence log\n\n")
    today = datetime.date.today().isoformat()
    with open(path, "a") as f:
        f.write(f"## {stage['id']}, {stage['title']}  ({today})\n")
        if copied:
            for c in copied:
                f.write(f"- Filed: `{c}`\n")
        else:
            f.write("- (no documents pulled this stage)\n")
        f.write("\n")

def run_refresh(deal_folder):
    env = dict(os.environ); env["CLAUDE_PLUGIN_ROOT"] = ROOT
    r = subprocess.run([sys.executable, REFRESH, deal_folder],
                       capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()

def run_stage(deal_folder, stage):
    os.makedirs(deal_folder, exist_ok=True)
    # 1. structure + templates (stage 0)
    if stage.get("create_structure"):
        for t in TREE:
            os.makedirs(os.path.join(deal_folder, t), exist_ok=True)
        xlsx_dest = os.path.join(deal_folder, "mandate-tracker.xlsx")
        shutil.copy2(os.path.join(ASSETS, "mandate-tracker-template.xlsx"), xlsx_dest)
        os.chmod(xlsx_dest, 0o644)         # copy2 preserves the template's read-only bits; refresh must reopen this workbook to save in place
        shutil.copy2(os.path.join(ASSETS, "NDA-template-EXAMPLE.docx"),
                     os.path.join(deal_folder, "nda", "NDA-template-EXAMPLE.docx"))
        shutil.copy2(os.path.join(ASSETS, "HOT-template-EXAMPLE.docx"),
                     os.path.join(deal_folder, "04-legals", "HOT-template-EXAMPLE.docx"))
    # 2. pull documents
    copied = []
    for c in stage.get("copies", []):
        copied += copy_one(c["src"], c["dest"], deal_folder)
    if stage.get("write_dataroom_index"):
        write_dataroom_index(deal_folder)
    # 3. tracker
    tpath = os.path.join(deal_folder, "tracker.json")
    if os.path.exists(tpath):
        with open(tpath) as f:
            tracker = json.load(f)
    else:
        tracker = json.loads(json.dumps(EMPTY_TRACKER))
    for k, v in EMPTY_TRACKER.items():
        tracker.setdefault(k, json.loads(json.dumps(v)))
    apply_patch(tracker, stage.get("tracker", {}))
    with open(tpath, "w") as f:
        json.dump(tracker, f, indent=2, ensure_ascii=False)
    # 4. refresh + snapshot
    rc, msg = run_refresh(deal_folder)
    write_snapshot(deal_folder, tracker)
    log_correspondence(deal_folder, stage, copied)
    return {"id": stage["id"], "skill": stage.get("skill",""), "title": stage["title"],
            "narration": stage.get("narration",""), "copied": copied,
            "schedules": stage.get("schedules", []), "gate": stage.get("gate",""),
            "refresh_rc": rc, "refresh_msg": msg,
            "stage_after": tracker["deal"].get("current_stage",""),
            "round_after": tracker["deal"].get("current_round",0)}

def write_dataroom_index(deal_folder):
    base = os.path.join(deal_folder, "01-dataroom")
    lines = ["# Data room index", ""]
    for cat in ["title","leases","financial","compliance","planning","management","diligence"]:
        d = os.path.join(base, cat)
        if os.path.isdir(d):
            files = sorted(f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)))
            if files:
                lines.append(f"## {cat.title()}")
                lines += [f"- {f}" for f in files] + [""]
    with open(os.path.join(base, "INDEX.md"), "w") as f:
        f.write("\n".join(lines) + "\n")

def main():
    if "--list" in sys.argv:
        for s in load_script()["stages"]:
            print(s["id"], "-", s["title"])
        return
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    deal_folder = os.path.abspath(sys.argv[1])
    stage_id = sys.argv[2]
    stages = load_script()["stages"]
    targets = stages if stage_id == "all" else [s for s in stages if s["id"] == stage_id]
    if not targets:
        print("Unknown stage id:", stage_id); sys.exit(1)
    out = [run_stage(deal_folder, s) for s in targets]
    print(json.dumps(out if stage_id == "all" else out[0], indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
