/* ==========================================================================
   NeuroSense AI — Professional Help JS
   Purpose:
   - Fetch issue-based external professional support recommendations
   - Display counsellor / psychologist / psychiatrist / helpline guidance
   - Never present NeuroSense AI as psychiatrist
   ========================================================================== */

async function loadProfessionalHelp(checkin = null, message = ""){
    const box = document.getElementById("professionalHelpBox");

    if(!box){
        return;
    }

    box.classList.add("show");
    box.innerHTML = `
        <div class="professional-loading">
            Finding safe professional support resources...
        </div>
    `;

    try{
        const localSaved = localStorage.getItem("neurosense_wellbeing_checkin");

        if(!checkin && localSaved){
            try{
                checkin = JSON.parse(localSaved);
            }catch(err){
                checkin = {};
            }
        }

        const res = await fetch("/api/professional_help", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                checkin:checkin || {},
                message:message || checkin?.current_thoughts || "",
                emotion:window.currentEmotion || "neutral",
                safety:{}
            })
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not load professional help.");
        }

        renderProfessionalHelp(data);

    }catch(err){
        console.error(err);

        box.innerHTML = `
            <div class="professional-error">
                Could not load professional resources right now.
                <br>
                You can still contact:
                <br><br>
                <strong>Tele MANAS:</strong> 14416 or 1800-891-4416<br>
                <strong>iCALL:</strong> 9152987821<br>
                <strong>Vandrevala Foundation:</strong> +91 9999 666 555
            </div>
        `;
    }
}

function renderProfessionalHelp(data){
    const box = document.getElementById("professionalHelpBox");

    if(!box){
        return;
    }

    const urgency = data.urgency || "none";
    const emergency = Boolean(data.emergency);

    const urgencyClass = emergency
        ? "emergency"
        : urgency === "urgent"
            ? "urgent"
            : urgency === "soon"
                ? "soon"
                : "routine";

    const issueTags = data.issue_tags || [];
    const recommendations = data.recommendations || [];
    const resources = data.resources || [];

    let html = `
        <div class="professional-card ${urgencyClass}">
            <div class="professional-head">
                <div>
                    <h3>👨‍⚕️ Professional Help Outside NeuroSense AI</h3>
                    <p>
                        NeuroSense AI is not a psychiatrist and does not diagnose or prescribe.
                        These are referral suggestions for qualified human support.
                    </p>
                </div>

                <span class="urgency-pill ${urgencyClass}">
                    ${escapeHtml(String(urgency).toUpperCase())}
                </span>
            </div>
    `;

    if(data.user_facing_message){
        html += `
            <div class="professional-message">
                ${escapeHtml(data.user_facing_message)}
            </div>
        `;
    }

    if(issueTags.length){
        html += `
            <div class="issue-tags">
                ${issueTags.map(tag => `<span>${escapeHtml(formatIssueTag(tag))}</span>`).join("")}
            </div>
        `;
    }

    if(recommendations.length){
        html += `
            <div class="professional-section">
                <h4>Suggested Support Type</h4>
                <div class="recommendation-list">
        `;

        recommendations.forEach((rec) => {
            html += `
                <div class="recommendation-item">
                    <strong>${escapeHtml(rec.professional || "Mental health professional")}</strong>
                    <p>
                        <b>Issue:</b> ${escapeHtml(formatIssueTag(rec.issue || ""))}
                        <br>
                        <b>Urgency:</b> ${escapeHtml(rec.urgency || "routine")}
                        <br>
                        ${escapeHtml(rec.reason || "")}
                    </p>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;
    }

    html += `
        <div class="professional-section">
            <h4>Verified Support Resources</h4>
            <div class="resource-list">
    `;

    if(resources.length){
        resources.forEach((r) => {
            html += renderResource(r);
        });
    }else{
        html += `
            ${renderResource({
                name:"Tele MANAS",
                type:"Government mental health helpline",
                phone:"14416",
                alternate_phone:"1800-891-4416",
                available:"24/7"
            })}
            ${renderResource({
                name:"iCALL Psychosocial Helpline",
                type:"Counselling helpline",
                phone:"9152987821",
                email:"icall@tiss.ac.in"
            })}
            ${renderResource({
                name:"Vandrevala Foundation",
                type:"Mental health counselling and crisis support",
                phone:"+91 9999 666 555",
                whatsapp:"+91 9999 666 555",
                available:"24/7"
            })}
        `;
    }

    html += `
            </div>
        </div>
    `;

    if(data.disclaimer){
        html += `
            <div class="professional-disclaimer">
                ${escapeHtml(data.disclaimer)}
            </div>
        `;
    }

    html += `
        </div>
    `;

    box.innerHTML = html;
}

function renderResource(resource){
    const website = resource.website
        ? `<p><strong>Website:</strong> <a href="${escapeAttr(resource.website)}" target="_blank" rel="noopener">Open official link</a></p>`
        : "";

    return `
        <div class="resource-item">
            <h5>${escapeHtml(resource.name || "Support Resource")}</h5>
            <p>${escapeHtml(resource.type || "")}</p>

            ${resource.phone ? `<p><strong>Phone:</strong> ${escapeHtml(resource.phone)}</p>` : ""}
            ${resource.alternate_phone ? `<p><strong>Alternate:</strong> ${escapeHtml(resource.alternate_phone)}</p>` : ""}
            ${resource.whatsapp ? `<p><strong>WhatsApp:</strong> ${escapeHtml(resource.whatsapp)}</p>` : ""}
            ${resource.email ? `<p><strong>Email:</strong> ${escapeHtml(resource.email)}</p>` : ""}
            ${resource.available ? `<p><strong>Available:</strong> ${escapeHtml(resource.available)}</p>` : ""}
            ${website}
            ${resource.notes ? `<p class="resource-note">${escapeHtml(resource.notes)}</p>` : ""}
        </div>
    `;
}

function formatIssueTag(tag){
    return String(tag || "")
        .replaceAll("_"," ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
}

function escapeHtml(text){
    return String(text || "")
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}

function escapeAttr(text){
    return String(text || "")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}

window.loadProfessionalHelp = loadProfessionalHelp;
window.renderProfessionalHelp = renderProfessionalHelp;