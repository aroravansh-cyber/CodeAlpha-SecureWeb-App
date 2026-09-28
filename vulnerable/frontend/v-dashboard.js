(function () {
  "use strict";

  const CONFIG = {
    API_BASE: "http://127.0.0.1:5000/api",
    LOGIN_URL: "v-index.html",
    ATTENDANCE_WINDOW_HOURS: 3
  };

  const state = {
    me: null,
    timetable: [],
    students: [],
    activeLecture: null,
    attendanceRoster: [],
    hierarchy: {}
  };

  const $ = (sel, root) =>
    (root || document).querySelector(sel);

  const $all = (sel, root) =>
    Array.from(
      (root || document).querySelectorAll(sel)
    );

  function el(tag, props, children) {
    const node = document.createElement(tag);

    Object.entries(props || {}).forEach(([key, value]) => {
      if (key === "class") {
        node.className = value;
      } else if (key.startsWith("data-")) {
        node.setAttribute(key, value);
      } else {
        node[key] = value;
      }
    });

    (children || []).forEach((child) => {
      node.appendChild(
        typeof child === "string"
          ? document.createTextNode(child)
          : child
      );
    });

    return node;
  }

  function showToast(message, type) {
    const toast = $("#toast");

    if (!toast) {
      alert(message);
      return;
    }

    toast.textContent = message;
    toast.className =
      "toast toast--" + (type || "info");

    toast.classList.add("is-visible");

    clearTimeout(window.__toastTimer);

    window.__toastTimer = setTimeout(() => {
      toast.classList.remove("is-visible");
    }, 3000);
  }

  function initials(name) {
    return (name || "Faculty")
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((word) => word[0].toUpperCase())
      .join("");
  }

  function avatarPlaceholder(name) {
    return (
      "data:image/svg+xml;charset=UTF-8," +
      encodeURIComponent(`
        <svg xmlns="http://www.w3.org/2000/svg"
             width="100"
             height="100"
             viewBox="0 0 100 100">
          <rect width="100" height="100" rx="50" fill="#15181c"/>
          <text x="50"
                y="55"
                text-anchor="middle"
                font-family="Arial"
                font-size="32"
                fill="#3fb8e8">
            ${initials(name)}
          </text>
        </svg>
      `)
    );
  }

  async function apiRequest(path, options) {
    const opts = Object.assign(
      {
        credentials: "include",
        headers: {}
      },
      options || {}
    );

    if (
      opts.body &&
      !(opts.body instanceof FormData)
    ) {
      opts.headers["Content-Type"] =
        "application/json";
    }

    let response;

    try {
      response = await fetch(
        CONFIG.API_BASE + path,
        opts
      );
    } catch (error) {
      throw {
        networkError: true,
        message: "Could not reach the server."
      };
    }

    if (
      response.status === 401 ||
      response.status === 403
    ) {
      window.location.href =
        CONFIG.LOGIN_URL;

      throw {
        authError: true
      };
    }

    let data = null;

    try {
      data = await response.json();
    } catch (error) {}

    if (!response.ok) {
      throw {
        apiError: true,
        status: response.status,
        message:
          (data && data.message) ||
          "Request failed."
      };
    }

    return data;
  }

  async function loadMe() {
    try {
      state.me = await apiRequest("/me");
      renderProfile();
    } catch (err) {
      if (err.authError) return;

      showToast(
        "Could not load faculty profile.",
        "error"
      );
    }
  }

  async function loadHierarchy() {
    try {
      state.hierarchy =
        await apiRequest("/hierarchy");

      populateHierarchyFilters();
    } catch (err) {
      if (err.authError) return;

      showToast(
        "Could not load program hierarchy.",
        "error"
      );
    }
  }

  async function loadTimetable() {
    try {
      state.timetable =
        await apiRequest("/timetable");

      renderTimetable();
      renderDashboardTimetablePreview();
      renderStats();
    } catch (err) {
      if (err.authError) return;

      state.timetable = [];

      renderTimetable();
      renderDashboardTimetablePreview();
      renderStats();

      showToast(
        "Could not load timetable.",
        "error"
      );
    }
  }

  async function loadStudents() {
    try {
      state.students =
        await apiRequest("/students");

      renderStudents();
      renderStats();
    } catch (err) {
      if (err.authError) return;

      state.students = [];

      renderStudents();
      renderStats();

      showToast(
        "Could not load students.",
        "error"
      );
    }
  }

  async function loadAttendanceForLecture(
    lecture
  ) {
    state.activeLecture = lecture;

    try {
      state.attendanceRoster =
        await apiRequest(
          "/attendance?lecture_id=" +
            encodeURIComponent(lecture.id)
        );

      renderAttendance();
    } catch (err) {
      if (err.authError) return;

      state.attendanceRoster = [];

      renderAttendance();

      showToast(
        "Could not load attendance.",
        "error"
      );
    }
  }

  function renderProfile() {
    const me = state.me;

    if (!me) return;

    const name =
      me.full_name || "Faculty";

    const photo =
      me.photo_url ||
      avatarPlaceholder(name);

    if ($("#chipName")) {
      $("#chipName").textContent = name;
    }

    if ($("#chipAvatar")) {
      $("#chipAvatar").src = photo;
    }

    if ($("#profFullName")) {
      $("#profFullName").textContent =
        me.full_name || "–";
    }

    if ($("#profEmail")) {
      $("#profEmail").textContent =
        me.email || "–";
    }

    if ($("#profStaffId")) {
      $("#profStaffId").textContent =
        me.faculty_id || "–";
    }

    if ($("#profDesignation")) {
      $("#profDesignation").textContent =
        me.designation || "–";
    }

    if ($("#profBranch")) {
      $("#profBranch").textContent =
        me.department || "–";
    }

    if ($("#profilePhoto")) {
      $("#profilePhoto").src = photo;
    }

    const preview =
      $("#dashboardProfilePreview");

    if (!preview) return;

    preview.innerHTML = "";

    preview.appendChild(
      el(
        "div",
        {
          class: "profile-card"
        },
        [
          el(
            "div",
            {
              class: "profile-card__photo"
            },
            [
              el(
                "img",
                {
                  src: photo,
                  alt: ""
                }
              )
            ]
          ),

          el(
            "dl",
            {
              class: "profile-card__details"
            },
            [
              el(
                "div",
                {
                  class: "detail-row"
                },
                [
                  el("dt", {}, ["Name"]),
                  el(
                    "dd",
                    {},
                    [me.full_name || "–"]
                  )
                ]
              ),

              el(
                "div",
                {
                  class: "detail-row"
                },
                [
                  el(
                    "dt",
                    {},
                    ["Designation"]
                  ),
                  el(
                    "dd",
                    {},
                    [me.designation || "–"]
                  )
                ]
              ),

              el(
                "div",
                {
                  class: "detail-row"
                },
                [
                  el(
                    "dt",
                    {},
                    ["Program"]
                  ),
                  el(
                    "dd",
                    {},
                    [me.department || "–"]
                  )
                ]
              )
            ]
          )
        ]
      )
    );
  }

  async function handlePhotoUpload(file) {
    if (!file) return;

    const formData =
      new FormData();

    formData.append(
      "photo",
      file
    );

    try {
      const result =
        await apiRequest(
          "/profile/photo",
          {
            method: "POST",
            body: formData
          }
        );

      if (
        result &&
        result.photo_url
      ) {
        state.me.photo_url =
          result.photo_url;

        renderProfile();

        showToast(
          "Profile photo updated.",
          "success"
        );
      }
    } catch (err) {
      if (err.authError) return;

      showToast(
        "Couldn't upload photo.",
        "error"
      );
    }
  }

  function formatTime(iso) {
    const date =
      new Date(iso);

    return date.toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit"
      }
    );
  }

  function statusPill(status) {
    const safeStatus =
      status || "pending";

    return el(
      "span",
      {
        class:
          "status-pill status-pill--" +
          safeStatus
      },
      [
        safeStatus
          .charAt(0)
          .toUpperCase() +
          safeStatus.slice(1)
      ]
    );
  }

  function renderTimetable() {
    const body =
      $("#timetableBody");

    if (!body) return;

    body.innerHTML = "";

    if ($("#timetableDate")) {
      $("#timetableDate").textContent =
        new Date().toLocaleDateString(
          undefined,
          {
            weekday: "long",
            month: "short",
            day: "numeric"
          }
        );
    }

    if (
      state.timetable.length === 0
    ) {
      body.appendChild(
        el(
          "tr",
          {},
          [
            el(
              "td",
              {
                colspan: "8",
                class: "empty-note"
              },
              [
                "No lectures scheduled for today."
              ]
            )
          ]
        )
      );

      return;
    }

    state.timetable.forEach(
      (lecture) => {
        const row =
          el(
            "tr",
            {},
            [
              el(
                "td",
                {},
                [lecture.name]
              ),

              el(
                "td",
                {
                  class: "cell-id"
                },
                [
                  formatTime(
                    lecture.start_time
                  )
                ]
              ),

              el(
                "td",
                {
                  class: "cell-id"
                },
                [
                  formatTime(
                    lecture.end_time
                  )
                ]
              ),

              el(
                "td",
                {},
                [lecture.branch]
              ),

              el(
                "td",
                {},
                [lecture.year]
              ),

              el(
                "td",
                {},
                [lecture.room]
              ),

              el(
                "td",
                {},
                [
                  statusPill(
                    lecture.status
                  )
                ]
              ),

              el(
                "td",
                {},
                [
                  el(
                    "button",
                    {
                      class:
                        "row-link",
                      type:
                        "button",
                      "data-open-lecture":
                        lecture.id
                    },
                    [
                      "Take attendance →"
                    ]
                  )
                ]
              )
            ]
          );

        body.appendChild(row);
      }
    );

    $all(
      "[data-open-lecture]",
      body
    ).forEach((button) => {
      button.addEventListener(
        "click",
        () => {
          const lecture =
            state.timetable.find(
              (item) =>
                item.id ===
                button.getAttribute(
                  "data-open-lecture"
                )
            );

          if (!lecture) return;

          switchView(
            "attendance"
          );

          loadAttendanceForLecture(
            lecture
          );
        }
      );
    });
  }

  function renderDashboardTimetablePreview() {
    const preview =
      $("#dashboardTimetablePreview");

    if (!preview) return;

    preview.innerHTML = "";

    const upcoming =
      state.timetable.slice(0, 4);

    if (upcoming.length === 0) {
      preview.appendChild(
        el(
          "p",
          {
            class: "empty-note"
          },
          [
            "No lectures scheduled for today."
          ]
        )
      );

      return;
    }

    const table =
      el(
        "table",
        {
          class: "data-table"
        }
      );

    const tbody =
      el("tbody");

    upcoming.forEach(
      (lecture) => {
        tbody.appendChild(
          el(
            "tr",
            {},
            [
              el(
                "td",
                {},
                [lecture.name]
              ),

              el(
                "td",
                {
                  class: "cell-id"
                },
                [
                  formatTime(
                    lecture.start_time
                  ) +
                  " – " +
                  formatTime(
                    lecture.end_time
                  )
                ]
              ),

              el(
                "td",
                {},
                [lecture.room]
              ),

              el(
                "td",
                {},
                [
                  statusPill(
                    lecture.status
                  )
                ]
              )
            ]
          )
        );
      }
    );

    table.appendChild(tbody);

    preview.appendChild(table);
  }

  function attendanceWindowInfo(
    lecture
  ) {
    const start =
      new Date(
        lecture.start_time
      );

    const windowEnd =
      new Date(
        start.getTime() +
          CONFIG.ATTENDANCE_WINDOW_HOURS *
            3600000
      );

    const now =
      new Date();

    return {
      open:
        now >= start &&
        now <= windowEnd,
      closesAt:
        windowEnd
    };
  }

  function renderAttendance() {
    const lecture =
      state.activeLecture;

    const body =
      $("#attendanceBody");

    if (!body) return;

    body.innerHTML = "";

    if (!lecture) {
      if (
        $("#attendanceLectureTitle")
      ) {
        $("#attendanceLectureTitle")
          .textContent =
          "Select a lecture";
      }

      if (
        $("#attendanceLectureMeta")
      ) {
        $("#attendanceLectureMeta")
          .textContent =
          "Choose a lecture from Timetable to take attendance.";
      }

      if (
        $("#attendanceWindowBadge")
      ) {
        $("#attendanceWindowBadge")
          .textContent =
          "Window: closed";
      }

      body.appendChild(
        el(
          "tr",
          {},
          [
            el(
              "td",
              {
                colspan: "5",
                class: "empty-note"
              },
              [
                "No lecture selected yet."
              ]
            )
          ]
        )
      );

      return;
    }

    const win =
      attendanceWindowInfo(
        lecture
      );

    if (
      $("#attendanceLectureTitle")
    ) {
      $("#attendanceLectureTitle")
        .textContent =
        lecture.name;
    }

    if (
      $("#attendanceLectureMeta")
    ) {
      $("#attendanceLectureMeta")
        .textContent =
        lecture.branch +
        " · " +
        lecture.year +
        " · Room " +
        lecture.room +
        " · " +
        formatTime(
          lecture.start_time
        ) +
        "–" +
        formatTime(
          lecture.end_time
        );
    }

    if (
      $("#attendanceWindowBadge")
    ) {
      $("#attendanceWindowBadge")
        .textContent = win.open
          ? "Window open until " +
            win.closesAt.toLocaleTimeString(
              [],
              {
                hour: "2-digit",
                minute: "2-digit"
              }
            )
          : "Window: closed";

      $("#attendanceWindowBadge")
        .className =
        "badge" +
        (
          win.open
            ? ""
            : " badge--muted"
        );
    }

    const search =
      (
        $("#attendanceSearch")?.value ||
        ""
      ).toLowerCase();

    const statusFilter =
      $("#attendanceStatusFilter")
        ?.value || "";

    const rows =
      state.attendanceRoster.filter(
        (student) => {

          const name =
            (
              student.name || ""
            ).toLowerCase();

          const roll =
            (
              student.roll_no ||
              student.id ||
              ""
            ).toLowerCase();

          const matchesSearch =
            !search ||
            name.includes(search) ||
            roll.includes(search);

          const matchesStatus =
            statusFilter === "all" ||
            !statusFilter ||
            student.status ===
              statusFilter;

          return (
            matchesSearch &&
            matchesStatus
          );
        }
      );

    if (rows.length === 0) {
      body.appendChild(
        el(
          "tr",
          {},
          [
            el(
              "td",
              {
                colspan: "5",
                class: "empty-note"
              },
              [
                "No students match your filters."
              ]
            )
          ]
        )
      );

      return;
    }

    rows.forEach(
      (student) => {

        const markButton =
          el(
            "button",
            {
              class:
                "btn btn--primary btn--sm",
              type:
                "button",
              "data-mark-present":
                student.id
            },
            [
              student.status ===
              "present"
                ? "Present"
                : "Mark Present"
            ]
          );

        if (
          student.status ===
            "present" ||
          !win.open
        ) {
          markButton.disabled =
            true;
        }

        body.appendChild(
          el(
            "tr",
            {},
            [
              el(
                "td",
                {},
                [
                  el(
                    "img",
                    {
                      class:
                        "avatar-sm",
                      src:
                        student.photo_url ||
                        avatarPlaceholder(
                          student.name
                        ),
                      alt: ""
                    }
                  )
                ]
              ),

              el(
                "td",
                {
                  class:
                    "cell-id"
                },
                [
                  student.roll_no ||
                  student.id
                ]
              ),

              el(
                "td",
                {},
                [
                  student.name
                ]
              ),

              el(
                "td",
                {},
                [
                  statusPill(
                    student.status ||
                      "pending"
                  )
                ]
              ),

              el(
                "td",
                {},
                [
                  markButton
                ]
              )
            ]
          )
        );
      }
    );

    $all(
      "[data-mark-present]",
      body
    ).forEach((button) => {
      button.addEventListener(
        "click",
        () =>
          markPresent(
            button.getAttribute(
              "data-mark-present"
            )
          )
      );
    });
  }

  async function markPresent(
    studentId
  ) {
    const lecture =
      state.activeLecture;

    if (!lecture) return;

    try {
      const result =
        await apiRequest(
          "/attendance",
          {
            method: "POST",
            body: JSON.stringify({
              student_id:
                studentId,
              lecture_id:
                lecture.id
            })
          }
        );

      const status =
        (
          result &&
          result.status
        ) ||
        "present";

      updateStudentStatus(
        studentId,
        status
      );

      showToast(
        "Marked present.",
        "success"
      );
    } catch (err) {
      if (err.authError) return;

      if (
        err.apiError &&
        err.status === 409
      ) {
        showToast(
          err.message ||
            "Attendance window has closed.",
          "error"
        );
      } else {
        showToast(
          err.message ||
            "Couldn't mark attendance.",
          "error"
        );
      }
    }

    renderAttendance();
    renderStats();
  }

  function updateStudentStatus(
    studentId,
    status
  ) {
    state.attendanceRoster =
      state.attendanceRoster.map(
        (student) =>
          student.id === studentId
            ? Object.assign(
                {},
                student,
                { status }
              )
            : student
      );

    state.students =
      state.students.map(
        (student) =>
          student.id === studentId
            ? Object.assign(
                {},
                student,
                { status }
              )
            : student
      );
  }

  function populateHierarchyFilters() {
    const facultySelect =
      $("#filterFaculty");

    if (!facultySelect) return;

    facultySelect.innerHTML =
      '<option value="">Faculty: All</option>';

    Object.keys(
      state.hierarchy || {}
    ).forEach(
      (faculty) => {
        facultySelect.appendChild(
          el(
            "option",
            {
              value: faculty
            },
            [faculty]
          )
        );
      }
    );
  }

  function refreshBranchOptions() {
    const facultySelect =
      $("#filterFaculty");

    const branchSelect =
      $("#filterBranch");

    if (
      !facultySelect ||
      !branchSelect
    ) {
      return;
    }

    branchSelect.innerHTML =
      '<option value="">Branch: All</option>';

    const faculty =
      state.hierarchy[
        facultySelect.value
      ];

    if (faculty) {
      Object.keys(faculty).forEach(
        (program) => {
          branchSelect.appendChild(
            el(
              "option",
              {
                value: program
              },
              [program]
            )
          );
        }
      );
    }

    refreshSpecializationOptions();
  }

  function refreshSpecializationOptions() {
    const facultySelect =
      $("#filterFaculty");

    const branchSelect =
      $("#filterBranch");

    const specSelect =
      $("#filterSpecialization");

    if (
      !facultySelect ||
      !branchSelect ||
      !specSelect
    ) {
      return;
    }

    specSelect.innerHTML =
      '<option value="">Specialization: All</option>';

    const faculty =
      state.hierarchy[
        facultySelect.value
      ];

    const branch =
      faculty &&
      faculty[
        branchSelect.value
      ];

    if (
      branch &&
      Array.isArray(
        branch.specializations
      )
    ) {
      branch.specializations.forEach(
        (spec) => {
          specSelect.appendChild(
            el(
              "option",
              {
                value: spec
              },
              [spec]
            )
          );
        }
      );
    }

    refreshYearOptions();
  }

  function refreshYearOptions() {
    const facultySelect =
      $("#filterFaculty");

    const branchSelect =
      $("#filterBranch");

    const yearSelect =
      $("#filterYear");

    if (
      !facultySelect ||
      !branchSelect ||
      !yearSelect
    ) {
      return;
    }

    yearSelect.innerHTML =
      '<option value="">Year: All</option>';

    const faculty =
      state.hierarchy[
        facultySelect.value
      ];

    const branch =
      faculty &&
      faculty[
        branchSelect.value
      ];

    const years =
      branch &&
      Array.isArray(
        branch.years
      )
        ? branch.years
        : [];

    years.forEach(
      (year) => {
        yearSelect.appendChild(
          el(
            "option",
            {
              value: year
            },
            [year]
          )
        );
      }
    );
  }

  function renderStudents() {
    const body =
      $("#studentsBody");

    if (!body) return;

    body.innerHTML = "";

    const search =
      (
        $("#studentSearch")?.value ||
        ""
      ).toLowerCase();

    const faculty =
      $("#filterFaculty")?.value ||
      "";

    const branch =
      $("#filterBranch")?.value ||
      "";

    const spec =
      $("#filterSpecialization")
        ?.value || "";

    const year =
      $("#filterYear")?.value ||
      "";

    const status =
      $("#filterStatus")?.value ||
      "";

    const rows =
      state.students.filter(
        (student) => {

          const name =
            (
              student.name || ""
            ).toLowerCase();

          const roll =
            (
              student.roll_no ||
              student.id ||
              ""
            ).toLowerCase();

          if (
            search &&
            !(
              name.includes(search) ||
              roll.includes(search)
            )
          ) {
            return false;
          }

          if (
            faculty &&
            student.faculty !==
              faculty
          ) {
            return false;
          }

          if (
            branch &&
            student.branch !==
              branch
          ) {
            return false;
          }

          if (
            spec &&
            student.specialization !==
              spec
          ) {
            return false;
          }

          if (
            year &&
            student.year !==
              year
          ) {
            return false;
          }

          if (
            status &&
            student.status !==
              status
          ) {
            return false;
          }

          return true;
        }
      );

    if (rows.length === 0) {
      body.appendChild(
        el(
          "tr",
          {},
          [
            el(
              "td",
              {
                colspan: "7",
                class: "empty-note"
              },
              [
                "No students match your filters."
              ]
            )
          ]
        )
      );

      return;
    }

    rows.forEach(
      (student) => {

        body.appendChild(
          el(
            "tr",
            {},
            [
              el(
                "td",
                {},
                [
                  el(
                    "img",
                    {
                      class:
                        "avatar-sm",
                      src:
                        student.photo_url ||
                        avatarPlaceholder(
                          student.name
                        ),
                      alt: ""
                    }
                  )
                ]
              ),

              el(
                "td",
                {
                  class:
                    "cell-id"
                },
                [
                  student.roll_no ||
                  student.id
                ]
              ),

              el(
                "td",
                {},
                [
                  student.name
                ]
              ),

              el(
                "td",
                {},
                [
                  student.branch
                ]
              ),

              el(
                "td",
                {},
                [
                  student.specialization ||
                  "—"
                ]
              ),

              el(
                "td",
                {},
                [
                  student.year
                ]
              ),

              el(
                "td",
                {},
                [
                  statusPill(
                    student.status ||
                      "pending"
                  )
                ]
              )
            ]
          )
        );
      }
    );
  }

  function renderStats() {
    const total =
      state.students.length;

    const present =
      state.students.filter(
        (student) =>
          student.status ===
          "present"
      ).length;

    const absent =
      state.students.filter(
        (student) =>
          student.status ===
          "absent"
      ).length;

    const pending =
      total -
      present -
      absent;

    if ($("#statTotal")) {
      $("#statTotal").textContent =
        total;
    }

    if ($("#statPresent")) {
      $("#statPresent").textContent =
        present;
    }

    if ($("#statAbsent")) {
      $("#statAbsent").textContent =
        absent;
    }

    if ($("#statPending")) {
      $("#statPending").textContent =
        Math.max(
          pending,
          0
        );
    }

    if ($("#statLectures")) {
      $("#statLectures").textContent =
        state.timetable.length;
    }
  }

  const VIEW_TITLES = {
    dashboard: "Dashboard",
    timetable: "Timetable",
    attendance: "Attendance",
    students: "Students",
    profile: "Profile",
    settings: "Settings"
  };

  function switchView(
    viewName
  ) {
    $all(".view").forEach(
      (view) =>
        view.classList.remove(
          "is-active"
        )
    );

    const target =
      $("#view-" + viewName);

    if (target) {
      target.classList.add(
        "is-active"
      );
    }

    $all(
      ".nav__item[data-view]"
    ).forEach(
      (button) => {
        button.classList.toggle(
          "is-active",
          button.getAttribute(
            "data-view"
          ) === viewName
        );
      }
    );

    if ($("#viewTitle")) {
      $("#viewTitle").textContent =
        VIEW_TITLES[
          viewName
        ] ||
        "Dashboard";
    }

    closeSidebarOnMobile();
  }

  function closeSidebarOnMobile() {
    if ($("#sidebar")) {
      $("#sidebar").classList.remove(
        "is-open"
      );
    }

    if ($("#topbarScrim")) {
      $("#topbarScrim").classList.remove(
        "is-visible"
      );
    }
  }

  function tickClock() {
    if ($("#liveClock")) {
      $("#liveClock").textContent =
        new Date().toLocaleTimeString();
    }
  }

  async function logout() {
    try {
      await apiRequest(
        "/logout",
        {
          method: "POST"
        }
      );
    } catch (err) {}

    window.location.href =
      CONFIG.LOGIN_URL;
  }

  function wireEvents() {

    $all(
      ".nav__item[data-view]"
    ).forEach(
      (button) => {
        button.type =
          "button";

        button.addEventListener(
          "click",
          () =>
            switchView(
              button.getAttribute(
                "data-view"
              )
            )
        );
      }
    );

    $all(
      "[data-goto]"
    ).forEach(
      (button) => {
        button.addEventListener(
          "click",
          () =>
            switchView(
              button.getAttribute(
                "data-goto"
              )
            )
        );
      }
    );

    if ($("#logoutBtn")) {
      $("#logoutBtn")
        .addEventListener(
          "click",
          logout
        );
    }

    if (
      $("#settingsLogoutBtn")
    ) {
      $("#settingsLogoutBtn")
        .addEventListener(
          "click",
          logout
        );
    }

    if ($("#menuBtn")) {
      $("#menuBtn")
        .addEventListener(
          "click",
          () => {
            const isOpen =
              $("#sidebar")
                .classList.toggle(
                  "is-open"
                );

            if (
              $("#topbarScrim")
            ) {
              $("#topbarScrim")
                .classList.toggle(
                  "is-visible",
                  isOpen
                );
            }

            $("#menuBtn")
              .setAttribute(
                "aria-expanded",
                String(isOpen)
              );
          }
        );
    }

    if (
      $("#topbarScrim")
    ) {
      $("#topbarScrim")
        .addEventListener(
          "click",
          closeSidebarOnMobile
        );
    }

    if ($("#photoInput")) {
      $("#photoInput")
        .addEventListener(
          "change",
          (event) =>
            handlePhotoUpload(
              event.target.files[0]
            )
        );
    }

    if ($("#studentSearch")) {
      $("#studentSearch")
        .addEventListener(
          "input",
          renderStudents
        );
    }

    if ($("#filterFaculty")) {
      $("#filterFaculty")
        .addEventListener(
          "change",
          () => {
            refreshBranchOptions();
            renderStudents();
          }
        );
    }

    if ($("#filterBranch")) {
      $("#filterBranch")
        .addEventListener(
          "change",
          () => {
            refreshSpecializationOptions();
            renderStudents();
          }
        );
    }

    if (
      $("#filterSpecialization")
    ) {
      $("#filterSpecialization")
        .addEventListener(
          "change",
          renderStudents
        );
    }

    if ($("#filterYear")) {
      $("#filterYear")
        .addEventListener(
          "change",
          renderStudents
        );
    }

    if ($("#filterStatus")) {
      $("#filterStatus")
        .addEventListener(
          "change",
          renderStudents
        );
    }

    if (
      $("#attendanceSearch")
    ) {
      $("#attendanceSearch")
        .addEventListener(
          "input",
          renderAttendance
        );
    }

    if (
      $("#attendanceStatusFilter")
    ) {
      $("#attendanceStatusFilter")
        .addEventListener(
          "change",
          renderAttendance
        );
    }

    if ($("#globalSearch")) {
      $("#globalSearch")
        .addEventListener(
          "input",
          (event) => {
            switchView(
              "students"
            );

            if (
              $("#studentSearch")
            ) {
              $("#studentSearch")
                .value =
                event.target.value;
            }

            renderStudents();
          }
        );
    }
  }

  async function init() {
    wireEvents();

    tickClock();

    setInterval(
      tickClock,
      1000
    );

    setInterval(
      () => {
        if (
          state.timetable.length
        ) {
          renderTimetable();
        }

        if (
          state.activeLecture
        ) {
          renderAttendance();
        }
      },
      30000
    );

    await Promise.all([
      loadMe(),
      loadHierarchy(),
      loadTimetable(),
      loadStudents()
    ]);
  }

  document.addEventListener(
    "DOMContentLoaded",
    init
  );
})();