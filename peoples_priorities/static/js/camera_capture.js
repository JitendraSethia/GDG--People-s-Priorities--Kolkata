function setupCameraCapture({ cameraButton, fallbackInput, previewImg, onCapture }) {
  const isNative = () => !!(window.Capacitor && window.Capacitor.isNativePlatform && window.Capacitor.isNativePlatform());

  cameraButton.addEventListener("click", async () => {
    if (isNative()) {
      try {
        const { Camera } = window.Capacitor.Plugins;
        // 'uri' -> photo.webPath works across both the getPhoto() and newer
        // takePhoto() Capacitor camera APIs; base64/dataUrl result types were
        // dropped in newer versions, so webPath is the version-safe choice.
        const photo = await Camera.getPhoto({ resultType: "uri", source: "CAMERA", quality: 80 });
        const blob = await (await fetch(photo.webPath)).blob();
        previewImg.src = photo.webPath;
        previewImg.hidden = false;
        onCapture(blob);
      } catch (err) {
        console.warn("Native camera capture cancelled or failed", err);
      }
    } else {
      fallbackInput.click();
    }
  });

  fallbackInput.addEventListener("change", () => {
    const file = fallbackInput.files[0];
    if (!file) return;
    previewImg.src = URL.createObjectURL(file);
    previewImg.hidden = false;
    onCapture(file);
  });
}
