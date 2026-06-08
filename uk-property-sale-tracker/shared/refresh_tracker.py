#!/usr/bin/env python3
"""Rebuild mandate-tracker.xlsx for a deal from its tracker.json.

Usage: python refresh_tracker.py <deal-folder>

This is the only code that writes the workbook. Skills update tracker.json then
call this. Formatting and the live summary formulas come from the bundled builder,
so the rendered file is always consistent with the template.
"""
import json, os, sys, subprocess, glob
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation

DARK, MID, LIGHT, GREY, LINE, ACCENT = "1F4E45", "2E6B5E", "E8F0EE", "F2F2F2", "C9C9C9", "B98A2E"
FONT = "Arial"
thin = Side(style="thin", color=LINE)
border = Border(left=thin, right=thin, top=thin, bottom=thin)

# ---- seed checklists (used when the json arrays are empty) -------------------
SEED_TASKS = [
 ("1. Mandate & setup","Agree and sign agency / sale mandate","Agent","onboard-mandate"),
 ("1. Mandate & setup","Confirm fee basis, abort fee, marketing budget","Agent","onboard-mandate"),
 ("1. Mandate & setup","Confirm sale structure (asset vs share / SPV)","Agent","onboard-mandate"),
 ("1. Mandate & setup","Run AML / KYC on vendor and beneficial owners","Agent","onboard-mandate"),
 ("1. Mandate & setup","Confirm VAT position (OTT / TOGC) with client","Agent","onboard-mandate"),
 ("1. Mandate & setup","Agree process type and timetable","Agent","onboard-mandate"),
 ("1. Mandate & setup","Create deal folder, tracker and schedules","Agent","setup-deal"),
 ("2. Information & data room","Collect title documents","Agent","build-dataroom"),
 ("2. Information & data room","Collect leases, licences, deeds of variation","Agent","build-dataroom"),
 ("2. Information & data room","Compile and verify tenancy schedule / rent roll","Agent","build-dataroom"),
 ("2. Information & data room","Gather service charge budgets and accounts","Agent","build-dataroom"),
 ("2. Information & data room","Obtain EPC(s) and confirm validity","Agent","build-dataroom"),
 ("2. Information & data room","Obtain asbestos register, FRA, surveys","Agent","build-dataroom"),
 ("2. Information & data room","Collect deposits, AGAs, guarantees","Agent","build-dataroom"),
 ("2. Information & data room","Gather planning, building regs, warranties","Agent","build-dataroom"),
 ("2. Information & data room","Commission / compile vendor due diligence","Agent","build-dataroom"),
 ("2. Information & data room","Build and index the data room","Agent","build-dataroom"),
 ("3. Marketing & buyers","Build and qualify target buyer list","Agent","manual"),
 ("3. Marketing & buyers","Prepare teaser and Information Memorandum","Agent","manual"),
 ("3. Marketing & buyers","Issue teaser, log expressions of interest","Agent","review-inbox"),
 ("3. Marketing & buyers","Issue NDAs to interested parties","Agent","manage-ndas"),
 ("3. Marketing & buyers","Chase unsigned NDAs (every 2 days)","Agent","manage-ndas"),
 ("3. Marketing & buyers","File signed NDAs, grant data room access","Agent","review-inbox"),
 ("3. Marketing & buyers","Run buyer AML / KYC and proof of funds","Agent","qualify-buyer"),
 ("3. Marketing & buyers","Arrange inspections / tenant liaison","Agent","manual"),
 ("3. Marketing & buyers","Run and log data room Q&A","Agent","manual"),
 ("4. Bids & offers","Issue round 1 process letter","Agent","request-bids"),
 ("4. Bids & offers","Receive and log round 1 bids","Agent","process-bids"),
 ("4. Bids & offers","Analyse bids, report to client","Agent","process-bids"),
 ("4. Bids & offers","Issue round 2 best-and-final process letter","Agent","request-bids"),
 ("4. Bids & offers","Log round 2 bids and compare rounds","Agent","process-bids"),
 ("4. Bids & offers","Notify unsuccessful bidders","Agent","select-and-hot"),
 ("5. Preferred bidder & HoT","Select preferred bidder with client","Agent","select-and-hot"),
 ("5. Preferred bidder & HoT","Negotiate and agree Heads of Terms","Agent","select-and-hot"),
 ("5. Preferred bidder & HoT","Confirm exclusivity / lockout","Agent","select-and-hot"),
 ("6. Legal & completion","Instruct vendor solicitors, issue contract pack","Solicitor","track-legals"),
 ("6. Legal & completion","Coordinate CPSE replies and enquiries","Solicitor","track-legals"),
 ("6. Legal & completion","Support due diligence and searches","Solicitor","track-legals"),
 ("6. Legal & completion","Manage deposit and exchange","Solicitor","track-legals"),
 ("6. Legal & completion","Coordinate to completion and apportionments","Solicitor","track-legals"),
 ("6. Legal & completion","Tenant / managing agent handover","Agent","track-legals"),
 ("7. Reporting & close","Regular (weekly) client progress reports","Agent","client-report"),
 ("7. Reporting & close","Close data room, archive records","Agent","manual"),
 ("7. Reporting & close","Invoice fee and disbursements","Agent","client-report"),
 ("7. Reporting & close","Issue final closing report to client","Agent","client-report"),
]
SEED_DOCS = [
 ("Title","Official copies of register and title plan"),
 ("Title","Filed documents / restrictive covenants"),
 ("Leasing","Leases, underleases and counterparts"),
 ("Leasing","Licences and deeds of variation / side letters"),
 ("Leasing","Tenancy schedule / rent roll (verified)"),
 ("Leasing","Rent deposit deeds and AGAs / guarantees"),
 ("Financial","Service charge budgets and reconciled accounts"),
 ("Financial","Arrears report and rent receipts"),
 ("Compliance","EPC certificate(s)"),
 ("Compliance","Asbestos register / survey"),
 ("Compliance","Fire risk assessment"),
 ("Compliance","Condition / structural / M&E surveys"),
 ("Planning","Planning consents and conditions"),
 ("Planning","Building regulations approvals"),
 ("Planning","Collateral warranties / latent defects cover"),
 ("Management","Management agreement and managing agent details"),
 ("Diligence","Vendor due diligence report"),
 ("Diligence","Replies to standard pre-contract enquiries (CPSE)"),
]
SEED_LEGALS = [
 "Preferred bidder confirmed","Heads of Terms agreed and circulated","Exclusivity / lockout in place",
 "Vendor solicitors instructed","Contract pack issued to buyer solicitors","CPSE replies provided",
 "Buyer searches submitted","Pre-contract enquiries answered","Buyer board / IC approval confirmed",
 "Buyer funding confirmed","Contract approved / engrossed","Exchange of contracts","Deposit received",
 "Completion","Completion statement and apportionments","Notices to tenants / rent authority",
 "Managing agent handover",
]
NDA_MAP = {"not_sent":"Not sent","sent":"Sent","signed":"Signed"}
AML_MAP = {"pending":"Pending","clear":"Clear","flagged":"Flagged"}
POF_MAP = {"pending":"Pending","verified":"Verified","insufficient":"Insufficient"}
BID_MAP = {"none":"None","requested":"Requested","received":"Received","declined":"Declined"}

def t(ws, text, span):
    c = ws.cell(row=1, column=1, value=text)
    c.font = Font(name=FONT, bold=True, size=15, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=DARK)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=span)
    ws.row_dimensions[1].height = 30

def hr(ws, row, headers):
    for i, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=i, value=h)
        c.font = Font(name=FONT, bold=True, size=10, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=MID)
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True, indent=1)
        c.border = border
    ws.row_dimensions[row].height = 30

def bnd(ws, row, text, span):
    c = ws.cell(row=row, column=1, value=text)
    c.font = Font(name=FONT, bold=True, size=10, color=DARK)
    for col in range(1, span+1):
        cc = ws.cell(row=row, column=col); cc.fill = PatternFill("solid", fgColor=LIGHT); cc.border = border
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=span)

def cols(ws, widths):
    for c, w in widths.items(): ws.column_dimensions[c].width = w

def dc(ws, row, col, value=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name=FONT, size=10)
    c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
    c.border = border
    return c

def zebra(ws, row, ncol):
    if row % 2 == 0:
        for col in range(1, ncol+1):
            ws.cell(row=row, column=col).fill = PatternFill("solid", fgColor=GREY)

def build(data):
    deal = data.get("deal", {})
    wb = Workbook()

    # 1 Mandate Summary
    ws = wb.active; ws.title = "Mandate Summary"; t(ws, "MANDATE SUMMARY", 4)
    cols(ws, {"A":26,"B":34,"C":26,"D":34})
    def kv(row, k1, v1, k2, v2):
        a = ws.cell(row=row, column=1, value=k1); a.font = Font(name=FONT, bold=True, size=10, color=DARK)
        a.alignment = Alignment(vertical="center", indent=1); a.border = border
        dc(ws, row, 2, v1)
        c = ws.cell(row=row, column=3, value=k2); c.font = Font(name=FONT, bold=True, size=10, color=DARK)
        c.alignment = Alignment(vertical="center", indent=1); c.border = border
        dc(ws, row, 4, v2)
    g = deal.get
    bnd(ws,3,"DEAL",4)
    kv(4,"Property name",g("name",""),"Mandate ref",g("mandate_ref",""))
    kv(5,"Address",g("address",""),"Sector / asset type",g("sector",""))
    kv(6,"Client / vendor",g("client",""),"Tenure",g("tenure",""))
    kv(7,"Sale structure (asset / share)",g("sale_structure",""),"VAT position (OTT / TOGC)",g("vat_position",""))
    bnd(ws,8,"MANDATE TERMS",4)
    kv(9,"Mandate type",g("mandate_type",""),"Instruction date",g("instruction_date",""))
    kv(10,"Agent / surveyor",g("agent",""),"Fee basis",g("fee_basis",""))
    kv(11,"Sending email account",g("agent_email",""),"Abort fee",g("abort_fee",""))
    kv(12,"Process type",g("process_type",""),"Send mode (auto / draft)",g("send_mode",""))
    kv(13,"Quoting price",g("quoting_price",""),"Target NIY",g("target_niy",""))
    bnd(ws,14,"KEY DATES",4)
    kv(15,"Launch date",g("launch_date",""),"Round 1 process letter",g("bid_request_date_round_1",""))
    kv(16,"Round 2 (best & final)",g("bid_request_date_round_2",""),"Preferred bidder selected",g("preferred_bidder_date",""))
    kv(17,"Heads of Terms agreed",g("hot_date",""),"Target exchange",g("target_exchange",""))
    kv(18,"Target completion",g("target_completion",""),"Actual completion",g("actual_completion",""))
    bnd(ws,20,"LIVE STATUS (auto-calculated)",4)
    def metric(row, col, label, formula, fmt=None, gold=False):
        l = ws.cell(row=row, column=col, value=label); l.font = Font(name=FONT, bold=True, size=10, color=DARK)
        l.alignment = Alignment(vertical="center", indent=1); l.border = border
        v = ws.cell(row=row, column=col+1, value=formula)
        v.font = Font(name=FONT, bold=True, size=11, color=(ACCENT if gold else "000000"))
        v.alignment = Alignment(vertical="center", indent=1); v.border = border
        if fmt: v.number_format = fmt
    metric(21,1,"Buyers on list","=COUNTA('Buyer Pipeline'!A4:A203)")
    metric(21,3,"NDAs issued","=COUNTIF('Buyer Pipeline'!E4:E203,\"Sent\")+COUNTIF('Buyer Pipeline'!E4:E203,\"Signed\")")
    metric(22,1,"NDAs signed","=COUNTIF('Buyer Pipeline'!E4:E203,\"Signed\")")
    metric(22,3,"Buyers qualified (AML + PoF)","=COUNTIFS('Buyer Pipeline'!J4:J203,\"Clear\",'Buyer Pipeline'!K4:K203,\"Verified\")")
    metric(23,1,"Round 1 bids received","=COUNTIF('Buyer Pipeline'!L4:L203,\"Received\")")
    metric(23,3,"Round 2 bids received","=COUNTIF('Buyer Pipeline'!M4:M203,\"Received\")")
    metric(24,1,"Round 3 bids received","=COUNTIF('Buyer Pipeline'!N4:N203,\"Received\")")
    metric(24,3,"Highest offer (any round)","=MAX('Bid Log'!B4:D203)", fmt='£#,##0;(£#,##0);"-"', gold=True)
    metric(25,1,"Tasks outstanding","=COUNTIF('Task Checklist'!D4:D200,\"Not started\")+COUNTIF('Task Checklist'!D4:D200,\"In progress\")")
    metric(25,3,"Current stage", g("current_stage",""))
    n = ws.cell(row=27, column=1, value="Counts pull live from the other tabs and update on recalculation.")
    n.font = Font(name=FONT, italic=True, size=9, color="666666")
    ws.merge_cells(start_row=27, start_column=1, end_row=27, end_column=4)
    ws.freeze_panes = "A2"

    # 2 Task Checklist
    ws2 = wb.create_sheet("Task Checklist"); t(ws2,"TASK CHECKLIST  (full sale lifecycle)",7)
    cols(ws2, {"A":18,"B":48,"C":16,"D":16,"E":13,"F":13,"G":30})
    hr(ws2,3,["Phase","Task","Owner","Status","Due date","Date done","Automated by"])
    tasks = data.get("tasks") or [{"phase":p,"task":tk,"owner":o,"status":"Not started","due":"","done":"","automated_by":a} for (p,tk,o,a) in SEED_TASKS]
    r = 4
    for it in tasks:
        dc(ws2,r,1,it.get("phase","")); dc(ws2,r,2,it.get("task","")); dc(ws2,r,3,it.get("owner",""))
        dc(ws2,r,4,it.get("status","Not started")); dc(ws2,r,5,it.get("due","")); dc(ws2,r,6,it.get("done","")); dc(ws2,r,7,it.get("automated_by",""))
        zebra(ws2,r,7); r += 1
    dv = DataValidation(type="list", formula1='"Not started,In progress,Complete,N/A,Blocked"', allow_blank=True)
    ws2.add_data_validation(dv); dv.add(f"D4:D{r-1}"); ws2.freeze_panes = "A4"

    # 3 Information & Data Room
    ws3 = wb.create_sheet("Information & Data Room"); t(ws3,"INFORMATION & DATA ROOM CHECKLIST",6)
    cols(ws3, {"A":22,"B":42,"C":14,"D":16,"E":13,"F":30})
    hr(ws3,3,["Category","Document","Received","In data room","Date","Notes"])
    docs = data.get("dataroom") or [{"category":c,"document":d,"received":"No","in_dataroom":"No","date":"","notes":""} for (c,d) in SEED_DOCS]
    r = 4
    for it in docs:
        dc(ws3,r,1,it.get("category","")); dc(ws3,r,2,it.get("document","")); dc(ws3,r,3,it.get("received","No"))
        dc(ws3,r,4,it.get("in_dataroom","No")); dc(ws3,r,5,it.get("date","")); dc(ws3,r,6,it.get("notes",""))
        zebra(ws3,r,6); r += 1
    dv = DataValidation(type="list", formula1='"Yes,No,N/A"', allow_blank=True)
    ws3.add_data_validation(dv); dv.add(f"C4:D{r-1}"); ws3.freeze_panes = "A4"

    # 4 Buyer Pipeline
    ws4 = wb.create_sheet("Buyer Pipeline"); t(ws4,"BUYER PIPELINE",15)
    cols(ws4, {"A":22,"B":22,"C":26,"D":13,"E":12,"F":13,"G":13,"H":11,"I":13,"J":12,"K":13,"L":11,"M":11,"N":11,"O":30})
    hr(ws4,3,["Buyer","Company","Contact email","Enquiry date","NDA status","NDA sent","Last chase","Chase count","NDA signed","AML/KYC","Proof of funds","R1 bid","R2 bid","R3 bid","Notes"])
    buyers = data.get("buyers", [])
    last = max(4 + len(buyers), 24)
    for r in range(4, last):
        b = buyers[r-4] if r-4 < len(buyers) else {}
        dc(ws4,r,1,b.get("name","")); dc(ws4,r,2,b.get("company","")); dc(ws4,r,3,b.get("email",""))
        dc(ws4,r,4,b.get("enquiry_date","")); dc(ws4,r,5,NDA_MAP.get(b.get("nda_status",""),""))
        dc(ws4,r,6,b.get("nda_sent_date","")); dc(ws4,r,7,b.get("last_chase_date",""))
        dc(ws4,r,8,b.get("chase_count","") if b else ""); dc(ws4,r,9,b.get("nda_signed_date",""))
        dc(ws4,r,10,AML_MAP.get(b.get("aml_status",""),"")); dc(ws4,r,11,POF_MAP.get(b.get("pof_status",""),""))
        dc(ws4,r,12,BID_MAP.get(b.get("bid_status_round_1",""),"")); dc(ws4,r,13,BID_MAP.get(b.get("bid_status_round_2",""),""))
        dc(ws4,r,14,BID_MAP.get(b.get("bid_status_round_3",""),"")); dc(ws4,r,15,b.get("notes","")); zebra(ws4,r,15)
    for spec,colrange in [('"Not sent,Sent,Signed"',"E"),('"Pending,Clear,Flagged"',"J"),('"Pending,Verified,Insufficient"',"K")]:
        dv = DataValidation(type="list", formula1=spec, allow_blank=True); ws4.add_data_validation(dv); dv.add(f"{colrange}4:{colrange}203")
    for colrange in ("L","M","N"):
        dv = DataValidation(type="list", formula1='"None,Requested,Received,Declined"', allow_blank=True); ws4.add_data_validation(dv); dv.add(f"{colrange}4:{colrange}203")
    ws4.freeze_panes = "A4"

    # 5 Bid Log  (three-round client-ready comparison matrix)
    from datetime import date as _date
    ws5 = wb.create_sheet("Bid Log"); t(ws5,"BID COMPARISON",15)
    cols(ws5, {"A":24,"B":15,"C":15,"D":15,"E":15,"F":15,"G":15,"H":9,"I":9,"J":9,"K":18,"L":30,"M":16,"N":18,"O":26})
    # subtitle row (part of the copy-paste block)
    cr = int(deal.get("current_round",0) or 0) or 1
    sub = ws5.cell(row=2, column=1, value=f"{deal.get('name','(property)')}:  Round {cr} bid comparison        Prepared {_date.today().strftime('%d %b %Y')}")
    sub.font = Font(name=FONT, bold=True, size=10, color=DARK)
    sub.alignment = Alignment(vertical="center", indent=1)
    ws5.merge_cells(start_row=2, start_column=1, end_row=2, end_column=15)
    ws5.row_dimensions[2].height = 20
    hr(ws5,3,["Bidder","R1 price","R2 price","R3 price","Chg R1>R2","Chg R2>R3","Latest offer","R1 NIY","R2 NIY","R3 NIY","Movement","Conditions (latest)","Completion (latest)","Funding / PoF","Notes"])

    bids = data.get("bids", [])
    by_buyer = {}
    for bd in bids:
        try: rd = int(bd.get("round",1) or 1)
        except (TypeError, ValueError): rd = 1
        by_buyer.setdefault(bd.get("buyer",""), {})[rd] = bd
    money = '£#,##0;(£#,##0);"-"'; pct = '0.00%'
    GREEN, RED, GREYTXT = "1F7A3D", "C0392B", "777777"

    rows = []
    for buyer, rounds in by_buyer.items():
        if not buyer: continue
        present = sorted(rounds)
        latest_r = present[-1]; latest = rounds[latest_r]
        lp = latest.get("offer_price")
        if len(present) == 1:
            mv, mc = ("Round 1", GREYTXT) if present[0]==1 else (f"New in R{present[0]}", GREEN)
        else:
            a = rounds[present[-2]].get("offer_price"); b = rounds[present[-1]].get("offer_price")
            if isinstance(a,(int,float)) and isinstance(b,(int,float)):
                mv, mc = ("Improved", GREEN) if b>a else (("Reduced", RED) if b<a else ("Held", GREYTXT))
            else:
                mv, mc = "Updated", GREYTXT
        if cr >= 2 and latest_r < cr:
            mv, mc = f"Withdrawn (last R{latest_r})", RED
        rows.append({"buyer":buyer, "rounds":rounds,
                     "latest":latest, "lp": lp if isinstance(lp,(int,float)) else -1, "mv":mv, "mc":mc})
    rows.sort(key=lambda x: x["lp"], reverse=True)

    n_rows = max(len(rows), 8)
    for i in range(n_rows):
        r = 4 + i
        rec = rows[i] if i < len(rows) else None
        leader = (rec is not None and i == 0 and rec["lp"] >= 0)
        # bidder
        cb = dc(ws5,r,1, rec["buyer"] if rec else "")
        if leader: cb.font = Font(name=FONT, size=10, bold=True)
        # prices per round (B,C,D)
        for ci, rd in ((2,1),(3,2),(4,3)):
            val = ""
            if rec and rd in rec["rounds"]:
                v = rec["rounds"][rd].get("offer_price")
                val = v if isinstance(v,(int,float)) else ""
            c = dc(ws5,r,ci,val); c.number_format = money
        # deltas as formulas (E,F)
        ce = dc(ws5,r,5, f'=IF(AND(B{r}<>"",C{r}<>""),C{r}-B{r},"")'); ce.number_format = money
        cf = dc(ws5,r,6, f'=IF(AND(C{r}<>"",D{r}<>""),D{r}-C{r},"")'); cf.number_format = money
        # latest offer formula (G)
        cg = dc(ws5,r,7, f'=IF(D{r}<>"",D{r},IF(C{r}<>"",C{r},IF(B{r}<>"",B{r},"")))'); cg.number_format = money
        if leader: cg.font = Font(name=FONT, size=10, bold=True, color=ACCENT)
        # NIY per round (H,I,J)
        for ci, rd in ((8,1),(9,2),(10,3)):
            val = ""
            if rec and rd in rec["rounds"]:
                v = rec["rounds"][rd].get("niy")
                val = v if isinstance(v,(int,float)) else ""
            c = dc(ws5,r,ci,val); c.number_format = pct
        # movement (K)
        ck = dc(ws5,r,11, rec["mv"] if rec else "")
        if rec: ck.font = Font(name=FONT, size=10, bold=True, color=rec["mc"])
        # latest qualitative terms (L,M,N,O)
        lt = rec["latest"] if rec else {}
        dc(ws5,r,12, lt.get("conditions",""))
        dc(ws5,r,13, lt.get("completion",""))
        dc(ws5,r,14, lt.get("pof","") or lt.get("funding_type",""))
        dc(ws5,r,15, lt.get("notes",""))
        zebra(ws5,r,15)

    # legend + paste guidance (below the copy-paste block, not part of it)
    lr = 4 + n_rows + 1
    leg = ws5.cell(row=lr, column=1, value="Movement: Improved / Held / Reduced compares a bidder's latest round with their previous round. Withdrawn = bid in an earlier round, none in the current round. New = first bid after round 1.")
    leg.font = Font(name=FONT, italic=True, size=9, color="666666")
    ws5.merge_cells(start_row=lr, start_column=1, end_row=lr, end_column=15)
    pn = ws5.cell(row=lr+1, column=1, value=f"To send to the client, select rows 1 to {3+n_rows} and copy into the report. Figures are exclusive of VAT and costs.")
    pn.font = Font(name=FONT, italic=True, size=9, color="666666")
    ws5.merge_cells(start_row=lr+1, start_column=1, end_row=lr+1, end_column=15)
    ws5.freeze_panes = "A4"

    # 6 Legal & Completion
    ws6 = wb.create_sheet("Legal & Completion"); t(ws6,"LEGAL & COMPLETION MILESTONES",6)
    cols(ws6, {"A":42,"B":18,"C":16,"D":14,"E":14,"F":30})
    hr(ws6,3,["Milestone","Responsible","Status","Target date","Actual date","Notes"])
    legals = data.get("legals") or [{"milestone":m,"responsible":"","status":"Not started","target_date":"","actual_date":"","notes":""} for m in SEED_LEGALS]
    r = 4
    for it in legals:
        dc(ws6,r,1,it.get("milestone","")); dc(ws6,r,2,it.get("responsible","")); dc(ws6,r,3,it.get("status","Not started"))
        dc(ws6,r,4,it.get("target_date","")); dc(ws6,r,5,it.get("actual_date","")); dc(ws6,r,6,it.get("notes","")); zebra(ws6,r,6); r += 1
    dv = DataValidation(type="list", formula1='"Not started,In progress,Complete,N/A"', allow_blank=True)
    ws6.add_data_validation(dv); dv.add(f"C4:C{r-1}"); ws6.freeze_panes = "A4"

    # 7 Client Reporting
    ws7 = wb.create_sheet("Client Reporting"); t(ws7,"CLIENT REPORTING LOG",6)
    cols(ws7, {"A":14,"B":22,"C":20,"D":24,"E":14,"F":34})
    hr(ws7,3,["Date","Report type","Period covered","Sent to","Method","Summary / notes"])
    rep = data.get("reporting", [])
    last = max(4 + len(rep), 24)
    for r in range(4, last):
        it = rep[r-4] if r-4 < len(rep) else {}
        dc(ws7,r,1,it.get("date","")); dc(ws7,r,2,it.get("type","")); dc(ws7,r,3,it.get("period",""))
        dc(ws7,r,4,it.get("sent_to","")); dc(ws7,r,5,it.get("method","")); dc(ws7,r,6,it.get("notes","")); zebra(ws7,r,6)
    dv = DataValidation(type="list", formula1='"Weekly update,Bid report,Ad hoc,Closing report"', allow_blank=True)
    ws7.add_data_validation(dv); dv.add("B4:B203"); ws7.freeze_panes = "A4"
    return wb

def find_recalc():
    for p in ["/mnt/skills/public/xlsx/scripts/recalc.py",
              os.path.expanduser("~/.claude/skills/xlsx/scripts/recalc.py")]:
        if os.path.exists(p):
            return p
    hits = glob.glob("/mnt/skills/**/xlsx/scripts/recalc.py", recursive=True)
    return hits[0] if hits else None

def main():
    if len(sys.argv) < 2:
        print("usage: refresh_tracker.py <deal-folder>"); sys.exit(1)
    folder = sys.argv[1]
    with open(os.path.join(folder, "tracker.json")) as f:
        data = json.load(f)
    out = os.path.join(folder, "mandate-tracker.xlsx")
    build(data).save(out)
    rc = find_recalc()
    if rc:
        try:
            subprocess.run([sys.executable, rc, out], capture_output=True, timeout=120)
        except Exception:
            pass
    print(f"refreshed {out}")

if __name__ == "__main__":
    main()
