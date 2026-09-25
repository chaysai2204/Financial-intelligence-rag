// =========================================================
// FilingIQ Frontend
// =========================================================


// ---------------------------------------------------------
// Database data sent from FastAPI/Jinja
// ---------------------------------------------------------

const filingData = JSON.parse(
    document.getElementById("filing-data")?.textContent || "[]"
);


// ---------------------------------------------------------
// Main DOM references
// ---------------------------------------------------------

const chatMessages =
    document.getElementById("chatMessages");

const chatForm =
    document.getElementById("chatForm");

const chatInput =
    document.getElementById("chatInput");

const sendBtn =
    document.getElementById("sendBtn");

const companySelect =
    document.getElementById("chatCompanySelect");

const yearSelect =
    document.getElementById("chatYearSelect");

const companyFilterWrapper =
    document.getElementById("companyFilterWrapper");

const yearFilterWrapper =
    document.getElementById("yearFilterWrapper");

const contextControls =
    document.getElementById("contextControls");



// =========================================================
// 1. AUTO-CONFIGURE CHAT FILTERS
// =========================================================

function configureContextFilters() {

    // If only one actual company exists,
    // auto-select it and hide the dropdown.
    if (
        companySelect &&
        companySelect.options.length === 2
    ) {
        companySelect.selectedIndex = 1;

        if (companyFilterWrapper) {
            companyFilterWrapper.style.display = "none";
        }
    }


    // If only one actual fiscal year exists,
    // auto-select it and hide the dropdown.
    if (
        yearSelect &&
        yearSelect.options.length === 2
    ) {
        yearSelect.selectedIndex = 1;

        if (yearFilterWrapper) {
            yearFilterWrapper.style.display = "none";
        }
    }


    // Hide the whole filter row if both filters disappeared.
    const companyHidden =
        !companyFilterWrapper ||
        companyFilterWrapper.style.display === "none";

    const yearHidden =
        !yearFilterWrapper ||
        yearFilterWrapper.style.display === "none";


    if (
        contextControls &&
        companyHidden &&
        yearHidden
    ) {
        contextControls.style.display = "none";
    }
}


configureContextFilters();



// =========================================================
// 2. GENERAL HELPERS
// =========================================================

function showToast(
    title,
    message,
    type = "success"
) {

    const container =
        document.getElementById("toastContainer");

    if (!container) {
        return;
    }


    const toast =
        document.createElement("div");

    toast.className =
        `toast ${type === "error" ? "error" : ""}`;


    const titleElement =
        document.createElement("strong");

    titleElement.textContent =
        title;


    const messageElement =
        document.createElement("span");

    messageElement.textContent =
        message;


    toast.append(
        titleElement,
        messageElement
    );


    container.appendChild(
        toast
    );


    setTimeout(
        () => toast.remove(),
        4500
    );
}



// =========================================================
// 3. USER MESSAGE RENDERING
// =========================================================

function addUserMessage(text) {

    if (!chatMessages) {
        return;
    }


    const message =
        document.createElement("div");


    message.className =
        "user-card";


    message.textContent =
        text;


    chatMessages.appendChild(
        message
    );


    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}



// =========================================================
// 4. LOADING / TYPING STATE
// =========================================================

function addTyping() {

    if (!chatMessages) {
        return;
    }


    const element =
        document.createElement("div");


    element.className =
        "assistant-card";


    element.id =
        "typing-card";


    element.innerHTML = `
        <div class="assistant-label">
            FilingIQ is analyzing
        </div>

        <div class="typing">
            <i></i>
            <i></i>
            <i></i>
        </div>
    `;


    chatMessages.appendChild(
        element
    );


    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}


function removeTyping() {

    document
        .getElementById("typing-card")
        ?.remove();
}



// =========================================================
// 5. SOURCE CARD
// =========================================================

function createSourceCard(source) {

    const details =
        document.createElement("details");


    details.className =
        "source-card";


    const summary =
        document.createElement("summary");


    const sourceTitle =
        document.createElement("span");


    sourceTitle.textContent =
        `[Source ${source.citation_id}] ` +
        `${source.company || "Unknown company"} ` +
        `· FY${source.year || "—"}`;


    const metadata =
        document.createElement("span");


    metadata.className =
        "source-meta";


    const metadataParts = [
        source.filing_type,
        source.ticker,
        source.chunk_index != null
            ? `chunk ${source.chunk_index}`
            : null,
    ].filter(Boolean);


    metadata.textContent =
        metadataParts.join(" · ");


    summary.append(
        sourceTitle,
        metadata
    );


    const evidence =
        document.createElement("p");


    evidence.textContent =
        source.evidence ||
        "No evidence preview available.";


    details.append(
        summary,
        evidence
    );


    return details;
}



// =========================================================
// 6. AI RESPONSE RENDERING
// =========================================================

function addAssistantResponse(data) {

    if (!chatMessages) {
        return;
    }


    const card =
        document.createElement("div");


    card.className =
        "assistant-card";


    // Header
    const header =
        document.createElement("div");


    header.className =
        "response-head";


    const label =
        document.createElement("div");


    label.className =
        "assistant-label";


    label.textContent =
        "FilingIQ";


    // Route badge
    const route =
        document.createElement("span");


    const isStructured =
        data.route === "structured";


    route.className =
        `route-pill ${
            isStructured
                ? "structured"
                : "rag"
        }`;


    route.textContent =
        isStructured
            ? "Structured KPI"
            : "Evidence RAG";


    header.append(
        label,
        route
    );


    // Answer
    const answer =
        document.createElement("div");


    answer.textContent =
        data.answer ||
        "No response received.";


    card.append(
        header,
        answer
    );


    // Sources
    const sources =
        Array.isArray(data.sources)
            ? data.sources
            : [];


    if (sources.length > 0) {

        const sourceWrapper =
            document.createElement("div");


        sourceWrapper.className =
            "sources-wrap";


        const sourceTitle =
            document.createElement("div");


        sourceTitle.className =
            "sources-title";


        sourceTitle.textContent =
            `${sources.length} source${
                sources.length === 1
                    ? ""
                    : "s"
            }`;


        sourceWrapper.appendChild(
            sourceTitle
        );


        sources.forEach(source => {

            sourceWrapper.appendChild(
                createSourceCard(source)
            );

        });


        card.appendChild(
            sourceWrapper
        );

    }

    // RAG no-evidence / abstention state
    else if (
        data.route === "rag"
    ) {

        const note =
            document.createElement("div");


        note.className =
            "abstention-note";


        note.textContent =
            "No supporting filing evidence was returned for this question.";


        card.appendChild(
            note
        );
    }


    chatMessages.appendChild(
        card
    );


    chatMessages.scrollTop =
        chatMessages.scrollHeight;
}



// =========================================================
// 7. SEND CHAT QUESTION
// =========================================================

async function sendQuestion(question) {

    const cleanQuestion =
        question.trim();


    if (
        !cleanQuestion ||
        !sendBtn ||
        sendBtn.disabled
    ) {
        return;
    }


    addUserMessage(
        cleanQuestion
    );


    if (chatInput) {
        chatInput.value = "";
    }


    sendBtn.disabled = true;
    sendBtn.textContent = "Working…";


    addTyping();


    // Build payload
    const payload = {
        question: cleanQuestion,
    };


    if (
        companySelect?.value
    ) {
        payload.company =
            companySelect.value;
    }


    if (
        yearSelect?.value
    ) {
        payload.year =
            Number(
                yearSelect.value
            );
    }


    try {

        const response =
            await fetch(
                "/api/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body:
                        JSON.stringify(
                            payload
                        ),
                }
            );


        const data =
            await response
                .json()
                .catch(
                    () => ({})
                );


        removeTyping();


        if (!response.ok) {

            addAssistantResponse({
                route: "rag",

                answer:
                    data.detail ||
                    `Request failed (${response.status}).`,

                sources: [],
            });


            return;
        }


        addAssistantResponse(
            data
        );

    }

    catch (error) {

        removeTyping();


        addAssistantResponse({
            route: "rag",

            answer:
                "Unable to reach the API. Please verify that the server is running.",

            sources: [],
        });

    }

    finally {

        sendBtn.disabled =
            false;


        sendBtn.textContent =
            "Ask";


        chatInput?.focus();
    }
}



// =========================================================
// 8. CHAT FORM EVENTS
// =========================================================

chatForm?.addEventListener(
    "submit",
    event => {

        event.preventDefault();


        sendQuestion(
            chatInput?.value || ""
        );
    }
);


chatInput?.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();


            chatForm?.requestSubmit();
        }
    }
);



// =========================================================
// 9. EXAMPLE PROMPT BUTTONS
// =========================================================

document
    .querySelectorAll(
        "[data-prompt]"
    )
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                sendQuestion(
                    button.dataset.prompt || ""
                );
            }
        );
    });



// =========================================================
// 10. QUALITATIVE INSIGHTS
// =========================================================

const insightSelect =
    document.getElementById(
        "insightRecordSelect"
    );


const insightsSection =
    document.getElementById(
        "insights"
    );


const insightsNavItem =
    document.getElementById(
        "insightsNavItem"
    );



// ---------------------------------------------------------
// Convert qualitative fields into list items
// ---------------------------------------------------------

function cleanInsightValues(value) {

    if (!value) {
        return [];
    }


    return String(value)
        .split("\n")
        .map(item =>
            item
                .replace(/^[-•*]\s*/, "")
                .trim()
        )
        .filter(Boolean);
}



// ---------------------------------------------------------
// Render growth/risk list
// ---------------------------------------------------------

function renderInsightList(
    elementId,
    values,
    emptyMessage
) {

    const container =
        document.getElementById(
            elementId
        );


    if (!container) {
        return;
    }


    container.innerHTML = "";


    const cleaned =
        Array.isArray(values)
            ? values.filter(Boolean)
            : [];


    if (
        cleaned.length === 0
    ) {

        const empty =
            document.createElement(
                "div"
            );


        empty.className =
            "empty-insight";


        empty.textContent =
            emptyMessage;


        container.appendChild(
            empty
        );


        return;
    }


    cleaned.forEach(text => {

        const item =
            document.createElement(
                "div"
            );


        item.className =
            "insight-item";


        item.textContent =
            text;


        container.appendChild(
            item
        );
    });
}



// ---------------------------------------------------------
// Render selected filing
// ---------------------------------------------------------

function selectInsightRecord(
    documentId
) {

    const record =
        filingData.find(
            row =>
                String(
                    row.document_id
                ) ===
                String(
                    documentId
                )
        );


    if (!record) {

        renderInsightList(
            "growthDriversList",
            [],
            "Growth drivers were not extracted for this filing."
        );


        renderInsightList(
            "riskFactorsList",
            [],
            "Risk factors were not extracted for this filing."
        );


        return;
    }


    const growthDrivers =
        cleanInsightValues(
            record.growth_drivers
        );


    const riskFactors =
        cleanInsightValues(
            record.risk_factors
        );


    renderInsightList(
        "growthDriversList",
        growthDrivers,
        "Growth drivers were not extracted for this filing."
    );


    renderInsightList(
        "riskFactorsList",
        riskFactors,
        "Risk factors were not extracted for this filing."
    );
}



// ---------------------------------------------------------
// Configure insight selector
//
// IMPORTANT:
// The section is NEVER hidden now.
// ---------------------------------------------------------

function configureInsightsSection() {

    if (!insightsSection) {
        return;
    }


    // Always keep the section visible.
    insightsSection.style.display = "";


    if (insightsNavItem) {
        insightsNavItem.style.display = "";
    }


    // If there is only one filing,
    // select it automatically and hide only the dropdown.
    if (
        insightSelect &&
        insightSelect.options.length === 1
    ) {

        insightSelect.selectedIndex = 0;

        insightSelect.style.display =
            "none";
    }


    // Render initial filing
    if (
        insightSelect?.value
    ) {

        selectInsightRecord(
            insightSelect.value
        );

    } else {

        renderInsightList(
            "growthDriversList",
            [],
            "Growth drivers were not extracted for this filing."
        );


        renderInsightList(
            "riskFactorsList",
            [],
            "Risk factors were not extracted for this filing."
        );
    }
}



// Change filing
insightSelect?.addEventListener(
    "change",
    () => {

        selectInsightRecord(
            insightSelect.value
        );
    }
);


configureInsightsSection();



// =========================================================
// 11. PDF UPLOAD FLOW
// =========================================================

const dropzone =
    document.getElementById(
        "dropzone"
    );


const fileInput =
    document.getElementById(
        "fileInput"
    );


const progressContainer =
    document.getElementById(
        "progressContainer"
    );


const progressBarFill =
    document.getElementById(
        "progressBarFill"
    );


const progressStatus =
    document.getElementById(
        "progressStatus"
    );


const progressPercent =
    document.getElementById(
        "progressPercent"
    );



// ---------------------------------------------------------
// Click file chooser
// ---------------------------------------------------------

dropzone?.addEventListener(
    "click",
    () => {

        fileInput?.click();

    }
);



// ---------------------------------------------------------
// Drag over
// ---------------------------------------------------------

[
    "dragenter",
    "dragover",
].forEach(eventName => {

    dropzone?.addEventListener(
        eventName,
        event => {

            event.preventDefault();


            dropzone.classList.add(
                "dragover"
            );
        }
    );
});



// ---------------------------------------------------------
// Drag leave / drop
// ---------------------------------------------------------

[
    "dragleave",
    "drop",
].forEach(eventName => {

    dropzone?.addEventListener(
        eventName,
        event => {

            event.preventDefault();


            dropzone.classList.remove(
                "dragover"
            );
        }
    );
});



// ---------------------------------------------------------
// Drop file
// ---------------------------------------------------------

dropzone?.addEventListener(
    "drop",
    event => {

        const file =
            event
                .dataTransfer
                ?.files?.[0];


        if (file) {

            uploadFile(
                file
            );
        }
    }
);



// ---------------------------------------------------------
// File chooser
// ---------------------------------------------------------

fileInput?.addEventListener(
    "change",
    () => {

        const file =
            fileInput
                .files?.[0];


        if (file) {

            uploadFile(
                file
            );
        }
    }
);



// =========================================================
// 12. UPLOAD FUNCTION
// =========================================================

function uploadFile(file) {

    // Validate extension
    if (
        !file.name
            .toLowerCase()
            .endsWith(".pdf")
    ) {

        showToast(
            "Invalid file",
            "Only PDF files are supported.",
            "error"
        );


        return;
    }


    // Validate size
    if (
        file.size >
        50 * 1024 * 1024
    ) {

        showToast(
            "File too large",
            "PDF uploads are limited to 50 MB.",
            "error"
        );


        return;
    }


    // Start progress UI
    if (progressContainer) {
        progressContainer.hidden =
            false;
    }


    if (progressStatus) {
        progressStatus.textContent =
            "Uploading and processing…";
    }


    if (progressBarFill) {
        progressBarFill.style.width =
            "8%";
    }


    if (progressPercent) {
        progressPercent.textContent =
            "8%";
    }


    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    const xhr =
        new XMLHttpRequest();


    xhr.open(
        "POST",
        "/api/upload"
    );



    // Upload progress
    xhr.upload.onprogress =
        event => {

            if (
                !event.lengthComputable
            ) {
                return;
            }


            const percentage =
                Math.min(
                    70,
                    Math.max(
                        8,
                        Math.round(
                            (
                                event.loaded /
                                event.total
                            ) * 70
                        )
                    )
                );


            if (progressBarFill) {
                progressBarFill.style.width =
                    `${percentage}%`;
            }


            if (progressPercent) {
                progressPercent.textContent =
                    `${percentage}%`;
            }
        };



    // Upload completed
    xhr.onload =
        () => {

            if (
                xhr.status >= 200 &&
                xhr.status < 300
            ) {

                if (progressBarFill) {
                    progressBarFill.style.width =
                        "100%";
                }


                if (progressPercent) {
                    progressPercent.textContent =
                        "100%";
                }


                if (progressStatus) {
                    progressStatus.textContent =
                        "Complete";
                }


                showToast(
                    "Ingestion complete",
                    `${file.name} was processed successfully.`
                );


                setTimeout(
                    () =>
                        location.reload(),
                    1000
                );

            }

            else {

                if (progressContainer) {
                    progressContainer.hidden =
                        true;
                }


                let payload = {};


                try {

                    payload =
                        JSON.parse(
                            xhr.responseText
                        );

                }

                catch {

                    payload = {};

                }


                showToast(
                    "Ingestion failed",

                    payload.detail ||
                    "The filing could not be processed.",

                    "error"
                );
            }
        };



    // Network failure
    xhr.onerror =
        () => {

            if (progressContainer) {
                progressContainer.hidden =
                    true;
            }


            showToast(
                "Connection error",
                "Unable to reach the ingestion API.",
                "error"
            );
        };


    xhr.send(
        formData
    );
}