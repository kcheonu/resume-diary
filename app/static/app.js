const $ = (selector, parent = document) => parent.querySelector(selector);
const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
const toast = $("#toast");
let toastTimer;
let activePlanId = null;

function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    let message = `요청에 실패했습니다 (${response.status}).`;
    try {
      const payload = await response.json();
      if (payload.detail) {
        message = Array.isArray(payload.detail)
          ? payload.detail.map((item) => item.msg).join(", ")
          : payload.detail;
      }
    } catch {
      // Keep the HTTP status message when the response is not JSON.
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }
  return response.status === 204 ? null : response.json();
}

function formatDate(value) {
  if (!value) return "날짜 미정";
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("ko-KR", { month: "short", day: "numeric" }).format(date);
}

function escapeText(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) ? url.href : "#";
  } catch {
    return "#";
  }
}

function renderJobs(jobs) {
  $("#job-count").textContent = jobs.length;
  const list = $("#job-list");
  if (!jobs.length) {
    list.innerHTML = '<p class="empty-state">아직 저장한 공고가 없어요. 관심 있는 공고를 기록해 보세요.</p>';
    return;
  }
  list.innerHTML = jobs.slice(0, 5).map((job, index) => `
    <article class="job-item">
      <div class="company-mark color-${index % 3}">${escapeText((job.company || "?").slice(0, 1))}</div>
      <div>
        <h3 class="job-title">${escapeText(job.title)}</h3>
        <div class="job-meta"><span>${escapeText(job.company)}</span><span class="separator">·</span><span>${job.deadline ? `마감 ${formatDate(job.deadline)}` : escapeText(job.source)}</span></div>
      </div>
      <a class="source-pill" href="${escapeText(safeUrl(job.url))}" target="_blank" rel="noopener noreferrer" aria-label="공고 원문 열기">${escapeText(job.source)} ↗</a>
    </article>`).join("");
}

function renderRecommendations(items) {
  $("#recommend-count").textContent = items.length;
  const container = $("#recommendation-list");
  if (!items.length) {
    container.innerHTML = '<p class="muted-note">입력한 기술과 일치하는 공고가 아직 없어요.</p>';
    return;
  }
  container.innerHTML = items.slice(0, 5).map((item) => `
    <article class="recommend-card">
      <div>
        <h3>${escapeText(item.job.title)} · ${escapeText(item.job.company)}</h3>
        <p>${escapeText(item.job.source)}에서 저장한 공고</p>
        <div class="match-tags">${item.matched_skills.map((skill) => `<span class="match-tag">${escapeText(skill)}</span>`).join("")}</div>
      </div>
      <span class="match-score">${item.match_score}%</span>
    </article>`).join("");
}

function renderSchedule(plan) {
  activePlanId = plan.id;
  $("#task-count").textContent = plan.tasks.filter((task) => task.status !== "completed").length;
  $("#schedule-content").innerHTML = `
    <div class="plan-header"><strong>${escapeText(plan.goal)}</strong><span>${formatDate(plan.start_date)} — ${formatDate(plan.end_date)}</span></div>
    <div class="task-list">${plan.tasks.map((task) => `
      <label class="task-item ${task.status === "completed" ? "completed" : ""}">
        <input class="task-check" type="checkbox" data-task-id="${task.id}" ${task.status === "completed" ? "checked" : ""} aria-label="${escapeText(task.title)} 완료">
        <span class="task-title">${escapeText(task.title)}</span><span class="task-date">${formatDate(task.scheduled_date)}</span>
      </label>`).join("")}</div>`;
  $("#replan-form").classList.remove("hidden");
  const replanForm = $("#replan-form");
  replanForm.elements.start_date.value = plan.start_date;
  replanForm.elements.end_date.value = plan.end_date;
}

async function refreshJobs() {
  const jobs = await api("/jobs?limit=100");
  renderJobs(jobs);
}

async function loadSavedPlan() {
  const savedPlanId = localStorage.getItem("career-note-plan-id");
  if (!savedPlanId) {
    $("#task-count").textContent = "0";
    return;
  }
  try {
    const plan = await api(`/schedules/${encodeURIComponent(savedPlanId)}`);
    renderSchedule(plan);
  } catch (error) {
    if (error.status === 404) {
      localStorage.removeItem("career-note-plan-id");
      $("#task-count").textContent = "0";
      return;
    }
    showToast(error.message, true);
  }
}

function splitSkills(value) {
  return value.split(",").map((skill) => skill.trim()).filter(Boolean);
}

function formDate(value) {
  return value ? `${value}T00:00:00` : null;
}

async function initialize() {
  $("#today-label").textContent = new Intl.DateTimeFormat("ko-KR", {
    year: "numeric", month: "long", day: "numeric", weekday: "short",
  }).format(new Date());
  try {
    await refreshJobs();
  } catch (error) {
    $("#job-list").innerHTML = `<p class="empty-state">${escapeText(error.message)}</p>`;
    showToast(error.message, true);
  }
  await loadSavedPlan();

  $("#job-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const payload = {
      source: values.get("source"),
      company: values.get("company").trim(),
      title: values.get("title").trim(),
      url: values.get("url").trim(),
      skills: splitSkills(values.get("skills") || ""),
      description: (values.get("description") || "").trim(),
      deadline: formDate(values.get("deadline")),
    };
    try {
      await api("/jobs", { method: "POST", body: JSON.stringify(payload) });
      form.reset();
      await refreshJobs();
      showToast("공고를 다이어리에 저장했어요.");
    } catch (error) {
      showToast(error.message, true);
    }
  });

  $("#recommend-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const skills = splitSkills(event.currentTarget.elements.skills.value);
    try {
      const recommendations = await api("/jobs/recommendations", {
        method: "POST",
        body: JSON.stringify({ skills, limit: 20 }),
      });
      renderRecommendations(recommendations);
    } catch (error) {
      showToast(error.message, true);
    }
  });

  $("#schedule-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const tasks = values.get("tasks").split(/\r?\n/).map((title) => title.trim()).filter(Boolean);
    try {
      const plan = await api("/schedules", {
        method: "POST",
        body: JSON.stringify({
          goal: values.get("goal").trim(),
          start_date: values.get("start_date"),
          end_date: values.get("end_date"),
          tasks: tasks.map((title) => ({ title })),
        }),
      });
      localStorage.setItem("career-note-plan-id", plan.id);
      renderSchedule(plan);
      showToast("준비 일정을 만들었어요.");
    } catch (error) {
      showToast(error.message, true);
    }
  });

  $("#replan-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!activePlanId) return;
    const values = new FormData(event.currentTarget);
    try {
      const plan = await api(`/schedules/${activePlanId}/replan`, {
        method: "POST",
        body: JSON.stringify({
          start_date: values.get("start_date"),
          end_date: values.get("end_date"),
        }),
      });
      renderSchedule(plan);
      showToast("미완료 일정을 다시 배치했어요.");
    } catch (error) {
      showToast(error.message, true);
    }
  });

  $("#schedule-content").addEventListener("change", async (event) => {
    const checkbox = event.target.closest("[data-task-id]");
    if (!checkbox || !activePlanId) return;
    try {
      await api(`/schedules/${activePlanId}/tasks/${checkbox.dataset.taskId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: checkbox.checked ? "completed" : "pending" }),
      });
      const plan = await api(`/schedules/${activePlanId}`);
      renderSchedule(plan);
    } catch (error) {
      checkbox.checked = !checkbox.checked;
      showToast(error.message, true);
    }
  });
}

initialize();
