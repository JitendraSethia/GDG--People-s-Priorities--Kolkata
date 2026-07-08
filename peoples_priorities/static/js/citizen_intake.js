const NAME_PATTERN = /^[\p{L}\p{M}]+(?:[ '\-][\p{L}\p{M}]+)*$/u;
const PHONE_PATTERN = /^(?:\+91|91|0)?[6-9]\d{9}$/;

function nativeGeolocation() {
  var isNative = window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform();
  return isNative ? window.Capacitor.Plugins.Geolocation : null;
}

async function getCurrentPosition() {
  const native = nativeGeolocation();
  if (native) {
    const pos = await native.getCurrentPosition({ enableHighAccuracy: true, timeout: 10000 });
    return { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
  }
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Geolocation isn't available in this browser."));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
      (err) => reject(err)
    );
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("intake-form");
  if (!form) return;

  const langButtons = document.querySelectorAll(".lang-toggle button");
  const languageInput = document.getElementById("language");
  const micBtn = document.getElementById("mic-btn");
  const textarea = document.getElementById("raw_text");
  const geoBtn = document.getElementById("geo-btn");
  const geoStatus = document.getElementById("geo-status");
  const wardResult = document.getElementById("ward-result");
  const latInput = document.getElementById("latitude");
  const lngInput = document.getElementById("longitude");
  const cameraBtn = document.getElementById("camera-btn");
  const photoFallbackInput = document.getElementById("photo-fallback-input");
  const photoPreview = document.getElementById("photo-preview");
  const nameInput = document.getElementById("citizen_name");
  const phoneInput = document.getElementById("citizen_phone");
  const nameHint = document.getElementById("name-hint");
  const phoneHint = document.getElementById("phone-hint");
  const errorBox = document.getElementById("form-error");

  let capturedPhoto = null;

  langButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      langButtons.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      languageInput.value = btn.dataset.lang;
      textarea.placeholder = btn.dataset.placeholder || textarea.placeholder;
    });
  });

  if (window.setupVoiceIntake && micBtn) {
    setupVoiceIntake({ micButton: micBtn, textarea, langSelect: languageInput });
  }

  if (window.setupCameraCapture && cameraBtn) {
    setupCameraCapture({
      cameraButton: cameraBtn,
      fallbackInput: photoFallbackInput,
      previewImg: photoPreview,
      onCapture: (blob) => { capturedPhoto = blob; },
    });
  }

  geoBtn.addEventListener("click", async () => {
    geoBtn.setAttribute("aria-busy", "true");
    geoStatus.textContent = "Locating…";
    wardResult.hidden = true;
    try {
      const { latitude, longitude } = await getCurrentPosition();
      latInput.value = latitude;
      lngInput.value = longitude;
      geoStatus.textContent = "Location captured ✓";

      const nearest = await Api.get("/api/wards/nearest", { lat: latitude, lng: longitude });
      wardResult.textContent = `Detected ward: ${nearest.ward}`;
      wardResult.hidden = false;
    } catch (err) {
      geoStatus.textContent = "Couldn't get your location — please enable GPS and try again.";
    } finally {
      geoBtn.removeAttribute("aria-busy");
    }
  });

  function validateField(input, pattern, hintEl, message) {
    const value = input.value.trim();
    if (value && !pattern.test(value)) {
      hintEl.textContent = message;
      return false;
    }
    hintEl.textContent = "";
    return true;
  }

  nameInput.addEventListener("blur", () => validateField(nameInput, NAME_PATTERN, nameHint, "Name can only contain letters."));
  phoneInput.addEventListener("blur", () => validateField(phoneInput, PHONE_PATTERN, phoneHint, "Enter a valid 10-digit mobile number."));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorBox.textContent = "";

    const rawText = textarea.value.trim();
    const nameValid = validateField(nameInput, NAME_PATTERN, nameHint, "Name can only contain letters.");
    const phoneValid = validateField(phoneInput, PHONE_PATTERN, phoneHint, "Enter a valid 10-digit mobile number.");

    if (!rawText) {
      errorBox.textContent = "Please describe the issue.";
      return;
    }
    if (!latInput.value || !lngInput.value) {
      errorBox.textContent = "Please detect your location before submitting.";
      return;
    }
    if (!nameValid || !phoneValid) {
      errorBox.textContent = "Please fix the highlighted fields.";
      return;
    }

    const formData = new FormData();
    formData.append("raw_text", rawText);
    formData.append("language", languageInput.value || "en");
    formData.append("latitude", latInput.value);
    formData.append("longitude", lngInput.value);
    if (nameInput.value.trim()) formData.append("citizen_name", nameInput.value.trim());
    if (phoneInput.value.trim()) formData.append("citizen_phone", phoneInput.value.trim());
    if (capturedPhoto) formData.append("photo", capturedPhoto, "photo.jpg");

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.setAttribute("aria-busy", "true");
    submitBtn.disabled = true;

    try {
      const res = await fetch("/api/grievances", { method: "POST", body: formData });
      const result = await res.json();
      if (!res.ok) throw new Error(result.message || "Something went wrong. Please try again.");
      window.location.href = `/report/confirmation/${result.ticket_id}`;
    } catch (err) {
      errorBox.textContent = err.message || "Something went wrong. Please try again.";
      submitBtn.removeAttribute("aria-busy");
      submitBtn.disabled = false;
    }
  });
});
