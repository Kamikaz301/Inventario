"""
============================================================================
inject.py — Script de referencia de la depuración del Excel (no lo usa la app)
============================================================================
Qué hizo:
  Inyectó las hojas nuevas (Inventario, Compras, Revisar) dentro del paquete
  .xlsx ORIGINAL, sin regenerar el archivo con openpyxl (eso dañaba el Excel).
  Las partes originales quedan intactas; solo cambian los índices que deben
  listar las hojas nuevas (workbook.xml, rels, Content_Types, app.xml).

Depende de: Python 3 y openpyxl (solo para leer el libro con las hojas nuevas).
Uso: python inject.py ORIGINAL.xlsx HOJAS_NUEVAS.xlsx SALIDA.xlsx

Ojo: tiene valores fijos del archivo de 2026 (sheet12 = Hoja1, rId12, rId16 =
calcChain, sheet8 = Tommy). Para reutilizarlo hay que revisarlos primero.
============================================================================
"""
import sys, os, re, shutil, zipfile, tempfile, datetime
from xml.sax.saxutils import escape
import openpyxl
from openpyxl.utils import get_column_letter

ORIG, NEWSRC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
tmp = tempfile.mkdtemp()
with zipfile.ZipFile(ORIG) as z:
    z.extractall(tmp)
    orig_order = z.namelist()
P = lambda *a: os.path.join(tmp, *a)
rd = lambda p: open(P(p), encoding='utf-8').read()
def wr(p, s): open(P(p), 'w', encoding='utf-8').write(s)

# ---------------- estilos: se agregan los que necesitan las hojas nuevas ----------------
st = rd('xl/styles.xml')
def bump(tag, s, add):
    m = re.search(r'<%s count="(\d+)"' % tag, s)
    n = int(m.group(1))
    s = s.replace(m.group(0), '<%s count="%d"' % (tag, n + add), 1)
    return s, n
st, _ = bump('numFmts', st, 1)
st = st.replace('</numFmts>', '<numFmt numFmtId="200" formatCode="&quot;$&quot;#,##0.00"/></numFmts>', 1)
st, font_hdr = bump('fonts', st, 1)
st = st.replace('</fonts>', '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/><scheme val="minor"/></font></fonts>', 1)
st, fill_hdr = bump('fills', st, 1)
st = st.replace('</fills>', '<fill><patternFill patternType="solid"><fgColor rgb="FF1F2937"/><bgColor indexed="64"/></patternFill></fill></fills>', 1)
new_xfs = [
    f'<xf numFmtId="0" fontId="{font_hdr}" fillId="{fill_hdr}" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>',
    '<xf numFmtId="200" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>',
    '<xf numFmtId="14" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>',
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>',
]
st, xf0 = bump('cellXfs', st, len(new_xfs))
st = st.replace('</cellXfs>', ''.join(new_xfs) + '</cellXfs>', 1)
S_HDR, S_MONEY, S_DATE, S_WRAP = xf0, xf0 + 1, xf0 + 2, xf0 + 3
wr('xl/styles.xml', st)

# ---------------- textos compartidos ----------------
sst = rd('xl/sharedStrings.xml')
m = re.search(r'<sst [^>]*count="(\d+)" uniqueCount="(\d+)"', sst)
count, uniq = int(m.group(1)), int(m.group(2))
existing = {}
for i, si in enumerate(re.findall(r'<si>(.*?)</si>', sst, re.S)):
    mm = re.fullmatch(r'<t(?: xml:space="preserve")?>(.*?)</t>', si, re.S)
    if mm: existing.setdefault(mm.group(1), i)
added = []
def sidx(text):
    global count
    key = escape(text)
    count += 1
    if key not in existing:
        existing[key] = uniq + len(added); added.append(key)
    return existing[key]

# ---------------- XML de cada hoja nueva, a partir del libro armado con openpyxl ----------------
src = openpyxl.load_workbook(NEWSRC)
SPEC = {
    'Inventario': dict(money={5, 6, 7, 12, 13}, date=set(), wrap=set(), freeze='C2'),
    'Compras': dict(money={7, 8, 9, 10, 12, 13}, date={5}, wrap=set(), freeze='C2'),
    'Revisar': dict(money=set(), date=set(), wrap={3, 4, 5, 6}, freeze='A2'),
}
EPOCH = datetime.datetime(1899, 12, 30)

def sheet_xml(ws, spec, selected):
    nrow, ncol = ws.max_row, ws.max_column
    last = f'{get_column_letter(ncol)}{nrow}'
    cols = ''.join(f'<col min="{i}" max="{i}" width="{ws.column_dimensions[get_column_letter(i)].width}" customWidth="1"/>' for i in range(1, ncol + 1))
    rows = []
    for r in range(1, nrow + 1):
        cells = []
        for c in range(1, ncol + 1):
            v = ws.cell(r, c).value
            ref = f'{get_column_letter(c)}{r}'
            s = S_HDR if r == 1 else (S_MONEY if c in spec['money'] else S_DATE if c in spec['date'] else S_WRAP if c in spec['wrap'] else 0)
            sa = f' s="{s}"' if s else ''
            if v is None:
                if s: cells.append(f'<c r="{ref}"{sa}/>')
                continue
            if isinstance(v, str) and v.startswith('='):
                cells.append(f'<c r="{ref}"{sa}><f>{escape(v[1:])}</f></c>')
            elif isinstance(v, str):
                cells.append(f'<c r="{ref}"{sa} t="s"><v>{sidx(v)}</v></c>')
            elif isinstance(v, (datetime.datetime, datetime.date)):
                d = datetime.datetime(v.year, v.month, v.day)
                cells.append(f'<c r="{ref}"{sa}><v>{(d - EPOCH).days}</v></c>')
            elif isinstance(v, bool):
                cells.append(f'<c r="{ref}"{sa} t="b"><v>{int(v)}</v></c>')
            else:
                cells.append(f'<c r="{ref}"{sa}><v>{repr(float(v)) if isinstance(v, float) else v}</v></c>')
        ht = ' ht="32" customHeight="1"' if r == 1 else ''
        rows.append(f'<row r="{r}"{ht}>{"".join(cells)}</row>')
    fz = spec['freeze']
    if fz == 'C2':
        pane = ('<pane xSplit="2" ySplit="1" topLeftCell="C2" activePane="bottomRight" state="frozen"/>'
                '<selection pane="topRight" activeCell="C1" sqref="C1"/><selection pane="bottomLeft" activeCell="A2" sqref="A2"/>'
                '<selection pane="bottomRight" activeCell="C2" sqref="C2"/>')
    else:
        pane = '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/><selection pane="bottomLeft" activeCell="A2" sqref="A2"/>'
    tab = ' tabSelected="1"' if selected else ''
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheetPr><tabColor rgb="FF1F2937"/></sheetPr>'
            f'<dimension ref="A1:{last}"/>'
            f'<sheetViews><sheetView{tab} workbookViewId="0">{pane}</sheetView></sheetViews>'
            '<sheetFormatPr defaultRowHeight="15"/>'
            f'<cols>{cols}</cols><sheetData>{"".join(rows)}</sheetData>'
            f'<autoFilter ref="A1:{last}"/>'
            '<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>'
            '</worksheet>'), last

new = [('Inventario', 'sheet13.xml', 'rId17', 18), ('Compras', 'sheet14.xml', 'rId18', 19), ('Revisar', 'sheet15.xml', 'rId19', 20)]
ranges = {}
for name, fname, rid, sid in new:
    xml, last = sheet_xml(src[name], SPEC[name], name == 'Inventario')
    wr(f'xl/worksheets/{fname}', xml)
    ranges[name] = last

# cerrar textos compartidos
sst = re.sub(r'count="\d+" uniqueCount="\d+"', f'count="{count}" uniqueCount="{uniq + len(added)}"', sst, 1)
sst = sst.replace('</sst>', ''.join(f'<si><t xml:space="preserve">{t}</t></si>' for t in added) + '</sst>')
wr('xl/sharedStrings.xml', sst)

# ---------------- workbook.xml ----------------
wb = rd('xl/workbook.xml')
wb = wb.replace('<sheet name="Hoja1" sheetId="15" r:id="rId12"/>', '')
first = ''.join(f'<sheet name="{n}" sheetId="{sid}" r:id="{rid}"/>' for n, f, rid, sid in new)
wb = wb.replace('<sheets>', '<sheets>' + first, 1)
wb = re.sub(r'firstSheet="\d+" activeTab="\d+"', 'firstSheet="0" activeTab="0"', wb)
dn = ''.join(f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">{n}!$A$1:${re.match(r"([A-Z]+)(\d+)", ranges[n]).group(1)}${re.match(r"([A-Z]+)(\d+)", ranges[n]).group(2)}</definedName>' for i, (n, *_r) in enumerate(new))
assert '<definedNames>' not in wb
wb = wb.replace('</sheets>', '</sheets><definedNames>' + dn + '</definedNames>', 1)
wb = wb.replace('<calcPr calcId="191029"/>', '<calcPr calcId="191029" fullCalcOnLoad="1"/>')
assert 'fullCalcOnLoad' in wb and 'Hoja1' not in wb
wr('xl/workbook.xml', wb)

# ---------------- rels / content types / quitar Hoja1 y calcChain ----------------
rels = rd('xl/_rels/workbook.xml.rels')
rels = re.sub(r'<Relationship Id="rId12" [^>]*/>', '', rels)
rels = re.sub(r'<Relationship Id="rId16" [^>]*calcChain[^>]*/>', '', rels)
assert 'sheet12.xml' not in rels and 'calcChain' not in rels
rels = rels.replace('</Relationships>', ''.join(
    f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/{f}"/>'
    for n, f, rid, sid in new) + '</Relationships>')
wr('xl/_rels/workbook.xml.rels', rels)

ct = rd('[Content_Types].xml')
ct = ct.replace('<Override PartName="/xl/worksheets/sheet12.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>', '')
ct = ct.replace('<Override PartName="/xl/calcChain.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>', '')
assert 'sheet12.xml' not in ct and 'calcChain' not in ct
ct = ct.replace('</Types>', ''.join(
    f'<Override PartName="/xl/worksheets/{f}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    for n, f, rid, sid in new) + '</Types>')
wr('[Content_Types].xml', ct)
os.remove(P('xl/worksheets/sheet12.xml')); os.remove(P('xl/calcChain.xml'))

# La hoja de Tommy era la pestaña seleccionada; ahora solo debe estarlo Inventario
s8 = rd('xl/worksheets/sheet8.xml')
assert s8.count('tabSelected="1"') == 1
wr('xl/worksheets/sheet8.xml', s8.replace(' tabSelected="1"', '', 1))

# lista de hojas en app.xml
app = rd('docProps/app.xml')
names = [n for n, *_ in new] + re.findall(r'<sheet name="([^"]+)"', rd('xl/workbook.xml'))[3:]
app = re.sub(r'<vt:i4>12</vt:i4>', f'<vt:i4>{len(names)}</vt:i4>', app)
app = re.sub(r'<TitlesOfParts>.*</TitlesOfParts>',
             '<TitlesOfParts><vt:vector size="%d" baseType="lpstr">%s</vt:vector></TitlesOfParts>' % (len(names), ''.join(f'<vt:lpstr>{escape(n)}</vt:lpstr>' for n in names)), app)
wr('docProps/app.xml', app)

# ---------------- empaquetar ----------------
parts = [p for p in orig_order if p not in ('xl/worksheets/sheet12.xml', 'xl/calcChain.xml')]
parts += [f'xl/worksheets/{f}' for n, f, rid, sid in new]
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for p in parts:
        z.write(P(p), p)
shutil.rmtree(tmp)
print('ok', OUT, 'strings added', len(added))
