"""Generate one HTML email signature per row of the employee CSV.

Usage: python3 scripts/generate_signatures.py employees.csv [output_dir]

The CSV uses the Google Sheet headers: Name, Job position, Phone,
Phone extension, email, whatsapp, web, Photo URL.
"""
import csv
import html
import re
import sys
import unicodedata
from pathlib import Path

PHOTO = (
    '      <img style="border-radius: 50%; margin-bottom:10px;" src="{url}" width="100" alt="{name}"><br>\n'
)
JOB = (
    '      <span style="font-size:14px;">\n'
    '        {job}\n'
    '      </span><br>\n'
)
PHONE = (
    '      <span style="font-size:13px"><img src="https://i.imgur.com/ozzs17h.png" width="13" alt=""> '
    '<a style="color:inherit; text-decoration:none;" href="tel:{href}">{text}</a></span>\n'
    '      <br>\n'
)
WHATSAPP = (
    '      <span style="font-size:13px"><img src="https://i.imgur.com/hFxYYzd.png" width="13" alt=""> '
    '<a style="color:inherit; text-decoration:none;" href="https://wa.me/34{digits}">{text}</a></span>\n'
    '      <br>\n'
)

TEMPLATE = """<table width="300" style="font-family:Tahoma, sans-serif;">
  <tr>
    <td style="padding-right:50px;padding-top:10px;vertical-align:top;width:180px;">
      <img src="https://i.imgur.com/SSdSv0V.png" width="150" alt="Protegim"><br>
{photo}      <span style="font-size:14px; font-weight:bold;{name_style}">
        {name}
      </span><br>
{job}      <br>
{phone}{whatsapp}      <span style="font-size:13px"><img src="https://i.imgur.com/7OiO7Qw.png" width="13" alt=""> <a style="color:inherit; text-decoration:none;" href="mailto:{email}">{email}</a></span>
      <br>
      <span style="font-size:13px"><a style="color:#ED6E1C; font-weight:600; text-decoration:none;" href="https://protegim.cat/">{web}</a></span>
      <br><br>
      <a href="https://protegim.cat/opinions-protegim/">
        <img src="https://i.imgur.com/UZ59ZRO.png" width="230" alt="Opinions Protegim"><br>
      </a>
    </td>
  </tr>
</table>
<span style="background:white;font-family:Tahoma;font-size:12px;color:#979797;"><br><br>La informació de contacte que ens faciliti serà tractada per ISP Grup i les seves empreses col·laboradores amb la finalitat d’oferir-li informació comercial dels serveis sol·licitats i enviar-li comunicacions sobre ofertes, beneficis i serveis i informacions complementàries al seu servei.
  La seva informació de servei, serà tractada en exclusiva per ISP Grup, i compartida, en cas necessari, amb el fabricant Ajax Systems i la central receptora d’alarmes, amb l’única finalitat de donar-li el servei contractat i resoldre les seves peticions.
  En qualsevol moment podrà indicar la revocació del consentiment atorgat, o exercir els seus drets d’ARCO adreçant-se a ISP Grup Carrer Mas Pujol 36B | 08520 | Les Franqueses del Vallès | Barcelona o en legal@ispgrup.cat
  Per a més informació visiti el web <a style="color:inherit;" href="https://www.protegim.cat">www.protegim.cat</a></span>
"""


def clean(value):
    return re.sub(r"\s+", " ", (value or "")).strip().rstrip(".")


def digits(value):
    return re.sub(r"\D", "", value or "")


def pretty(number):
    return " ".join(number[i:i + 3] for i in range(0, len(number), 3))


def slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("'", "")).strip("-")


def render(row):
    name = clean(row["Name"])
    job = clean(row["Job position"])
    phone = digits(row["Phone"])
    ext = digits(row["Phone extension"])
    whatsapp = digits(row["whatsapp"])
    photo = clean(row["Photo URL"])
    e = html.escape

    phone_html = ""
    if phone:
        phone_text = pretty(phone) + (f" – Ext. {ext}" if ext else "")
        phone_href = phone + (f",{ext}" if ext else "")
        phone_html = PHONE.format(href=phone_href, text=e(phone_text))

    return TEMPLATE.format(
        photo=PHOTO.format(url=e(photo), name=e(name)) if photo else "",
        name=e(name),
        # Signatures without a photo (departments, some people) get space below the logo.
        name_style="" if photo else " display:inline-block; margin-top:20px;",
        job=JOB.format(job=e(job)) if job else "",
        phone=phone_html,
        whatsapp=WHATSAPP.format(digits=whatsapp, text=pretty(whatsapp)) if whatsapp else "",
        email=e(clean(row["email"])),
        web=e(clean(row["web"]) or "www.protegim.cat"),
    )


def main():
    source = Path(sys.argv[1])
    out_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "signatures")
    out_dir.mkdir(parents=True, exist_ok=True)
    used = set()
    with source.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name, job = clean(row["Name"]), clean(row["Job position"])
            if not name:
                continue
            if job and not clean(row["Photo URL"]):
                print(f"no photo: {name} ({job})", file=sys.stderr)
            base = slug(f"{name} {job}")
            filename, n = base, 2
            while filename in used:
                filename, n = f"{base}-{n}", n + 1
            used.add(filename)
            (out_dir / f"{filename}.html").write_text(render(row), encoding="utf-8")
            print(f"{out_dir / filename}.html")


if __name__ == "__main__":
    main()
