const API_BASE = "http://localhost/api";

let accessToken = localStorage.getItem("access_token") || null;
let currentTaskId = null;
let pollingInterval = null;

// Віртуальна матриця (зберігається в пам'яті, не в DOM)
let virtualMatrix = [];
let virtualVector = [];

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
        console.log(`[API Request] ${method} ${path}`, body ? `Body size: ${JSON.stringify(body).length} bytes` : '');
        
        res = await fetch(API_BASE + path, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });
    } catch (networkErr) {
        console.error('[API Request] Network error:', networkErr);
        throw { detail: "Помилка з'єднання з сервером. Перевірте інтернет-з'єднання." };
    }

    let data = null;
    try {
        const textResponse = await res.text();
        console.log(`[API Response] Status: ${res.status}, Body length: ${textResponse.length}`);
        
        if (textResponse) {
            data = JSON.parse(textResponse);
        }
    } catch (parseErr) {
        console.error('[API Response] JSON parse error:', parseErr);
        data = null;
    }

    if (!res.ok) {
        console.error(`[API Response] Error ${res.status}:`, data);
        
        if (res.status === 413) {
            throw { detail: "Матриця занадто велика для передачі. Спробуйте менший розмір." };
        }
        
        if (res.status === 422) {
            throw { detail: "Помилка валідації даних. Перевірте формат матриці." };
        }
        
        if (res.status === 500) {
            throw { detail: "Внутрішня помилка сервера. Спробуйте пізніше або зменште розмір матриці." };
        }
        
        if (data && data.detail) {
            throw { detail: data.detail };
        } else {
            throw { detail: `Помилка сервера (код ${res.status})` };
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
    if (n > 5000) n = 5000;
    sizeInput.value = n;

    const matrixContainer = document.getElementById("matrix-container");
    const rhsContainer = document.getElementById("rhs-container");

    // Для великих матриць (>100) не створюємо DOM елементи
    if (n > 100) {
        // Ініціалізуємо віртуальну матрицю
        virtualMatrix = Array(n).fill(0).map(() => Array(n).fill(0));
        virtualVector = Array(n).fill(0);
        
        matrixContainer.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #9ca3af;">
                <p>Матриця ${n}×${n} занадто велика для відображення</p>
                <p style="font-size: 0.9rem; margin-top: 8px;">Використовуйте "Автозаповнення" для генерації значень</p>
            </div>
        `;
        rhsContainer.innerHTML = `
            <div style="padding: 40px; text-align: center; color: #9ca3af;">
                <p>Вектор b</p>
                <p style="font-size: 0.9rem;">${n} елементів</p>
            </div>
        `;
        return;
    }

    // Для невеликих матриць створюємо input поля
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
    if (n > 5000) n = 5000;
    sizeInput.value = n;

    const min = -10;
    const max = 10;

    // Якщо велика матриця - заповнюємо віртуальну
    if (n > 100) {
        console.log(`[Fill Random] Generating ${n}×${n} virtual matrix...`);
        const startTime = performance.now();
        
        virtualMatrix = Array(n).fill(0).map(() => 
            Array(n).fill(0).map(() => Math.floor(Math.random() * (max - min + 1)) + min)
        );
        virtualVector = Array(n).fill(0).map(() => 
            Math.floor(Math.random() * (max - min + 1)) + min
        );
        
        const elapsed = ((performance.now() - startTime) / 1000).toFixed(2);
        console.log(`[Fill Random] Generated in ${elapsed}s`);
        
        alert(`Згенеровано матрицю ${n}×${n} та вектор b з випадковими значеннями від ${min} до ${max}\n(час генерації: ${elapsed}s)`);
        return;
    }

    // Для невеликих матриць заповнюємо input поля
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
    if (n > 5000) n = 5000;
    sizeInput.value = n;

    // Якщо велика матриця - використовуємо віртуальну
    if (n > 100) {
        console.log(`[Collect Matrix] Using virtual matrix ${n}×${n}`);
        return { 
            matrix: virtualMatrix, 
            rhs: virtualVector 
        };
    }

    // Для невеликих матриць збираємо з input полів
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

function updateProgress(progress) {
    const fillEl = document.getElementById("progress-fill");
    const textEl = document.getElementById("progress-text");
    
    const percent = Math.min(100, Math.max(0, progress));
    fillEl.style.width = percent + "%";
    textEl.textContent = Math.floor(percent) + "%";
}

function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

async function startPolling(taskId) {
    stopPolling();
    
    const resultEl = document.getElementById("solve-result");
    const cancelBtn = document.getElementById("cancel-btn");
    
    pollingInterval = setInterval(async () => {
        try {
            // Отримуємо статус задачі
            const status = await apiRequest("GET", `/tasks/status/${taskId}`, null, false);
            
            if (status.status === "processing") {
                // Оновлюємо прогрес
                updateProgress(status.progress || 0);
                
            } else if (status.status === "completed") {
                // Задача завершена - отримуємо результат
                stopPolling();
                updateProgress(100);
                
                const result = await apiRequest("GET", `/tasks/result/${taskId}`, null, false);
                
                if (result.solution) {
                    const n = result.solution.length;
                    let text = `Розв'язок (${n} змінних):\n`;
                    
                    // Показуємо перші 20 значень для великих векторів
                    const showCount = Math.min(20, n);
                    for (let i = 0; i < showCount; i++) {
                        text += `x${i + 1} = ${result.solution[i]}\n`;
                    }
                    if (n > 20) {
                        text += `\n... та ще ${n - 20} значень\n`;
                        text += `\nПовний розв'язок збережено в історії завдань.`;
                    }
                    resultEl.textContent = text;
                } else {
                    resultEl.textContent = "Результат отримано, але розв'язок відсутній";
                }
                
                cancelBtn.classList.add("hidden");
                currentTaskId = null;
                
            } else if (status.status === "cancelled") {
                // Задача скасована
                stopPolling();
                resetProgress();
                resultEl.textContent = "Завдання скасовано";
                cancelBtn.classList.add("hidden");
                currentTaskId = null;
                
            } else if (status.status === "error") {
                // Помилка виконання
                stopPolling();
                resetProgress();
                
                const result = await apiRequest("GET", `/tasks/result/${taskId}`, null, false);
                resultEl.textContent = "Помилка: " + (result?.error || "невідома помилка");
                
                cancelBtn.classList.add("hidden");
                currentTaskId = null;
                
            } else if (status.status === "not_found") {
                // Задача не знайдена
                stopPolling();
                resetProgress();
                resultEl.textContent = "Задача не знайдена";
                cancelBtn.classList.add("hidden");
                currentTaskId = null;
            }
            
        } catch (err) {
            console.error("Polling error:", err);
            stopPolling();
            resultEl.textContent = "Помилка перевірки статусу: " + (err?.detail || "невідома");
            cancelBtn.classList.add("hidden");
        }
    }, 500); // Перевірка кожні 500мс
}

async function cancelCurrentTask() {
    if (!currentTaskId) return;
    
    try {
        await apiRequest("POST", `/tasks/cancel/${currentTaskId}`, null, false);
        // Polling продовжиться і виявить статус "cancelled"
    } catch (err) {
        console.error("Cancel error:", err);
        alert("Помилка скасування: " + (err?.detail || "невідома"));
    }
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

    const n = matrix.length;

    html += `<h4>Матриця A (${n}×${n})</h4>`;
    if (Array.isArray(matrix) && matrix.length > 0) {
        // Показуємо тільки перші 10×10 для великих матриць
        const showSize = Math.min(10, n);
        html += "<table>";
        for (let i = 0; i < showSize; i++) {
            html += "<tr>";
            for (let j = 0; j < showSize; j++) {
                const v = matrix[i][j];
                html += `<td>${typeof v === "number" ? v.toFixed(2) : v}</td>`;
            }
            if (n > 10) {
                html += "<td>...</td>";
            }
            html += "</tr>";
        }
        if (n > 10) {
            html += "<tr><td colspan='" + (showSize + 1) + "'>... та ще " + (n - showSize) + " рядків</td></tr>";
        }
        html += "</table>";
    } else {
        html += "<p class='muted-text'>Немає даних матриці.</p>";
    }

    html += `<h4>Вектор b (${rhs.length} елементів)</h4>`;
    if (Array.isArray(rhs) && rhs.length > 0) {
        const showCount = Math.min(10, rhs.length);
        html += "<table>";
        for (let i = 0; i < showCount; i++) {
            const v = rhs[i];
            html += `<tr><td>${typeof v === "number" ? v.toFixed(2) : v}</td></tr>`;
        }
        if (rhs.length > 10) {
            html += `<tr><td>... та ще ${rhs.length - 10} елементів</td></tr>`;
        }
        html += "</table>";
    } else {
        html += "<p class='muted-text'>Немає даних вектора.</p>";
    }

    html += `<h4>Розв'язок x</h4>`;
    if (Array.isArray(solution)) {
        const showCount = Math.min(10, solution.length);
        html += "<table>";
        for (let i = 0; i < showCount; i++) {
            const v = solution[i];
            html += `<tr><td>x${i+1} = ${typeof v === "number" ? v.toFixed(6) : v}</td></tr>`;
        }
        if (solution.length > 10) {
            html += `<tr><td>... та ще ${solution.length - 10} значень</td></tr>`;
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
        stopPolling();
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
        const cancelBtn = document.getElementById("cancel-btn");
        
        resultEl.textContent = "";
        resetProgress();
        stopPolling();

        const { matrix, rhs } = collectMatrixAndVector();

        console.log(`[Solve] Sending matrix ${matrix.length}×${matrix.length}`);

        try {
            // Відправляємо запит на розв'язання
            const data = await apiRequest("POST", "/gauss/solve", {
                matrix,
                rhs
            }, true);

            if (data.task_id) {
                currentTaskId = data.task_id;
                resultEl.textContent = "Завдання прийнято та перебуває в обробці...\nTask ID: " + data.task_id;
                
                // Показуємо кнопку скасування
                cancelBtn.classList.remove("hidden");
                
                // Запускаємо polling для відстеження прогресу
                await startPolling(data.task_id);
            } else {
                resultEl.textContent = "Помилка: не отримано task_id";
            }

        } catch (err) {
            stopPolling();
            resetProgress();
            resultEl.textContent = "Помилка: " + (err?.detail || "невідома");
            cancelBtn.classList.add("hidden");
            console.error("[Solve] Error:", err);
        }
    });

    // Кнопка скасування
    document.getElementById("cancel-btn").addEventListener("click", () => {
        cancelCurrentTask();
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