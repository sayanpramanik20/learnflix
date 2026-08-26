"""
End-to-end demo script -- run this once the server is up to rehearse (or
sanity-check) the full flow without clicking through Swagger UI manually.

Usage:
    uvicorn app.main:app --reload   # in one terminal
    python demo.py                   # in another

Walks through: create student -> simulate struggling on "Fractions" ->
get a recommendation -> get an AI-generated explanation -> check the
dashboard -> answer correctly a few times -> see mastery rise on the
dashboard.
"""
import time
import requests

BASE = "http://127.0.0.1:8000"


def main():
    # 1. Create a student
    r = requests.post(f"{BASE}/students", json={"name": "Aarav", "grade": "8"})
    r.raise_for_status()
    student = r.json()
    print(f"Created student: {student}\n")
    sid = student["id"]

    # 2. Find the "Fractions" topic and its practice content
    topics = requests.get(f"{BASE}/topics").json()
    fractions = next(t for t in topics if t["name"] == "Fractions")
    contents = requests.get(f"{BASE}/topics/{fractions['id']}/contents").json()
    practice = next(c for c in contents if c["format"] == "practice")

    # 3. Simulate the student struggling: two wrong answers in a row
    for _ in range(2):
        resp = requests.post(
            f"{BASE}/interact",
            json={
                "student_id": sid,
                "content_id": practice["id"],
                "correct": False,
                "time_taken_seconds": 45,
                "rewinds": 0,
            },
        ).json()
        print("Logged wrong attempt ->", resp)

    # 4. Ask for a recommendation -- should now favour "practice" format
    rec = requests.get(f"{BASE}/recommend/{sid}").json()
    print(f"\nRecommendation after struggling: {rec}\n")

    # 5. Get a Gemini-generated explanation personalised to this student
    explain = requests.post(
        f"{BASE}/explain", json={"student_id": sid, "topic_id": fractions["id"]}
    ).json()
    print(f"AI explanation ({explain['style_used']} style):\n{explain['explanation']}\n")

    # 6. Answer correctly a few times, watch mastery climb
    for _ in range(4):
        resp = requests.post(
            f"{BASE}/interact",
            json={
                "student_id": sid,
                "content_id": practice["id"],
                "correct": True,
                "time_taken_seconds": 20,
                "rewinds": 0,
            },
        ).json()
        print("Logged correct attempt -> p_know:", resp["p_know_after"])
        time.sleep(0.1)

    # 7. Dashboard view (what a teacher/parent would see)
    dash = requests.get(f"{BASE}/dashboard/{sid}").json()
    print(f"\nDashboard: {dash}")


if __name__ == "__main__":
    main()
