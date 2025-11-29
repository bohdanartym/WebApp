const API_BASE = "http://localhost/api";

let accessToken = localStorage.getItem("access_token") || null;

function setToken(token) {
    accessToken = token;
    localStorage.setItem("access_token", token);
    updateUserInfo();
    showMainContent();
}

function clearToken() {
    accessToken = null;
    localStorage.removeItem("access_token");
    updateUserInfo();
    showAuth();
}

function updateUserInfo() {
    const el = document.getElementById("user-info");
    if (accessToken) {
        el.textContent = "Авторизовано";
    } else {
        el.textContent = "";
    }
}

async function apiRequest(method, path, body = null, auth = false) {
    const headers = { "Content-Type": "application/json" };
    if (auth && accessToken) {
        headers["Authorization"] = "Bearer " + accessToken;
    }

    let res;
    try {
        res = await fetch(API_BASE + path, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });
    } catch (networkErr) {
        throw { detail: "Помилка з'єднання з сервером" };
    }

    let data = null;
    try {
        data = await res.json();
    } catch {
        data = null;
    }

    if (!res.ok) {
        if (data && data.detail) {
            throw { detail: data.detail };
        } else {
            throw { detail: "Невідома помилка сервера" };
        }
    }

    return data;
}

function showAuth() {
    document.getElementById("auth-section").classList.remove("hidden");
    document.getElementById("main-content").classList.add("hidden");
}

function showMainContent() {
    document.getElementById("auth-section").classList.add("hidden");
    document.getElementById("main-content").classList.remove("hidden");
    showSolver();
}

function showSolver() {
    document.getElementById("solver-section").classList.remove("hidden");
    document.getElementById("history-section").classList.add("hidden");
}

function showHistory() {
    document.getElementById("solver-section").classList.add("hidden");
    document.getElementById("history-section").classList.remove("hidden");
}

function generateMatrixGrid() {
    const sizeInput = document.getElementById("matrix-size");
    let n = parseInt(sizeInput.value, 10);
    if (isNaN(n) || n < 2) n = 2;
    if (n > 100) n = 100;
    sizeInput.value = n;

    const matrixContainer = document.getElementById("matrix-container");
    const rhsContainer = document.getElementById("rhs-container");

    const table = document.createElement("table");
    for (let i = 0; i < n; i++) {
        const row = document.createElement("tr");
        for (let j = 0; j < n; j++) {
            const cell = document.createElement("td");
            const input = document.createElement("input");
            input.type = "number";
            input.step = "any";
            input.id = `cell-${i}-${j}`;
            cell.appendChild(input);
            row.appendChild(cell);
        }
        table.appendChild(row);
    }
    matrixContainer.innerHTML = "";
    matrixContainer.appendChild(table);

    const rhsColumn = document.createElement("table");
    for (let i = 0; i < n; i++) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        const input = document.createElement("input");
        input.type = "number";
        input.step = "any";
        input.id = `rhs-${i}`;

        cell.appendChild(input);
        row.appendChild(cell);
        rhsColumn.appendChild(row);
    }

    rhsContainer.innerHTML = "";
    rhsContainer.appendChild(rhsColumn);
}

function fillMatrixRandom() {
    const sizeInput = document.getElementById("matrix-size");
    let n = parseInt(sizeInput.value, 10);
    if (isNaN(n) || n < 2) n = 2;
    if (n > 100) n = 100;
    sizeInput.value = n;

    const min = -10;
    const max = 10;

    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
            const el = document.getElementById(`cell-${i}-${j}`);
            if (!el) continue;
            const val = Math.floor(Math.random() * (max - min + 1)) + min;
            el.value = String(val);
        }
        const rhsEl = document.getElementById(`rhs-${i}`);
        if (rhsEl) {
            const val = Math.floor(Math.random() * (max - min + 1)) + min;
            rhsEl.value = String(val);
        }
    }
}

function collectMatrixAndVector() {
    const sizeInput = document.getElementById("matrix-size");
    let n = parseInt(sizeInput.value, 10);
    if (isNaN(n) || n < 2) n = 2;
    if (n > 100) n = 100;
    sizeInput.value = n;

    const matrix = [];
    const rhs = [];

    for (let i = 0; i < n; i++) {
        const row = [];
        for (let j = 0; j < n; j++) {
            const el = document.getElementById(`cell-${i}-${j}`);
            let val = parseFloat(el?.value ?? "0");
            if (isNaN(val)) val = 0;
            row.push(val);
        }
        matrix.push(row);

        const rhsEl = document.getElementById(`rhs-${i}`);
        let valB = parseFloat(rhsEl?.value ?? "0");
        if (isNaN(valB)) valB = 0;
        rhs.push(valB);
    }

    return { matrix, rhs };
}

function resetProgress() {
    document.getElementById("progress-fill").style.width = "0%";
    document.getElementById("progress-text").textContent = "0%";
}

async function loadHistory() {
    const table = document.getElementById("history-table");
    const body = document.getElementById("history-body");
    const empty = document.getElementById("history-empty");

    body.innerHTML = "";
    empty.classList.add("hidden");
    table.classList.remove("hidden");

    try {
        let data = await apiRequest("GET", "/tasks/user/me", null, true);
        data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        if (!Array.isArray(data) || data.length === 0) {
            table.classList.add("hidden");
            empty.classList.remove("hidden");
            return;
        }

        data.forEach((task, index) => {
            const tr = document.createElement("tr");

            const idTd = document.createElement("td");
            idTd.textContent = index + 1;

            const createdTd = document.createElement("td");
            if (task.created_at) {
                createdTd.textContent = new Date(task.created_at).toLocaleString();
            } else {
                createdTd.textContent = "-";
            }

            const sizeTd = document.createElement("td");
            let sizeText = "-";
            if (task.input_data && task.input_data.matrix && Array.isArray(task.input_data.matrix)) {
                const n = task.input_data.matrix.length;
                sizeText = `${n}×${n}`;
            }
            sizeTd.textContent = sizeText;

            const actionsTd = document.createElement("td");
            const btn = document.createElement("button");
            btn.textContent = "Деталі";
            btn.className = "secondary-btn small";
            btn.addEventListener("click", () => showTaskDetails(task));
            actionsTd.appendChild(btn);

            tr.appendChild(idTd);
            tr.appendChild(createdTd);
            tr.appendChild(sizeTd);
            tr.appendChild(actionsTd);

            body.appendChild(tr);
        });

    } catch (err) {
        table.classList.add("hidden");
        empty.classList.remove("hidden");
        empty.textContent = "Помилка завантаження історії.";
        console.error("history error", err);
    }
}

function showTaskDetails(task) {
    const overlay = document.getElementById("modal-overlay");
    const content = document.getElementById("modal-content");

    const matrix = task.input_data?.matrix ?? [];
    const rhs = task.input_data?.rhs ?? task.input_data?.vector ?? [];
    const solution = task.result?.solution ?? task.result ?? null;

    let html = "";

    html += "<h4>Матриця A</h4>";
    if (Array.isArray(matrix) && matrix.length > 0) {
        html += "<table>";
        for (const row of matrix) {
            html += "<tr>";
            for (const v of row) {
                html += `<td>${typeof v === "number" ? v.toFixed(2) : v}</td>`;
            }
            html += "</tr>";
        }
        html += "</table>";
    } else {
        html += "<p class='muted-text'>Немає даних матриці.</p>";
    }

    html += "<h4>Вектор b</h4>";
    if (Array.isArray(rhs) && rhs.length > 0) {
        html += "<table>";
        for (const v of rhs) {
            html += `<tr><td>${typeof v === "number" ? v.toFixed(2) : v}</td></tr>`;
        }
        html += "</table>";
    } else {
        html += "<p class='muted-text'>Немає даних вектора.</p>";
    }

    html += "<h4>Розв'язок x</h4>";
    if (Array.isArray(solution)) {
        html += "<table>";
        for (const v of solution) {
            html += `<tr><td>${typeof v === "number" ? v.toFixed(6) : v}</td></tr>`;
        }
        html += "</table>";
    } else {
        html += "<pre class='result'>" + JSON.stringify(task.result, null, 2) + "</pre>";
    }

    content.innerHTML = html;
    overlay.classList.remove("hidden");
}

function hideModal() {
    document.getElementById("modal-overlay").classList.add("hidden");
}

function switchAuthMode(mode) {
    const loginTab = document.getElementById("tab-login");
    const registerTab = document.getElementById("tab-register");
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");

    if (mode === "login") {
        loginTab.classList.add("active");
        registerTab.classList.remove("active");
        loginForm.classList.remove("hidden");
        registerForm.classList.add("hidden");
    } else {
        loginTab.classList.remove("active");
        registerTab.classList.add("active");
        loginForm.classList.add("hidden");
        registerForm.classList.remove("hidden");
    }
}

function init() {

    document.getElementById("tab-login").addEventListener("click", () => switchAuthMode("login"));
    document.getElementById("tab-register").addEventListener("click", () => switchAuthMode("register"));

    document.getElementById("login-btn").addEventListener("click", async () => {
        const out = document.getElementById("login-result");
        out.style.display = "none";
        out.textContent = "";

        try {
            const data = await apiRequest("POST", "/auth/login", {
                email: document.getElementById("login-email").value,
                password: document.getElementById("login-password").value
            });

            out.style.display = "none";
            out.textContent = "";

            if (data.access_token) {
                setToken(data.access_token);
            }

        } catch (err) {
            let msg = "Сталася помилка";
            if (typeof err === "string") {
                msg = err;
            } else if (err && typeof err === "object") {
                if (typeof err.detail === "string") {
                    msg = err.detail;
                } else if (Array.isArray(err.detail) && err.detail.length > 0) {
                    if (err.detail[0].msg) msg = err.detail[0].msg;
                } else {
                    for (const key in err) {
                        if (typeof err[key] === "string") {
                            msg = err[key];
                            break;
                        }
                    }
                }
            }
            out.textContent = msg;
            out.style.display = "block";
        }
    });

    document.getElementById("register-btn").addEventListener("click", async () => {
        const out = document.getElementById("reg-result");
        out.style.display = "none";
        out.textContent = "";

        try {
            await apiRequest("POST", "/auth/register", {
                name: document.getElementById("reg-name").value,
                email: document.getElementById("reg-email").value,
                password: document.getElementById("reg-password").value
            });

            alert("Реєстрація успішна! Тепер увійдіть у систему.");
            switchAuthMode("login");

        } catch (err) {
            let msg = "Сталася помилка";
            if (typeof err === "string") {
                msg = err;
            } else if (err && typeof err === "object") {
                if (typeof err.detail === "string") {
                    msg = err.detail;
                } else if (Array.isArray(err.detail) && err.detail.length > 0) {
                    if (err.detail[0].msg) msg = err.detail[0].msg;
                } else {
                    for (const key in err) {
                        if (typeof err[key] === "string") {
                            msg = err[key];
                            break;
                        }
                    }
                }
            }
            out.textContent = msg;
            out.style.display = "block";
        }
    });

    document.getElementById("open-solver").addEventListener("click", () => {
        showSolver();
    });

    document.getElementById("open-history").addEventListener("click", () => {
        showHistory();
        loadHistory();
    });

    document.getElementById("logout-btn").addEventListener("click", () => {
        clearToken();
    });

    document.getElementById("generate-matrix-btn").addEventListener("click", () => {
        generateMatrixGrid();
    });

    document.getElementById("fill-random-btn").addEventListener("click", () => {
        fillMatrixRandom();
    });


    document.getElementById("solve-btn").addEventListener("click", async () => {
        const resultEl = document.getElementById("solve-result");
        resultEl.textContent = "";
        resetProgress();

        const { matrix, rhs } = collectMatrixAndVector();

        const fillEl = document.getElementById("progress-fill");
        const textEl = document.getElementById("progress-text");

        fillEl.style.width = "0%";
        textEl.textContent = "0%";

        let fakeP = 0;
        const fakeInterval = setInterval(() => {
            if (fakeP < 90) {
                fakeP += Math.random() * 15 + 10; 
                if (fakeP > 90) fakeP = 90;
                fillEl.style.width = fakeP + "%";
                textEl.textContent = Math.floor(fakeP) + "%";
            }
        }, 10); 

        try {

            const data = await apiRequest("POST", "/gauss/solve", {
                matrix,
                rhs
            }, true);

            clearInterval(fakeInterval);

            let finP = fakeP;
            const finishInterval = setInterval(() => {
                finP += 10;
                if (finP >= 100) {
                    finP = 100;
                    clearInterval(finishInterval);
                }
                fillEl.style.width = finP + "%";
                textEl.textContent = Math.floor(finP) + "%";
            }, 20); 

            const solution = data.solution;
            let text = "Розв'язок:\n";
            solution.forEach((x, i) => {
                text += `x${i + 1} = ${x}\n`;
            });
            resultEl.textContent = text;

        } catch (err) {
            clearInterval(fakeInterval);
            resetProgress();
            resultEl.textContent = "Помилка: " + (err?.detail || "невідома");
            console.error(err);
        }
    });

    document.getElementById("reload-history-btn").addEventListener("click", () => {
        loadHistory();
    });

    document.getElementById("modal-close").addEventListener("click", hideModal);
    document.getElementById("modal-overlay").addEventListener("click", (e) => {
        if (e.target.id === "modal-overlay") hideModal();
    });

    updateUserInfo();
    generateMatrixGrid();

    if (accessToken) {
        showMainContent();
    } else {
        showAuth();
    }
}

window.addEventListener("DOMContentLoaded", init);