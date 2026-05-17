/* ==========================================================================
   NeuroSense AI — Research Chat JS
   Purpose:
   - Research Chat UI
   - Template quick select
   - Ollama status check
   - Research chat history
   - Safe rendering
   ========================================================================== */

const researchForm = document.getElementById("researchForm");
const researchInput = document.getElementById("researchInput");
const researchMessages = document.getElementById("researchMessages");
const templateQuickList = document.getElementById("templateQuickList");
const selectedTemplateBox = document.getElementById("selectedTemplateBox");
const selectedTemplateTitle = document.getElementById("selectedTemplateTitle");
const ollamaStatus = document.getElementById("ollamaStatus");

let selectedTemplateId = null;
let selectedTemplateName = null;
let allTemplatesFromQuickList = [];

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
    if(!researchMessages){
        return;
    }

    const div = document.createElement("div");
    div.className = `message ${role}`;

    const avatar = role === "user" ? "🙂" : "🧠";

    let metaHtml = "";

    if(meta){
        metaHtml = `
            <div class="meta">
                ${meta.model ? `Model: ${escapeHtml(meta.model)} · ` : ""}
                ${meta.template_title ? `Template: ${escapeHtml(meta.template_title)} · ` : ""}
                ${meta.risk_level ? `Risk: ${escapeHtml(meta.risk_level)}` : ""}
            </div>
        `;
    }

    div.innerHTML = `
        <div class="avatar">${avatar}</div>

        <div class="bubble">
            ${role === "assistant" ? "<strong>NeuroSense Research Agent</strong>" : "<strong>You</strong>"}

            <div>
                ${role === "assistant" ? markdownToHtml(content) : escapeHtml(content)}
            </div>

            ${metaHtml}
        </div>
    `;

    researchMessages.appendChild(div);
    researchMessages.scrollTop = researchMessages.scrollHeight;
}

function addTyping(){
    if(!researchMessages){
        return;
    }

    removeTyping();

    const div = document.createElement("div");
    div.className = "message assistant";
    div.id = "typingMessage";

    div.innerHTML = `
        <div class="avatar">🧠</div>

        <div class="bubble">
            <strong>NeuroSense Research Agent</strong>
            <p class="typing">Researching safely with agents and Ollama...</p>
        </div>
    `;

    researchMessages.appendChild(div);
    researchMessages.scrollTop = researchMessages.scrollHeight;
}

function removeTyping(){
    const typing = document.getElementById("typingMessage");

    if(typing){
        typing.remove();
    }
}

/* ==========================================================================
   OLLAMA STATUS
   ========================================================================== */

async function checkOllamaStatus(){
    if(!ollamaStatus){
        return;
    }

    try{
        const res = await fetch("/api/ollama/status");
        const data = await res.json();

        if(data.available){
            ollamaStatus.textContent = `Ollama connected · ${data.research_model || "model ready"}`;
            ollamaStatus.className = "ok";
        }else{
            ollamaStatus.textContent = "Ollama not running. Start with: ollama serve";
            ollamaStatus.className = "bad";
        }

    }catch(err){
        console.error("Ollama status error:", err);
        ollamaStatus.textContent = "Could not check Ollama status.";
        ollamaStatus.className = "bad";
    }
}

/* ==========================================================================
   TEMPLATE QUICK LIST
   ========================================================================== */

async function loadQuickTemplates(){
    if(!templateQuickList){
        return [];
    }

    templateQuickList.innerHTML = `
        <div class="empty">
            Loading templates...
        </div>
    `;

    try{
        const res = await fetch("/api/templates");
        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not load templates.");
        }

        const templates = data.templates || [];
        allTemplatesFromQuickList = templates;

        if(!templates.length){
            templateQuickList.innerHTML = `
                <div class="empty">
                    No templates found.
                </div>
            `;

            return [];
        }

        templateQuickList.innerHTML = "";

        templates.slice(0, 10).forEach((template) => {
            const item = document.createElement("button");
            item.className = "template-item";
            item.type = "button";

            item.innerHTML = `
                <strong>${escapeHtml(template.title)}</strong>

                <span>
                    ${escapeHtml(formatCategory(template.category))}
                    ·
                    ${escapeHtml(formatCategory(template.output_type))}
                </span>
            `;

            item.onclick = () => {
                selectTemplate(template.id, template.title);
            };

            templateQuickList.appendChild(item);
        });

        return templates;

    }catch(err){
        console.error("Template load error:", err);

        templateQuickList.innerHTML = `
            <div class="empty">
                Could not load templates.
            </div>
        `;

        return [];
    }
}

function selectTemplate(id, title){
    selectedTemplateId = id;
    selectedTemplateName = title;

    if(selectedTemplateTitle){
        selectedTemplateTitle.textContent = title || "Selected template";
    }

    if(selectedTemplateBox){
        selectedTemplateBox.classList.remove("hidden");
    }
}

function clearSelectedTemplate(){
    selectedTemplateId = null;
    selectedTemplateName = null;

    if(selectedTemplateBox){
        selectedTemplateBox.classList.add("hidden");
    }

    if(selectedTemplateTitle){
        selectedTemplateTitle.textContent = "None";
    }
}

function formatCategory(value){
    return String(value || "")
        .replaceAll("_"," ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ==========================================================================
   SEND RESEARCH MESSAGE
   ========================================================================== */

async function sendResearchMessage(query){
    const cleanQuery = String(query || "").trim();

    if(!cleanQuery){
        return;
    }

    addMessage("user", cleanQuery);
    addTyping();

    try{
        const res = await fetch("/api/research_chat", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                query:cleanQuery,
                template_id:selectedTemplateId
            })
        });

        const data = await res.json();

        removeTyping();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Research chat failed.");
        }

        addMessage(
            "assistant",
            data.answer || "No answer generated.",
            {
                model:data.model,
                template_title:data.template_title || selectedTemplateName,
                risk_level:data.risk_level
            }
        );

    }catch(err){
        console.error("Research chat error:", err);
        removeTyping();

        addMessage(
            "assistant",
            err.message || "Something went wrong while generating the research response."
        );
    }
}

/* ==========================================================================
   HISTORY
   ========================================================================== */

async function loadResearchHistory(){
    try{
        const res = await fetch("/api/research_chat/history");
        const data = await res.json();

        if(!res.ok || data.ok === false){
            return;
        }

        const history = data.history || [];

        history.forEach((item) => {
            if(item.query){
                addMessage("user", item.query);
            }

            if(item.answer){
                addMessage(
                    "assistant",
                    item.answer,
                    {
                        model:item.model,
                        template_title:item.template_title,
                        risk_level:item.risk_level
                    }
                );
            }
        });

    }catch(err){
        console.warn("Could not load research history:", err);
    }
}

async function clearResearchHistory(){
    const ok = confirm("Clear research chat history?");

    if(!ok){
        return;
    }

    try{
        const res = await fetch("/api/research_chat/history", {
            method:"DELETE"
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not clear history.");
        }

        if(researchMessages){
            researchMessages.innerHTML = "";
        }

        addMessage(
            "assistant",
            "Research history cleared. Ask me a new wellness research question or choose a template."
        );

    }catch(err){
        console.error("Clear history error:", err);
        addMessage("assistant", err.message || "Could not clear history.");
    }
}

/* ==========================================================================
   TEMPLATE RESULT FROM /templates PAGE
   ========================================================================== */

function loadSelectedTemplateFromUrlOrStorage(){
    const params = new URLSearchParams(window.location.search);

    const templateFromUrl =
        params.get("template_id") ||
        localStorage.getItem("neurosense_selected_template");

    if(templateFromUrl && allTemplatesFromQuickList.length){
        const found = allTemplatesFromQuickList.find(
            (template) => template.id === templateFromUrl
        );

        if(found){
            selectTemplate(found.id, found.title);
        }

        localStorage.removeItem("neurosense_selected_template");
    }
}

function loadLastTemplateResult(){
    const lastResult = localStorage.getItem("neurosense_last_template_result");

    if(!lastResult){
        return;
    }

    try{
        const data = JSON.parse(lastResult);

        if(data.query){
            addMessage("user", data.query);
        }

        if(data.answer){
            addMessage(
                "assistant",
                data.answer,
                {
                    model:data.model,
                    template_title:data.template_title,
                    risk_level:data.risk_level
                }
            );
        }

    }catch(err){
        console.warn("Could not load last template result:", err);
    }

    localStorage.removeItem("neurosense_last_template_result");
}

/* ==========================================================================
   FORM EVENTS
   ========================================================================== */

if(researchForm){
    researchForm.addEventListener("submit", (e) => {
        e.preventDefault();

        const query = researchInput.value.trim();

        if(!query){
            return;
        }

        researchInput.value = "";
        sendResearchMessage(query);
    });
}

if(researchInput){
    researchInput.addEventListener("keydown", (e) => {
        if(e.key === "Enter" && !e.shiftKey){
            e.preventDefault();

            if(researchForm){
                researchForm.requestSubmit();
            }
        }
    });
}

/* ==========================================================================
   INIT
   ========================================================================== */

document.addEventListener("DOMContentLoaded", async () => {
    checkOllamaStatus();

    await loadQuickTemplates();

    loadSelectedTemplateFromUrlOrStorage();

    loadResearchHistory();

    loadLastTemplateResult();
});

/* ==========================================================================
   GLOBALS
   ========================================================================== */

window.selectTemplate = selectTemplate;
window.clearSelectedTemplate = clearSelectedTemplate;
window.clearResearchHistory = clearResearchHistory;
window.sendResearchMessage = sendResearchMessage;