/* ==========================================================================
   NeuroSense AI — Knowledge Chat JS
   Mental-health-only grounded chat with report upload context

   Supports:
   - Knowledge Chat messages
   - Approved KB source display
   - Mental Wellness Assessment upload
   - Personalized Wellness Plan upload
   - Report-context-aware questions
   - History load / clear
   ========================================================================== */

const knowledgeForm = document.getElementById("knowledgeForm");
const knowledgeInput = document.getElementById("knowledgeInput");
const knowledgeMessages = document.getElementById("knowledgeMessages");
const knowledgeStatus = document.getElementById("knowledgeStatus");

const assessmentFile = document.getElementById("assessmentFile");
const solutionFile = document.getElementById("solutionFile");

const assessmentState = document.getElementById("assessmentState");
const solutionState = document.getElementById("solutionState");

const reportContextBanner = document.getElementById("reportContextBanner");
const reportContextText = document.getElementById("reportContextText");

let reportContext = {
    assessment: null,
    solution: null
};

/* ==========================================================================
   SAFE TEXT HELPERS
   ========================================================================== */

function escapeHtml(text){
    return String(text || "")
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}

function markdownToHtml(text){
    let safe = escapeHtml(text || "");

    safe = safe.replace(/^### (.*)$/gm, "<h3>$1</h3>");
    safe = safe.replace(/^## (.*)$/gm, "<h2>$1</h2>");
    safe = safe.replace(/^# (.*)$/gm, "<h1>$1</h1>");
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/\n/g, "<br>");

    return safe;
}

/* ==========================================================================
   MESSAGE UI
   ========================================================================== */

function addMessage(role, content, meta = null){
    if(!knowledgeMessages){
        return;
    }

    const div = document.createElement("div");
    div.className = `message ${role}`;

    const avatar = role === "user" ? "🙂" : "📚";

    let sourceHtml = "";

    if(meta && Array.isArray(meta.sources) && meta.sources.length){
        sourceHtml = `
            <div class="sources">
                <strong>Source basis:</strong>
                ${meta.sources.map(src => `
                    <span>${escapeHtml(src.title || src.id || "Knowledge Source")}</span>
                `).join("")}
            </div>
        `;
    }

    let metaHtml = "";

    if(meta){
        metaHtml = `
            <div class="meta">
                ${meta.model ? `Model: ${escapeHtml(meta.model)} · ` : ""}
                ${meta.grounded ? "Grounded: Yes · " : ""}
                ${meta.used_ollama ? "Ollama: Yes" : "Ollama: No"}
            </div>
        `;
    }

    div.innerHTML = `
        <div class="avatar">${avatar}</div>

        <div class="bubble">
            ${role === "assistant" ? "<strong>NeuroSense Knowledge Agent</strong>" : "<strong>You</strong>"}

            <div>
                ${role === "assistant" ? markdownToHtml(content) : escapeHtml(content)}
            </div>

            ${sourceHtml}
            ${metaHtml}
        </div>
    `;

    knowledgeMessages.appendChild(div);
    knowledgeMessages.scrollTop = knowledgeMessages.scrollHeight;
}

function addTyping(){
    if(!knowledgeMessages){
        return;
    }

    removeTyping();

    const div = document.createElement("div");
    div.className = "message assistant";
    div.id = "typingMessage";

    div.innerHTML = `
        <div class="avatar">📚</div>
        <div class="bubble">
            <strong>NeuroSense Knowledge Agent</strong>
            <p class="typing">Checking scope, retrieving approved knowledge, and validating response...</p>
        </div>
    `;

    knowledgeMessages.appendChild(div);
    knowledgeMessages.scrollTop = knowledgeMessages.scrollHeight;
}

function removeTyping(){
    const typing = document.getElementById("typingMessage");

    if(typing){
        typing.remove();
    }
}

/* ==========================================================================
   STATUS
   ========================================================================== */

async function checkKnowledgeStatus(){
    if(!knowledgeStatus){
        return;
    }

    try{
        const res = await fetch("/api/knowledge/status");
        const data = await res.json();

        if(data.ok){
            knowledgeStatus.textContent = `Knowledge engine ready · ${data.item_count || 0} approved items`;
            knowledgeStatus.className = "ok";
        }else{
            knowledgeStatus.textContent = data.error || "Knowledge engine not ready.";
            knowledgeStatus.className = "bad";
        }

    }catch(err){
        console.error("Knowledge status error:", err);
        knowledgeStatus.textContent = "Could not check knowledge engine.";
        knowledgeStatus.className = "bad";
    }
}

/* ==========================================================================
   CHAT API
   ========================================================================== */

async function sendKnowledgeMessage(query){
    const clean = String(query || "").trim();

    if(!clean){
        return;
    }

    addMessage("user", clean);
    addTyping();

    try{
        const res = await fetch("/api/knowledge_chat", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                query: clean,
                report_context: reportContext
            })
        });

        const data = await res.json();

        removeTyping();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Knowledge Chat failed.");
        }

        addMessage(
            "assistant",
            data.answer || "No answer generated.",
            {
                sources:data.sources || [],
                model:data.model,
                used_ollama:data.used_ollama,
                grounded:data.grounded
            }
        );

    }catch(err){
        console.error("Knowledge chat error:", err);
        removeTyping();

        addMessage(
            "assistant",
            err.message || "Something went wrong while generating a grounded response."
        );
    }
}

/* ==========================================================================
   HISTORY
   ========================================================================== */

async function loadKnowledgeHistory(){
    try{
        const res = await fetch("/api/knowledge_chat/history");
        const data = await res.json();

        if(!res.ok || data.ok === false){
            return;
        }

        const history = data.history || [];

        history.forEach(item => {
            if(item.query){
                addMessage("user", item.query);
            }

            if(item.answer){
                addMessage("assistant", item.answer, {
                    sources:item.sources || [],
                    model:item.model,
                    used_ollama:item.used_ollama,
                    grounded:item.grounded
                });
            }
        });

    }catch(err){
        console.warn("Could not load knowledge history:", err);
    }
}

async function clearKnowledgeHistory(){
    const ok = confirm("Clear Knowledge Chat history?");

    if(!ok){
        return;
    }

    try{
        const res = await fetch("/api/knowledge_chat/history", {
            method:"DELETE"
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not clear Knowledge Chat history.");
        }

        if(knowledgeMessages){
            knowledgeMessages.innerHTML = "";
        }

        addMessage(
            "assistant",
            "Knowledge Chat history cleared. Ask a mental-health or NeuroSense AI question."
        );

    }catch(err){
        console.error("Clear Knowledge Chat history error:", err);
        addMessage("assistant", err.message || "Could not clear Knowledge Chat history.");
    }
}

/* ==========================================================================
   REPORT UPLOAD CONTEXT
   ========================================================================== */

async function uploadKnowledgeReport(type){
    const input = type === "assessment" ? assessmentFile : solutionFile;
    const state = type === "assessment" ? assessmentState : solutionState;

    if(!input || !input.files || !input.files[0]){
        alert("Please choose a file first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", input.files[0]);
    formData.append("report_type", type);

    state.textContent = "Uploading and reading...";
    state.classList.remove("ok", "bad");

    try{
        const res = await fetch("/api/knowledge_chat/upload_report", {
            method:"POST",
            body:formData
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Upload failed.");
        }

        reportContext[type] = {
            report_type:type,
            filename:data.filename,
            summary:data.summary,
            extracted_text:data.extracted_text
        };

        state.textContent = `${data.filename} added`;
        state.classList.add("ok");

        updateReportContextBanner();

        addMessage(
            "assistant",
            type === "assessment"
                ? "Mental Wellness Assessment report uploaded. You can now ask questions about the assessment findings."
                : "Personalized Wellness Plan report uploaded. You can now ask questions about the suggested practices and support plan.",
            {
                sources:[
                    {
                        title:data.filename,
                        id:type
                    }
                ],
                used_ollama:false,
                grounded:true
            }
        );

    }catch(err){
        console.error("Report upload error:", err);

        state.textContent = err.message || "Upload failed.";
        state.classList.add("bad");
    }
}

function updateReportContextBanner(){
    if(!reportContextBanner || !reportContextText){
        return;
    }

    const hasAssessment = Boolean(reportContext.assessment);
    const hasSolution = Boolean(reportContext.solution);

    if(!hasAssessment && !hasSolution){
        reportContextBanner.classList.add("hidden");
        return;
    }

    reportContextBanner.classList.remove("hidden");

    const parts = [];

    if(hasAssessment){
        parts.push("Assessment report added");
    }

    if(hasSolution){
        parts.push("Solution report added");
    }

    reportContextText.textContent = parts.join(" · ");
}

function clearReportContext(){
    reportContext = {
        assessment:null,
        solution:null
    };

    if(assessmentState){
        assessmentState.textContent = "Not uploaded";
        assessmentState.classList.remove("ok", "bad");
    }

    if(solutionState){
        solutionState.textContent = "Not uploaded";
        solutionState.classList.remove("ok", "bad");
    }

    if(assessmentFile){
        assessmentFile.value = "";
    }

    if(solutionFile){
        solutionFile.value = "";
    }

    updateReportContextBanner();

    addMessage(
        "assistant",
        "Report context cleared. I will now answer only from the approved NeuroSense AI knowledge base."
    );
}

/* ==========================================================================
   FORM EVENTS
   ========================================================================== */

if(knowledgeForm){
    knowledgeForm.addEventListener("submit", (e) => {
        e.preventDefault();

        const query = knowledgeInput.value.trim();

        if(!query){
            return;
        }

        knowledgeInput.value = "";
        sendKnowledgeMessage(query);
    });
}

if(knowledgeInput){
    knowledgeInput.addEventListener("keydown", (e) => {
        if(e.key === "Enter" && !e.shiftKey){
            e.preventDefault();

            if(knowledgeForm){
                knowledgeForm.requestSubmit();
            }
        }
    });
}

/* ==========================================================================
   INIT
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    checkKnowledgeStatus();
    loadKnowledgeHistory();
    updateReportContextBanner();
});

/* ==========================================================================
   GLOBALS
   ========================================================================== */

window.uploadKnowledgeReport = uploadKnowledgeReport;
window.clearReportContext = clearReportContext;
window.clearKnowledgeHistory = clearKnowledgeHistory;
window.sendKnowledgeMessage = sendKnowledgeMessage;