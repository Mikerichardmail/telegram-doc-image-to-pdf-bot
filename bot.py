import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from PIL import Image
from docx import Document
from reportlab.pdfgen import canvas

BOT_TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_URL = os.getenv("PUBLIC_URL")  # e.g. https://your-service.onrender.com
PORT = int(os.getenv("PORT", "10000"))  # Render sets PORT

def doc_to_pdf(docx_path, pdf_path):
    from docx import Document
    from reportlab.pdfgen import canvas
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
    await update.message.reply_text("👋 Send a DOC/DOCX or JPG/PNG — I’ll return a PDF.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    photos = update.message.photo
    os.makedirs("downloads", exist_ok=True)

    if photos:
        f = await photos[-1].get_file()
        in_path, out_path = "downloads/input.jpg", "downloads/output.pdf"
        await f.download_to_drive(in_path)
        try:
            image_to_pdf(in_path, out_path)
            await update.message.reply_document(open(out_path, "rb"), filename="converted.pdf")
        except Exception as e:
            await update.message.reply_text(f"❌ Image error: {e}")
        return

    if doc:
        f = await doc.get_file()
        name = (doc.file_name or "upload").lower()
        in_path, out_path = f"downloads/{name}", "downloads/output.pdf"
        await f.download_to_drive(in_path)
        try:
            if name.endswith((".doc", ".docx")):
                doc_to_pdf(in_path, out_path)
            elif name.endswith((".jpg", ".jpeg", ".png")):
                image_to_pdf(in_path, out_path)
            else:
                await update.message.reply_text("⚠️ Supported: DOC/DOCX, JPG, PNG.")
                return
            await update.message.reply_document(open(out_path, "rb"), filename="converted.pdf")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
        return

    await update.message.reply_text("⚠️ Send a file (DOC/DOCX/JPG/PNG).")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN missing")
    if not PUBLIC_URL:
        raise RuntimeError("PUBLIC_URL missing (Render web service URL)")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))

    # Use a secret path for the webhook
    webhook_path = f"/{BOT_TOKEN}"
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=webhook_path,
        webhook_url=f"{PUBLIC_URL}{webhook_path}",
    )

if __name__ == "__main__":
    main()
