import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image
from docx import Document
from reportlab.pdfgen import canvas

BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL")
PORT = int(os.getenv("PORT", "10000"))

def doc_to_pdf(docx_path, pdf_path):
    doc = Document(docx_path)
    c = canvas.Canvas(pdf_path)
    text = c.beginText(40, 800)
    for para in doc.paragraphs:
        for line in para.text.split("\n"):
            text.textLine(line)
        text.textLine("")
        if text.getY() < 60:
            c.drawText(text); c.showPage()
            text = c.beginText(40, 800)
    c.drawText(text); c.save()

def image_to_pdf(image_path, pdf_path):
    image = Image.open(image_path).convert("RGB")
    image.save(pdf_path, "PDF", resolution=100.0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a DOC/DOCX or JPG/PNG — I'll return a PDF.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    os.makedirs("downloads", exist_ok=True)
    if update.message.photo:
        f = await update.message.photo[-1].get_file()
        in_path, out_path = "downloads/input.jpg", "downloads/output.pdf"
        await f.download_to_drive(in_path)
        image_to_pdf(in_path, out_path)
        await update.message.reply_document(open(out_path, "rb"), filename="converted.pdf")
        return
    if update.message.document:
        doc = update.message.document
        f = await doc.get_file()
        name = (doc.file_name or "upload").lower()
        in_path, out_path = f"downloads/{name}", "downloads/output.pdf"
        await f.download_to_drive(in_path)
        if name.endswith((".doc", ".docx")):
            doc_to_pdf(in_path, out_path)
        elif name.endswith((".jpg", ".jpeg", ".png")):
            image_to_pdf(in_path, out_path)
        else:
            await update.message.reply_text("Supported: DOC/DOCX, JPG, PNG.")
            return
        await update.message.reply_document(open(out_path, "rb"), filename="converted.pdf")
        return
    await update.message.reply_text("Send a file (DOC/DOCX/JPG/PNG).")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing")
    if not PUBLIC_URL:
        raise RuntimeError("PUBLIC_URL missing (set to your Render web URL)")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
    webhook_path = f"/{BOT_TOKEN}"
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path,
        webhook_url=f"{PUBLIC_URL}{webhook_path}",
    )

if __name__ == "__main__":
    main()
