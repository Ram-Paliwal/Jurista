"""
Focused Automated Verification Test Suite for Community Experiences,
Interactive Map Data Contract, and Private Evidence Vault
"""
import sys
import json
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_community_tests():
    print("=== STARTING COMMUNITY EXPERIENCES & MAP VERIFICATION ===")
    session_id = "test-community-session-999"

    # 1. Health check
    req = urllib.request.Request("http://127.0.0.1:8000/api/health")
    with urllib.request.urlopen(req) as resp:
        health = json.loads(resp.read().decode("utf-8"))
    print(f"[1] Server Health: status={health['status']}")
    assert health["status"] == "healthy"

    # 2. Create Community Report with Approximate Location
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
    print(f"[2] Create Community Report with Location: status={res_create_rep['success']}")
    created_rep = res_create_rep["report"]
    print(f"    id={created_rep['id']}, lat={created_rep['latitude']}, lon={created_rep['longitude']}, locality={created_rep['approx_location_name']}")
    assert res_create_rep["success"] is True
    assert created_rep["latitude"] == 12.9784
    assert created_rep["longitude"] == 77.6408
    assert created_rep["is_public"] is True

    # 3. Fetch Reports and Verify Marker Data & Allegation Notice
    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports")
    with urllib.request.urlopen(req) as resp:
        res_feed = json.loads(resp.read().decode("utf-8"))
    print(f"[3] Fetch Community Reports Feed & Markers: count={res_feed['count']}")
    print(f"    Allegation Safety Notice: {res_feed['allegation_notice'][:75]}...")
    assert res_feed["success"] is True
    assert len(res_feed["reports"]) > 0
    found_rep = next((r for r in res_feed["reports"] if r["id"] == created_rep["id"]), None)
    assert found_rep is not None
    assert found_rep["latitude"] == 12.9784
    assert found_rep["longitude"] == 77.6408
    assert "allegation_disclaimer" in found_rep

    # 4. Create Report Without Location (Unmapped Report)
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
    print(f"[4] Create Report Without Location: id={res_unmapped['report']['id']}, lat={res_unmapped['report']['latitude']}")
    assert res_unmapped["success"] is True
    assert res_unmapped["report"]["latitude"] is None
    assert res_unmapped["report"]["longitude"] is None

    # 5. Server-side Safety: Unpublished Drafts NEVER appear on Public Map
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
    print(f"[5] Create Private Draft Report: id={draft_id}, is_public={res_draft['report']['is_public']}")

    # Verify that public feed strictly DOES NOT contain this draft report
    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports")
    with urllib.request.urlopen(req) as resp:
        res_public_feed = json.loads(resp.read().decode("utf-8"))
    assert not any(r["id"] == draft_id for r in res_public_feed["reports"])
    print("    Verified: Private draft report is strictly excluded from public map feed.")

    # 6. Single Report Details & Access Control
    req = urllib.request.Request(f"http://127.0.0.1:8000/api/community/reports/{created_rep['id']}")
    with urllib.request.urlopen(req) as resp:
        res_single = json.loads(resp.read().decode("utf-8"))
    print(f"[6] Single Report Detail: title={res_single['report']['title'][:50]}...")
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
        print(f"    Verified: Unauthorized access to private report returns HTTP 404.")

    # 7. Synchronized Filter Queries (Topic and Mapped Only)
    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports?topic=Consumer+Dispute")
    with urllib.request.urlopen(req) as resp:
        res_topic_filtered = json.loads(resp.read().decode("utf-8"))
    print(f"[7] Topic Filter: matching 'Consumer Dispute' count={res_topic_filtered['count']}")
    for r in res_topic_filtered["reports"]:
        assert r["topic"].lower() == "consumer dispute"

    req = urllib.request.Request("http://127.0.0.1:8000/api/community/reports?has_location_only=true")
    with urllib.request.urlopen(req) as resp:
        res_mapped_filtered = json.loads(resp.read().decode("utf-8"))
    print(f"    Mapped Only Filter: count={res_mapped_filtered['count']}")
    for r in res_mapped_filtered["reports"]:
        assert r["latitude"] is not None and r["longitude"] is not None

    # 8. Coordinate Validation (Invalid Lat/Lon rejection)
    bad_payload = {
        "title": "Invalid Lat Coordinate Test Report",
        "topic": "Consumer Dispute",
        "description": "Testing that out-of-range coordinates are rejected with HTTP 422.",
        "latitude": 150.0, # invalid latitude > 90
        "longitude": 75.0,
        "is_public": True,
        "session_id": session_id
    }
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8000/api/community/reports",
            headers={"Content-Type": "application/json"},
            data=json.dumps(bad_payload).encode("utf-8")
        )
        with urllib.request.urlopen(req) as resp:
            pass
        assert False, "Should have rejected latitude > 90"
    except urllib.error.HTTPError as e:
        assert e.code in (400, 422)
        print(f"[8] Coordinate Validation: Out-of-bounds latitude correctly rejected with HTTP {e.code}.")

    # 9. Private Evidence Vault Management & Separation from Public Map
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
    print(f"[9] Create Private Evidence Vault Item: id={res_vault_create['item']['id']}")
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
    print("    Verified: Evidence Vault items are strictly isolated per session UUID.")

    # Strict separation: public community reports NEVER contain the private vault title or private location
    req_pub = urllib.request.Request("http://127.0.0.1:8000/api/community/reports")
    with urllib.request.urlopen(req_pub) as resp:
        res_pub_check = json.loads(resp.read().decode("utf-8"))
    for pub in res_pub_check["reports"]:
        assert "Palm Heights" not in (pub.get("approx_location_name") or "")
        assert "Security Deposit Cheque Counterfoil" not in pub["title"]
    print("    Verified: Private Evidence Vault records NEVER appear on public map or feed.")

    # Clean up vault item
    req_del = urllib.request.Request(
        f"http://127.0.0.1:8000/api/vault/items/{vault_item_id}?session_id={session_id}",
        method="DELETE"
    )
    with urllib.request.urlopen(req_del) as resp:
        res_del = json.loads(resp.read().decode("utf-8"))
    assert res_del["success"] is True
    print("    Verified: Vault item deletion succeeds.")

    print("\n>>> ALL 9 COMMUNITY MAP & EVIDENCE VAULT TESTS PASSED! <<<")

if __name__ == "__main__":
    run_community_tests()
