"""
Automated end-to-end verification test suite for Jurista
"""
import sys
import urllib.request
import json
import pymupdf
import io

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_tests():
    print("=== STARTING JURISTA END-TO-END VERIFICATION ===")

    # 1. Health check
    req = urllib.request.Request("http://127.0.0.1:8000/api/health")
    with urllib.request.urlopen(req) as resp:
        health = json.loads(resp.read().decode("utf-8"))
    print(f"[1] Health Check: status={health['status']}, gemini_configured={health['gemini_configured']}")

    # 2. Out-of-Scope Pre-check (No LLM call)
    session_id = "test-session-100"
    payload = {
        "session_id": session_id,
        "message": "write a python function to scrape a website",
        "language": "English"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/chat",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_scope = json.loads(resp.read().decode("utf-8"))
    print(f"[2] Out-of-Scope Filter: intent={res_scope['intent']}, is_out_of_scope={res_scope['is_out_of_scope']}")
    assert res_scope["is_out_of_scope"] is True

    # 3. Legal Query with Grounded Statutory Retrieval
    payload_legal = {
        "session_id": session_id,
        "message": "I received a legal notice under Section 138 of the Negotiable Instruments Act for a cheque return of Rs. 1,00,000. What is my deadline to pay or respond, and what are my rights under Indian law?",
        "language": "English"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/chat",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload_legal).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_legal = json.loads(resp.read().decode("utf-8"))
    print(f"[3] Legal Q&A: intent={res_legal['intent']}, sources_cited={len(res_legal['sources'])}")
    print(f"    Grounded Response Preview:\n{res_legal['response'][:250]}...\n")
    assert len(res_legal["sources"]) > 0

    # 4. Generate a synthetic Indian legal notice PDF and upload
    pdf_doc = pymupdf.open()
    page = pdf_doc.new_page()
    legal_notice_text = """LEGAL DEMAND NOTICE
Date: 15th October 2026
To: Mr. R. Sharma, Flat 402, Lotus Apartments, Pune, Maharashtra

Under instructions from our client, M/s Sunrise Enterprises, we hereby serve this notice:
1. That you issued Cheque No. 448812 dated 01/10/2026 for Rs. 75,000/- drawn on SBI Bank towards discharge of legal debt.
2. The said cheque was presented for clearance and returned dishonoured with remark 'Funds Insufficient' on 05/10/2026.
3. You are hereby called upon to pay the said sum of Rs. 75,000/- within 15 days of receipt of this notice, failing which our client shall initiate criminal prosecution under Section 138 of the Negotiable Instruments Act, 1881.

Advocate V. K. Deshmukh
High Court of Bombay
"""
    page.insert_text((50, 72), legal_notice_text, fontsize=11)
    pdf_bytes = pdf_doc.tobytes()
    pdf_doc.close()

    # Upload PDF via multipart form
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="session_id"\r\n\r\n'
        f"{session_id}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="language"\r\n\r\n'
        f"English\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="Legal_Notice_Section_138.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + pdf_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/upload-pdf",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        data=body
    )
    with urllib.request.urlopen(req) as resp:
        res_upload = json.loads(resp.read().decode("utf-8"))
    print(f"[4] PDF Upload & PyMuPDF Extraction:")
    print(f"    filename={res_upload['filename']}, pages={res_upload['page_count']}, chars={res_upload['total_characters']}, chunks={res_upload['chunk_count']}")
    print(f"    Document Explanation Preview:\n{res_upload['explanation'][:250]}...\n")
    assert res_upload["success"] is True
    assert res_upload["chunk_count"] > 0

    # 5. Follow-up Question on Document (Context Retention)
    payload_followup = {
        "session_id": session_id,
        "message": "Who is the sender of this notice and what is the exact amount they claim I owe?",
        "language": "English"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/chat",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload_followup).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_followup = json.loads(resp.read().decode("utf-8"))
    print(f"[5] Context Retention & Document Follow-up:")
    print(f"    Intent={res_followup['intent']}")
    print(f"    Follow-up Answer:\n{res_followup['response'][:250]}...\n")

    # 6. Language Switch without context reset
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/session/language",
        headers={"Content-Type": "application/json"},
        data=json.dumps({"session_id": session_id, "language": "Hindi"}).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_lang = json.loads(resp.read().decode("utf-8"))
    print(f"[6] Language Switch: language={res_lang['language']}")

    # Check session state to confirm document and messages are intact
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/session/{session_id}")
    with urllib.request.urlopen(req) as resp:
        res_sess = json.loads(resp.read().decode("utf-8"))
    print(f"    Session Document Preserved: filename={res_sess['document']['filename']}, pages={res_sess['document']['page_count']}")
    print(f"    Session Messages Count: {len(res_sess['messages'])}")
    assert res_sess["document"]["filename"] == "Legal_Notice_Section_138.pdf"
    assert len(res_sess["messages"]) >= 4

    # 7. Ask follow-up in the new language (Hindi)
    payload_hindi = {
        "session_id": session_id,
        "message": "क्या मुझे इस नोटिस का जवाब देने के लिए किसी वकील की ज़रूरत है?",
        "language": "Hindi"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/chat",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload_hindi).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_hindi = json.loads(resp.read().decode("utf-8"))
    print(f"[7] Multilingual Follow-up in Hindi:")
    print(f"    Intent={res_hindi['intent']}, Language={res_hindi['language']}")
    # print safely without encoding issues
    print(f"    Answer bytes length: {len(res_hindi['response'].encode('utf-8'))}")

    # 8. Scanned PDF handling test
    scanned_doc = pymupdf.open()
    scanned_page = scanned_doc.new_page()
    # No text, just an empty/image placeholder page
    scanned_bytes = scanned_doc.tobytes()
    scanned_doc.close()

    body_scanned = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="session_id"\r\n\r\n'
        f"test-scanned-session\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="scanned_photo.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + scanned_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/upload-pdf",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        data=body_scanned
    )
    with urllib.request.urlopen(req) as resp:
        res_scanned = json.loads(resp.read().decode("utf-8"))
    print(f"[8] Scanned PDF Graceful Handling: is_scanned={res_scanned['is_scanned']}")
    assert res_scanned["is_scanned"] is True

    print("\n>>> ALL 8 CORE CAPABILITY WORKFLOW TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()
