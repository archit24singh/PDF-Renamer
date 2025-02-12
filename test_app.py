import io
import unittest
from app import app  # Assumes your Flask app is defined in app.py

class BufferOverflowTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the Flask test client.
        self.app = app.test_client()
        self.app.testing = True

    def create_dummy_pdf(self, content: str):
        """
        Create a dummy PDF file in memory using a minimal PDF structure.
        This is a very basic PDF and is only intended for testing text extraction.
        """
        # Note: This minimal PDF structure may not work for all PDF parsers,
        # but it should be enough for PyPDF2 in many cases.
        pdf_data = (
            b"%PDF-1.4\n"
            b"1 0 obj\n"
            b"<< /Type /Catalog /Pages 2 0 R >>\n"
            b"endobj\n"
            b"2 0 obj\n"
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
            b"endobj\n"
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /Contents 4 0 R >>\n"
            b"endobj\n"
            b"4 0 obj\n"
            b"<< /Length " + str(len(content)).encode() + b" >>\n"
            b"stream\n" + content.encode() + b"\nendstream\n"
            b"endobj\n"
            b"xref\n"
            b"0 5\n"
            b"0000000000 65535 f \n"
            b"0000000010 00000 n \n"
            b"0000000053 00000 n \n"
            b"0000000102 00000 n \n"
            b"0000000178 00000 n \n"
            b"trailer\n"
            b"<< /Size 5 /Root 1 0 R >>\n"
            b"startxref\n"
            b"250\n"
            b"%%EOF"
        )
        return io.BytesIO(pdf_data)

    def test_single_valid_pdf(self):
        """Test uploading a single valid PDF with expected content."""
        content = (
            "ELBERT W. ROBINSON\n"
            "Some Address\n"
            "Some City, ST ZIP\n"
            "Date of Birth: 08/06/1972\n"
            "First Phone: 281-111-1111\n"
            "Second Phone: (832)882-4384\n"
        )
        dummy_pdf = self.create_dummy_pdf(content)
        data = {"files": (dummy_pdf, "test.pdf")}
        response = self.app.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        # Check that the returned data starts with the ZIP file signature "PK"
        self.assertTrue(response.data.startswith(b"PK"))

    def test_very_large_pdf(self):
        """Test uploading a very large PDF file to simulate resource stress."""
        # Create a very large content string (e.g., 1 million characters)
        large_content = (
            "ELBERT W. ROBINSON\n" +
            "A" * 1_000_000 + "\n" +
            "Date of Birth: 08/06/1972\n"
            "First Phone: 281-111-1111\n"
            "Second Phone: (832)882-4384\n"
        )
        dummy_pdf = self.create_dummy_pdf(large_content)
        data = {"files": (dummy_pdf, "large_test.pdf")}
        response = self.app.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        # Verify the response is a ZIP file by checking the PK header.
        self.assertTrue(response.data.startswith(b"PK"))

    def test_bulk_upload_many_small_files(self):
        """Test uploading many small PDF files (e.g., 500 files) at once."""
        files = []
        content = (
            "ELBERT W. ROBINSON\n"
            "Some Address\n"
            "Some City, ST ZIP\n"
            "Date of Birth: 08/06/1972\n"
            "First Phone: 281-111-1111\n"
            "Second Phone: (832)882-4384\n"
        )
        for i in range(500):
            dummy_pdf = self.create_dummy_pdf(content)
            files.append((dummy_pdf, f"test_{i}.pdf"))
        data = {"files": files}
        response = self.app.post("/", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        # Check that the response is a ZIP file (starts with the "PK" header)
        self.assertTrue(response.data.startswith(b"PK"))

if __name__ == "__main__":
    unittest.main()
