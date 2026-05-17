/* ==========================================================================
   NeuroSense AI — Insights Dashboard + Real-Time Project Accuracy
   File: static/js/dashboard.js

   Final behavior:
   - User dashboard stays real-time
   - Project Accuracy is visible to logged-in users
   - Admin dashboard access remains protected from backend/templates
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  initInsightRefresh();
  initPracticeClickTracking();
  initInsightFeedback();
  initPrivacyControls();
  initCardsGlow();
  initWellnessNews();
  initReliabilityStatus();
  initDashboardAccuracy();
});

/* ==========================================================================
   REFRESH / REAL-TIME INSIGHTS
   ========================================================================== */

function initInsightRefresh() {
  const refreshBtn = [...document.querySelectorAll("button"), ...document.querySelectorAll("a")]
    .find((btn) => String(btn.textContent || "").includes("Refresh"));

  if (refreshBtn) {
    refreshBtn.addEventListener("click", (e) => {
      if (
        refreshBtn.tagName.toLowerCase() === "a" &&
        refreshBtn.getAttribute("href") === "#"
      ) {
        e.preventDefault();
      }

      updateLastUpdated();
      loadDashboardAccuracy();
      initWellnessNews();

      showMiniToast("Dashboard refreshed");

      setTimeout(() => {
        location.reload();
      }, 500);
    });
  }

  setInterval(async () => {
    try {
      const res = await fetch("/api/insights_data", {
        method: "GET",
        headers: {
          "Accept": "application/json",
          "Cache-Control": "no-cache"
        }
      });

      if (!res.ok) return;

      await res.json();
      updateLastUpdated();

    } catch (error) {
      console.warn("Insights refresh failed:", error);
    }
  }, 60000);
}

/* ==========================================================================
   REAL-TIME PROJECT ACCURACY
   ========================================================================== */

function initDashboardAccuracy() {
  loadDashboardAccuracy();

  setInterval(() => {
    loadDashboardAccuracy();
  }, 10000);
}

async function loadDashboardAccuracy() {
  try {
    const res = await fetch("/api/project/accuracy", {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "Cache-Control": "no-cache"
      }
    });

    if (!res.ok) {
      console.warn("Accuracy API unavailable:", res.status);
      setAccuracyFallback();
      return;
    }

    const data = await res.json();

    if (!(data.ok || data.success)) {
      console.warn("Accuracy API failed:", data.error);
      setAccuracyFallback();
      return;
    }

    const accuracy = data.accuracy || {};
    const breakdown = accuracy.breakdown || {};
    const raw = accuracy.raw || {};

    const overall = Number(accuracy.overall_accuracy || 0);
    const grade = accuracy.grade || "Good";
    const updatedAt = accuracy.updated_at || getCurrentTimeLabel();

    setText("dashboardAccuracy", `${formatPercent(overall)}%`);
    setText("dashboardAccuracyGrade", `${grade} • Real-time`);
    setText("dashboardAccuracyUpdated", `Updated ${updatedAt}`);

    setText("accuracyFeedbackScore", `${formatPercent(breakdown.user_feedback_score)}%`);
    setText("accuracySafetyScore", `${formatPercent(breakdown.safety_pass_rate)}%`);
    setText("accuracyEmotionScore", `${formatPercent(breakdown.emotion_confidence)}%`);
    setText("accuracyReportScore", `${formatPercent(breakdown.report_success_rate)}%`);
    setText("accuracySessionScore", `${formatPercent(breakdown.session_completion_rate)}%`);

    setText("accuracyTotalUsers", raw.total_users ?? "--");
    setText("accuracyTotalSessions", raw.total_sessions ?? "--");
    setText("accuracyTotalReports", raw.total_reports ?? "--");
    setText("accuracyTotalFeedback", raw.total_feedback ?? "--");

    updateAccuracyBars(breakdown);
    updateAccuracyRing(overall);
    updateAccuracyCardState(overall, grade);

  } catch (error) {
    console.warn("Dashboard accuracy load failed:", error);
    setAccuracyFallback();
  }
}

function setAccuracyFallback() {
  const score = document.getElementById("dashboardAccuracy");
  const grade = document.getElementById("dashboardAccuracyGrade");
  const updated = document.getElementById("dashboardAccuracyUpdated");

  if (score && !score.textContent.trim()) {
    score.textContent = "--%";
  }

  if (grade && !grade.textContent.trim()) {
    grade.textContent = "Waiting for live data";
  }

  if (updated && !updated.textContent.trim()) {
    updated.textContent = "Accuracy API unavailable";
  }
}

function updateAccuracyBars(breakdown) {
  const map = {
    accuracyFeedbackBar: breakdown.user_feedback_score,
    accuracySafetyBar: breakdown.safety_pass_rate,
    accuracyEmotionBar: breakdown.emotion_confidence,
    accuracyReportBar: breakdown.report_success_rate,
    accuracySessionBar: breakdown.session_completion_rate
  };

  Object.entries(map).forEach(([id, value]) => {
    const el = document.getElementById(id);

    if (!el) return;

    const safeValue = clamp(Number(value || 0), 0, 100);

    el.style.width = `${safeValue}%`;
    el.setAttribute("aria-valuenow", String(safeValue));
  });
}

function updateAccuracyRing(value) {
  const ring = document.getElementById("dashboardAccuracyRing");

  if (!ring) return;

  const safeValue = clamp(Number(value || 0), 0, 100);

  ring.style.setProperty("--accuracy", `${safeValue}%`);
  ring.setAttribute("aria-label", `Project accuracy ${safeValue}%`);
}

function updateAccuracyCardState(score, grade) {
  const card = document.getElementById("projectAccuracyCard");

  if (!card) return;

  card.classList.remove(
    "accuracy-excellent",
    "accuracy-very-good",
    "accuracy-good",
    "accuracy-low"
  );

  if (score >= 90) {
    card.classList.add("accuracy-excellent");
  } else if (score >= 80) {
    card.classList.add("accuracy-very-good");
  } else if (score >= 70) {
    card.classList.add("accuracy-good");
  } else {
    card.classList.add("accuracy-low");
  }

  card.setAttribute(
    "title",
    `Overall project accuracy: ${formatPercent(score)}% (${grade})`
  );
}

/* ==========================================================================
   PRACTICE CLICK TRACKING
   ========================================================================== */

function initPracticeClickTracking() {
  document.querySelectorAll(".start-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      try {
        const card = btn.closest(".practice-card");

        const practice = card && card.querySelector("strong")
          ? card.querySelector("strong").textContent.trim()
          : "Practice";

        const payload = {
          practice: practice,
          completed: false,
          source: "insights_recommendation",
          created_at: new Date().toISOString()
        };

        if (navigator.sendBeacon) {
          navigator.sendBeacon(
            "/api/practices/log",
            new Blob(
              [JSON.stringify(payload)],
              {
                type: "application/json"
              }
            )
          );
        } else {
          fetch("/api/practices/log", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Accept": "application/json"
            },
            body: JSON.stringify(payload)
          }).catch(() => {});
        }

        showMiniToast(`${practice} started`);

      } catch (error) {
        console.warn("Practice click tracking failed:", error);
      }
    });
  });
}

/* ==========================================================================
   HELPFUL / NOT HELPFUL FEEDBACK
   ========================================================================== */

function initInsightFeedback() {
  document.querySelectorAll(".feedback-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const target = btn.dataset.feedbackTarget || "insight";
      const label = btn.dataset.feedbackLabel || "helpful";

      try {
        btn.disabled = true;

        const res = await fetch("/api/feedback", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          body: JSON.stringify({
            target,
            label,
            feedback: label,
            value: label !== "not_helpful",
            context: document.getElementById("thought-section")?.innerText || "",
            page: "dashboard_insights"
          })
        });

        const data = await res.json();

        if (!res.ok || !(data.ok || data.success)) {
          throw new Error(data.error || "Feedback save failed");
        }

        showMiniToast(
          label === "not_helpful"
            ? "Thanks — we’ll improve this insight"
            : "Feedback saved"
        );

        document.querySelectorAll(".feedback-btn").forEach((otherBtn) => {
          if (otherBtn.dataset.feedbackTarget === target) {
            otherBtn.classList.remove("selected");
          }
        });

        btn.classList.add("selected");

        setTimeout(() => {
          loadDashboardAccuracy();
        }, 500);

      } catch (error) {
        console.warn("Feedback failed:", error);
        showMiniToast("Could not save feedback right now");
      } finally {
        btn.disabled = false;
      }
    });
  });
}

/* ==========================================================================
   PRIVACY / DATA CONTROL
   ========================================================================== */

function initPrivacyControls() {
  document.querySelectorAll("[data-clear-type]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const type = btn.dataset.clearType;
      const label = btn.textContent.trim();

      const ok = confirm(
        `${label}? This will remove selected local NeuroSense history.`
      );

      if (!ok) return;

      try {
        btn.disabled = true;

        const res = await fetch("/api/user/clear-data", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Accept": "application/json"
          },
          body: JSON.stringify({
            type
          })
        });

        const data = await res.json();

        if (!res.ok || !(data.ok || data.success)) {
          throw new Error(data.error || "Clear request failed");
        }

        showMiniToast("Selected history cleared");

        setTimeout(() => {
          location.reload();
        }, 900);

      } catch (error) {
        console.warn("Clear data failed:", error);
        showMiniToast(error.message || "Could not clear data");
      } finally {
        btn.disabled = false;
      }
    });
  });
}

/* ==========================================================================
   WELLNESS NEWS
   ========================================================================== */

async function initWellnessNews() {
  const grid = document.getElementById("wellnessNewsGrid");

  if (!grid) return;

  try {
    const res = await fetch("/api/wellness-news", {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "Cache-Control": "no-cache"
      }
    });

    const data = await res.json();
    const items = data.items || [];

    if (!items.length) {
      grid.innerHTML = `
        <div class="news-item">
          <div class="news-thumb">🧠</div>

          <div>
            <div class="news-meta">
              <span>Wellness</span>
              <small>Today</small>
            </div>

            <h4>No wellness news available right now</h4>

            <p>
              Please check again later for mental health, sleep, movement,
              and fitness updates.
            </p>
          </div>
        </div>
      `;

      initCardsGlow();
      return;
    }

    grid.innerHTML = items.slice(0, 6).map((item) => {
      const title = escapeHtml(item.title || "Wellness update");

      const description = escapeHtml(
        item.description ||
        item.summary ||
        "Read more about this wellness topic."
      );

      const category = escapeHtml(item.category || "Wellness");
      const source = escapeHtml(item.source || "News");

      const published = escapeHtml(
        formatNewsDate(item.published || item.time || "Today")
      );

      const icon = escapeHtml(item.icon || item.image || "🧠");

      const url = escapeAttribute(
        item.url ||
        "https://news.google.com/search?q=mental%20health%20wellbeing%20fitness%20sleep"
      );

      return `
        <div class="news-item">
          <div class="news-thumb">${icon}</div>

          <div>
            <div class="news-meta">
              <span>${category}</span>
              <small>${published}</small>
            </div>

            <h4>${title}</h4>

            <p>${description}</p>

            <div class="news-source">
              Source: ${source}
            </div>

            <a
              href="${url}"
              target="_blank"
              rel="noopener noreferrer"
              class="read"
            >
              Read more →
            </a>
          </div>
        </div>
      `;
    }).join("");

    initCardsGlow();

  } catch (error) {
    console.error("Wellness news loading failed:", error);

    grid.innerHTML = `
      <div class="news-item">
        <div class="news-thumb">🧠</div>

        <div>
          <div class="news-meta">
            <span>Offline</span>
            <small>Today</small>
          </div>

          <h4>News could not load</h4>

          <p>
            Please check your connection or try again later.
          </p>
        </div>
      </div>
    `;

    initCardsGlow();
  }
}

function formatNewsDate(value) {
  if (!value || value === "Today") return "Today";

  try {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "Today";
    }

    return date.toLocaleDateString([], {
      day: "2-digit",
      month: "short"
    });

  } catch (e) {
    return "Today";
  }
}

/* ==========================================================================
   RELIABILITY STATUS
   ========================================================================== */

async function initReliabilityStatus() {
  updateLastUpdated();

  try {
    const res = await fetch("/api/reliability/status", {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "Cache-Control": "no-cache"
      }
    });

    if (!res.ok) return;

    const data = await res.json();

    if (data.last_updated) {
      updateLastUpdated(new Date(data.last_updated));
    }

  } catch (error) {
    console.warn("Reliability status unavailable:", error);
  }
}

function updateLastUpdated(date = new Date()) {
  const pill = document.getElementById("lastUpdatedPill");

  if (!pill) return;

  pill.textContent = `Last updated: ${date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  })}`;
}

/* ==========================================================================
   CARD GLOW EFFECT
   ========================================================================== */

function initCardsGlow() {
  document
    .querySelectorAll(
      ".panel, .welcome-card, .summary-card, .practice-card, .news-item, .reliability-panel, .data-panel, .accuracy-panel, .accuracy-item"
    )
    .forEach((card) => {
      if (card.dataset.glowBound === "true") return;

      card.dataset.glowBound = "true";

      card.addEventListener("mousemove", (e) => {
        const rect = card.getBoundingClientRect();

        card.style.setProperty(
          "--mx",
          `${e.clientX - rect.left}px`
        );

        card.style.setProperty(
          "--my",
          `${e.clientY - rect.top}px`
        );
      });
    });
}

/* ==========================================================================
   MINI TOAST
   ========================================================================== */

function showMiniToast(message, subtext = "") {
  const oldToast = document.querySelector(".insights-toast");

  if (oldToast) {
    oldToast.remove();
  }

  const toast = document.createElement("div");

  toast.className = "insights-toast";

  toast.innerHTML = `
    <strong>${escapeHtml(message)}</strong>
    ${subtext ? `<span>${escapeHtml(subtext)}</span>` : ""}
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(12px)";
    toast.style.transition = ".25s ease";

    setTimeout(() => {
      toast.remove();
    }, 260);
  }, 2800);
}

/* ==========================================================================
   HELPERS
   ========================================================================== */

function setText(id, value) {
  const el = document.getElementById(id);

  if (!el) return;

  el.textContent = value;
}

function formatPercent(value) {
  const num = Number(value || 0);

  if (Number.isNaN(num)) return "0";

  if (Number.isInteger(num)) return String(num);

  return num.toFixed(1).replace(/\.0$/, "");
}

function getCurrentTimeLabel() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit"
  });
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}