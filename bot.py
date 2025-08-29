import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image
from docx import Document
from reportlab.pdfgen import canvas

TOKEN = os.getenv("BOT_TOKEN")  # Bot token from Render environment

# --- DOCX to PDF (simple text extraction) ---
def doc_to_pdf(docx_path, pdf_path):
    doc = Document(docx_path)
    c = canvas.Canvas(pdf_path)
    text = c.beginText(40, 800)
    # very simple text-only export (no images/layout)
    for para in doc.paragraphs:
        for line in para.text.split("\n"):
            text.textLine(line)
        text.textLine("")  # blank line between paragraphs
        if text.getY() < 60:
            c.drawText(text)
            c.showPage()
            text = c.beginText(40, 800)
    c.drawText(text)
    c.save()

# --- Image to PDF (single image -> single page) ---
def image_to_pdf(image_path, pdf_path):
    image = Image.open(image_path).convert("RGB")
    image.save(pdf_path, "PDF", resolution=100.0)

# --- /start command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a DOC/DOCX or an image (JPG/PNG). I’ll convert it to a PDF and send it back!")

# --- Handle file uploads ---
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc_msg = update.message.document
    photo_msg = update.message.photo

    os.makedirs("downloads", exist_ok=True)

    # If user sent a photo (Telegram treats camera images as photos)
    if photo_msg:
        tfile = await photo_msg[-1].get_file()
        input_path = "downloads/input_image.jpg"
        output_path = "downloads/output.pdf"
        await tfile.download_to_drive(input_path)
        try:
            image_to_pdf(input_path, output_path)
            await update.message.reply_document(document=open(output_path, "rb"), filename="converted.pdf")
        except Exception as e:
            await update.message.reply_text(f"❌ Error converting image: {e}")
        return

    # If user sent a document (docx/jpg/png as document)
    if doc_msg:
        tfile = await doc_msg.get_file()
        file_name = doc_msg.file_name or "upload"
        input_path = f"downloads/{file_name}"
        output_path = "downloads/output.pdf"
        await tfile.download_to_drive(input_path)

        try:
            fn = file_name.lower()
            if fn.endswith((".doc", ".docx")):
                doc_to_pdf(input_path, output_path)
            elif fn.endswith((".jpg", ".jpeg", ".png")):
                image_to_pdf(input_path, output_path)
            else:
                await update.message.reply_text("⚠️ Supported types: DOC/DOCX, JPG, PNG.")
                return

            await update.message.reply_document(document=open(output_path, "rb"), filename="converted.pdf")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
        return

    await update.message.reply_text("⚠️ Please send a DOC/DOCX or an image (JPG/PNG).")

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is not set. Add it in Render (Environment Variables).")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
    print("✅ Bot is running…")
    app.run_polling()

if __name__ == "__main__":
    main()
