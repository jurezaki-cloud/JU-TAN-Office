from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from app.database.travel_order_repository import travel_order_repository
from app.modules.travel_orders.travel_order_dialog import TravelOrderDialog
from app.widgets.cards.enterprise_card import EnterpriseCard

class TravelOrderPage(QWidget):
    def __init__(self):
        super().__init__(); self.setObjectName("TravelOrderPage")
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(16)
        top=QHBoxLayout(); title=QLabel("Potni nalogi"); title.setObjectName("PageTitle")
        self.btn_new=QPushButton("Nov potni nalog"); self.btn_new.setObjectName("PrimaryButton")
        self.btn_edit=QPushButton("Odpri"); self.btn_edit.setObjectName("SecondaryButton")
        self.btn_cancel=QPushButton("Storniraj"); self.btn_cancel.setObjectName("DangerButton")
        self.btn_pdf=QPushButton("PDF"); self.btn_pdf.setObjectName("SecondaryButton")
        top.addWidget(title); top.addStretch(); top.addWidget(self.btn_new); top.addWidget(self.btn_edit); top.addWidget(self.btn_pdf); top.addWidget(self.btn_cancel); layout.addLayout(top)
        card=EnterpriseCard("DashboardCard"); self.table=QTableWidget(0,8)
        self.table.setHorizontalHeaderLabels(["Številka","Zaposleni","Relacija","Odhod","Prihod","Km","Skupaj","Status"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        card.body.addWidget(self.table); layout.addWidget(card,1)
        self.btn_new.clicked.connect(self.new_order); self.btn_edit.clicked.connect(self.edit_order); self.btn_pdf.clicked.connect(self.export_pdf); self.btn_cancel.clicked.connect(self.cancel_order)
        self.table.doubleClicked.connect(lambda _: self.edit_order()); self.refresh()
    def refresh(self):
        rows=travel_order_repository.get_all(); self.table.setRowCount(len(rows))
        for y,r in enumerate(rows):
            vals=(r[1],r[2],r[3],r[4] or "",r[5] or "",f"{float(r[6] or 0):.2f}",f"{float(r[7] or 0):.2f} €",r[8] or "")
            for x,v in enumerate(vals):
                item=QTableWidgetItem(str(v)); item.setData(256,r[0]); self.table.setItem(y,x,item)
        self.table.resizeColumnsToContents()
    def selected_id(self):
        row=self.table.currentRow()
        return self.table.item(row,0).data(256) if row>=0 and self.table.item(row,0) else None
    def new_order(self):
        if TravelOrderDialog(self).exec(): self.refresh()
    def edit_order(self):
        oid=self.selected_id()
        if oid and TravelOrderDialog(self,oid).exec(): self.refresh()
    def cancel_order(self):
        from PySide6.QtWidgets import QMessageBox
        oid=self.selected_id()
        if oid and QMessageBox.question(self,"Storniranje","Storniram izbrani potni nalog?")==QMessageBox.Yes:
            travel_order_repository.cancel(oid); self.refresh()

    def export_pdf(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast_info
        from app.pdf.travel_order_pdf import export_travel_order
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        if not allow("export", self): return
        oid=self.selected_id()
        if not oid:
            toast_info(self,"Najprej izberi potni nalog."); return
        row=travel_order_repository.get_by_id(oid)
        path=export_travel_order(row)
        audit("export",f"travel_order:{oid}")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
