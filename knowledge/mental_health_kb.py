"""
===============================================================================
NeuroSense AI — Approved Mental Health Knowledge Base
===============================================================================

Purpose:
- Approved knowledge base for Knowledge Chat.
- Knowledge Chat answers only from this mental-health / NeuroSense AI scope.
- Helps reduce hallucinations because answers are grounded in controlled content.

Safety:
- No diagnosis
- No medicine prescription
- No psychiatrist impersonation
- Crisis escalation when needed
===============================================================================
"""

from typing import Dict, List, Any


KB_VERSION = "1.1.0"


MENTAL_HEALTH_KB: List[Dict[str, Any]] = [
    {
        "id": "scope_neurosense_ai",
        "title": "What NeuroSense AI Can and Cannot Do",
        "category": "neurosense_ai",
        "keywords": [
            "neurosense",
            "neurosense ai",
            "what can you do",
            "limitations",
            "mental health assistant",
            "assistant",
            "psychiatrist",
            "doctor",
            "diagnosis",
            "medicine",
        ],
        "content": """
NeuroSense AI is a supportive mental wellness assistant. It can help users reflect on emotions, understand stress patterns, generate safe coping suggestions, provide grounding exercises, guide wellbeing check-ins, explain reports, and suggest professional help when needed.

NeuroSense AI is not a psychiatrist, doctor, psychologist, emergency service, or replacement for licensed professional care. It must not diagnose mental disorders, prescribe medication, recommend medicine dosage, or tell users to start/stop medication.

If a user may be unsafe, at risk of self-harm, or in crisis, NeuroSense AI should encourage immediate human support, trusted people, local emergency services, and crisis helplines.
""",
        "safety_note": "Always state limitations when the user asks for diagnosis, medication, or professional-level decisions.",
    },
    {
        "id": "stress_basics",
        "title": "Stress Basics",
        "category": "stress",
        "keywords": [
            "stress",
            "stressed",
            "pressure",
            "overloaded",
            "burnout",
            "burned out",
            "tension",
            "workload",
            "mental pressure",
            "overwhelmed",
            "mentally exhausted",
            "drained",
        ],
        "content": """
Stress is the body's response to pressure, demand, uncertainty, or perceived threat. A small amount of stress can help with focus, but too much stress can affect sleep, concentration, mood, appetite, and energy.

Common signs of stress include racing thoughts, irritability, headache, body tension, difficulty sleeping, low motivation, and feeling emotionally overloaded.

Safe stress support steps include slow breathing, breaking tasks into smaller steps, taking short movement breaks, writing down priorities, reducing overstimulation, and talking to a trusted person.

If stress continues for many days, affects daily functioning, or feels unmanageable, speaking with a counsellor or mental health professional can help.
""",
        "safety_note": "Do not diagnose burnout or anxiety disorder. Use non-diagnostic language.",
    },
    {
        "id": "work_break_trip_support",
        "title": "Work Stress, Rest Breaks, Leave, and Short Trips",
        "category": "stress",
        "keywords": [
            "work stress",
            "office stress",
            "job stress",
            "leave work",
            "take leave",
            "take a break",
            "break from work",
            "trip",
            "vacation",
            "travel",
            "mentally tired",
            "mentally exhausted",
            "not feeling well mentally",
            "burnout",
            "burned out",
            "overwhelmed at work",
            "workload",
            "rest",
            "should i go",
            "should i take leave",
            "go for a trip",
        ],
        "content": """
When someone is not feeling well mentally, it can be helpful to pause and assess what kind of support they need. A short break, rest day, or planned trip may help if the person is mentally exhausted, overstimulated, or burned out. However, leaving work suddenly may create extra stress if there are urgent responsibilities, financial pressure, or unresolved work expectations.

A safer approach is to first check:
1. How intense the distress feels right now.
2. Whether the person feels safe.
3. Whether urgent work responsibilities can be handed over or delayed.
4. Whether a short rest, talking to someone, or taking planned leave would help.
5. Whether the person is using the trip to recover or to avoid a serious ongoing problem.

A trip can support wellbeing if it includes rest, sleep, reduced pressure, healthy routine, and emotional reflection. But if distress is severe, persistent, or includes unsafe thoughts, professional help or immediate human support is more important than travel.

NeuroSense AI should not make the decision for the user. It can help the user think through the decision safely and choose a balanced next step.
""",
        "safety_note": "Do not make major life/work decisions for the user. Help them assess safety, urgency, support, and professional-help needs.",
    },
    {
        "id": "anxiety_grounding",
        "title": "Anxiety-Like Feelings and Grounding",
        "category": "anxiety",
        "keywords": [
            "anxiety",
            "anxious",
            "panic",
            "fear",
            "nervous",
            "overthinking",
            "racing thoughts",
            "grounding",
            "breathing",
        ],
        "content": """
Anxiety-like feelings can include worry, fear, overthinking, restlessness, tight chest, fast heartbeat, or difficulty relaxing. These feelings do not automatically mean someone has an anxiety disorder.

Grounding helps bring attention back to the present moment. A simple grounding method is 5-4-3-2-1: notice 5 things you can see, 4 things you can feel, 3 things you can hear, 2 things you can smell, and 1 thing you can taste.

Box breathing can also help: breathe in for 4 seconds, hold for 4 seconds, breathe out for 4 seconds, and hold for 4 seconds. Repeat slowly.

If anxiety-like feelings are intense, frequent, or affecting daily life, it is better to speak with a licensed mental health professional.
""",
        "safety_note": "Do not say the user has anxiety disorder. Say anxiety-like feelings.",
    },
    {
        "id": "sleep_support",
        "title": "Sleep Support and Emotional Recovery",
        "category": "sleep",
        "keywords": [
            "sleep",
            "insomnia",
            "tired",
            "can't sleep",
            "sleep problem",
            "night",
            "wakeup",
            "fatigue",
            "rest",
        ],
        "content": """
Sleep and mental wellbeing are closely connected. Poor sleep can increase irritability, sadness, stress sensitivity, and difficulty focusing. Stress and overthinking can also make sleep harder.

Safe sleep support includes keeping a consistent sleep/wake time, reducing screen exposure before bed, avoiding heavy emotional problem-solving at night, writing tomorrow's tasks before bed, keeping the room calm, and using a short breathing exercise.

A sleep wind-down routine can include dim lights, slow breathing, journaling, stretching, and avoiding stimulating content close to bedtime.

If sleep problems continue, become severe, or interfere with daily functioning, the user should consult a qualified health professional.
""",
        "safety_note": "Do not recommend sleep medicines or dosages.",
    },
    {
        "id": "loneliness_support",
        "title": "Loneliness and Social Support",
        "category": "loneliness",
        "keywords": [
            "lonely",
            "alone",
            "isolated",
            "no friends",
            "social support",
            "connection",
            "ignored",
            "left out",
        ],
        "content": """
Loneliness is the feeling of lacking meaningful connection, even if people are physically around. It can affect mood, motivation, sleep, and self-worth.

Supportive steps include sending a small message to a trusted person, joining a safe community or group, creating a small routine that includes human contact, and practicing self-kindness rather than self-blame.

A simple message can be: "I am having a difficult day. Can we talk for a few minutes?" If talking feels hard, a text message or voice note may feel easier.

If loneliness becomes persistent or is connected with hopelessness or unsafe thoughts, professional support or a helpline can be helpful.
""",
        "safety_note": "Escalate if loneliness includes self-harm, hopelessness, or immediate danger.",
    },
    {
        "id": "academic_pressure",
        "title": "Academic Pressure and Exam Stress",
        "category": "academic_pressure",
        "keywords": [
            "exam",
            "study",
            "college",
            "assignment",
            "academic",
            "marks",
            "project",
            "deadline",
            "cgpa",
            "student",
            "career pressure",
        ],
        "content": """
Academic pressure can come from exams, deadlines, projects, placements, family expectations, or fear of failure. It can lead to stress, procrastination, sleep issues, self-doubt, and emotional overload.

Safe support includes breaking tasks into smaller steps, using study blocks, taking planned breaks, writing a realistic to-do list, prioritizing urgent work, and avoiding all-or-nothing thinking.

A useful method is: choose one small task, set a 25-minute timer, take a 5-minute break, and repeat. Progress should be measured by consistency, not perfection.

If academic pressure leads to panic, persistent low mood, or unsafe thoughts, the user should speak with a trusted person, counsellor, or professional.
""",
        "safety_note": "Avoid diagnosing depression or anxiety from exam stress.",
    },
    {
        "id": "self_doubt",
        "title": "Self-Doubt and Thought Reframing",
        "category": "self_doubt",
        "keywords": [
            "self doubt",
            "self-doubt",
            "not good enough",
            "worthless",
            "failure",
            "confidence",
            "low confidence",
            "negative thoughts",
            "overthinking myself",
        ],
        "content": """
Self-doubt often includes harsh thoughts such as "I am not good enough" or "I always fail." These thoughts can feel true when a person is stressed, but they are not always accurate.

A safe reframing method is:
1. Write the harsh thought.
2. Ask: What evidence supports it?
3. Ask: What evidence does not support it?
4. Write a kinder, more balanced thought.
5. Take one small action that supports confidence.

Example: Instead of "I always fail," a balanced thought could be "I am struggling right now, but I can take one step and improve with support."
""",
        "safety_note": "If self-doubt becomes hopelessness or self-harm thinking, escalate to support.",
    },
    {
        "id": "anger_regulation",
        "title": "Anger Regulation",
        "category": "anger",
        "keywords": [
            "anger",
            "angry",
            "rage",
            "irritated",
            "frustrated",
            "shouting",
            "control anger",
            "aggression",
        ],
        "content": """
Anger is a normal emotion, but it can become harmful when it leads to unsafe actions, harsh words, or loss of control. Anger often appears when someone feels hurt, disrespected, stressed, or powerless.

Safe anger regulation steps include pausing before responding, stepping away from the situation, slow breathing, relaxing the shoulders and jaw, writing the feeling down, and returning to the conversation when calmer.

A useful phrase is: "I need a few minutes to calm down before I respond."

If anger feels uncontrollable, causes harm, or creates safety concerns, professional help is strongly recommended.
""",
        "safety_note": "If there is threat of violence or harm, encourage immediate safety and emergency support.",
    },
    {
        "id": "mood_tracking",
        "title": "Mood Tracking",
        "category": "mood_tracking",
        "keywords": [
            "mood",
            "mood tracking",
            "emotion",
            "emotion detection",
            "mood trend",
            "journal",
            "check in",
            "wellbeing score",
        ],
        "content": """
Mood tracking helps users notice patterns in emotions, sleep, stress, social connection, and daily habits. It is not a diagnosis, but it can support self-awareness.

A simple mood entry can include: mood level, main emotion, trigger, body sensation, thought, need, coping action, and one kind sentence.

In NeuroSense AI, mood trends may come from emotion logs, check-ins, chat engagement, and wellbeing responses. These are supportive indicators, not clinical measurements.

If mood is persistently low, unstable, or connected with unsafe thoughts, users should speak with a qualified professional.
""",
        "safety_note": "Never present app mood scores as clinical diagnosis.",
    },
    {
        "id": "wellbeing_checkin",
        "title": "Wellbeing Check-In Score",
        "category": "wellbeing_checkin",
        "keywords": [
            "checkin",
            "check-in",
            "score",
            "wellbeing score",
            "risk level",
            "mental wellbeing test",
            "social wellbeing",
        ],
        "content": """
The NeuroSense AI wellbeing check-in score is a supportive indicator based on user responses such as stress level, social connection, sleep quality, emotional safety, support availability, current mood, and concerns.

A lower score means the user may need more support that day. A higher score suggests a more stable check-in state. This score is not a medical diagnosis or clinical assessment.

The score should be used to personalize support, such as suggesting grounding, sleep support, social connection, professional help guidance, or crisis resources when needed.

If the user feels unsafe or has thoughts of self-harm, the score is less important than immediate human support.
""",
        "safety_note": "State that the score is supportive only, not diagnostic.",
    },
    {
        "id": "reports_explanation",
        "title": "Assessment and Solution Reports",
        "category": "reports",
        "keywords": [
            "report",
            "assessment report",
            "solution report",
            "generated report",
            "suggestions",
            "top 5 suggestions",
            "mood report",
        ],
        "content": """
NeuroSense AI can generate two kinds of reports.

The Assessment Report summarizes observational data such as session data, detected emotions, mood trend, wellbeing check-in responses, conversation history summary, engagement patterns, and risk/support level.

The Solution Report provides safe, practical suggestions such as top 5 practices, grounding exercises, sleep support, social support steps, professional help guidance, and crisis resources.

Reports are not clinical diagnosis, psychiatric evaluation, or medical treatment plans. They are supportive wellness summaries.
""",
        "safety_note": "Do not present reports as medical documents.",
    },
    {
        "id": "professional_help",
        "title": "Professional Help Guidance",
        "category": "professional_help",
        "keywords": [
            "professional help",
            "psychiatrist",
            "psychologist",
            "counsellor",
            "therapist",
            "therapy",
            "doctor",
            "mental health professional",
        ],
        "content": """
A counsellor can support emotional concerns, coping skills, stress, relationships, and adjustment difficulties.

A psychologist can provide structured psychological assessment and therapy for deeper or ongoing emotional patterns.

A psychiatrist is a medical doctor who can assess mental health conditions and prescribe medication when clinically appropriate.

NeuroSense AI cannot replace any of these professionals. If symptoms are severe, persistent, unsafe, or medication-related, the user should consult a qualified professional.
""",
        "safety_note": "Medication-related questions should be referred to a psychiatrist or doctor.",
    },
    {
        "id": "crisis_safety",
        "title": "Crisis Safety and Immediate Support",
        "category": "crisis_safety",
        "keywords": [
            "suicide",
            "kill myself",
            "self harm",
            "hurt myself",
            "unsafe",
            "end my life",
            "crisis",
            "emergency",
            "danger",
            "hopeless",
        ],
        "content": """
If someone feels at risk of harming themselves, ending their life, or being in immediate danger, they should seek human help immediately.

Safe steps include: contact a trusted person now, move away from anything that could be used for harm, avoid being alone if possible, contact local emergency services, or call a crisis helpline.

India support resources include Tele MANAS 14416 or 1800-891-4416, iCALL 9152987821, Vandrevala Foundation +91 9999 666 555, KIRAN 1800-599-0019, and AASRA 022-27546669.

NeuroSense AI cannot provide emergency intervention. Immediate human support is the priority.
""",
        "safety_note": "For crisis, prioritize immediate support over explanation.",
    },
]


def get_all_kb_items() -> List[Dict[str, Any]]:
    return MENTAL_HEALTH_KB


def get_kb_status() -> Dict[str, Any]:
    categories = sorted(set(item.get("category", "general") for item in MENTAL_HEALTH_KB))

    return {
        "ok": True,
        "version": KB_VERSION,
        "item_count": len(MENTAL_HEALTH_KB),
        "categories": categories,
        "scope": "mental_health_and_neurosense_ai_only",
    }


if __name__ == "__main__":
    print(get_kb_status())