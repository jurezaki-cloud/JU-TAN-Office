from __future__ import annotations
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from app.core.constants import EXPORT_DIR
from app.pdf.pdf_company import load_company, load_pdf_options
from app.pdf.pdf_footer import draw_footer
from app.pdf.pdf_header import build_header
from app.pdf.pdf_styles import BORDER, PAD, styles

def _eur(v): return f"{float(v or 0):,.2f} €".replace(",", " ")

def export_travel_order(row) -> Path:
    company=load_company(); options=load_pdf_options(); look=styles()
    folder=Path(options["folder"]) if options.get("folder") else EXPORT_DIR
    folder.mkdir(parents=True,exist_ok=True); path=folder/f"{row[1]}.pdf"
    doc=SimpleDocTemplate(str(path),pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=16*mm,bottomMargin=22*mm,
                          title=f"Potni nalog {row[1]}",author=company.name or "JU-TAN Office")
    story=[]; story.extend(build_header(company,options))
    story += [Paragraph("POTNI NALOG IN OBRAČUN POTNIH STROŠKOV",look["title"]),Spacer(1,PAD)]
    info=[["Številka",row[1],"Status",row[22]],["Zaposleni / voznik",row[2],"Namen",row[3] or "—"],
          ["Relacija",row[4],"Vozilo",f"{row[5] or '—'} · {row[6] or '—'}"],
          ["Odhod",row[7] or "—","Prihod",row[8] or "—"],
          ["Začetni km",str(row[9] or 0),"Končni km",str(row[10] or 0)],["Prevoženo",f"{row[11] or 0} km","Tarifa",f"{row[12] or 0} €/km"]]
    t=Table([[Paragraph(str(c),look["body"]) for c in r] for r in info],colWidths=[34*mm,56*mm,28*mm,62*mm])
    t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.35,BORDER),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),5)]))
    story += [t,Spacer(1,PAD),Paragraph("Obračun stroškov",look["label"])]
    costs=[["Kilometrina",_eur(row[13])],["Dnevnice",_eur(row[14])],["Parkirnine",_eur(row[15])],
           ["Cestnine",_eur(row[16])],["Gorivo",_eur(row[17])],["Drugi stroški",_eur(row[18])],
           ["SKUPAJ",_eur(row[20])],["Predujem",_eur(row[19])],["ZA IZPLAČILO / VRAČILO",_eur(row[21])]]
    ct=Table([[Paragraph(str(a),look["body"]),Paragraph(str(b),look["body_right"])] for a,b in costs],colWidths=[120*mm,60*mm])
    ct.setStyle(TableStyle([("LINEABOVE",(0,6),(-1,6),.7,BORDER),("LINEABOVE",(0,8),(-1,8),.7,BORDER),("PADDING",(0,0),(-1,-1),5)]))
    story += [ct,Spacer(1,PAD)]
    if row[23]: story += [Paragraph("Opombe",look["label"]),Paragraph(str(row[23]).replace("\n","<br/>"),look["body"]),Spacer(1,PAD)]
    sig=Table([["Podpis zaposlenega","Odobril / podpis odgovorne osebe"],["\n\n________________________","\n\n________________________"]],colWidths=[90*mm,90*mm])
    sig.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),6)])); story.append(sig)
    footer=options.get("footer") or ""
    website=options.get("website_url") or ""
    doc.build(
        story,
        onFirstPage=lambda c,d: draw_footer(c,d,footer,website_url=website),
        onLaterPages=lambda c,d: draw_footer(c,d,footer,website_url=website),
    )
    return path
