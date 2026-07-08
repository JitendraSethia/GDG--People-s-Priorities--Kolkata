function setupVoiceIntake({ micButton, textarea, langSelect }) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    micButton.disabled = true;
    micButton.title = "Voice input isn't supported in this browser";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;

  const langMap = { en: "en-IN", bn: "bn-IN", hi: "hi-IN" };
  let recording = false;

  micButton.addEventListener("click", () => {
    if (recording) {
      recognition.stop();
      return;
    }
    recognition.lang = langMap[langSelect.value] || "en-IN";
    try {
      recognition.start();
    } catch (err) {
      console.warn("speech recognition failed to start", err);
    }
  });

  recognition.addEventListener("start", () => {
    recording = true;
    micButton.classList.add("recording");
    micButton.textContent = "Listening…";
  });

  recognition.addEventListener("end", () => {
    recording = false;
    micButton.classList.remove("recording");
    micButton.textContent = "🎤 Speak";
  });

  recognition.addEventListener("result", (event) => {
    const transcript = Array.from(event.results).map((r) => r[0].transcript).join(" ");
    textarea.value = textarea.value ? `${textarea.value} ${transcript}` : transcript;
  });

  recognition.addEventListener("error", (event) => {
    console.warn("speech recognition error", event.error);
  });
}
