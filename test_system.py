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

    # -------------------------------------------------------------
    # Community Experiences & Interactive Map Automated Verification
    # -------------------------------------------------------------

    # 9. Create Community Report with Approximate Location
    report_payload = {
        "title": "E-Commerce Refusal to Replace Defective Electronics under Warranty",
        "topic": "Consumer Dispute",
        "description": "Purchased an LED television that failed within 10 days of delivery. Authorized service center confirmed manufacturing panel defect. Seller refused replacement citing 7-day return policy. Preparing e-Daakhil filing for deficiency of service under Consumer Protection Act 2019.",
        "approx_location_name": "Indiranagar, Bengaluru, Karnataka",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "incident_date": "2026-10-14",
        "is_public": True,
        "session_id": session_id
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/community/reports",
        headers={"Content-Type": "application/json"},
        data=json.dumps(report_payload).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_create_rep = json.loads(resp.read().decode("utf-8"))
    print(f"[9] Create Community Report with Location: status={res_create_rep['success']}")
    created_rep = res_create_rep["report"]
    print(f"    id={created_rep['id']}, lat={created_rep['latitude']}, lon={created_rep['longitude']}, locality={created_rep['approx_location_name']}")
    assert res_create_rep["success"] is True
    assert created_rep["latitude"] == 12.9784
    assert created_rep["longitude"] == 77.6408
    assert created_rep["is_public"] is True

    # 10. Fetch Reports and Verify Marker Data & Allegation Notice
    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports")
    with urllib.request.urlopen(req) as resp:
        res_feed = json.loads(resp.read().decode("utf-8"))
    print(f"[10] Fetch Community Reports Feed & Markers: count={res_feed['count']}")
    print(f"     Allegation Safety Notice: {res_feed['allegation_notice'][:80]}...")
    assert res_feed["success"] is True
    assert len(res_feed["reports"]) > 0
    # Verify our created report is returned with valid coordinates
    found_rep = next((r for r in res_feed["reports"] if r["id"] == created_rep["id"]), None)
    assert found_rep is not None
    assert found_rep["latitude"] == 12.9784
    assert found_rep["longitude"] == 77.6408
    assert "allegation_disclaimer" in found_rep

    # 11. Create Report Without Location (Unmapped Report)
    unmapped_payload = {
        "title": "Unfair Bank Charges Deducted Without Advance SMS Notification",
        "topic": "Consumer Dispute",
        "description": "Bank deducted recurring monthly SMS alert charges and balance maintenance fees without providing advance electronic statement or consent. Registered complaint on RBI CMS portal.",
        "approx_location_name": None,
        "latitude": None,
        "longitude": None,
        "incident_date": "2026-10-12",
        "is_public": True,
        "session_id": session_id
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/community/reports",
        headers={"Content-Type": "application/json"},
        data=json.dumps(unmapped_payload).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_unmapped = json.loads(resp.read().decode("utf-8"))
    print(f"[11] Create Report Without Location: id={res_unmapped['report']['id']}, lat={res_unmapped['report']['latitude']}")
    assert res_unmapped["success"] is True
    assert res_unmapped["report"]["latitude"] is None
    assert res_unmapped["report"]["longitude"] is None

    # 12. Server-side Safety: Unpublished Drafts NEVER appear on Public Map
    draft_payload = {
        "title": "Private Draft Incident - Defamatory Threat over Social Media",
        "topic": "Cyber Fraud & Scams",
        "description": "Private draft notes for ongoing cyber bullying consultation, not yet ready for public view.",
        "approx_location_name": "Mumbai, Maharashtra",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "is_public": False,
        "session_id": session_id
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/community/reports",
        headers={"Content-Type": "application/json"},
        data=json.dumps(draft_payload).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_draft = json.loads(resp.read().decode("utf-8"))
    draft_id = res_draft["report"]["id"]
    print(f"[12] Create Private Draft Report: id={draft_id}, is_public={res_draft['report']['is_public']}")

    # Verify that public feed strictly DOES NOT contain this draft report
    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports")
    with urllib.request.urlopen(req) as resp:
        res_public_feed = json.loads(resp.read().decode("utf-8"))
    assert not any(r["id"] == draft_id for r in res_public_feed["reports"])
    print("     Verified: Private draft report is strictly excluded from public map feed.")

    # 13. Single Report Details & Access Control
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/community/reports/{created_rep['id']}")
    with urllib.request.urlopen(req) as resp:
        res_single = json.loads(resp.read().decode("utf-8"))
    print(f"[13] Single Report Detail: title={res_single['report']['title'][:50]}...")
    assert res_single["success"] is True
    assert res_single["report"]["id"] == created_rep["id"]

    # Trying to fetch private report as an unauthorized third party should 404
    try:
        req_unauth = urllib.request.Request(f"http://127.0.0.1:8000/api/community/reports/{draft_id}?session_id=stranger-session-uuid")
        with urllib.request.urlopen(req_unauth) as resp:
            pass
        assert False, "Should have raised HTTP 404 for unauthorized draft report"
    except urllib.error.HTTPError as e:
        assert e.code == 404
        print(f"     Verified: Unauthorized access to private report returns HTTP 404.")

    # 14. Synchronized Filter Queries (Topic and Mapped Only)
    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports?topic=Consumer+Dispute")
    with urllib.request.urlopen(req) as resp:
        res_topic_filtered = json.loads(resp.read().decode("utf-8"))
    print(f"[14] Topic Filter: matching 'Consumer Dispute' count={res_topic_filtered['count']}")
    for r in res_topic_filtered["reports"]:
        assert r["topic"].lower() == "consumer dispute"

    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports?has_location_only=true")
    with urllib.request.urlopen(req) as resp:
        res_mapped_filtered = json.loads(resp.read().decode("utf-8"))
    print(f"     Mapped Only Filter: count={res_mapped_filtered['count']}")
    for r in res_mapped_filtered["reports"]:
        assert r["latitude"] is not None and r["longitude"] is not None

    # 15. Private Evidence Vault Management & Separation from Public Map
    vault_payload = {
        "session_id": session_id,
        "title": "Private Rent Agreement Copy & Security Deposit Cheque Counterfoil",
        "item_type": "Contract Agreement",
        "description": "Original registered leave and license agreement with clause 14 specifying ₹50,000 refundable deposit within 7 days of vacation.",
        "approx_location": "Flat 304, Palm Heights, Pune (Private Location Note)"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/vault/items",
        headers={"Content-Type": "application/json"},
        data=json.dumps(vault_payload).encode("utf-8")
    )
    with urllib.request.urlopen(req) as resp:
        res_vault_create = json.loads(resp.read().decode("utf-8"))
    print(f"[15] Create Private Evidence Vault Item: id={res_vault_create['item']['id']}")
    vault_item_id = res_vault_create["item"]["id"]
    assert res_vault_create["success"] is True

    # Fetch vault items for this session
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/vault/items?session_id={session_id}")
    with urllib.request.urlopen(req) as resp:
        res_vault_list = json.loads(resp.read().decode("utf-8"))
    assert res_vault_list["count"] >= 1
    assert any(i["id"] == vault_item_id for i in res_vault_list["items"])

    # Strict isolation: another session gets 0 items
    req_other = urllib.request.Request("http://127.0.0.1:8000/api/vault/items?session_id=completely-different-session")
    with urllib.request.urlopen(req_other) as resp:
        res_vault_other = json.loads(resp.read().decode("utf-8"))
    assert res_vault_other["count"] == 0
    print("     Verified: Evidence Vault items are strictly isolated per session UUID.")

    # Strict separation: public community reports NEVER contain the private vault title or private location
    req_pub = urllib.request.Request("http://127.0.0.1:8000/api/community/reports")
    with urllib.request.urlopen(req_pub) as resp:
        res_pub_check = json.loads(resp.read().decode("utf-8"))
    for pub in res_pub_check["reports"]:
        assert "Palm Heights" not in (pub.get("approx_location_name") or "")
        assert "Security Deposit Cheque Counterfoil" not in pub["title"]
    print("     Verified: Private Evidence Vault records NEVER appear on public map or feed.")

    # Clean up vault item
    req_del = urllib.request.Request(
        f"http://127.0.0.1:8000/api/vault/items/{vault_item_id}?session_id={session_id}",
        method="DELETE"
    )
    with urllib.request.urlopen(req_del) as resp:
        res_del = json.loads(resp.read().decode("utf-8"))
    assert res_del["success"] is True
    print("     Verified: Vault item deletion succeeds.")

    print("\n>>> ALL 15 END-TO-END VERIFICATION & COMMUNITY MAP TESTS PASSED SUCCESSFULLY! <<<")


if __name__ == "__main__":
    run_tests()

