/* ==========================================================================
   NeuroSense AI — Reports JS
   Supports:
   - Assessment Report PDF/CSV
   - Solution Report PDF/CSV
   - Saved report listing
   ========================================================================== */

const reportStatus = document.getElementById("reportStatus");
const savedReportsList = document.getElementById("savedReportsList");

function setReportStatus(message, type = "info"){
    if(!reportStatus){
        return;
    }

    reportStatus.classList.add("show");
    reportStatus.classList.remove("success", "error");

    if(type === "success"){
        reportStatus.classList.add("success");
    }

    if(type === "error"){
        reportStatus.classList.add("error");
    }

    reportStatus.textContent = message;
}

async function generateReport(reportType = "solution", format = "pdf"){
    const validReportTypes = ["assessment", "solution", "combined"];
    const validFormats = ["pdf", "csv"];

    if(!validReportTypes.includes(reportType)){
        reportType = "solution";
    }

    if(!validFormats.includes(format)){
        format = "pdf";
    }

    const label = reportType === "assessment"
        ? "Assessment Report"
        : reportType === "solution"
            ? "Solution Report"
            : "Combined Report";

    setReportStatus(`Generating ${label} ${format.toUpperCase()}...`);

    try{
        const res = await fetch("/api/report/generate", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                format:format,
                report_type:reportType
            })
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Report generation failed.");
        }

        if(!data.token){
            throw new Error("Download token missing from server response.");
        }

        setReportStatus(`${label} generated successfully. Download will start now.`, "success");

        const downloadUrl = `/api/report/download?token=${encodeURIComponent(data.token)}`;

        window.location.href = downloadUrl;

        setTimeout(() => {
            loadSavedReports();
        }, 1500);

    }catch(err){
        console.error(err);
        setReportStatus(err.message || "Report generation failed.", "error");
    }
}

async function generateAndDownload(reportType = "solution", format = "pdf"){
    const validReportTypes = ["assessment", "solution", "combined"];
    const validFormats = ["pdf", "csv"];

    if(!validReportTypes.includes(reportType)){
        reportType = "solution";
    }

    if(!validFormats.includes(format)){
        format = "pdf";
    }

    setReportStatus(`Generating and saving ${reportType} report...`);

    try{
        const res = await fetch("/api/generate_and_download", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                format:format,
                report_type:reportType
            })
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Report generation failed.");
        }

        if(!data.token){
            throw new Error("Download token missing from server response.");
        }

        setReportStatus("Report saved and generated successfully.", "success");

        window.location.href = `/api/report/download?token=${encodeURIComponent(data.token)}`;

        setTimeout(() => {
            loadSavedReports();
        }, 1500);

    }catch(err){
        console.error(err);
        setReportStatus(err.message || "Report generation failed.", "error");
    }
}

async function loadSavedReports(){
    if(!savedReportsList){
        return;
    }

    savedReportsList.innerHTML = `
        <div class="saved-empty">
            Loading saved reports...
        </div>
    `;

    try{
        const res = await fetch("/api/saved_reports");
        const data = await res.json();

        const reports = data.reports || [];

        if(!reports.length){
            savedReportsList.innerHTML = `
                <div class="saved-empty">
                    No saved reports yet. Generate a report to see it here.
                </div>
            `;
            return;
        }

        savedReportsList.innerHTML = "";

        reports.forEach((item) => {
            const report = item.report || item;
            const id = item.id || report.report_id || "Unknown";
            const generatedAt = item.generated_at || report.generated_at || "";
            const risk = report.risk_level || "unknown";
            const topEmotion = report.top_emotion || "neutral";
            const moodTrend = report.mood_trend || "stable";

            const div = document.createElement("div");
            div.className = "saved-item";

            div.innerHTML = `
                <div>
                    <h3>${escapeHtml(id)}</h3>
                    <p>
                        Generated: ${escapeHtml(formatDate(generatedAt))}
                        · Risk: ${escapeHtml(String(risk).toUpperCase())}
                        · Emotion: ${escapeHtml(String(topEmotion))}
                        · Trend: ${escapeHtml(String(moodTrend))}
                    </p>
                </div>

                <div class="actions">
                    <button class="btn" onclick="deleteSavedReport('${escapeJs(id)}')">
                        Delete
                    </button>
                </div>
            `;

            savedReportsList.appendChild(div);
        });

    }catch(err){
        console.error(err);

        savedReportsList.innerHTML = `
            <div class="saved-empty">
                Could not load saved reports.
            </div>
        `;
    }
}

async function deleteSavedReport(reportId){
    if(!reportId){
        return;
    }

    const ok = confirm(`Delete report ${reportId}?`);

    if(!ok){
        return;
    }

    try{
        const res = await fetch("/api/report/delete", {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                report_id:reportId
            })
        });

        const data = await res.json();

        if(!res.ok || data.ok === false){
            throw new Error(data.error || "Could not delete report.");
        }

        setReportStatus("Report deleted successfully.", "success");
        loadSavedReports();

    }catch(err){
        console.error(err);
        setReportStatus(err.message || "Could not delete report.", "error");
    }
}

function formatDate(value){
    if(!value){
        return "Unknown";
    }

    try{
        const d = new Date(value);

        if(Number.isNaN(d.getTime())){
            return value;
        }

        return d.toLocaleString([], {
            year:"numeric",
            month:"short",
            day:"2-digit",
            hour:"2-digit",
            minute:"2-digit"
        });

    }catch(err){
        return value;
    }
}

function escapeHtml(text){
    return String(text || "")
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}

function escapeJs(text){
    return String(text || "")
        .replaceAll("\\","\\\\")
        .replaceAll("'","\\'")
        .replaceAll('"','\\"');
}

document.addEventListener("DOMContentLoaded", () => {
    loadSavedReports();
});