from .db import get_db


def get_documents_by_vehicle(vehicle_id):
    conn = get_db()
    docs = conn.execute(
        "SELECT * FROM documents WHERE vehicle_id = ? ORDER BY uploaded_at DESC", (vehicle_id,)
    ).fetchall()
    conn.close()
    return docs


def get_document_by_id(doc_id):
    conn = get_db()
    doc = conn.execute(
        """SELECT d.*, v.user_id FROM documents d
           JOIN vehicles v ON d.vehicle_id = v.id WHERE d.id = ?""",
        (doc_id,),
    ).fetchone()
    conn.close()
    return doc


def create_document(vehicle_id, filename, original_name):
    conn = get_db()
    conn.execute(
        "INSERT INTO documents (vehicle_id, filename, original_name) VALUES (?, ?, ?)",
        (vehicle_id, filename, original_name),
    )
    conn.commit()
    conn.close()


def delete_document(doc_id):
    conn = get_db()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()


def count_documents_by_vehicle(vehicle_id):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM documents WHERE vehicle_id = ?", (vehicle_id,)
    ).fetchone()[0]
    conn.close()
    return count
