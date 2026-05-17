/* ==========================================================================
   NeuroSense AI — Wellbeing Check-In JS
   Purpose:
   - Collect mental/social wellbeing form data
   - Calculate frontend score instantly
   - Save normalized check-in to backend
   - Display safe non-diagnostic result
   ========================================================================== */

const wellbeingForm = document.getElementById("wellbeingForm");
const assessmentResult = document.getElementById("assessmentResult");
const resultTitle = document.getElementById("resultTitle");
const resultText = document.getElementById("resultText");

function collectWellbeingFormData(){
    if(!wellbeingForm){
        return null;
    }

    const formData = new FormData(wellbeingForm);

    const concerns = [];

    document.querySelectorAll('input[name="concerns"]:checked').forEach((item) => {
        concerns.push(item.value);
    });

    return {
        mood: formData.get("mood"),
        stress: Number(formData.get("stress") || 0),
        social_connection: Number(formData.get("social_connection") || 0),
        sleep: formData.get("sleep"),
        concerns: concerns,
        emotional_safety: Number(formData.get("emotional_safety") || 0),
        support_available: formData.get("support_available"),
        current_thoughts: formData.get("current_thoughts") || "",
        created_at: new Date().toISOString()
    };
}

function calculateWellbeingScore(data){
    let score = 100;

    score -= data.stress * 8;
    score -= (6 - data.social_connection) * 6;
    score -= (6 - data.emotional_safety) * 7;

    if(data.sleep === "poor"){
        score -= 10;
    }

    if(data.sleep === "very_poor"){
        score -= 18;
    }

    if(data.support_available === "maybe"){
        score -= 8;
    }

    if(data.support_available === "no"){
        score -= 15;
    }

    score -= Math.min((data.concerns || []).length * 4, 20);

    if(["sad","anxious","angry","overwhelmed"].includes(data.mood)){
        score -= 12;
    }

    return Math.max(0, Math.min(100, score));
}

function calculateRiskLevel(data){
    const score = data.wellbeing_score ?? calculateWellbeingScore(data);

    if(
        data.stress >= 4 ||
        data.emotional_safety <= 2 ||
        data.support_available === "no" ||
        data.mood === "overwhelmed" ||
        score <= 30
    ){
        return "high";
    }

    if(
        data.stress >= 3 ||
        data.social_connection <= 2 ||
        data.sleep === "poor" ||
        data.sleep === "very_poor" ||
        ["sad","anxious","angry"].includes(data.mood) ||
        score <= 60
    ){
        return "medium";
    }

    return "low";
}

function showWellbeingResult(score, risk, message){
    if(!assessmentResult || !resultTitle || !resultText){
        return;
    }

    assessmentResult.classList.add("show");

    resultTitle.textContent = `Check-In Saved • Score: ${score}/100`;

    if(message){
        resultText.textContent = message;
        return;
    }

    if(risk === "high"){
        resultText.textContent = "You seem emotionally overloaded today. Please choose a chat mode and consider talking to a trusted person, helpline, or licensed professional if you feel unsafe.";
    }else if(risk === "medium"){
        resultText.textContent = "You may be experiencing some stress or emotional pressure. NeuroSense AI will keep the conversation supportive and grounding.";
    }else{
        resultText.textContent = "Your check-in suggests a relatively stable state today. You can continue with any mode that feels comfortable.";
    }
}

async function saveWellbeingCheckin(){
    const payload = collectWellbeingFormData();

    if(!payload){
        return;
    }

    payload.wellbeing_score = calculateWellbeingScore(payload);
    payload.risk_level = calculateRiskLevel(payload);

    localStorage.setItem(
        "neurosense_wellbeing_checkin",
        JSON.stringify(payload)
    );

    showWellbeingResult(
        payload.wellbeing_score,
        payload.risk_level
    );

    try{
        const res = await fetch("/api/wellbeing_checkin", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify(payload)
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Backend save failed.");
        }

        const backendScore = data.wellbeing_score ?? data.checkin?.wellbeing_score ?? payload.wellbeing_score;
        const backendRisk = data.risk_level ?? data.checkin?.risk_level ?? payload.risk_level;

        const savedPayload = data.checkin || payload;

        localStorage.setItem(
            "neurosense_wellbeing_checkin",
            JSON.stringify(savedPayload)
        );

        showWellbeingResult(
            backendScore,
            backendRisk,
            getBackendMessage(backendRisk)
        );

        if(window.loadProfessionalHelp){
            window.loadProfessionalHelp(savedPayload);
        }

    }catch(err){
        console.warn("Wellbeing backend save failed:", err);
        showWellbeingResult(
            payload.wellbeing_score,
            payload.risk_level,
            "Check-in saved locally. Backend could not be reached right now."
        );
    }

    if(assessmentResult){
        assessmentResult.scrollIntoView({
            behavior:"smooth",
            block:"center"
        });
    }
}

function getBackendMessage(risk){
    if(risk === "high"){
        return "Your answers suggest a high support need today. NeuroSense AI is not a medical service, but it may help to speak with a trusted person, helpline, or licensed professional.";
    }

    if(risk === "medium"){
        return "Your answers suggest moderate emotional pressure. Supportive coping practices and a safe conversation may help.";
    }

    return "Your answers suggest a relatively stable state today. You can still use NeuroSense AI for reflection and emotional support.";
}

function resetAssessment(){
    if(wellbeingForm){
        wellbeingForm.reset();
    }

    if(assessmentResult){
        assessmentResult.classList.remove("show");
    }

    localStorage.removeItem("neurosense_wellbeing_checkin");

    const professionalBox = document.getElementById("professionalHelpBox");

    if(professionalBox){
        professionalBox.innerHTML = "";
        professionalBox.classList.remove("show");
    }
}

function restorePreviousCheckin(){
    const saved = localStorage.getItem("neurosense_wellbeing_checkin");

    if(!saved){
        return;
    }

    try{
        const data = JSON.parse(saved);

        if(!data){
            return;
        }

        const score = data.wellbeing_score ?? calculateWellbeingScore(data);
        const risk = data.risk_level ?? calculateRiskLevel(data);

        if(assessmentResult && resultTitle && resultText){
            assessmentResult.classList.add("show");
            resultTitle.textContent = "Previous Check-In Found";
            resultText.textContent = `Previous wellbeing score: ${score}/100 • Risk level: ${String(risk).toUpperCase()}. You can update it anytime.`;
        }

    }catch(err){
        console.warn("Could not restore previous check-in:", err);
    }
}

function stopVoiceIfAvailable(){
    try{
        if(window.stopAllVoiceAudio){
            window.stopAllVoiceAudio();
        }

        if(window.speechSynthesis){
            window.speechSynthesis.cancel();
        }

        document.querySelectorAll("audio").forEach((audio) => {
            try{
                audio.pause();
                audio.currentTime = 0;
            }catch(err){}
        });
    }catch(err){
        console.warn("Voice cleanup skipped:", err);
    }
}

if(wellbeingForm){
    wellbeingForm.addEventListener("submit", (e) => {
        e.preventDefault();
        saveWellbeingCheckin();
    });
}

window.addEventListener("DOMContentLoaded", () => {
    stopVoiceIfAvailable();
    restorePreviousCheckin();
});

window.addEventListener("pageshow", stopVoiceIfAvailable);
window.addEventListener("beforeunload", stopVoiceIfAvailable);

window.calculateWellbeingScore = calculateWellbeingScore;
window.calculateRiskLevel = calculateRiskLevel;
window.saveWellbeingCheckin = saveWellbeingCheckin;
window.resetAssessment = resetAssessment;
window.collectWellbeingFormData = collectWellbeingFormData;