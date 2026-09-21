# Politika zasebnosti — JU-TAN Office Enterprise

**Izdajatelj:** JU-TAN Studio  
**Izdelek:** JU-TAN Office Enterprise  
**Različica dokumenta:** 1.0  
**Datum:** 2026-09-21  
**Stik:** support@ju-tan.com · https://www.ju-tan.com

Ta dokument opisuje, kako JU-TAN Office obravnava osebne in poslovne podatke pri lokalni namizni uporabi programa.

## 1. Upravitelj in namen

JU-TAN Studio je proizvajalec programske opreme. Za podatke, ki jih vnesete v aplikacijo (stranke, dokumenti, zaloga, uporabniki), ste **vi (vaše podjetje)** upravitelj osebnih podatkov v smislu GDPR / ZVOP-2.

Program je namenjen notranji poslovni rabi: vodenje strank, dokumentov, zaloge, poročil in povezanih evidenc.

## 2. Kje so podatki shranjeni

- Poslovna baza, dokumenti, varnostne kopije, dnevniki in izvoz so shranjeni **lokalno** na vaši napravi ali v mapah, ki jih določite ob namestitvi (npr. ProgramData / prenosna mapa).
- JU-TAN Studio **ne gosti** vaše poslovne baze in nima samodejnega dostopa do vsebine vaših dokumentov.

## 3. Katere podatke aplikacija obdeluje

Odvisno od vaše uporabe lahko aplikacija hrani:

- podatke podjetja (naziv, naslov, davčna številka, kontakt),
- podatke strank, dobaviteljev in stikov,
- poslovne dokumente (ponudbe, naročila, računi, plačila),
- artikle, zalogo in povezane evidence,
- lokalne uporabniške račune, vloge in dnevnike dogodkov (audit),
- nastavitve aplikacije in morebitne šifrirane skrivnosti (npr. SMTP),
- podatke o licenci / napravi, potrebne za aktivacijo in preverjanje licence.

Gesla so shranjena kot kriptografski hash; skrivnosti so zaščitene lokalno (npr. strojni ključ / DPAPI na Windows).

## 4. Prenosi in omrežje

- Osebni in poslovni podatki iz baze **se ne pošiljajo** na strežnike JU-TAN Studio zaradi vsakodnevnega dela.
- Omrežni klici so omejeni na funkcije, ki jih omogočite ali zahteva izdelek, na primer:
  - aktivacija / preverjanje licence,
  - morebitno preverjanje posodobitev (če je kanal nastavljen),
  - vaša lastna konfiguracija (npr. e-pošta SMTP).
- Pri preverjanju licence se lahko izmenjajo tehnični identifikatorji naprave in podatki o licenci — ne vsebina vaših poslovnih dokumentov.

## 5. Hramba in brisanje

- Trajanje hrambe določate vi v skladu z računovodskimi in davčnimi obveznostmi.
- Odstranitev programa (uninstall) **ne zbriše** baze, varnostnih kopij in dokumentov v podatkovnih mapah.
- Za izbris ali izvoz podatkov uporabite funkcije v Nastavitvah (varnostne kopije / izvoz) ali se obrnite na svojega skrbnika IT. Celovit GDPR paket izvoza/brisanja se lahko dopolni v prihodnjih izdajah.

## 6. Varnost

- Lokalna SQLite baza z zaščito dostopa na nivoju sistema Windows in aplikacije (prijava, vloge RBAC, audit).
- Priporočamo šifriranje diska, omejen dostop do delovnih postaj in redne varnostne kopije.
- Podrobnosti: glejte `docs/SECURITY.md` in `docs/ADMIN_GUIDE.md`.

## 7. Obdelovalci

JU-TAN Studio kot proizvajalec ne deluje kot obdelovalec vaše poslovne baze. Če uporabljate zunanje storitve (e-pošta, gostovanje datotek), za te poskrbite ločeno v skladu z njihovimi pogoji.

## 8. Pravice posameznikov

Če ste upravitelj podatkov in prejmete zahtevo posameznika (vpogled, popravek, izbris, prenosljivost), jo izpolnite z orodji v aplikaciji in svojo notranjo politiko. Za tehnično pomoč pri lokalnem izvozu se lahko obrnete na support@ju-tan.com.

## 9. Spremembe

Posodobitve te politike bodo objavljene v dokumentaciji izdelka in/ali na https://www.ju-tan.com. Nadaljnja uporaba po posodobitvi pomeni seznanjenost z novo različico.

## 10. Kontakt

**JU-TAN Studio**  
E-pošta: support@ju-tan.com  
Splet: https://www.ju-tan.com

---

*Ta dokument je informativna politika zasebnosti za lokalni namizni izdelek in ne nadomešča pravnega svetovanja. Za posebne pogodbene ureditve se obrnite na JU-TAN Studio.*
