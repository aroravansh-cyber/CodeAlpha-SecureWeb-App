(function () {
  "use strict";

  /* ----------------------------------------------------
     1. CONFIG
     ---------------------------------------------------- */

  const CONFIG = {
    API_BASE: "http://127.0.0.1:5000/api",
    LOGIN_URL: "v-index.html",
    ATTENDANCE_WINDOW_HOURS: 3
  };

  /* ----------------------------------------------------
     2. APP STATE
     ---------------------------------------------------- */

  const state = {
    me: null,               // logged-in faculty profile
    timetable: [],          // today's lectures
    students: [],           // all students visible to this faculty
    activeLecture: null,    // lecture currently open in Attendance view
    attendanceRoster: [],   // students + status for the active lecture
    serverTimeOffsetMs: 0,  // (server time) - (client time), for display only
    hierarchy: {}           // Faculty -> Branch -> Specialization -> Years
  };

  /* ----------------------------------------------------
     3. SMALL DOM HELPERS
     ---------------------------------------------------- */

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $all = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  function el(tag, props, children) {
    const node = document.createElement(tag);
    if (props) {
      Object.keys(props).forEach((key) => {
        if (key === "class") node.className = props[key];
        else if (key === "html") node.innerHTML = props[key];
        else node.setAttribute(key, props[key]);
      });
    }
    (children || []).forEach((child) => {
      if (child) node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    });
    return node;
  }

  function showToast(message, type) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.className = "toast is-visible" + (type ? " is-" + type : "");
    clearTimeout(showToast._t);
    showToast._t = setTimeout(() => {
      toast.className = "toast";
    }, 3200);
  }

  function initials(name) {
    if (!name) return "?";
    return name.trim().split(/\s+/).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
  }

  function avatarPlaceholder(name) {
    // Simple inline SVG avatar so we never depend on a broken <img> path.
    const label = initials(name);
    const svg =
      '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">' +
      '<rect width="64" height="64" fill="#161f2c"/>' +
      '<text x="32" y="38" font-family="Inter,sans-serif" font-size="22" fill="#22d3ee" text-anchor="middle">' + label + "</text>" +
      "</svg>";
    return "data:image/svg+xml;base64," + btoa(svg);
  }

  /* ----------------------------------------------------
     4. API WRAPPER
     ---------------------------------------------------- */

  async function apiRequest(path, options) {
    const opts = Object.assign({ credentials: "include", headers: {} }, options || {});
    if (opts.body && !(opts.body instanceof FormData)) {
      opts.headers["Content-Type"] = "application/json";
    }
    let response;
    try {
      response = await fetch(CONFIG.API_BASE + path, opts);
    } catch (networkErr) {
      throw { networkError: true, message: "Could not reach the server." };
    }

    if (response.status === 401 || response.status === 403) {
        window.location.href = CONFIG.LOGIN_URL;
        throw { authError: true };
    }

    let data = null;
    try { data = await response.json(); } catch (e) { /* no JSON body */ }

    if (!response.ok) {
      throw { apiError: true, status: response.status, message: (data && data.message) || "Request failed." };
    }
    return data;
  }

  /* ----------------------------------------------------
     5. DEMO DATA
     (used only as a fallback so the UI is reviewable before
     every backend endpoint exists — remove as endpoints go live)
     ---------------------------------------------------- */

  const DEMO_HIERARCHY = {
    "Engineering": {
      "Computer Science & Engineering": {
        specializations: ["Cyber Security", "Data Science", "AI & ML"],
        years: ["1st Year", "2nd Year", "3rd Year", "4th Year"]
      },
      "Mechanical Engineering": {
        specializations: [],
        years: ["1st Year", "2nd Year", "3rd Year", "4th Year"]
      },
      "Electronics & Communication": {
        specializations: ["VLSI Design"],
        years: ["1st Year", "2nd Year", "3rd Year", "4th Year"]
      }
    },
    "Business": {
      "Business Administration": {
        specializations: ["Finance", "Marketing", "Human Resources"],
        years: ["1st Year", "2nd Year"]
      }
    },
    "Science": {
      "Physics": {
        specializations: [],
        years: ["1st Year", "2nd Year", "3rd Year"]
      }
    }
  };


  function demoStudents() {
    const names = [
      "Rahul Verma", "Sneha Patil", "Aarav Mehta", "Ishita Rao", "Kabir Singh",
      "Priya Nair", "Dev Kulkarni", "Ananya Iyer", "Vivaan Joshi", "Riya Kapoor",
      "Arjun Desai", "Meera Pillai", "Kunal Shah", "Tanya Bhatt", "Yash Malhotra",
      "Sanya Chawla", "Rohan Gupta", "Nisha Reddy", "Aditya Menon", "Pooja Saxena"
    ];
    return names.map((name, i) => ({
      id: "CSE21" + String(100 + i),
      roll_no: "CSE21" + String(100 + i),
      name,
      photo_url: "",
      faculty: "Engineering",
      branch: "Computer Science & Engineering",
      specialization: i % 2 === 0 ? "Cyber Security" : "Data Science",
      year: "2nd Year",
      status: "pending"
    }));
  }

  function demoTimetable(now) {
    // Builds a realistic-looking timetable around the current time of day.
    const base = new Date(now);
    base.setHours(9, 0, 0, 0);
    const lectures = [
      { name: "Network Security Fundamentals", room: "LH-204", branch: "CSE · Cyber Security", year: "2nd Year", durationMin: 60 },
      { name: "Data Structures Lab", room: "Lab-3", branch: "CSE · Data Science", year: "2nd Year", durationMin: 90 },
      { name: "Applied Cryptography", room: "LH-107", branch: "CSE · Cyber Security", year: "3rd Year", durationMin: 60 },
      { name: "Machine Learning Basics", room: "LH-301", branch: "CSE · Data Science", year: "2nd Year", durationMin: 60 },
      { name: "Thermodynamics", room: "LH-112", branch: "Mechanical Engineering", year: "2nd Year", durationMin: 60 }
    ];

    let cursor = new Date(base);
    return lectures.map((lec, idx) => {
      const start = new Date(cursor);
      const end = new Date(start.getTime() + lec.durationMin * 60000);
      cursor = new Date(end.getTime() + 15 * 60000); // 15-min gap between lectures

      let status = "upcoming";
      if (now >= end) status = "completed";
      else if (now >= start && now < end) status = "ongoing";

      return {
        id: "LEC-" + (idx + 1),
        name: lec.name,
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        branch: lec.branch,
        year: lec.year,
        room: lec.room,
        status
      };
    });
  }

  /* ----------------------------------------------------
     6. DATA LOADING
     ---------------------------------------------------- */

  async function loadMe() {
  try {
    state.me = await apiRequest("/me");
    renderProfile();
  } catch (err) {
    if (err.authError) return;

    showToast("Could not load faculty profile.", "error");
  }
}
  async function loadHierarchy() {
    try {
      state.hierarchy = await apiRequest("/hierarchy");
    } catch (err) {
      state.hierarchy = DEMO_HIERARCHY;
    }
    populateHierarchyFilters();
  }

  async function loadTimetable() {
    try {
      state.timetable = await apiRequest("/timetable");
    } catch (err) {
      if (err.authError) return;
      state.timetable = demoTimetable(new Date());
    }
    renderTimetable();
    renderDashboardTimetablePreview();
    renderStats();
  }

  async function loadStudents() {
    try {
      state.students = await apiRequest("/students");
    } catch (err) {
      if (err.authError) return;
      state.students = demoStudents();
    }
    renderStudents();
    renderStats();
  }

  async function loadAttendanceForLecture(lecture) {
    state.activeLecture = lecture;
    try {
      state.attendanceRoster = await apiRequest("/attendance?lecture_id=" + encodeURIComponent(lecture.id));
    } catch (err) {
      if (err.authError) return;
      // Fall back to students matching this lecture's branch/year, demo-only.
      state.attendanceRoster = state.students
        .filter((s) => lecture.branch.indexOf(s.branch) !== -1 || s.branch.indexOf(lecture.branch.split("·")[0].trim()) !== -1)
        .map((s) => Object.assign({}, s, { status: s.status || "pending" }));
      if (state.attendanceRoster.length === 0) state.attendanceRoster = state.students.slice(0, 8);
    }
    renderAttendance();
  }

  /* ----------------------------------------------------
     7. RENDER: PROFILE
     ---------------------------------------------------- */

  function renderProfile() {
    const me = state.me;

    if (!me) return;

    $("#chipName").textContent = me.full_name || "Faculty";
    $("#chipAvatar").src = me.photo_url || avatarPlaceholder(me.full_name);

    $("#profFullName").textContent = me.full_name || "–";
    $("#profEmail").textContent = me.email || "–";
    $("#profStaffId").textContent = me.faculty_id || "–";
    $("#profDesignation").textContent = me.designation || "–";
    $("#profBranch").textContent = me.department || "–";

    $("#profilePhoto").src = me.photo_url || avatarPlaceholder(me.full_name);

    const preview = $("#dashboardProfilePreview");

    preview.innerHTML = "";

    preview.appendChild(
        el("div", { class: "profile-card" }, [
            el("div", { class: "profile-card__photo" }, [
                el("img", {
                    src: me.photo_url || avatarPlaceholder(me.full_name),
                    alt: ""
                })
            ]),

            el("dl", { class: "profile-card__details" }, [
                el("div", { class: "detail-row" }, [
                    el("dt", {}, ["Name"]),
                    el("dd", {}, [me.full_name || "–"])
                ]),

                el("div", { class: "detail-row" }, [
                    el("dt", {}, ["Designation"]),
                    el("dd", {}, [me.designation || "–"])
                ]),

                el("div", { class: "detail-row" }, [
                    el("dt", {}, ["Department"]),
                    el("dd", {}, [me.department || "–"])
                ])
            ])
        ])
    );
}

  async function handlePhotoUpload(file) {
    if (!file) return;

    const formData = new FormData();
    formData.append("photo", file);

    try {
        const result = await apiRequest("/profile/photo", {
            method: "POST",
            body: formData
        });

        if (result && result.photo_url) {
            state.me.photo_url = result.photo_url;
            renderProfile();
            showToast("Profile photo updated.", "success");
        }

    } catch (err) {
        if (err.authError) return;

        showToast("Couldn't upload photo — showing a local preview only.", "error");

        const localUrl = URL.createObjectURL(file);
        state.me.photo_url = localUrl;
        renderProfile();
    }
}

  /* ----------------------------------------------------
     8. RENDER: TIMETABLE
     ---------------------------------------------------- */

  function formatTime(iso) {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function statusPill(status) {
    return el("span", { class: "status-pill status-pill--" + status }, [
      status.charAt(0).toUpperCase() + status.slice(1)
    ]);
  }

  function renderTimetable() {
    const body = $("#timetableBody");
    body.innerHTML = "";
    $("#timetableDate").textContent = new Date().toLocaleDateString(undefined, {
      weekday: "long", month: "short", day: "numeric"
    });

    if (state.timetable.length === 0) {
      body.appendChild(el("tr", {}, [el("td", { colspan: "8", class: "empty-note" }, ["No lectures scheduled for today."])]));
      return;
    }

    state.timetable.forEach((lec) => {
      const row = el("tr", {}, [
        el("td", {}, [lec.name]),
        el("td", { class: "cell-id" }, [formatTime(lec.start_time)]),
        el("td", { class: "cell-id" }, [formatTime(lec.end_time)]),
        el("td", {}, [lec.branch]),
        el("td", {}, [lec.year]),
        el("td", {}, [lec.room]),
        el("td", {}, [statusPill(lec.status)]),
        el("td", {}, [
          el("button", { class: "row-link", type: "button", "data-open-lecture": lec.id }, ["Take attendance →"])
        ])
      ]);
      body.appendChild(row);
    });

    $all("[data-open-lecture]", body).forEach((btn) => {
      btn.addEventListener("click", () => {
        const lecture = state.timetable.find((l) => l.id === btn.getAttribute("data-open-lecture"));
        if (lecture) {
          switchView("attendance");
          loadAttendanceForLecture(lecture);
        }
      });
    });
  }

  function renderDashboardTimetablePreview() {
    const preview = $("#dashboardTimetablePreview");
    preview.innerHTML = "";
    const upcoming = state.timetable.slice(0, 4);
    if (upcoming.length === 0) {
      preview.appendChild(el("p", { class: "empty-note" }, ["No lectures scheduled for today."]));
      return;
    }
    const table = el("table", { class: "data-table" });
    const tbody = el("tbody");
    upcoming.forEach((lec) => {
      tbody.appendChild(el("tr", {}, [
        el("td", {}, [lec.name]),
        el("td", { class: "cell-id" }, [formatTime(lec.start_time) + " – " + formatTime(lec.end_time)]),
        el("td", {}, [lec.room]),
        el("td", {}, [statusPill(lec.status)])
      ]));
    });
    table.appendChild(tbody);
    preview.appendChild(table);
  }

  /* ----------------------------------------------------
     9. RENDER: ATTENDANCE
     ---------------------------------------------------- */

  function attendanceWindowInfo(lecture) {
    const start = new Date(lecture.start_time);
    const windowEnd = new Date(start.getTime() + CONFIG.ATTENDANCE_WINDOW_HOURS * 3600000);
    const now = new Date();
    return { open: now >= start && now <= windowEnd, closesAt: windowEnd };
  }

  function renderAttendance() {
    const lecture = state.activeLecture;
    const body = $("#attendanceBody");
    body.innerHTML = "";

    if (!lecture) {
      $("#attendanceLectureTitle").textContent = "Select a lecture";
      $("#attendanceLectureMeta").textContent = "Choose a lecture from Timetable to take attendance.";
      $("#attendanceWindowBadge").textContent = "Window: closed";
      body.appendChild(el("tr", {}, [el("td", { colspan: "5", class: "empty-note" }, ["No lecture selected yet."])]));
      return;
    }

    const win = attendanceWindowInfo(lecture);
    $("#attendanceLectureTitle").textContent = lecture.name;
    $("#attendanceLectureMeta").textContent =
      lecture.branch + " · " + lecture.year + " · Room " + lecture.room + " · " + formatTime(lecture.start_time) + "–" + formatTime(lecture.end_time);
    $("#attendanceWindowBadge").textContent = win.open
      ? "Window open until " + win.closesAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : "Window: closed";
    $("#attendanceWindowBadge").className = "badge" + (win.open ? "" : " badge--muted");

    const search = ($("#attendanceSearch").value || "").toLowerCase();
    const statusFilter = $("#attendanceStatusFilter").value;

    const rows = state.attendanceRoster.filter((s) => {
      const matchesSearch = !search || s.name.toLowerCase().includes(search) || (s.roll_no || s.id).toLowerCase().includes(search);
      const matchesStatus = statusFilter === "all" || !statusFilter || s.status === statusFilter;
      return matchesSearch && matchesStatus;
    });

    if (rows.length === 0) {
      body.appendChild(el("tr", {}, [el("td", { colspan: "5", class: "empty-note" }, ["No students match your filters."])]));
      return;
    }

    rows.forEach((student) => {
      const markBtn = el("button", {
        class: "btn btn--primary btn--sm",
        type: "button",
        "data-mark-present": student.id
      }, ["Mark Present"]);

      if (student.status === "present" || !win.open) markBtn.setAttribute("disabled", "true");

      body.appendChild(el("tr", {}, [
        el("td", {}, [el("img", { class: "avatar-sm", src: student.photo_url || avatarPlaceholder(student.name), alt: "" })]),
        el("td", { class: "cell-id" }, [student.roll_no || student.id]),
        el("td", {}, [student.name]),
        el("td", {}, [statusPill(student.status || "pending")]),
        el("td", {}, [markBtn])
      ]));
    });

    $all("[data-mark-present]", body).forEach((btn) => {
      btn.addEventListener("click", () => markPresent(btn.getAttribute("data-mark-present")));
    });
  }

  async function markPresent(studentId) {
    const lecture = state.activeLecture;
    if (!lecture) return;
    try {
      const result = await apiRequest("/attendance", {
        method: "POST",
        body: JSON.stringify({ student_id: studentId, lecture_id: lecture.id })
      });
      const status = (result && result.status) || "present";
      updateStudentStatus(studentId, status);
      showToast(status === "present" ? "Marked present." : "Server declined the update.", status === "present" ? "success" : "error");
    } catch (err) {
      if (err.authError) return;
      const declined = err.apiError && err.status === 409;
      showToast(declined ? "Attendance window has closed for this lecture." : "Couldn't reach the server — try again.", "error");
    }
    renderAttendance();
    renderStats();
  }

  function updateStudentStatus(studentId, status) {
    state.attendanceRoster = state.attendanceRoster.map((s) => (s.id === studentId ? Object.assign({}, s, { status }) : s));
    state.students = state.students.map((s) => (s.id === studentId ? Object.assign({}, s, { status }) : s));
  }

  /* ----------------------------------------------------
     10. RENDER: STUDENTS
     ---------------------------------------------------- */

  function populateHierarchyFilters() {
    const facultySel = $("#filterFaculty");
    Object.keys(state.hierarchy).forEach((faculty) => {
      facultySel.appendChild(el("option", { value: faculty }, [faculty]));
    });
  }

  function refreshBranchOptions() {
    const facultySel = $("#filterFaculty");
    const branchSel = $("#filterBranch");
    branchSel.innerHTML = '<option value="">Branch: All</option>';
    const faculty = state.hierarchy[facultySel.value];
    if (faculty) {
      Object.keys(faculty).forEach((branch) => branchSel.appendChild(el("option", { value: branch }, [branch])));
    }
    refreshSpecializationOptions();
  }

  function refreshSpecializationOptions() {
    const facultySel = $("#filterFaculty");
    const branchSel = $("#filterBranch");
    const specSel = $("#filterSpecialization");
    specSel.innerHTML = '<option value="">Specialization: All</option>';
    const faculty = state.hierarchy[facultySel.value];
    const branch = faculty && faculty[branchSel.value];
    if (branch && branch.specializations && branch.specializations.length) {
      branch.specializations.forEach((spec) => specSel.appendChild(el("option", { value: spec }, [spec])));
    }
    refreshYearOptions();
  }

  function refreshYearOptions() {
    const facultySel = $("#filterFaculty");
    const branchSel = $("#filterBranch");
    const yearSel = $("#filterYear");
    yearSel.innerHTML = '<option value="">Year: All</option>';
    const faculty = state.hierarchy[facultySel.value];
    const branch = faculty && faculty[branchSel.value];
    const years = (branch && branch.years) || ["1st Year", "2nd Year", "3rd Year", "4th Year"];
    years.forEach((year) => yearSel.appendChild(el("option", { value: year }, [year])));
  }

  function renderStudents() {
    const body = $("#studentsBody");
    body.innerHTML = "";

    const search = ($("#studentSearch").value || "").toLowerCase();
    const faculty = $("#filterFaculty").value;
    const branch = $("#filterBranch").value;
    const spec = $("#filterSpecialization").value;
    const year = $("#filterYear").value;
    const status = $("#filterStatus").value;

    const rows = state.students.filter((s) => {
      if (search && !(s.name.toLowerCase().includes(search) || (s.roll_no || s.id).toLowerCase().includes(search))) return false;
      if (faculty && s.faculty !== faculty) return false;
      if (branch && s.branch !== branch) return false;
      if (spec && s.specialization !== spec) return false;
      if (year && s.year !== year) return false;
      if (status && s.status !== status) return false;
      return true;
    });

    if (rows.length === 0) {
      body.appendChild(el("tr", {}, [el("td", { colspan: "7", class: "empty-note" }, ["No students match your filters."])]));
      return;
    }

    rows.forEach((s) => {
      body.appendChild(el("tr", {}, [
        el("td", {}, [el("img", { class: "avatar-sm", src: s.photo_url || avatarPlaceholder(s.name), alt: "" })]),
        el("td", { class: "cell-id" }, [s.roll_no || s.id]),
        el("td", {}, [s.name]),
        el("td", {}, [s.branch]),
        el("td", {}, [s.specialization || "—"]),
        el("td", {}, [s.year]),
        el("td", {}, [statusPill(s.status || "pending")])
      ]));
    });
  }

  /* ----------------------------------------------------
     11. RENDER: STATS
     ---------------------------------------------------- */

  function renderStats() {
    const total = state.students.length;
    const present = state.students.filter((s) => s.status === "present").length;
    const absent = state.students.filter((s) => s.status === "absent").length;
    const pending = total - present - absent;

    $("#statTotal").textContent = total;
    $("#statPresent").textContent = present;
    $("#statAbsent").textContent = absent;
    $("#statPending").textContent = Math.max(pending, 0);
    $("#statLectures").textContent = state.timetable.length;
  }

  /* ----------------------------------------------------
     12. VIEW ROUTING
     ---------------------------------------------------- */

  const VIEW_TITLES = {
    dashboard: "Dashboard",
    timetable: "Timetable",
    attendance: "Attendance",
    students: "Students",
    profile: "Profile",
    settings: "Settings"
  };

  function switchView(viewName) {
    $all(".view").forEach((v) => v.classList.remove("is-active"));
    const target = $("#view-" + viewName);
    if (target) target.classList.add("is-active");

    $all(".nav__item[data-view]").forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-view") === viewName);
    });

    $("#viewTitle").textContent = VIEW_TITLES[viewName] || "Dashboard";
    closeSidebarOnMobile();
  }

  function closeSidebarOnMobile() {
    $("#sidebar").classList.remove("is-open");
    $("#topbarScrim").classList.remove("is-visible");
  }

  /* ----------------------------------------------------
     13. LIVE CLOCK
     ---------------------------------------------------- */

  function tickClock() {
    $("#liveClock").textContent = new Date().toLocaleTimeString();
  }

  /* ----------------------------------------------------
     14. LOGOUT
     ---------------------------------------------------- */

  async function logout() {
    try {
      await apiRequest("/logout", { method: "POST" });
    } catch (err) {
      // Even if the request fails, still send the user to the login page.
    }
    window.location.href = CONFIG.LOGIN_URL;
  }

  /* ----------------------------------------------------
     15. EVENT WIRING
     ---------------------------------------------------- */

  function wireEvents() {
    $all(".nav__item[data-view]").forEach((btn) => {
      btn.addEventListener("click", () => switchView(btn.getAttribute("data-view")));
    });

    $all("[data-goto]").forEach((btn) => {
      btn.addEventListener("click", () => switchView(btn.getAttribute("data-goto")));
    });

    $("#logoutBtn").addEventListener("click", logout);
    $("#settingsLogoutBtn").addEventListener("click", logout);

    $("#menuBtn").addEventListener("click", () => {
      const isOpen = $("#sidebar").classList.toggle("is-open");
      $("#topbarScrim").classList.toggle("is-visible", isOpen);
      $("#menuBtn").setAttribute("aria-expanded", String(isOpen));
    });
    $("#topbarScrim").addEventListener("click", closeSidebarOnMobile);

    $("#photoInput").addEventListener("change", (e) => handlePhotoUpload(e.target.files[0]));

    $("#studentSearch").addEventListener("input", renderStudents);
    $("#filterFaculty").addEventListener("change", () => { refreshBranchOptions(); renderStudents(); });
    $("#filterBranch").addEventListener("change", () => { refreshSpecializationOptions(); renderStudents(); });
    $("#filterSpecialization").addEventListener("change", renderStudents);
    $("#filterYear").addEventListener("change", renderStudents);
    $("#filterStatus").addEventListener("change", renderStudents);

    $("#attendanceSearch").addEventListener("input", renderAttendance);
    $("#attendanceStatusFilter").addEventListener("change", renderAttendance);

    $("#globalSearch").addEventListener("input", (e) => {
      switchView("students");
      $("#studentSearch").value = e.target.value;
      renderStudents();
    });

    $all(".nav__item[data-view]").forEach((btn) => btn.setAttribute("type", "button"));
  }

  /* ----------------------------------------------------
     16. INIT
     ---------------------------------------------------- */

  async function init() {
    wireEvents();
    tickClock();
    setInterval(tickClock, 1000);
    setInterval(() => { if (state.timetable.length) renderTimetable(); renderAttendance(); }, 30000);

    await Promise.all([loadMe(), loadHierarchy(), loadTimetable(), loadStudents()]);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
