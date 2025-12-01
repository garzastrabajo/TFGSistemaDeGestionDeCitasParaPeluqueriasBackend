from typing import Dict, Any

def update_barber_rating(barber_id: int, db: Dict[str, Any]) -> None:
    reviews = [r for r in db["reviews"] if r["barberId"] == barber_id]
    if not reviews:
        return
    avg = round(sum(r["rating"] for r in reviews) / len(reviews), 2)
    for b in db["barbers"]:
        if b["id"] == barber_id:
            b["ratingAverage"] = avg
            b["totalReviews"] = len(reviews)
            break