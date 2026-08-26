"""
Seeds a small but coherent topic/content graph so the demo has something
to click through immediately: two subjects, a couple of topics each with
a real prerequisite chain, and 3 content items (video/text/practice) per
topic so infer_preferred_format() always has something to recommend.
"""
from .database import SessionLocal, engine, Base
from . import models


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Topic).count() > 0:
            print("Already seeded, skipping.")
            return

        topics_data = [
            {"name": "Fractions", "subject": "Math", "prerequisites": ""},
            {"name": "Linear Equations", "subject": "Math", "prerequisites": "Fractions"},
            {"name": "Photosynthesis", "subject": "Science", "prerequisites": ""},
            {"name": "Cellular Respiration", "subject": "Science", "prerequisites": "Photosynthesis"},
        ]
        topics = {}
        for t in topics_data:
            topic = models.Topic(**t)
            db.add(topic)
            db.flush()
            topics[t["name"]] = topic

        content_data = [
            # Fractions
            ("Fractions", "video", 0.3, "Visualising fractions with pizza slices"),
            ("Fractions", "text", 0.3, "Analogy: fractions as sharing a chocolate bar"),
            ("Fractions", "practice", 0.4, "5 fraction addition problems"),
            # Linear Equations
            ("Linear Equations", "video", 0.4, "Balancing equations like a see-saw"),
            ("Linear Equations", "text", 0.4, "Analogy: solving for x as undoing steps"),
            ("Linear Equations", "practice", 0.5, "5 one-variable equations to solve"),
            # Photosynthesis
            ("Photosynthesis", "video", 0.3, "How leaves make food: animated walkthrough"),
            ("Photosynthesis", "text", 0.3, "Analogy: a leaf as a solar-powered kitchen"),
            ("Photosynthesis", "practice", 0.4, "Label the photosynthesis diagram"),
            # Cellular Respiration
            ("Cellular Respiration", "video", 0.4, "Mitochondria: the cell's power plant"),
            ("Cellular Respiration", "text", 0.4, "Analogy: respiration as burning fuel"),
            ("Cellular Respiration", "practice", 0.5, "Compare respiration vs photosynthesis quiz"),
        ]
        for topic_name, fmt, diff, title in content_data:
            db.add(
                models.Content(
                    topic_id=topics[topic_name].id,
                    title=title,
                    format=fmt,
                    difficulty=diff,
                    body=f"Static fallback content for '{title}'.",
                )
            )

        db.commit()
        print(f"Seeded {len(topics_data)} topics and {len(content_data)} content items.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
