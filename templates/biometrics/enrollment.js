(() => {
  const video = document.querySelector('#camera');
  const canvas = document.querySelector('#canvas');
  const field = document.querySelector('#form-face-data');
  const start = document.querySelector('#start-camera');
  const capture = document.querySelector('#capture');
  const save = document.querySelector('#save-enrollment');
  const status = document.querySelector('#camera-status');
  start.addEventListener('click', async () => {
    if (!navigator.mediaDevices?.getUserMedia) { status.textContent = 'Camera access is unavailable. Use HTTPS or localhost.'; return; }
    try {
      video.srcObject = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
      await video.play(); capture.disabled = false;
      status.textContent = 'Camera ready. Position one face in the frame, then capture.';
    } catch (error) { status.textContent = `Unable to start camera: ${error.name || 'permission denied'}.`; }
  });
  capture.addEventListener('click', () => {
    if (!video.videoWidth || !video.videoHeight) { status.textContent = 'Wait for the camera preview before capturing.'; return; }
    canvas.width = video.videoWidth; canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
    field.value = canvas.toDataURL('image/jpeg', 0.85); save.disabled = false;
    status.textContent = 'Face captured. Review the image and save enrollment.';
  });
  document.querySelector('#enroll-form').addEventListener('submit', event => {
    if (!field.value) { event.preventDefault(); status.textContent = 'Capture a face before saving enrollment.'; }
  });
})();
