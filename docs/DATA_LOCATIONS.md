# Lokacije podatkov — JU-TAN Office Enterprise

Ta dokument popisuje **izključno JU-TAN** mape in datoteke.
Namestitev / odstranitev sme briše le vsebino, ki pripada JU-TAN Office.
Uporabniški izvozi (PDF računov na Namizju, Dokumentih, …) se **ne** brišejo,
razen če so shranjeni znotraj spodnjih JU-TAN map.

## Nameščeni način (Setup.exe)

| Lokacija | Vsebina | Standardna odstranitev | Popolna odstranitev | Čista namestitev |
| --- | --- | --- | --- | --- |
| `%ProgramData%\JU-TAN Office\Data\` | Baza, nastavitve, dokumenti, skladišče | **Ohrani** | Izbriši (po potrditvi) | Ponastavi (po potrditvi) |
| `%ProgramData%\JU-TAN Office\Logs\` | Dnevniki | Ohrani | Izbriši | Ponastavi |
| `%ProgramData%\JU-TAN Office\Backup\` | Varnostne kopije | Ohrani | Izbriši **samo** če uporabnik izrecno označi | **Ohrani** (nova kopija se lahko doda) |
| `%ProgramData%\JU-TAN Office\Temp\` | Začasne datoteke | Ohrani | Izbriši | Ponastavi |
| `%ProgramData%\JU-TAN Office\Reports\` | Poročila / izvoz v JU-TAN mapi | Ohrani | Izbriši | Ponastavi |
| `C:\Program Files\JU-TAN Office\` | Program, bližnjice | Izbriši | Izbriši | Se zamenja |
| `%LocalAppData%\JU-TAN\Office\` | Spletna aktivacija / vezava naprave | **Ohrani** | **Ohrani** | **Ohrani** |

## Prenosni / razvojni način

| Lokacija | Vsebina |
| --- | --- |
| `<mapa_programa>\data\` | Baza in nastavitve |
| `<mapa_programa>\Backup\` | Varnostne kopije |
| `<mapa_programa>\Logs\` | Dnevniki |
| `<mapa_programa>\Reports\` | Poročila |
| `<mapa_programa>\Temp\` | Začasne datoteke |

## Licenca (ločeno od poslovnih podatkov)

- **Spletna aktivacija naprave:** `%LocalAppData%\JU-TAN\Office\license.json` (DPAPI).
- Ob standardni odstranitvi, ponovni namestitvi in čisti namestitvi se **ne** briše.
- Namen: ponovna namestitev **ne** porabi novega sedeža naprave, če je aktivacija še veljavna.
- Stara lokalna metapodatkovna datoteka `Data\license.json` (če obstaja) se ob čisti / popolni odstranitvi lahko zbriše; to **ni** spletna aktivacija.

## Kaj namestitev nikoli ne kopira

- Razvojne / demo baze (`ju_tan_demo.db`, `warehouse_demo.json`)
- Produkcijske / testne poslovne baze iz razvijalskega okolja
- Vzorčna podjetja, stranke, artikle, račune

Nova baza nastane iz sheme aplikacije ob prvem zagonu (prazen poslovni prostor).

## Načini namestitve

1. **Prva namestitev** (ni starih podatkov) — običajna čista namestitev.
2. **Nadgradi / ponovno namesti in ohrani podatke** — privzeto ob obstoječih podatkih; varnostna kopija pred nadgradnjo.
3. **Nova čista namestitev** — samo po izrecni izbiri + potrditvi; priporočena varnostna kopija pred izbrisom.

## Načini odstranitve

1. **Odstrani program** — program in bližnjice; poslovni podatki ostanejo.
2. **Popolnoma odstrani … in vse podatke** — po močni potrditvi; varnostne kopije samo, če uporabnik izrecno potrdi.

Tiha odstranitev (`/SILENT`) vedno pomeni **standardno** odstranitev (ohrani podatke).
