import pytest
from app.database.travel_order_repository import travel_order_repository

def _data(number="PN-TEST-1", status="Osnutek"):
    return dict(number=number,employee="Test Voznik",purpose="Sestanek",route="Ljubljana - Koper",
        vehicle="Osebno vozilo",registration="LJ TEST",departure_at="2026-09-19 08:00",return_at="2026-09-19 18:00",
        start_km=100,end_km=320,distance_km=220,mileage_rate=0.43,mileage_amount=94.6,per_diem_amount=20,
        parking=5,tolls=3,fuel=0,other_costs=0,advance=10,total=122.6,settlement=112.6,status=status,notes="")

def test_travel_order_roundtrip():
    oid=travel_order_repository.save(_data())
    row=travel_order_repository.get_by_id(oid)
    assert row[1]=="PN-TEST-1"; assert row[2]=="Test Voznik"; assert row[11]==220
    assert row[20]==pytest.approx(122.6); assert row[21]==pytest.approx(112.6)

def test_travel_order_cancel_preserves_record():
    oid=travel_order_repository.save(_data("PN-TEST-2"))
    travel_order_repository.cancel(oid)
    row=travel_order_repository.get_by_id(oid)
    assert row is not None; assert row[22]=="Storniran"

def test_travel_order_number_is_generated():
    assert travel_order_repository.next_number().startswith("PN-")
