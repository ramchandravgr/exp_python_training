
invoice_data = [
    {"id": "INV-001", "amount": 1200, "status": "valid"},
    {"id": "INV-002", "amount": 5500, "status": "valid"},
    {},
    {"id": "INV-003", "amount": 850, "status": "valid"},
    {"id": "INV-004", "amount": 6200, "status": "valid"},
    {},
    {"id": "INV-005", "amount": 3100, "status": "valid"},
    {"id": "INV-006", "amount": 450, "status": "valid"},
    {"id": "INV-007", "amount": 7100, "status": "valid"},
    {},
    {
        "id": "INV-008",
        "amount": 0,
        "status": "corrupted",
        "error_token": "e=855N2575.3Z344b2",
    },
    {"id": "INV-009", "amount": 1500, "status": "valid"},
    {"id": "INV-010", "amount": 9300, "status": "valid"},
    {},
    {"id": "INV-011", "amount": 2200, "status": "valid"},
    {"id": "INV-012", "amount": 5050, "status": "valid"},
    {"id": "INV-013", "amount": 1300, "status": "valid"},
    {},
    {"id": "INV-014", "amount": 4100, "status": "valid"},
    {"id": "INV-015", "amount": 8000, "status": "valid"},
]

for data in invoice_data:
    invoiceid = data.get("id")
    if(not data.get("id")):
        continue
    elif(data.get("amount")>5000):
        print(f"Invoice id {invoiceid} have value greater than 5000")
    elif(data.get("status") != "valid"):
        print(f"Invalid Invoice id {invoiceid}. Got Corrupted status")
        break