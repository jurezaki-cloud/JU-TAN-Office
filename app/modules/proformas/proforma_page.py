from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView,QHBoxLayout,QInputDialog,QMessageBox,QPushButton,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget
from app.core.permissions import audit, allow
from app.database.customer_repository import customer_repository
from app.database.offer_repository import offer_repository
from app.database.proforma_repository import proforma_repository
from app.pdf.pdf_export import pdf_export
from app.services.offer_service import offer_service
from app.services.print_center import print_center
from app.widgets.mail_center_dialog import MailCenterDialog

class ProformaPage(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("ProformaPage")
        layout=QVBoxLayout(self); actions=QHBoxLayout()
        self.btn_new=QPushButton("Nov predračun iz ponudbe"); self.btn_new.setObjectName("PrimaryButton")
        self.btn_pdf=QPushButton("PDF"); self.btn_mail=QPushButton("Pošlji po e-pošti")
        self.btn_print=QPushButton("Natisni"); self.btn_invoice=QPushButton("Pretvori v račun")
        for b in (self.btn_pdf,self.btn_mail,self.btn_print,self.btn_invoice): b.setObjectName("SecondaryButton")
        for b in (self.btn_new,self.btn_pdf,self.btn_mail,self.btn_print,self.btn_invoice): actions.addWidget(b)
        actions.addStretch(1); layout.addLayout(actions)
        self.table=QTableWidget(0,7); self.table.setHorizontalHeaderLabels(["Številka","Stranka","Datum","Rok","Znesek","Status","Ponudba"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers); self.table.horizontalHeader().setStretchLastSection(True); layout.addWidget(self.table,1)
        self.btn_new.clicked.connect(self.new_proforma); self.btn_pdf.clicked.connect(self.export_pdf)
        self.btn_mail.clicked.connect(self.email_document); self.btn_print.clicked.connect(self.print_document)
        self.btn_invoice.clicked.connect(self.convert_invoice); self.table.doubleClicked.connect(lambda _i:self.export_pdf()); self.refresh()
    def refresh(self):
        rows=proforma_repository.get_all(); self.table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            values=[row[1],row[2] or "—",row[3],row[4] or "—",f"{float(row[5] or 0):,.2f} €",row[6],row[7]]
            for c,value in enumerate(values):
                item=QTableWidgetItem(str(value)); item.setData(Qt.UserRole,row[0]); self.table.setItem(r,c,item)
    def selected_id(self):
        row=self.table.currentRow(); return int(self.table.item(row,0).data(Qt.UserRole)) if row>=0 and self.table.item(row,0) else None
    def new_proforma(self):
        if not allow("write",self): return
        offers=list(offer_repository.get_all())
        if not offers: QMessageBox.information(self,"Predračuni","Najprej ustvarite ponudbo."); return
        labels=[f"{r[1]} — {r[2] or '—'} — {float(r[6] or 0):,.2f} €" for r in offers]
        label,ok=QInputDialog.getItem(self,"Nov predračun","Izberi ponudbo:",labels,0,False)
        if not ok:return
        idx=labels.index(label); pid=proforma_repository.create_from_offer(offers[idx][0]); audit("create",f"proforma:{pid}:offer:{offers[idx][0]}"); self.refresh()
    def _path(self):
        pid=self.selected_id()
        if pid is None: raise ValueError("Najprej izberi predračun.")
        return pid,pdf_export.export_proforma(pid)
    def export_pdf(self):
        try: _pid,path=self._path(); pdf_export.show_result(self,path); self.refresh()
        except Exception as exc: QMessageBox.warning(self,"Predračun",str(exc))
    def print_document(self):
        try: _pid,path=self._path(); print_center.print_pdf(self,path); self.refresh()
        except Exception as exc: QMessageBox.warning(self,"Predračun",str(exc))
    def email_document(self):
        try:
            pid,path=self._path(); p=proforma_repository.get_by_id(pid); customer=customer_repository.get_by_id(p[3]) if p else None
            recipient=str(customer[8] or "") if customer else ""; number=str(p[1] or "")
            body=f"Spoštovani,\n\nv priponki vam pošiljamo predračun {number}.\n\nLep pozdrav,\nJU-TAN Studio"
            if MailCenterDialog(self,recipient=recipient,subject=f"Predračun {number}",body=body,attachment=path).exec(): self.refresh()
        except Exception as exc: QMessageBox.warning(self,"Mail Center",str(exc))
    def convert_invoice(self):
        if not allow("write",self):return
        pid=self.selected_id()
        if pid is None: QMessageBox.information(self,"Predračuni","Najprej izberi predračun."); return
        p=proforma_repository.get_by_id(pid)
        if p[8]: QMessageBox.information(self,"Predračuni","Predračun je že pretvorjen v račun."); return
        try:
            invoice_id,number=offer_service.convert_to_invoice(p[2]); proforma_repository.mark_converted(pid,invoice_id)
            audit("create",f"invoice_from_proforma:{pid}->{invoice_id}"); self.refresh(); QMessageBox.information(self,"Predračuni",f"Ustvarjen je račun {number}.")
        except Exception as exc: QMessageBox.warning(self,"Predračuni",str(exc))
