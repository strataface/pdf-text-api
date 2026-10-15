"""Generate our own sample PDFs (no third-party content). Requires reportlab (dev only) + Pillow + pypdf."""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter

# 1) text PDF, 2 pages, with a table and metadata
doc = SimpleDocTemplate("text_table.pdf", pagesize=A4, title="Sample Invoice", author="pdf-to-text tests")
ss = getSampleStyleSheet()
story = [Paragraph("Quarterly Report 2026", ss["Title"]), Paragraph("Revenue grew in every region during the third quarter.", ss["Normal"]), Spacer(1, 12),
         Table([["Region", "Q2", "Q3"], ["North", "120", "135"], ["South", "98", "110"]], style=[("GRID", (0, 0), (-1, -1), 0.5, "black")])]
from reportlab.platypus import PageBreak
story += [PageBreak(), Paragraph("Second page: notes and conclusions.", ss["Normal"])]
doc.build(story)

# 2) encrypted copy (user password "secret")
w = PdfWriter(clone_from=PdfReader("text_table.pdf")); w.encrypt("secret", algorithm="AES-256"); w.write("encrypted.pdf")

# 3) "scanned" PDF: an image-only page (no text layer)
img = Image.new("L", (1654, 2339), 255)  # A4 @ 200 dpi
d = ImageDraw.Draw(img)
try:
    f = ImageFont.truetype("DejaVuSans.ttf", 56)
except OSError:
    f = ImageFont.load_default(size=56)
for i, line in enumerate(["SCANNED DOCUMENT", "Invoice number 4711", "Total amount due: 250 EUR", "Thank you for your business."]):
    d.text((150, 200 + i * 120), line, fill=0, font=f)
img = img.rotate(0.7, fillcolor=255)  # slight skew like a real scan
img.save("scanned.pdf", "PDF", resolution=200)

# 4) not a PDF
open("not_a_pdf.pdf", "wb").write(b"<html>not a pdf</html>")

# 5) multilingual scanned page: Simplified Chinese + German (image only)
img = Image.new("L", (1654, 1000), 255)
d = ImageDraw.Draw(img)
try:
    zh = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 64)
except OSError:
    zh = None
if zh:
    d.text((150, 150), "发票号码 4711", fill=0, font=zh)
    d.text((150, 280), "应付总额 250 欧元", fill=0, font=zh)
    img.save("scanned_chi_sim.pdf", "PDF", resolution=200)
