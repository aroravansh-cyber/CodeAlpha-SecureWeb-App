const CONFIG = {
    API_BASE: "http://127.0.0.1:5000/api",
    LOGIN_URL: "s-index.html",
    ATTENDANCE_WINDOW_HOURS: 3,
    REFRESH_INTERVAL: 30000
};

const state = {
    me: null,
    timetable: [],
    students: [],
    hierarchy: {},
    activeLecture: null,
    attendanceRoster: [],
    attendanceSummary: {
        total: 0,
        present: 0,
        absent: 0,
        pending: 0
    }
};

function $(id) {
    return document.getElementById(id);
}

function escapeHTML(value) {
    if (value === null || value === undefined) return "";

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function normalizeStatus(value) {
    const status = String(value || "pending").toLowerCase();

    if (
        [
            "present",
            "absent",
            "pending",
            "upcoming",
            "ongoing",
            "completed"
        ].includes(status)
    ) {
        return status;
    }

    return "pending";
}

function getLectureId(lecture) {
    return (
        lecture?.database_id ??
        lecture?.lecture_id ??
        lecture?.id ??
        null
    );
}

function getStudentId(student) {
    return (
        student?.student_id ??
        student?.id ??
        null
    );
}

async function apiRequest(endpoint, options = {}) {
    const request = {
        credentials: "include",
        ...options,
        headers: {
            ...(options.headers || {})
        }
    };

    if (!(options.body instanceof FormData)) {
        request.headers["Content-Type"] = "application/json";
    }

    const response = await fetch(
        CONFIG.API_BASE + endpoint,
        request
    );

    let data = {};

    try {
        data = await response.json();
    } catch {
        data = {};
    }

    if (
        response.status === 401 ||
        response.status === 403
    ) {
        window.location.href = CONFIG.LOGIN_URL;
        return null;
    }

    if (!response.ok) {
        throw new Error(
            data.message ||
            data.error ||
            `Request failed (${response.status})`
        );
    }

    return data;
}

function parseDateTime(value) {
    if (!value) return null;

    const raw = String(value).trim();

    let date = null;

    if (
        /^\d{2}:\d{2}(:\d{2})?$/.test(raw)
    ) {
        const now = new Date();

        const parts = raw.split(":");

        now.setHours(
            Number(parts[0]),
            Number(parts[1]),
            Number(parts[2] || 0),
            0
        );

        date = now;
    } else {
        date = new Date(raw);
    }

    return Number.isNaN(date.getTime())
        ? null
        : date;
}

function formatTime(value) {
    const date = parseDateTime(value);

    if (!date) {
        return (
            typeof value === "string" &&
            /^\d{2}:\d{2}/.test(value)
        )
            ? value.slice(0, 5)
            : "--:--";
    }

    return date.toLocaleTimeString(
        "en-IN",
        {
            hour: "2-digit",
            minute: "2-digit",
            hour12: true
        }
    );
}

function formatDate(value) {
    const date = parseDateTime(value);

    if (!date) {
        return "--";
    }

    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );
}

function formatDateTimeValue(value) {
    if (!value) {
        return "—";
    }

    const date = parseDateTime(value);

    if (!date) {
        return String(value);
    }

    return `${formatDate(value)} · ${formatTime(value)}`;
}

function getTodayISO() {
    const now = new Date();

    return (
        `${now.getFullYear()}-` +
        `${String(now.getMonth() + 1).padStart(2, "0")}-` +
        `${String(now.getDate()).padStart(2, "0")}`
    );
}

function isSameDay(value, isoDate) {
    const date = parseDateTime(value);

    if (!date) {
        return false;
    }

    const current =
        `${date.getFullYear()}-` +
        `${String(date.getMonth() + 1).padStart(2, "0")}-` +
        `${String(date.getDate()).padStart(2, "0")}`;

    return current === isoDate;
}

function getLectureStatus(lecture) {
    const backendStatus =
        normalizeStatus(lecture?.status);

    const start =
        parseDateTime(
            lecture?.start_time ||
            lecture?.start
        );

    const end =
        parseDateTime(
            lecture?.end_time ||
            lecture?.end
        );

    if (!start || !end) {
        return backendStatus;
    }

    const now = new Date();

    if (now < start) {
        return "upcoming";
    }

    if (now <= end) {
        return "ongoing";
    }

    return "completed";
}

function isAttendanceOpen(lecture) {
    if (
        lecture?.attendance_open === true
    ) {
        return true;
    }

    const start =
        parseDateTime(
            lecture?.start_time ||
            lecture?.start
        );

    if (!start) {
        return false;
    }

    const now = new Date();

    const deadline =
        new Date(
            start.getTime() +
            CONFIG.ATTENDANCE_WINDOW_HOURS *
            60 *
            60 *
            1000
        );

    return (
        now >= start &&
        now <= deadline
    );
}

function getAttendanceDeadline(lecture) {
    const start =
        parseDateTime(
            lecture?.start_time ||
            lecture?.start
        );

    if (!start) {
        return null;
    }

    return new Date(
        start.getTime() +
        CONFIG.ATTENDANCE_WINDOW_HOURS *
        60 *
        60 *
        1000
    );
}

function statusLabel(status) {
    const labels = {
        present: "Present",
        absent: "Absent",
        pending: "Pending",
        upcoming: "Upcoming",
        ongoing: "Ongoing",
        completed: "Completed"
    };

    return (
        labels[status] ||
        "Pending"
    );
}

function statusMarkup(status) {
    const safeStatus =
        normalizeStatus(status);

    return `
        <span
            class="status-pill status-pill--${safeStatus}"
        >
            ${statusLabel(safeStatus)}
        </span>
    `;
}

function showToast(
    message,
    type = ""
) {
    const toast = $("toast");

    if (!toast) {
        return;
    }

    toast.textContent = message;

    toast.className =
        `toast is-visible ${
            type ? `is-${type}` : ""
        }`.trim();

    clearTimeout(
        showToast.timer
    );

    showToast.timer =
        setTimeout(() => {
            toast.classList.remove(
                "is-visible"
            );
        }, 3000);
}

async function loadMe() {
    try {
        const data =
            await apiRequest("/me");

        if (!data) {
            return;
        }

        state.me =
            data.faculty ||
            data;

        renderProfile();
        renderDashboardProfile();

    } catch (error) {
        console.error(
            "Failed to load faculty:",
            error
        );

        showToast(
            "Unable to load faculty profile.",
            "error"
        );
    }
}

function renderProfile() {
    const me = state.me;

    if (!me) {
        return;
    }

    const name =
        me.full_name ||
        me.name ||
        "Faculty";

    const email =
        me.email ||
        "—";

    const facultyId =
        me.faculty_id ||
        me.staff_id ||
        me.id ||
        "—";

    const designation =
        me.designation ||
        "Faculty";

    const department =
        me.department ||
        me.program ||
        "—";

    const photo =
        me.photo_url ||
        me.photo ||
        "";

    if ($("chipName")) {
        $("chipName").textContent =
            name;
    }

    if ($("profFullName")) {
        $("profFullName").textContent =
            name;
    }

    if ($("profEmail")) {
        $("profEmail").textContent =
            email;
    }

    if ($("profStaffId")) {
        $("profStaffId").textContent =
            facultyId;
    }

    if ($("profDesignation")) {
        $("profDesignation").textContent =
            designation;
    }

    if ($("profBranch")) {
        $("profBranch").textContent =
            department;
    }

    if (photo) {
        if ($("profilePhoto")) {
            $("profilePhoto").src =
                photo;

            $("profilePhoto").alt =
                name;
        }

        if ($("chipAvatar")) {
            $("chipAvatar").src =
                photo;

            $("chipAvatar").alt =
                name;
        }
    }
}

function renderDashboardProfile() {
    const container =
        $("dashboardProfilePreview");

    const me =
        state.me;

    if (!container || !me) {
        return;
    }

    const name =
        me.full_name ||
        me.name ||
        "Faculty";

    const email =
        me.email ||
        "—";

    const designation =
        me.designation ||
        "Faculty";

    const department =
        me.department ||
        "—";

    const photo =
        me.photo_url ||
        me.photo ||
        "";

    const initial =
        name.charAt(0).toUpperCase();

    container.innerHTML = `
        <div class="profile-preview-content">

            <div class="profile-preview-avatar">

                ${
                    photo
                        ? `
                            <img
                                src="${escapeHTML(photo)}"
                                alt="${escapeHTML(name)}"
                            >
                        `
                        : `
                            <span>
                                ${escapeHTML(initial)}
                            </span>
                        `
                }

            </div>

            <div class="profile-preview-info">

                <strong>
                    ${escapeHTML(name)}
                </strong>

                <span>
                    ${escapeHTML(designation)}
                </span>

                <small>
                    ${escapeHTML(department)}
                </small>

                <small>
                    ${escapeHTML(email)}
                </small>

            </div>

        </div>
    `;
}

async function loadHierarchy() {
    try {
        const data =
            await apiRequest(
                "/hierarchy"
            );

        if (!data) {
            return;
        }

        state.hierarchy =
            data.programs ||
            data ||
            {};

    } catch (error) {
        console.error(
            "Failed to load hierarchy:",
            error
        );
    }
}

async function loadTimetable() {
    try {
        const data =
            await apiRequest(
                "/timetable"
            );

        if (!data) {
            return;
        }

        state.timetable =
            Array.isArray(data)
                ? data
                : data.timetable ||
                  data.lectures ||
                  [];

        renderTimetableDate();
        renderTimetable();
        renderDashboardTimetable();
        renderStats();

    } catch (error) {
        console.error(
            "Failed to load timetable:",
            error
        );

        renderTimetableError();
    }
}

function renderTimetableDate() {
    const target =
        $("timetableDate");

    if (!target) {
        return;
    }

    target.textContent =
        new Date().toLocaleDateString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric"
            }
        );
}

function renderTimetableError() {
    const body =
        $("timetableBody");

    if (!body) {
        return;
    }

    body.innerHTML = `
        <tr>
            <td
                colspan="8"
                class="empty-note"
            >
                Unable to load timetable.
            </td>
        </tr>
    `;
}

function renderTimetable() {
    const body =
        $("timetableBody");

    if (!body) {
        return;
    }

    if (!state.timetable.length) {
        body.innerHTML = `
            <tr>
                <td
                    colspan="8"
                    class="empty-note"
                >
                    No timetable available.
                </td>
            </tr>
        `;

        return;
    }

    const sorted =
        [...state.timetable].sort(
            (a, b) => {

                const first =
                    parseDateTime(
                        a.start_time ||
                        a.start
                    )?.getTime() || 0;

                const second =
                    parseDateTime(
                        b.start_time ||
                        b.start
                    )?.getTime() || 0;

                return first - second;
            }
        );

    body.innerHTML =
        sorted.map(lecture => {

            const id =
                getLectureId(
                    lecture
                );

            const status =
                getLectureStatus(
                    lecture
                );

            const attendanceOpen =
                isAttendanceOpen(
                    lecture
                );

            const subject =
                lecture.subject ||
                lecture.name ||
                "Untitled Lecture";

            const program =
                lecture.program ||
                lecture.branch ||
                "—";

            const year =
                lecture.year ||
                "—";

            const room =
                lecture.room ||
                "—";

            const start =
                lecture.start_time ||
                lecture.start;

            const end =
                lecture.end_time ||
                lecture.end;

            let attendanceCell =
                `<span class="text-muted">—</span>`;

            if (
                id !== null &&
                attendanceOpen
            ) {
                attendanceCell = `
                    <button
                        type="button"
                        class="btn btn--primary btn--sm"
                        data-open-attendance="${escapeHTML(id)}"
                    >
                        Take Attendance
                    </button>
                `;
            } else if (
                status === "completed"
            ) {
                attendanceCell =
                    `<span class="text-muted">Closed</span>`;
            } else if (
                status === "upcoming"
            ) {
                attendanceCell =
                    `<span class="text-muted">Not open</span>`;
            }

            return `
                <tr>

                    <td>

                        <div
                            class="timetable-course"
                        >

                            ${escapeHTML(subject)}

                            ${
                                lecture.specialization
                                    ? `
                                        <small>
                                            ${escapeHTML(
                                                lecture.specialization
                                            )}
                                        </small>
                                    `
                                    : ""
                            }

                        </div>

                    </td>

                    <td class="timetable-time">
                        ${escapeHTML(
                            formatTime(start)
                        )}
                    </td>

                    <td class="timetable-time">
                        ${escapeHTML(
                            formatTime(end)
                        )}
                    </td>

                    <td class="timetable-program">
                        ${escapeHTML(program)}
                    </td>

                    <td class="timetable-year">
                        ${escapeHTML(year)}
                    </td>

                    <td class="timetable-room">
                        ${escapeHTML(room)}
                    </td>

                    <td>
                        ${statusMarkup(status)}
                    </td>

                    <td>
                        ${attendanceCell}
                    </td>

                </tr>
            `;

        }).join("");
}

function renderDashboardTimetable() {
    const container =
        $("dashboardTimetablePreview");

    if (!container) {
        return;
    }

    const today =
        getTodayISO();

    let lectures =
        state.timetable.filter(
            lecture =>
                isSameDay(
                    lecture.start_time ||
                    lecture.start,
                    today
                )
        );

    if (!lectures.length) {
        lectures =
            [...state.timetable]
                .sort(
                    (a, b) => {

                        const first =
                            parseDateTime(
                                a.start_time ||
                                a.start
                            )?.getTime() || 0;

                        const second =
                            parseDateTime(
                                b.start_time ||
                                b.start
                            )?.getTime() || 0;

                        return first - second;
                    }
                )
                .slice(0, 5);
    }

    if (!lectures.length) {
        container.innerHTML = `
            <p class="empty-note">
                No lectures scheduled.
            </p>
        `;

        return;
    }

    container.innerHTML =
        lectures
            .slice(0, 5)
            .map(lecture => {

                const status =
                    getLectureStatus(
                        lecture
                    );

                const subject =
                    lecture.subject ||
                    lecture.name ||
                    "Lecture";

                const program =
                    lecture.program ||
                    lecture.branch ||
                    "—";

                const year =
                    lecture.year ||
                    "—";

                const room =
                    lecture.room ||
                    "—";

                return `
                    <div
                        class="lecture-preview-row"
                    >

                        <div
                            class="lecture-preview-time"
                        >
                            ${escapeHTML(
                                formatTime(
                                    lecture.start_time ||
                                    lecture.start
                                )
                            )}
                        </div>

                        <div
                            class="lecture-preview-main"
                        >

                            <strong>
                                ${escapeHTML(subject)}
                            </strong>

                            <span>
                                ${escapeHTML(program)}
                                ·
                                ${escapeHTML(year)}
                            </span>

                        </div>

                        <div
                            class="lecture-preview-room"
                        >
                            ${escapeHTML(room)}
                        </div>

                        ${statusMarkup(status)}

                    </div>
                `;
            })
            .join("");
}

async function loadStudents() {
    try {
        const data =
            await apiRequest(
                "/students"
            );

        if (!data) {
            return;
        }

        state.students =
            Array.isArray(data)
                ? data
                : data.students ||
                  [];

        populateStudentFilters();
        renderStudents();
        renderStats();

    } catch (error) {
        console.error(
            "Failed to load students:",
            error
        );

        const body =
            $("studentsBody");

        if (body) {
            body.innerHTML = `
                <tr>
                    <td
                        colspan="7"
                        class="empty-note"
                    >
                        Unable to load students.
                    </td>
                </tr>
            `;
        }
    }
}

function setSelectOptions(
    select,
    label,
    values
) {
    if (!select) {
        return;
    }

    const current =
        select.value;

    select.innerHTML =
        `<option value="">${escapeHTML(label)}</option>` +
        values
            .map(
                value => `
                    <option
                        value="${escapeHTML(value)}"
                    >
                        ${escapeHTML(value)}
                    </option>
                `
            )
            .join("");

    if (values.includes(current)) {
        select.value =
            current;
    }
}

function populateStudentFilters() {
    const branches =
        [
            ...new Set(
                state.students
                    .map(
                        student =>
                            student.program ||
                            student.branch
                    )
                    .filter(Boolean)
            )
        ].sort();

    const specializations =
        [
            ...new Set(
                state.students
                    .map(
                        student =>
                            student.specialization
                    )
                    .filter(Boolean)
            )
        ].sort();

    const years =
        [
            ...new Set(
                state.students
                    .map(
                        student =>
                            student.year
                    )
                    .filter(Boolean)
            )
        ].sort();

    const facultyNames =
        [
            ...new Set(
                state.students
                    .map(
                        student =>
                            student.faculty ||
                            student.faculty_name
                    )
                    .filter(Boolean)
            )
        ].sort();

    setSelectOptions(
        $("filterBranch"),
        "Branch: All",
        branches
    );

    setSelectOptions(
        $("filterSpecialization"),
        "Specialization: All",
        specializations
    );

    setSelectOptions(
        $("filterYear"),
        "Year: All",
        years
    );

    setSelectOptions(
        $("filterFaculty"),
        "Faculty: All",
        facultyNames
    );
}

function renderStudents() {
    const body =
        $("studentsBody");

    if (!body) {
        return;
    }

    const search =
        (
            $("studentSearch")?.value ||
            ""
        )
            .trim()
            .toLowerCase();

    const facultyFilter =
        $("filterFaculty")?.value ||
        "";

    const branchFilter =
        $("filterBranch")?.value ||
        "";

    const specializationFilter =
        $("filterSpecialization")?.value ||
        "";

    const yearFilter =
        $("filterYear")?.value ||
        "";

    const statusFilter =
        (
            $("filterStatus")?.value ||
            ""
        ).toLowerCase();

    const filtered =
        state.students.filter(
            student => {

                const name =
                    String(
                        student.name ||
                        student.full_name ||
                        ""
                    ).toLowerCase();

                const roll =
                    String(
                        student.roll_no ||
                        student.roll_number ||
                        ""
                    ).toLowerCase();

                const program =
                    String(
                        student.program ||
                        student.branch ||
                        ""
                    );

                const specialization =
                    String(
                        student.specialization ||
                        ""
                    );

                const year =
                    String(
                        student.year ||
                        student.study_year ||
                        ""
                    );

                const status =
                    normalizeStatus(
                        student.status
                    );

                const faculty =
                    String(
                        student.faculty ||
                        student.faculty_name ||
                        ""
                    );

                const matchesSearch =
                    !search ||
                    name.includes(search) ||
                    roll.includes(search) ||
                    program
                        .toLowerCase()
                        .includes(search) ||
                    specialization
                        .toLowerCase()
                        .includes(search);

                return (
                    matchesSearch &&
                    (
                        !facultyFilter ||
                        faculty === facultyFilter
                    ) &&
                    (
                        !branchFilter ||
                        program === branchFilter
                    ) &&
                    (
                        !specializationFilter ||
                        specialization ===
                            specializationFilter
                    ) &&
                    (
                        !yearFilter ||
                        year === yearFilter
                    ) &&
                    (
                        !statusFilter ||
                        status === statusFilter
                    )
                );
            }
        );

    if (!filtered.length) {
        body.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="empty-note"
                >
                    No students found.
                </td>
            </tr>
        `;

        return;
    }

    body.innerHTML =
        filtered
            .map(student => {

                const name =
                    student.name ||
                    student.full_name ||
                    "Unknown Student";

                const roll =
                    student.roll_no ||
                    student.roll_number ||
                    "—";

                const program =
                    student.program ||
                    student.branch ||
                    "—";

                const specialization =
                    student.specialization ||
                    "—";

                const year =
                    student.year ||
                    student.study_year ||
                    "—";

                const status =
                    normalizeStatus(
                        student.status
                    );

                const photo =
                    student.photo_url ||
                    student.photo ||
                    "";

                const initial =
                    name
                        .charAt(0)
                        .toUpperCase();

                const avatar =
                    photo
                        ? `
                            <img
                                src="${escapeHTML(photo)}"
                                alt="${escapeHTML(name)}"
                            >
                        `
                        : `
                            <span>
                                ${escapeHTML(initial)}
                            </span>
                        `;

                return `
                    <tr>

                        <td>
                            <div
                                class="student-avatar"
                            >
                                ${avatar}
                            </div>
                        </td>

                        <td>
                            <strong>
                                ${escapeHTML(roll)}
                            </strong>
                        </td>

                        <td>
                            ${escapeHTML(name)}
                        </td>

                        <td>
                            ${escapeHTML(program)}
                        </td>

                        <td>
                            ${escapeHTML(
                                specialization
                            )}
                        </td>

                        <td>
                            ${escapeHTML(year)}
                        </td>

                        <td>
                            ${statusMarkup(status)}
                        </td>

                    </tr>
                `;
            })
            .join("");
}

async function openAttendance(lecture) {
    if (!lecture) {
        return;
    }

    state.activeLecture =
        lecture;

    state.attendanceRoster =
        [];

    state.attendanceSummary = {
        total: 0,
        present: 0,
        absent: 0,
        pending: 0
    };

    switchView(
        "attendance"
    );

    renderAttendanceSession();
    renderAttendance();

    const lectureId =
        getLectureId(lecture);

    if (lectureId === null) {
        showToast(
            "Lecture ID is missing.",
            "error"
        );

        return;
    }

    try {
        const data =
            await apiRequest(
                `/attendance/${encodeURIComponent(
                    lectureId
                )}`
            );

        if (!data) {
            return;
        }

        state.attendanceRoster =
            data.students ||
            data.roster ||
            data.attendance ||
            [];

        state.attendanceSummary =
            data.summary ||
            calculateAttendanceSummary(
                state.attendanceRoster
            );

        renderAttendanceSession();
        renderAttendance();
        renderStats();

    } catch (error) {
        console.error(
            "Attendance load failed:",
            error
        );

        const body =
            $("attendanceBody");

        if (body) {
            body.innerHTML = `
                <tr>
                    <td
                        colspan="7"
                        class="empty-note"
                    >
                        Unable to load attendance.
                    </td>
                </tr>
            `;
        }

        showToast(
            error.message ||
            "Unable to load attendance.",
            "error"
        );
    }
}

function renderAttendanceSession() {
    const lecture =
        state.activeLecture;

    if (!lecture) {
        return;
    }

    const subject =
        lecture.subject ||
        lecture.name ||
        "Attendance";

    const program =
        lecture.program ||
        lecture.branch ||
        "—";

    const year =
        lecture.year ||
        "—";

    const room =
        lecture.room ||
        "—";

    const deadline =
        getAttendanceDeadline(
            lecture
        );

    const open =
        isAttendanceOpen(
            lecture
        );

    if ($("attendanceLectureTitle")) {
        $("attendanceLectureTitle")
            .textContent =
            subject;
    }

    if ($("attendanceLectureMeta")) {
        $("attendanceLectureMeta")
            .textContent =
            `${program} · ${year} · ${room}`;
    }

    if ($("attendanceWindowBadge")) {
        $("attendanceWindowBadge")
            .textContent =
            open
                ? "Attendance Open"
                : "Attendance Closed";

        $("attendanceWindowBadge")
            .className =
            `badge ${
                open
                    ? "badge--good"
                    : "badge--muted"
            }`;
    }

    if ($("attendanceClassName")) {
        $("attendanceClassName")
            .textContent =
            `${program} · ${year}`;
    }

    if ($("attendanceDate")) {
        $("attendanceDate")
            .textContent =
            formatDate(
                lecture.start_time ||
                lecture.start
            );
    }

    if ($("attendanceLectureTime")) {
        $("attendanceLectureTime")
            .textContent =
            `${formatTime(
                lecture.start_time ||
                lecture.start
            )} – ${formatTime(
                lecture.end_time ||
                lecture.end
            )}`;
    }

    if ($("attendanceDeadline")) {
        $("attendanceDeadline")
            .textContent =
            deadline
                ? formatTime(deadline)
                : "—";
    }
}

function calculateAttendanceSummary(
    roster
) {
    const total =
        roster.length;

    const present =
        roster.filter(
            student =>
                normalizeStatus(
                    student.status
                ) === "present"
        ).length;

    const absent =
        roster.filter(
            student =>
                normalizeStatus(
                    student.status
                ) === "absent"
        ).length;

    const pending =
        total -
        present -
        absent;

    return {
        total,
        present,
        absent,
        pending
    };
}

function renderAttendance() {
    const body =
        $("attendanceBody");

    if (!body) {
        return;
    }

    const search =
        (
            $("attendanceSearch")?.value ||
            ""
        )
            .trim()
            .toLowerCase();

    const statusFilter =
        (
            $("attendanceStatusFilter")
                ?.value ||
            ""
        ).toLowerCase();

    const filtered =
        state.attendanceRoster.filter(
            student => {

                const name =
                    String(
                        student.name ||
                        student.full_name ||
                        ""
                    ).toLowerCase();

                const roll =
                    String(
                        student.roll_no ||
                        student.roll_number ||
                        ""
                    ).toLowerCase();

                const status =
                    normalizeStatus(
                        student.status
                    );

                return (
                    (
                        !search ||
                        name.includes(search) ||
                        roll.includes(search)
                    ) &&
                    (
                        !statusFilter ||
                        statusFilter === "all" ||
                        status === statusFilter
                    )
                );
            }
        );

    if (!filtered.length) {
        body.innerHTML = `
            <tr>
                <td
                    colspan="7"
                    class="empty-note"
                >
                    No students found.
                </td>
            </tr>
        `;

        updateAttendanceSummary();

        return;
    }

    const attendanceOpen =
        isAttendanceOpen(
            state.activeLecture
        );

    body.innerHTML =
        filtered
            .map(student => {

                const id =
                    getStudentId(
                        student
                    );

                const name =
                    student.name ||
                    student.full_name ||
                    "Unknown Student";

                const roll =
                    student.roll_no ||
                    student.roll_number ||
                    "—";

                const program =
                    student.program ||
                    student.branch ||
                    "—";

                const year =
                    student.year ||
                    student.study_year ||
                    "—";

                const status =
                    normalizeStatus(
                        student.status
                    );

                const photo =
                    student.photo_url ||
                    student.photo ||
                    "";

                const initial =
                    name
                        .charAt(0)
                        .toUpperCase();

                const avatar =
                    photo
                        ? `
                            <img
                                src="${escapeHTML(photo)}"
                                alt="${escapeHTML(name)}"
                            >
                        `
                        : `
                            <span>
                                ${escapeHTML(initial)}
                            </span>
                        `;

                let action =
                    `<span class="text-muted">Closed</span>`;

                if (
                    attendanceOpen &&
                    id !== null
                ) {
                    action = `
                        <div
                            class="attendance-actions"
                        >

                            <button
                                type="button"
                                class="btn btn--sm ${
                                    status === "present"
                                        ? "btn--primary"
                                        : "btn--ghost"
                                }"
                                data-attendance="present"
                                data-student-id="${escapeHTML(id)}"
                            >
                                Present
                            </button>

                            <button
                                type="button"
                                class="btn btn--sm ${
                                    status === "absent"
                                        ? "btn--danger"
                                        : "btn--ghost"
                                }"
                                data-attendance="absent"
                                data-student-id="${escapeHTML(id)}"
                            >
                                Absent
                            </button>

                        </div>
                    `;
                }

                return `
                    <tr>

                        <td>
                            <div
                                class="student-avatar"
                            >
                                ${avatar}
                            </div>
                        </td>

                        <td>
                            <strong>
                                ${escapeHTML(roll)}
                            </strong>
                        </td>

                        <td>
                            ${escapeHTML(name)}
                        </td>

                        <td>
                            ${escapeHTML(program)}
                            /
                            ${escapeHTML(year)}
                        </td>

                        <td>
                            ${statusMarkup(status)}
                        </td>

                        <td
                            class="attendance-marked-time"
                        >
                            ${escapeHTML(
                                formatDateTimeValue(
                                    student.marked_at
                                )
                            )}
                        </td>

                        <td
                            class="attendance-action"
                        >
                            ${action}
                        </td>

                    </tr>
                `;
            })
            .join("");

    updateAttendanceSummary();
}

function updateAttendanceSummary() {
    const summary =
        calculateAttendanceSummary(
            state.attendanceRoster
        );

    state.attendanceSummary =
        summary;

    if ($("attendanceTotal")) {
        $("attendanceTotal")
            .textContent =
            summary.total;
    }

    if ($("attendancePresent")) {
        $("attendancePresent")
            .textContent =
            summary.present;
    }

    if ($("attendanceAbsent")) {
        $("attendanceAbsent")
            .textContent =
            summary.absent;
    }

    if ($("attendancePending")) {
        $("attendancePending")
            .textContent =
            summary.pending;
    }
}

async function markAttendance(
    studentId,
    status
) {
    if (!state.activeLecture) {
        showToast(
            "Select a lecture first.",
            "error"
        );

        return;
    }

    if (
        !isAttendanceOpen(
            state.activeLecture
        )
    ) {
        showToast(
            "The attendance window is closed.",
            "error"
        );

        return;
    }

    const lectureId =
        getLectureId(
            state.activeLecture
        );

    if (lectureId === null) {
        showToast(
            "Lecture ID is missing.",
            "error"
        );

        return;
    }

    try {
        await apiRequest(
            "/attendance",
            {
                method: "POST",

                body: JSON.stringify({
                    student_id:
                        studentId,

                    lecture_id:
                        lectureId,

                    status:
                        status
                })
            }
        );

        const student =
            state.attendanceRoster.find(
                item =>
                    String(
                        getStudentId(item)
                    ) ===
                    String(studentId)
            );

        if (student) {
            student.status =
                status;

            student.marked_at =
                new Date().toISOString();
        }

        renderAttendance();
        renderStats();

        showToast(
            `Student marked ${status}.`,
            "success"
        );

    } catch (error) {
        console.error(
            "Mark attendance failed:",
            error
        );

        showToast(
            error.message ||
            "Unable to update attendance.",
            "error"
        );
    }
}

function renderStats() {
    const totalStudents =
        state.students.length;

    const today =
        getTodayISO();

    const todayLectures =
        state.timetable.filter(
            lecture =>
                isSameDay(
                    lecture.start_time ||
                    lecture.start,
                    today
                )
        ).length;

    const summary =
        calculateAttendanceSummary(
            state.attendanceRoster
        );

    if ($("statTotal")) {
        $("statTotal").textContent =
            totalStudents;
    }

    if ($("statPresent")) {
        $("statPresent").textContent =
            summary.present;
    }

    if ($("statAbsent")) {
        $("statAbsent").textContent =
            summary.absent;
    }

    if ($("statPending")) {
        $("statPending").textContent =
            summary.pending;
    }

    if ($("statLectures")) {
        $("statLectures").textContent =
            todayLectures;
    }
}

function switchView(viewName) {
    const validViews = [
        "dashboard",
        "timetable",
        "attendance",
        "students",
        "profile",
        "settings"
    ];

    if (
        !validViews.includes(
            viewName
        )
    ) {
        return;
    }

    document
        .querySelectorAll(
            "[data-view]"
        )
        .forEach(button => {

            const active =
                button.dataset.view ===
                viewName;

            button.classList.toggle(
                "is-active",
                active
            );

            button.classList.toggle(
                "active",
                active
            );

            button.setAttribute(
                "aria-current",
                active
                    ? "page"
                    : "false"
            );
        });

    document
        .querySelectorAll(
            "[data-view-panel]"
        )
        .forEach(panel => {

            const active =
                panel.dataset.viewPanel ===
                viewName;

            panel.classList.toggle(
                "is-active",
                active
            );

            panel.classList.toggle(
                "active",
                active
            );

            panel.style.display =
                active
                    ? ""
                    : "none";
        });

    const titles = {
        dashboard:
            "Dashboard",

        timetable:
            "Timetable",

        attendance:
            "Attendance",

        students:
            "Students",

        profile:
            "Profile",

        settings:
            "Settings"
    };

    if ($("viewTitle")) {
        $("viewTitle").textContent =
            titles[viewName];
    }

    if (
        viewName ===
        "dashboard"
    ) {
        renderStats();
        renderDashboardTimetable();
        renderDashboardProfile();
    }

    if (
        viewName ===
        "timetable"
    ) {
        renderTimetableDate();
        renderTimetable();
    }

    if (
        viewName ===
        "attendance"
    ) {
        renderAttendanceSession();
        renderAttendance();
    }

    if (
        viewName ===
        "students"
    ) {
        renderStudents();
    }

    if (
        viewName ===
        "profile"
    ) {
        renderProfile();
    }

    closeMobileSidebar();
}

function setupNavigation() {
    document
        .querySelectorAll(
            "[data-view]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                event => {

                    event.preventDefault();

                    switchView(
                        button.dataset.view
                    );
                }
            );
        });

    document
        .querySelectorAll(
            "[data-goto]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                event => {

                    event.preventDefault();

                    switchView(
                        button.dataset.goto
                    );
                }
            );
        });
}

function updateClock() {
    const clock =
        $("liveClock");

    if (!clock) {
        return;
    }

    clock.textContent =
        new Date().toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
                hour12: true
            }
        );
}

function openMobileSidebar() {
    const sidebar =
        $("sidebar");

    const scrim =
        $("topbarScrim");

    const menu =
        $("menuBtn");

    sidebar?.classList.add(
        "is-open"
    );

    scrim?.classList.add(
        "is-visible"
    );

    menu?.setAttribute(
        "aria-expanded",
        "true"
    );
}

function closeMobileSidebar() {
    const sidebar =
        $("sidebar");

    const scrim =
        $("topbarScrim");

    const menu =
        $("menuBtn");

    sidebar?.classList.remove(
        "is-open"
    );

    scrim?.classList.remove(
        "is-visible"
    );

    menu?.setAttribute(
        "aria-expanded",
        "false"
    );
}

async function handlePhotoUpload(
    event
) {
    const file =
        event.target.files?.[0];

    if (!file) {
        return;
    }

    const formData =
        new FormData();

    formData.append(
        "photo",
        file
    );

    try {
        const data =
            await apiRequest(
                "/profile/photo",
                {
                    method: "POST",
                    body: formData
                }
            );

        if (!data) {
            return;
        }

        if (
            state.me &&
            data.photo_url
        ) {
            state.me.photo_url =
                data.photo_url;
        }

        renderProfile();
        renderDashboardProfile();

        showToast(
            "Profile photo updated.",
            "success"
        );

    } catch (error) {
        console.error(
            "Photo upload failed:",
            error
        );

        showToast(
            error.message ||
            "Unable to upload profile photo.",
            "error"
        );

    } finally {
        event.target.value = "";
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
    } catch (error) {
        console.error(
            "Logout error:",
            error
        );
    } finally {
        window.location.href =
            CONFIG.LOGIN_URL;
    }
}

function setupEvents() {
    setupNavigation();

    $("logoutBtn")
        ?.addEventListener(
            "click",
            logout
        );

    $("settingsLogoutBtn")
        ?.addEventListener(
            "click",
            logout
        );

    $("studentSearch")
        ?.addEventListener(
            "input",
            renderStudents
        );

    $("filterFaculty")
        ?.addEventListener(
            "change",
            renderStudents
        );

    $("filterBranch")
        ?.addEventListener(
            "change",
            renderStudents
        );

    $("filterSpecialization")
        ?.addEventListener(
            "change",
            renderStudents
        );

    $("filterYear")
        ?.addEventListener(
            "change",
            renderStudents
        );

    $("filterStatus")
        ?.addEventListener(
            "change",
            renderStudents
        );

    $("attendanceSearch")
        ?.addEventListener(
            "input",
            renderAttendance
        );

    $("attendanceStatusFilter")
        ?.addEventListener(
            "change",
            renderAttendance
        );

    $("photoInput")
        ?.addEventListener(
            "change",
            handlePhotoUpload
        );

    $("menuBtn")
        ?.addEventListener(
            "click",
            () => {

                const sidebar =
                    $("sidebar");

                if (
                    sidebar?.classList.contains(
                        "is-open"
                    )
                ) {
                    closeMobileSidebar();
                } else {
                    openMobileSidebar();
                }
            }
        );

    $("topbarScrim")
        ?.addEventListener(
            "click",
            closeMobileSidebar
        );

    $("globalSearch")
        ?.addEventListener(
            "input",
            event => {

                const value =
                    event.target.value.trim();

                switchView(
                    "students"
                );

                if ($("studentSearch")) {
                    $("studentSearch").value =
                        value;

                    renderStudents();
                }
            }
        );

    document.addEventListener(
        "click",
        event => {

            const attendanceButton =
                event.target.closest(
                    "[data-attendance]"
                );

            if (attendanceButton) {

                const studentId =
                    attendanceButton.dataset
                        .studentId;

                const status =
                    attendanceButton.dataset
                        .attendance;

                if (
                    studentId &&
                    status
                ) {
                    markAttendance(
                        studentId,
                        status
                    );
                }

                return;
            }

            const openButton =
                event.target.closest(
                    "[data-open-attendance]"
                );

            if (openButton) {

                const lectureId =
                    openButton.dataset
                        .openAttendance;

                const lecture =
                    state.timetable.find(
                        item =>
                            String(
                                getLectureId(item)
                            ) ===
                            String(lectureId)
                    );

                if (lecture) {
                    openAttendance(
                        lecture
                    );
                }
            }
        }
    );
}

async function refreshData() {
    try {
        await Promise.all([
            loadTimetable(),
            loadStudents()
        ]);

        if (
            state.activeLecture
        ) {
            const lectureId =
                getLectureId(
                    state.activeLecture
                );

            const latest =
                state.timetable.find(
                    item =>
                        String(
                            getLectureId(item)
                        ) ===
                        String(lectureId)
                );

            if (latest) {

                state.activeLecture =
                    latest;

                const attendanceView =
                    document.querySelector(
                        '[data-view-panel="attendance"].is-active'
                    );

                if (attendanceView) {
                    await openAttendance(
                        latest
                    );
                }
            }
        }

        renderStats();

    } catch (error) {
        console.error(
            "Refresh failed:",
            error
        );
    }
}

async function init() {
    setupEvents();

    updateClock();

    setInterval(
        updateClock,
        1000
    );

    switchView(
        "dashboard"
    );

    try {
        await Promise.all([
            loadMe(),
            loadHierarchy(),
            loadTimetable(),
            loadStudents()
        ]);

        renderStats();

    } catch (error) {
        console.error(
            "Dashboard initialization failed:",
            error
        );
    }

    setInterval(
        refreshData,
        CONFIG.REFRESH_INTERVAL
    );
}

document.addEventListener(
    "DOMContentLoaded",
    init
);