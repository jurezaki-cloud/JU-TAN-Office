from PySide6.QtWidgets import QDoubleSpinBox, QFormLayout, QLabel
from app.widgets.cards.enterprise_card import EnterpriseCard

class TravelSettingsCard(EnterpriseCard):
    def __init__(self,parent=None):
        super().__init__("DashboardCard",parent)
        title=QLabel("Potni nalogi"); title.setObjectName("SectionTitle"); self.body.addWidget(title)
        hint=QLabel("Privzete tarife za nove potne naloge. Vrednosti lahko kadarkoli prilagodite."); hint.setObjectName("KpiHint"); hint.setWordWrap(True); self.body.addWidget(hint)
        form=QFormLayout()
        self.mileage=QDoubleSpinBox(); self.mileage.setDecimals(4); self.mileage.setRange(0,100); self.mileage.setSuffix(" €/km")
        self.per_diem=QDoubleSpinBox(); self.per_diem.setDecimals(2); self.per_diem.setRange(0,10000); self.per_diem.setSuffix(" €")
        form.addRow("Kilometrina",self.mileage); form.addRow("Domača dnevnica",self.per_diem); self.body.addLayout(form)
    def set_values(self,data):
        data=data or {}; self.mileage.setValue(float(data.get("mileage_rate",0) or 0)); self.per_diem.setValue(float(data.get("domestic_per_diem",0) or 0))
    def values(self):
        return {"mileage_rate":self.mileage.value(),"domestic_per_diem":self.per_diem.value()}
