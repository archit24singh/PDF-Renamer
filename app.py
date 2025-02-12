import re
import io
import zipfile
from flask import Flask, request, send_file, render_template_string
from PyPDF2 import PdfReader

app = Flask(__name__)

# Updated HTML template with Tailwind CSS for a professional look
UPLOAD_FORM = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PDF Renamer</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
  <div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold text-center mb-6">PDF Renamer</h1>
    <div class="bg-white p-6 rounded shadow-md max-w-md mx-auto">
      <form method="post" action="/" enctype="multipart/form-data" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700">Select PDF Files</label>
          <input type="file" name="files" multiple class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
        </div>
        <div>
          <input type="submit" value="Upload and Process" class="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none">
        </div>
      </form>
    </div>
  </div>
</body>
</html>
"""

def extract_info_from_pdf(file_stream):
    """
    Extracts the required information from a PDF file stream.
    
    Expected PDF text layout (based on your sample):
      - The first nonempty line is the full name (e.g., "ELBERT W. ROBINSON").
        We take the last word as the last name.
      - Somewhere in the text, "Date of Birth:" is followed by a date in mm/dd/yyyy format.
        We extract only the year.
      - Two phone numbers appear. We ignore the first phone number and use the full phone
        number from the second phone number.
    
    Returns:
        A tuple (lastname, birth_year, full_phone) if all are found; otherwise, (None, None, None).
    """
    try:
        reader = PdfReader(file_stream)
        text = ""
        # Extract text from all pages.
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        print("----- Extracted Text from PDF -----")
        print(text)
        print("----- End of Extracted Text -----")
    except Exception as e:
        print("Error reading PDF:", e)
        return None, None, None

    # --- Extract Last Name ---
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        name_line = lines[0]
        parts = name_line.split()
        lastname = parts[-1] if parts else None
    else:
        lastname = None

    # --- Extract Date of Birth ---
    dob_match = re.search(r"Date of Birth:\s*(\d{2}/\d{2}/\d{4})", text)
    dob = dob_match.group(1) if dob_match else None
    birth_year = None
    if dob:
        birth_year = dob.split('/')[-1]

    # --- Extract Phone Number (using the second occurrence) ---
    phone_matches = re.findall(r'(\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{4})', text)
    if len(phone_matches) >= 2:
        phone_raw = phone_matches[1]
        full_phone = re.sub(r'\D', '', phone_raw)
    else:
        full_phone = None

    print("Extracted Data:")
    print("Last Name:", lastname)
    print("DOB:", dob)
    print("Birth Year:", birth_year)
    print("Full Phone:", full_phone)

    if lastname and birth_year and full_phone:
        return lastname, birth_year, full_phone
    else:
        print("Failed to extract all required fields from PDF.")
        return None, None, None

@app.route("/", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        log_messages = []
        
        # Create separate in-memory ZIPs:
        # 1. For renamed PDF files.
        pdf_memory = io.BytesIO()
        with zipfile.ZipFile(pdf_memory, 'w', zipfile.ZIP_DEFLATED) as pdf_zip:
            files = request.files.getlist("files")
            if not files:
                msg = "No files uploaded."
                print(msg)
                log_messages.append(msg)
            for file in files:
                if file and file.filename.lower().endswith(".pdf"):
                    msg = f"Processing file: {file.filename}"
                    print(msg)
                    log_messages.append(msg)
                    file_bytes = file.read()
                    pdf_stream = io.BytesIO(file_bytes)
                    
                    lastname, birth_year, full_phone = extract_info_from_pdf(pdf_stream)
                    if lastname and birth_year and full_phone:
                        new_filename = f"{lastname.lower()}_{birth_year}_{full_phone}.pdf"
                        msg = f"Renaming file to: {new_filename}"
                        print(msg)
                        log_messages.append(msg)
                        pdf_zip.writestr(new_filename, file_bytes)
                    else:
                        msg = f"Skipping file {file.filename} due to extraction failure."
                        print(msg)
                        log_messages.append(msg)
        pdf_memory.seek(0)

        # 2. For the log file (as its own ZIP)
        log_memory = io.BytesIO()
        with zipfile.ZipFile(log_memory, 'w', zipfile.ZIP_DEFLATED) as log_zip:
            log_report = "\n".join(log_messages)
            log_zip.writestr("log_report.txt", log_report)
        log_memory.seek(0)

        # 3. Create a combined ZIP file that contains both the renamed PDFs ZIP and the log ZIP.
        combined_memory = io.BytesIO()
        with zipfile.ZipFile(combined_memory, 'w', zipfile.ZIP_DEFLATED) as combined_zip:
            combined_zip.writestr("renamed_pdfs.zip", pdf_memory.getvalue())
            combined_zip.writestr("log_report.zip", log_memory.getvalue())
        combined_memory.seek(0)

        return send_file(combined_memory, download_name="combined_files.zip", as_attachment=True)
    return render_template_string(UPLOAD_FORM)

if __name__ == "__main__":
    app.run(debug=True)
