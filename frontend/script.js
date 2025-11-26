const backendURL = "http://127.0.0.1:8000";
const studentIdInput = document.getElementById("studentId");
const userInput = document.getElementById("userInput");
const responseBox = document.getElementById("responseBox");
const quizSubmissionBox = document.getElementById("quizSubmissionBox");
const quizForm = document.getElementById("quizForm");
const quizTopicDisplay = document.getElementById("quizTopicDisplay");
const pdfUpload = document.getElementById("pdfUpload");
const uploadStatus = document.getElementById("uploadStatus");
const loader = document.getElementById("aiLoader");
const loaderText = loader ? loader.querySelector(".loader-text") : null;

let currentQuiz = { topic: null, questions: [] }; // Global state to hold the current quiz

// ---------- Helper function ----------
function showResponse(text) {
    toggleLoader(false);
    responseBox.innerHTML = text;
}

function toggleLoader(show, message = "Thinking...") {
    if (!loader) return;
    loader.style.display = show ? "flex" : "none";
    if (loaderText && message) {
        loaderText.textContent = message;
    }
}

// ---------- 0. Upload PDF ----------
async function uploadPDF() {
    const file = pdfUpload.files[0];
    
    if (!file) {
        uploadStatus.innerHTML = "❌ Please select a PDF file.";
        uploadStatus.style.color = "#dc3545";
        return;
    }
    
    if (!file.name.endsWith('.pdf')) {
        uploadStatus.innerHTML = "❌ Only PDF files are supported.";
        uploadStatus.style.color = "#dc3545";
        return;
    }
    
    uploadStatus.innerHTML = "⏳ Uploading and processing PDF...";
    uploadStatus.style.color = "#17a2b8";
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch(`${backendURL}/upload`, {
            method: "POST",
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            uploadStatus.innerHTML = `✅ ${data.message}`;
            uploadStatus.style.color = "#28a745";
            pdfUpload.value = ''; // Clear file input
        } else {
            uploadStatus.innerHTML = `❌ ${data.message}`;
            uploadStatus.style.color = "#dc3545";
        }
    } catch (error) {
        console.error("Upload error:", error);
        uploadStatus.innerHTML = "❌ Error uploading file. Check the server console.";
        uploadStatus.style.color = "#dc3545";
    }
}

// ---------- 1. Ask Tutor (Retrieval/Answer) ----------
async function getAnswer() {
    const question = userInput.value.trim();
    const student_id = studentIdInput.value.trim() || 'default_student';

    if (!question) {
        showResponse("❗ Please enter a question.");
        return;
    }

    toggleLoader(true, "Thinking...");
    showResponse("");
    quizSubmissionBox.style.display = 'none';

    const payload = { input_text: question, student_id: student_id };

    try {
        const response = await fetch(`${backendURL}/ask_answer`, { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        let output = `<strong>Tutor Response:</strong> ${data.natural_language_response}`;
        showResponse(output);

    } catch (error) {
        console.error("Fetch error:", error);
        showResponse("❌ Error connecting to the backend for answer. Check the server console.");
    }
}

// ---------- 2. Generate Quiz (Direct Quiz Generator) ----------
async function generateQuiz() {
    const topic = userInput.value.trim();
    const student_id = studentIdInput.value.trim() || 'default_student';

    if (!topic) {
        showResponse("❗ Please enter a topic in the input box to generate a quiz.");
        return;
    }

    toggleLoader(true, "Designing quiz...");
    showResponse("");
    quizSubmissionBox.style.display = 'none';

    const payload = { input_text: topic, student_id: student_id };

    try {
        const response = await fetch(`${backendURL}/quiz_generate`, { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.questions && data.questions.length > 0) {
            currentQuiz.topic = data.topic;
            currentQuiz.questions = data.questions;
            
            showResponse(`✅ **Quiz Generated:** Here is a quiz on **${data.topic}** (Difficulty is adapted to your profile).`);
            renderQuiz(data.questions);
        } else {
             showResponse(`❌ Could not generate quiz for topic: ${data.topic}. Please try a different topic.`);
        }

    } catch (error) {
        console.error("Quiz generation error:", error);
        showResponse("❌ Error connecting to the backend for quiz generation.");
    }
}

// Function to render the quiz questions for submission
function renderQuiz(questions) {
    quizForm.innerHTML = ''; 
    let html = '';
    
    questions.forEach((q, index) => {
        q.id = index + 1; 
        
        html += `<div style="margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">`;
        html += `<p><strong>Q${q.id}:</strong> ${q.q}</p>`;
        
        const optionMap = ['A', 'B', 'C', 'D']; 

        q.options.forEach((opt, optIndex) => {
            const label = optionMap[optIndex] || opt; 
            html += `<label style="display: block; margin-left: 10px;">
                        <input type="radio" name="question_${q.id}" value="${label}"> ${label}) ${opt}
                     </label>`;
        });
        html += `</div>`;
    });

    quizTopicDisplay.innerText = currentQuiz.topic;
    quizForm.innerHTML = html;
    quizSubmissionBox.style.display = 'block';
}


// ---------- 3. Quiz Submission ----------
async function submitQuiz() {
    const student_id = studentIdInput.value.trim() || 'default_student';
    if (!currentQuiz.topic || currentQuiz.questions.length === 0) {
        showResponse("No active quiz to submit.");
        return;
    }

    const submissionData = [];
    let allAnswered = true;

    currentQuiz.questions.forEach(q => {
        const selected = document.querySelector(`input[name="question_${q.id}"]:checked`);
        if (!selected) {
            allAnswered = false;
        }
        
        submissionData.push({
            question_id: q.id,
            student_answer: selected ? selected.value : null,
            correct_answer: q.correct_answer 
        });
    });
    
    if (!allAnswered) {
         showResponse("Please answer all questions before submitting.");
         return;
    }
    
    toggleLoader(true, "Reviewing answers...");
    showResponse("");

    const payload = {
        student_id: student_id,
        topic: currentQuiz.topic,
        submission: submissionData
    };
    
    try {
        const response = await fetch(`${backendURL}/quiz_submit`, { 
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        // Clear quiz UI and display feedback
        quizSubmissionBox.style.display = 'none';
        currentQuiz = { topic: null, questions: [] };

        showResponse(`<strong>Feedback:</strong> ${data.natural_language_response}`);

    } catch (error) {
        console.error("Submission error:", error);
        showResponse("❌ Error submitting quiz.");
    }
}


// ---------- 4. Progress Report ----------
async function getReport() {
    const student_id = studentIdInput.value.trim() || 'default_student';
    
    toggleLoader(true, "Compiling report...");
    showResponse("");

    try {
        const response = await fetch(`${backendURL}/progress/${student_id}`, { 
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        const data = await response.json();
        
        let reportText = `<h3>📊 Progress Report for ${data.student_id}</h3>`;
        reportText += `<strong>Summary:</strong> ${data.natural_language_summary}<br><br>`;
        reportText += `<strong>Agent Recommendation:</strong> ${data.agent_recommendation}<br><br>`;
        reportText += `<h4>Topic Strengths:</h4>`;
        
        reportText += `
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px;">Topic</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">Accuracy (%)</th>
                        <th style="border: 1px solid #ddd; padding: 8px;">Strength</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        for (const topic in data.progress) {
            const p = data.progress[topic];
            let color = 'lightgray';
            if (p.strength === 'strong') color = '#d4edda'; 
            else if (p.strength === 'weak') color = '#f8d7da'; 
            
            reportText += `
                <tr style="background-color: ${color};">
                    <td style="border: 1px solid #ddd; padding: 8px;">${topic}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">${p.accuracy}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-transform: capitalize;">${p.strength}</td>
                </tr>
            `;
        }
        
        reportText += `</tbody></table>`;
        
        showResponse(reportText);

    } catch (error) {
        console.error("Report error:", error);
        showResponse("❌ Error fetching report. Make sure the student ID is correct.");
    }
}