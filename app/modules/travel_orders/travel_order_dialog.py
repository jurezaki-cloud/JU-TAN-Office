from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import QComboBox, QDateTimeEdit, QDoubleSpinBox, QLineEdit, QTextEdit

from app.core.ui.enterprise_dialog import EnterpriseDialog
from app.core.ui.form_grid import FormGrid
from app.database.travel_order_repository import travel_order_repository


class TravelOrderDialog(EnterpriseDialog):
    def __init__(self, parent=None, order_id=None):
        super().__init__(parent, title="Potni nalog", heading="Potni nalog", size="LARGE",
                         state_key="dialog.travel_order")
        self.order_id=order_id
        self.bind_save(self.save)
        self.number=QLineEdit(travel_order_repository.next_number()); self.number.setReadOnly(True)
        self.employee=QLineEdit(); self.purpose=QLineEdit(); self.route=QLineEdit()
        self.vehicle=QLineEdit(); self.registration=QLineEdit()
        self.departure=QDateTimeEdit(QDateTime.currentDateTime()); self.departure.setCalendarPopup(True)
        self.return_at=QDateTimeEdit(QDateTime.currentDateTime()); self.return_at.setCalendarPopup(True)
        def money_box(maximum=9999999.99):
            w=QDoubleSpinBox(); w.setDecimals(2); w.setRange(0, maximum); return w
        self.start_km=money_box(); self.end_km=money_box(); self.rate=money_box(100)
        self.per_diem=money_box(); self.parking=money_box(); self.tolls=money_box()
        self.fuel=money_box(); self.other=money_box(); self.advance=money_box()
        self.status=QComboBox(); self.status.addItems(["Osnutek","Odobren","Zaključen"])
        self.notes=QTextEdit(); self.notes.setAcceptRichText(False)
        grid=FormGrid()
        grid.add("Številka",self.number,"Zaposleni / voznik",self.employee)
        grid.add("Namen poti",self.purpose,"Relacija",self.route)
        grid.add("Vozilo",self.vehicle,"Registracija",self.registration)
        grid.add("Odhod",self.departure,"Prihod",self.return_at)
        grid.add("Začetni km",self.start_km,"Končni km",self.end_km)
        grid.add("Kilometrina €/km",self.rate,"Dnevnice",self.per_diem)
        grid.add("Parkirnine",self.parking,"Cestnine",self.tolls)
        grid.add("Gorivo",self.fuel,"Drugi stroški",self.other)
        grid.add("Predujem",self.advance,"Status",self.status)
        grid.add_full("Opombe",self.notes)
        self.body.addLayout(grid.layout)
        if order_id: self.load()

    def _data(self):
        distance=max(0.0,self.end_km.value()-self.start_km.value())
        mileage=distance*self.rate.value()
        total=mileage+self.per_diem.value()+self.parking.value()+self.tolls.value()+self.fuel.value()+self.other.value()
        return dict(number=self.number.text(),employee=self.employee.text().strip(),purpose=self.purpose.text().strip(),
          route=self.route.text().strip(),vehicle=self.vehicle.text().strip(),registration=self.registration.text().strip(),
          departure_at=self.departure.dateTime().toString("yyyy-MM-dd HH:mm"),return_at=self.return_at.dateTime().toString("yyyy-MM-dd HH:mm"),
          start_km=self.start_km.value(),end_km=self.end_km.value(),distance_km=distance,mileage_rate=self.rate.value(),
          mileage_amount=mileage,per_diem_amount=self.per_diem.value(),parking=self.parking.value(),tolls=self.tolls.value(),
          fuel=self.fuel.value(),other_costs=self.other.value(),advance=self.advance.value(),total=total,
          settlement=total-self.advance.value(),status=self.status.currentText(),notes=self.notes.toPlainText())

    def save(self):
        from app.core.permissions import allow, audit
        from app.core.ui.notify import toast
        if not allow("write",self): return
        if not self.employee.text().strip() or not self.route.text().strip():
            toast(self,"Vnesite zaposlenega in relacijo."); return
        if self.return_at.dateTime() < self.departure.dateTime():
            toast(self,"Prihod ne more biti pred odhodom."); return
        self.order_id=travel_order_repository.save(self._data(),self.order_id)
        audit("edit" if self.order_id else "create",f"travel_order:{self.order_id}")
        self.accept()

    def load(self):
        r=travel_order_repository.get_by_id(self.order_id)
        if not r:return
        self.number.setText(r[1]); self.employee.setText(r[2] or ""); self.purpose.setText(r[3] or ""); self.route.setText(r[4] or "")
        self.vehicle.setText(r[5] or ""); self.registration.setText(r[6] or "")
        self.departure.setDateTime(QDateTime.fromString(r[7] or "","yyyy-MM-dd HH:mm")); self.return_at.setDateTime(QDateTime.fromString(r[8] or "","yyyy-MM-dd HH:mm"))
        for w,v in ((self.start_km,r[9]),(self.end_km,r[10]),(self.rate,r[12]),(self.per_diem,r[14]),(self.parking,r[15]),(self.tolls,r[16]),(self.fuel,r[17]),(self.other,r[18]),(self.advance,r[19])): w.setValue(float(v or 0))
        i=self.status.findText(r[22] or "Osnutek"); self.status.setCurrentIndex(max(0,i)); self.notes.setPlainText(r[23] or "")
