/* ==========================================================================
   NeuroSense AI — Templates JS
   ========================================================================== */

const templateGrid = document.getElementById("templateGrid");
const templateSearch = document.getElementById("templateSearch");
const categoryFilter = document.getElementById("categoryFilter");
const createTemplateForm = document.getElementById("createTemplateForm");
const templateStatus = document.getElementById("templateStatus");

let allTemplates = [];

function escapeHtml(text){
    return String(text || "")
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}

function formatCategory(value){
    return String(value || "")
        .replaceAll("_"," ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

function setStatus(message, type = "info"){
    if(!templateStatus){
        return;
    }

    templateStatus.className = `status-box show ${type}`;
    templateStatus.textContent = message;
}

async function loadTemplates(){
    if(!templateGrid){
        return;
    }

    templateGrid.innerHTML = `<div class="empty">Loading templates...</div>`;

    try{
        const res = await fetch("/api/templates");
        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not load templates.");
        }

        allTemplates = data.templates || [];

        renderTemplates();

    }catch(err){
        console.error(err);
        templateGrid.innerHTML = `<div class="empty">Could not load templates.</div>`;
    }
}

function renderTemplates(){
    if(!templateGrid){
        return;
    }

    const search = (templateSearch?.value || "").toLowerCase();
    const category = categoryFilter?.value || "";

    let filtered = allTemplates.filter((item) => {
        const text = `${item.title} ${item.description} ${item.category}`.toLowerCase();

        const matchesSearch = !search || text.includes(search);
        const matchesCategory = !category || item.category === category;

        return matchesSearch && matchesCategory;
    });

    if(!filtered.length){
        templateGrid.innerHTML = `<div class="empty">No templates matched your filter.</div>`;
        return;
    }

    templateGrid.innerHTML = "";

    filtered.forEach((template) => {
        const card = document.createElement("article");
        card.className = "template-card";

        const badge = template.is_prebuilt ? "Pre-built" : "Custom";

        card.innerHTML = `
            <div class="template-top">
                <span class="pill">${escapeHtml(badge)}</span>
                <span class="category">${escapeHtml(formatCategory(template.category))}</span>
            </div>

            <h2>${escapeHtml(template.title)}</h2>

            <p>${escapeHtml(template.description || "No description available.")}</p>

            <div class="template-meta">
                <span>Output: ${escapeHtml(formatCategory(template.output_type))}</span>
                <span>Risk: ${escapeHtml(template.risk_level || "low")}</span>
            </div>

            <div class="template-actions">
                <button onclick="runTemplate('${escapeHtml(template.id)}')">Run</button>
                <button class="secondary" onclick="openResearchWithTemplate('${escapeHtml(template.id)}')">Open in Research</button>
                ${template.is_prebuilt ? "" : `<button class="danger" onclick="deleteTemplate('${escapeHtml(template.id)}')">Delete</button>`}
            </div>
        `;

        templateGrid.appendChild(card);
    });
}

function openResearchWithTemplate(templateId){
    localStorage.setItem("neurosense_selected_template", templateId);
    window.location.href = `/research_chat?template_id=${encodeURIComponent(templateId)}`;
}

async function runTemplate(templateId){
    const query = prompt("Enter your question/context for this template:");

    if(!query){
        return;
    }

    try{
        const res = await fetch("/api/templates/run", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                template_id:templateId,
                query:query
            })
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not run template.");
        }

        localStorage.setItem(
            "neurosense_last_template_result",
            JSON.stringify(data)
        );

        window.location.href = "/research_chat";

    }catch(err){
        alert(err.message || "Template run failed.");
    }
}

async function deleteTemplate(templateId){
    const ok = confirm("Delete this custom template?");

    if(!ok){
        return;
    }

    try{
        const res = await fetch(`/api/templates/${encodeURIComponent(templateId)}`, {
            method:"DELETE"
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not delete template.");
        }

        await loadTemplates();

    }catch(err){
        alert(err.message || "Delete failed.");
    }
}

async function createTemplate(event){
    event.preventDefault();

    const payload = {
        title:document.getElementById("templateTitle").value.trim(),
        category:document.getElementById("templateCategory").value,
        output_type:document.getElementById("templateOutputType").value,
        description:document.getElementById("templateDescription").value.trim(),
        prompt:document.getElementById("templatePrompt").value.trim()
    };

    try{
        setStatus("Creating template...", "info");

        const res = await fetch("/api/templates", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify(payload)
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not create template.");
        }

        setStatus("Template created successfully. Redirecting...", "success");

        setTimeout(() => {
            window.location.href = "/templates";
        }, 700);

    }catch(err){
        setStatus(err.message || "Template creation failed.", "error");
    }
}

if(templateSearch){
    templateSearch.addEventListener("input", renderTemplates);
}

if(categoryFilter){
    categoryFilter.addEventListener("change", renderTemplates);
}

if(createTemplateForm){
    createTemplateForm.addEventListener("submit", createTemplate);
}

document.addEventListener("DOMContentLoaded", () => {
    loadTemplates();
});