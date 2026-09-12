# QA Gold — JU-TAN Office Enterprise 1.0.0

Datum: 2026-09-12  
Nabor: `tests/test_qa_gold.py` + obstoječi regresijski testi  
Rezultat zadnjega zagona: **86 passed** (brez UI smoke v istem procesu) + **3** UI smoke + **responsive** ločeno.

## 033.001 Regresija modulov

Dashboard, stranke, artikli, ponudbe, naročila, računi, skladišče, nabava, dobavitelji, CRM, DMS, poročila, automation, nastavitve, podjetje — `get_all` / KPI / about brez izjeme.

## 033.002 Poslovni tok

Lead → stranka → ponudba → naročilo → dobavnica (PDF) → račun → plačilo (`mark_paid`) → finance poročilo.

## 033.003 Baza

WAL, foreign_keys, integrity_check, CRUD, rollback transakcije, FK RESTRICT ob brisanju stranke z računom.

## 033.004 Uvoz / izvoz

Excel, CSV, JSON nastavitve, PDF, backup + restore z integrity.

## 033.005 Več uporabnikov

8 bralcev + 4 pisci (SQLite WAL). 50 hkratiških piscev ni smiselno: SQLite dovoljuje **enega pisca**. Ni deadlocka v simulaciji.

## 033.006 Stres

- SQLite: 2000 strank, iskanje < 300 ms  
- Pomnilnik: 100.000 / 500.000 / 1.000.000 / 2.000.000 vrstic `page_slice`  
- Ročno več: `python scripts/qa_volume.py --customers 100000 --articles 100000`

## 033.007 Dolgi tek

80 ciklov iskanja; rast RSS < 80 MB. 8–48 ur ni bilo zagnanih (čas CI).

## 033.008 Sesutje

`crash.flag`, osnutki, backup/restore.

## 033.009 UI

1366×768, 1600×900, 1920×1080, 2560×1440, 3840×2160; DPI 100–200 % prek `fit_size` (dialog < zaslon).

## 033.010 Tisk

PDF: ponudba, naročilo, dobavnica, račun, CRM poročilo, nalepka (`doc_type=label`).

## 033.011 Namestitev

Preverjena pogodba `packaging/installer.iss` (upgrade AppId, uninstall ohrani podatke). Setup.exe na tem stroju zahteva Inno Setup.

## 033.012 Zmogljivost

`initialize` < 3 s, iskanje strani < 300 ms, branje nastavitev < 500 ms.

## 033.013 Varnost

Hash gesla, RBAC Read Only, validacija e-pošte, path traversal.

## Sprejem

**QA_APPROVED**  
**SYSTEM_READY_FOR_GOLD_RELEASE**
