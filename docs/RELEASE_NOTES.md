# Release Notes — JU-TAN Office Enterprise 1.0.0 GOLD

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

Program se odstrani; baza, backupi in dokumenti ostanejo v ProgramData.
