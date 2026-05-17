from collections import Counter


MOOD_SCORE = {
    "happy": 9,
    "calm": 8,
    "neutral": 5,
    "sad": 3,
    "angry": 2,
    "fear": 2,
    "stress": 3,
}


def calculate_average_mood(
    emotions
):

    if not emotions:
        return 5.0

    values = [
        MOOD_SCORE.get(e, 5)
        for e in emotions
    ]

    return round(
        sum(values) / len(values),
        2
    )


def dominant_emotion(
    emotions
):

    if not emotions:
        return "neutral"

    counter = Counter(emotions)

    return counter.most_common(1)[0][0]