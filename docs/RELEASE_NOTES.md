# 1.0.8 — 05-10-2026

- Opis artikla se prenese v postavko računa in shrani ob izdaji ter urejanju.
- Opis je mogoče prilagoditi ob dodajanju postavke.
- PDF izpiše naziv in večvrstični opis ter pravilno enoto mere.

# Release Notes — JU-TAN Office Enterprise 1.0.3 GOLD

Datum: 2026-09-28

## Popravek 1.0.3

- Dokumentni urejevalnik: primarni gumb »Dodaj postavko« je spet jasno viden; prazen stan postavk in usklajene kartice.
- PDF računov/ponudb: poravnane ikone kontakta, odstranjena kratka zelena ločilna črta in odvečni poudarek pri stranki, podpis »Tanja Hrup« / Direktor, premaknjen blok Podatki za plačilo.
- Temni način in hierarhija gumbov utrjena v urednikih dokumentov.
- Namestitev: obstoječi podatki → izbira med ohranitvijo in čisto namestitvijo (z varnostno kopijo).
- Odstranitev: »Odstrani program« ohrani podatke; »Popolna odstranitev« zahteva potrditev; varnostne kopije le po izrecni izbiri.
- Aktivacija naprave v LocalAppData se ohrani (brez novega sedeža ob ponovni namestitvi). Glej `docs/DATA_LOCATIONS.md`.

## Popravek 1.0.2

- Računi in ponudbe prikazujejo blok direktorjevega podpisa. Na računu ostane tudi, če UPN QR zaradi nepopolnih plačilnih podatkov ni mogoč.
- Veljavni računi še vedno vsebujejo UPN QR; slika lastnoročnega podpisa se doda v Nastavitve → PDF, če je na voljo.

## Popravek 1.0.1

- Odpravljen napačen uvoz ob odprtju modula Stranke; pogled se zdaj pravilno naloži.
- Posodobljena različica programa in namestitvenega paketa. Podatkovna shema ostaja 3; obstoječi podatki se ohranijo.

## Izdaja 1.0.0

Datum: 2026-09-12  
Status: **GOLD RELEASE**  
Build: Production / 64-bit / RELEASE

## Paket

- `JU-TAN-Office-Setup.exe` (Inno Setup, če je build stroj pripravljen)
- `JU-TAN-Office-Portable.zip`
- `Version.txt`, `LICENSE.txt`, `SHA256SUMS.txt` (generiran v `dist/` **po** Authenticode podpisu)
- `docs/PRIVACY.md`, `docs/INSTALL.md`, `docs/USER_GUIDE.md`, `docs/ADMIN_GUIDE.md`
- `docs/RELEASE_NOTES.md`, `docs/SECURITY.md`, `docs/SIGNING.md`
- `USER_GUIDE.pdf`, `ADMIN_GUIDE.pdf` (če obstajata)

## Podpisovanje

Razvojni/RC buildi ne zahtevajo certifikata. Produkcijski podpis: certifikat `CN=JU-TAN Studio` v `Cert:\CurrentUser\My` (ali `JU_TAN_PFX` kot fallback), nato `.\scripts\build_release.ps1 -RequireSigned` in `.\scripts\verify_release_signatures.ps1 -RequireSigned`. Glej `docs/SIGNING.md`.

## Vsebina 1.0

Prodaja (ponudbe, naročila, računi, plačila), stranke, artikli, skladišče, nabava, CRM, DMS, poročila, automation, varnost (RBAC, gesla, audit), installer, prvi zagon.

## Zahteve

Windows 10/11 x64. SQLite vgrajen. Ni .NET / SQL Server.

## Odstranitev

Ob odstranitvi izberete:

1. **Odstrani program** — program in bližnjice; poslovni podatki v `%ProgramData%\JU-TAN Office` ostanejo za morebitno ponovno namestitev.
2. **Popolnoma odstrani JU-TAN Office in vse podatke** — po močni potrditvi zbriše lokalne poslovne podatke. Lokalne varnostne kopije se brišejo le, če to izrecno potrdite.

Aktivacija naprave v `%LocalAppData%\JU-TAN\Office` se ohrani (da ponovna namestitev ne porabi novega sedeža).

Podrobnosti: `docs/DATA_LOCATIONS.md`.

