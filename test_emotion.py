"""
test_emotion.py  –  Improved emotion detection test
Improvements:
  - CLAHE preprocessing for better detection in any lighting
  - Wider Haar-cascade params to catch more face sizes/angles
  - Smoothed emotion display (rolling average over last N frames)
  - Graceful FER → DeepFace fallback chain (same as app.py)
  - No new library dependencies (cv2, numpy already required)
"""
import cv2
import numpy as np
import time
from collections import deque


# ── Camera Selection ──────────────────────────────────────────────────────────

def _select_camera() -> int:
    """
    Scans all available camera devices (indices 0-4) and lets the user
    pick one by number. Works with:
      - Built-in laptop webcam        (usually index 0)
      - Windows Phone Link            (shows phone camera as a virtual webcam)
      - DroidCam / EpocCam / Camo     (virtual webcam apps)
      - Any USB camera

    No new libraries required — uses only OpenCV's VideoCapture probing.
    """
    print("\n📷  Scanning for available cameras...")
    available = []
    for idx in range(5):  # check indices 0-4
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)  # CAP_DSHOW = faster on Windows
        if cap.isOpened():
            ret, _ = cap.read()          # confirm it can actually deliver a frame
            if ret:
                available.append(idx)
            cap.release()

    if not available:
        print("❌ No cameras found at all. Check your connections.")
        return 0

    if len(available) == 1:
        print(f"✅ Only one camera found (index {available[0]}) — using it.")
        return available[0]

    # Multiple cameras found — let the user choose
    print(f"\n✅ Found {len(available)} camera(s):\n")
    labels = {
        0: "Built-in laptop webcam",
        1: "External / Phone Link / DroidCam",
        2: "External / Phone Link / DroidCam",
        3: "External camera",
        4: "External camera",
    }
    for i, idx in enumerate(available):
        hint = labels.get(idx, "Camera")
        print(f"  {i + 1}: Camera index {idx}  —  {hint}")

    print()
    while True:
        choice = input(f"Choose camera [1-{len(available)}, default=1]: ").strip()
        if choice == "" or choice == "1":
            chosen = available[0]
            break
        if choice.isdigit() and 1 <= int(choice) <= len(available):
            chosen = available[int(choice) - 1]
            break
        print(f"   Please enter a number between 1 and {len(available)}.")

    print(f"✅ Using camera index {chosen}")
    return chosen

# ── Preprocessing ────────────────────────────────────────────────────────────

def preprocess_frame(frame):
    """
    Apply CLAHE on the L channel (LAB space) to normalise brightness.
    Dramatically improves detection under dim, harsh, or uneven lighting.
    Returns an enhanced BGR frame AND a grey version for Haar.
    """
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced_bgr = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
    enhanced_gray = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2GRAY)
    return enhanced_bgr, enhanced_gray


# ── Haar face detector (quick pre-filter) ────────────────────────────────────

def load_haar():
    try:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cc = cv2.CascadeClassifier(path)
        if cc.empty():
            return None
        return cc
    except Exception:
        return None


def detect_faces_haar(gray, cascade):
    """
    More permissive params than default → catches more face sizes/positions.
    Returns list of (x, y, w, h) tuples.
    """
    if cascade is None:
        return []
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.05,
        minNeighbors=3,
        minSize=(24, 24),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return faces if len(faces) > 0 else []


# ── Emotion smoothing ─────────────────────────────────────────────────────────

class EmotionSmoother:
    """Rolling average of raw score dicts over the last `window` frames."""
    EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral", "contempt"]

    def __init__(self, window=5):
        self.window = window
        self.history = deque(maxlen=window)

    def update(self, scores: dict) -> dict:
        norm = {e: float(scores.get(e, 0.0)) for e in self.EMOTIONS}
        self.history.append(norm)
        avg = {}
        for e in self.EMOTIONS:
            avg[e] = sum(f[e] for f in self.history) / len(self.history)
        return avg

    def top(self, scores: dict) -> tuple:
        top_e = max(scores, key=scores.get)
        return top_e, scores[top_e]


# ── FER backend ───────────────────────────────────────────────────────────────

def run_fer(smoother, haar):
    from fer import FER
    detector = FER(mtcnn=True)
    print("✅ FER loaded (MTCNN face detector)")
    cap = cv2.VideoCapture(_select_camera())
    if not cap.isOpened():
        print("❌ Cannot open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Testing emotion detection (FER)… Press 'q' to quit.")
    fps_t = time.time()
    fps_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        enhanced, gray = preprocess_frame(frame)

        haar_faces = detect_faces_haar(gray, haar)
        for (x, y, w, h) in haar_faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 200, 0), 1)

        rgb = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
        results = detector.detect_emotions(rgb)

        if results:
            # ── Limit to the single largest detected face ──
            best = max(results, key=lambda r: r["box"][2] * r["box"][3])
            box = best["box"]
            x, y, w, h = box

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            raw = best["emotions"]
            smoothed = smoother.update(raw)
            top_e, top_s = smoother.top(smoothed)

            cv2.putText(frame, f"{top_e}: {top_s:.2f}",
                        (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            bar_x = 10
            for i, (emo, val) in enumerate(sorted(smoothed.items(), key=lambda kv: -kv[1])):
                bar_w = int(val * 150)
                cv2.rectangle(frame, (bar_x, 10 + i * 22), (bar_x + bar_w, 28 + i * 22),
                              (0, 180, 100), -1)
                cv2.putText(frame, f"{emo[:7]} {val:.2f}",
                            (bar_x + bar_w + 4, 26 + i * 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        else:
            cv2.putText(frame, "No face detected", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        fps_count += 1
        elapsed = time.time() - fps_t
        if elapsed >= 1.0:
            fps = fps_count / elapsed
            fps_count = 0
            fps_t = time.time()
        else:
            fps = fps_count / max(elapsed, 0.001)
        cv2.putText(frame, f"FPS: {fps:.1f}  Backend: FER+MTCNN  [Enhanced lighting]",
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (180, 180, 255), 1)

        cv2.imshow("Emotion Test — NeuroSense", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ── DeepFace backend ──────────────────────────────────────────────────────────

def run_deepface(smoother, haar):
    from deepface import DeepFace
    print("✅ DeepFace loaded")
    cap = cv2.VideoCapture(_select_camera())
    if not cap.isOpened():
        print("❌ Cannot open camera.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Testing emotion detection (DeepFace)… Press 'q' to quit.")
    fps_t = time.time()
    fps_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        enhanced, gray = preprocess_frame(frame)
        haar_faces = detect_faces_haar(gray, haar)

        # ── Limit to the single largest Haar face ──
        if len(haar_faces) > 1:
            haar_faces = [max(haar_faces, key=lambda f: f[2] * f[3])]

        try:
            result = DeepFace.analyze(
                enhanced,
                actions=["emotion"],
                enforce_detection=False,
                detector_backend="opencv",
                silent=True,
            )
            if isinstance(result, list):
                result = result[0]

            for (x, y, w, h) in haar_faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            raw = result["emotion"]
            smoothed = smoother.update(raw)
            top_e, top_s = smoother.top(smoothed)

            cv2.putText(frame, f"{top_e}: {top_s:.2f}",
                        (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            bar_x = 10
            for i, (emo, val) in enumerate(sorted(smoothed.items(), key=lambda kv: -kv[1])):
                bar_w = int(val * 150)
                cv2.rectangle(frame, (bar_x, 55 + i * 22), (bar_x + bar_w, 73 + i * 22),
                              (0, 180, 100), -1)
                cv2.putText(frame, f"{emo[:7]} {val:.2f}",
                            (bar_x + bar_w + 4, 71 + i * 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        except Exception as e:
            cv2.putText(frame, f"Error: {e}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        fps_count += 1
        elapsed = time.time() - fps_t
        fps = fps_count / max(elapsed, 0.001)
        if elapsed >= 1.0:
            fps_count = 0
            fps_t = time.time()
        cv2.putText(frame, f"FPS: {fps:.1f}  Backend: DeepFace  [Enhanced lighting]",
                    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (180, 180, 255), 1)

        cv2.imshow("Emotion Test — NeuroSense", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    smoother = EmotionSmoother(window=5)
    haar = load_haar()
    if haar:
        print("✅ Haar cascade loaded")
    else:
        print("⚠️  Haar cascade unavailable")

    try:
        run_fer(smoother, haar)
    except ImportError as e1:
        print(f"⚠️  FER not available: {e1}")
        try:
            run_deepface(smoother, haar)
        except ImportError as e2:
            print(f"❌ DeepFace also not available: {e2}")
            print("Install at least one backend:  pip install fer  OR  pip install deepface")
    except Exception as e:
        print(f"❌ FER runtime error: {e}")
        print("Falling back to DeepFace...")
        try:
            run_deepface(smoother, haar)
        except Exception as e2:
            print(f"❌ DeepFace also failed: {e2}")
