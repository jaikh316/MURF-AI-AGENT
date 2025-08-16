
let mediaRecorder;
let recordedChunks = [];
let isRecording = false;
let sessionId = "default-session"; // or generate dynamically

const recordButton = document.getElementById("recordButton");
const chatContainer = document.getElementById("chatContainer");
const echoAudioPlayer = document.getElementById("echoAudioPlayer");
const statusMessage = document.getElementById("echoStatusMessage");

// Toggle record/stop on button click
recordButton.addEventListener("click", () => {
  if (!isRecording) {
    startRecording();
  } else {
    stopRecording();
  }
});

function startRecording() {
  navigator.mediaDevices
    .getUserMedia({ audio: true })
    .then((stream) => {
      recordedChunks = [];
      mediaRecorder = new MediaRecorder(stream);
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunks.push(e.data);
      };
      mediaRecorder.onstop = sendAudioToAgent;
      mediaRecorder.start();
      isRecording = true;
      updateButton();
      statusMessage.textContent = "Recording...";
    })
    .catch((err) => {
      console.error("Microphone access denied:", err);
      statusMessage.textContent = "Microphone access denied.";
    });
}

function stopRecording() {
  mediaRecorder.stop();
  isRecording = false;
  updateButton();
  statusMessage.textContent = "Processing...";
}

function updateButton() {
  recordButton.textContent = isRecording
    ? "⏹ Stop Recording"
    : "🎤 Start Recording";
  recordButton.classList.toggle("recording", isRecording);
}

async function sendAudioToAgent() {
  const blob = new Blob(recordedChunks, { type: "audio/webm" });
  const formData = new FormData();
  formData.append("file", blob, "recording.webm");

  try {
    const response = await fetch(
      `/agent/chat/${encodeURIComponent(sessionId)}`,
      {
        method: "POST",
        body: formData,
      }
    );
    const data = await response.json();

    if (data.transcription) {
      chatContainer.innerHTML += `<div class="user-message"><b>You:</b> ${data.transcription}</div>`;
    }
    if (data.llm_reply) {
      chatContainer.innerHTML += `<div class="assistant-message"><b>Assistant:</b> ${data.llm_reply}</div>`;
    }
    if (data.error) {
      chatContainer.innerHTML += `<div class="error-message">Error: ${data.error}</div>`;
    }
    chatContainer.scrollTop = chatContainer.scrollHeight;

    if (data.murf_audio_url) {
      echoAudioPlayer.src = data.murf_audio_url;
      await echoAudioPlayer.play();
    } else if (data.llm_reply) {
      speechSynthesis.speak(new SpeechSynthesisUtterance(data.llm_reply));
    } else {
      speechSynthesis.speak(
        new SpeechSynthesisUtterance("I'm having trouble connecting right now.")
      );
    }

    statusMessage.textContent = "Ready.";
  } catch (err) {
    console.error("Error sending audio:", err);
    chatContainer.innerHTML += `<div class="error-message">Network error — please try again.</div>`;
    speechSynthesis.speak(
      new SpeechSynthesisUtterance("I'm having trouble connecting right now.")
    );
    statusMessage.textContent = "Error occurred.";
  }
}
