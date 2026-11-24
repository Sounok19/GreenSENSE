(function () {
  'use strict';

  var form = document.getElementById('upload-form');
  if (!form) return;

  var input = document.getElementById('leaf-input');
  var dropzone = document.getElementById('dropzone');
  var stage = document.getElementById('stage');
  var preview = document.getElementById('preview');
  var analyzeBtn = document.getElementById('analyze-btn');
  var resetBtn = document.getElementById('reset-btn');
  var errorBox = document.getElementById('upload-error');
  var busyOverlay = document.getElementById('busy');

  var MAX_SOURCE_BYTES = 25 * 1024 * 1024; // what we accept before cropping in the browser
  var MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // server limit for an uncropped upload

  var cropper = null;
  var objectUrl = null;
  var currentFile = null;
  var busy = false;

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }

  function clearError() {
    errorBox.hidden = true;
    errorBox.textContent = '';
  }

  function setBusy(state) {
    busy = state;
    analyzeBtn.disabled = state;
    resetBtn.disabled = state;
    analyzeBtn.classList.toggle('is-loading', state);
    busyOverlay.hidden = !state;
  }

  function teardown() {
    if (cropper) {
      cropper.destroy();
      cropper = null;
    }
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    preview.onload = null;
    preview.onerror = null;
    preview.removeAttribute('src');
  }

  function resetUI() {
    teardown();
    currentFile = null;
    try { input.value = ''; } catch (e) { /* ignore */ }
    stage.hidden = true;
    dropzone.hidden = false;
    setBusy(false);
  }

  function handleFile(file) {
    if (!file) return;
    clearError();

    var looksLikeImage = /^image\//.test(file.type) || /\.(jpe?g|png|webp|gif|bmp)$/i.test(file.name);
    if (!looksLikeImage) {
      resetUI();
      showError('Please choose an image file (JPG or PNG).');
      return;
    }
    if (file.size > MAX_SOURCE_BYTES) {
      resetUI();
      showError('That photo is too large. Choose one under 25 MB.');
      return;
    }

    teardown();
    currentFile = file;
    objectUrl = URL.createObjectURL(file);

    preview.onload = function () {
      preview.onload = null;
      dropzone.hidden = true;
      stage.hidden = false;
      if (window.Cropper) {
        cropper = new Cropper(preview, {
          viewMode: 1,
          autoCropArea: 0.9,
          background: false,
          guides: false,
          responsive: true,
          minCropBoxWidth: 64,
          minCropBoxHeight: 64
        });
      }
    };
    preview.onerror = function () {
      resetUI();
      showError("This image couldn't be opened. Try a JPG or PNG photo.");
    };
    preview.src = objectUrl;
  }

  function send(file) {
    try {
      var transfer = new DataTransfer();
      transfer.items.add(file);
      input.files = transfer.files;
      form.submit();
    } catch (err) {
      // Older browsers without DataTransfer: post with fetch and show the response page.
      var data = new FormData();
      data.append('file', file, file.name || 'leaf.jpg');
      fetch(form.action, { method: 'POST', body: data })
        .then(function (response) { return response.text(); })
        .then(function (html) {
          document.open();
          document.write(html);
          document.close();
        })
        .catch(function () {
          setBusy(false);
          showError('Upload failed. Check your connection and try again.');
        });
    }
  }

  input.addEventListener('change', function () {
    handleFile(input.files && input.files[0]);
  });

  resetBtn.addEventListener('click', function () {
    clearError();
    resetUI();
    input.focus();
  });

  ['dragenter', 'dragover'].forEach(function (name) {
    dropzone.addEventListener(name, function (e) {
      e.preventDefault();
      dropzone.classList.add('is-over');
    });
  });
  ['dragleave', 'dragend', 'drop'].forEach(function (name) {
    dropzone.addEventListener(name, function () { dropzone.classList.remove('is-over'); });
  });
  dropzone.addEventListener('drop', function (e) {
    e.preventDefault();
    var files = e.dataTransfer && e.dataTransfer.files;
    if (files && files.length) handleFile(files[0]);
  });
  // Stop the browser from navigating to a file dropped outside the drop zone.
  ['dragover', 'drop'].forEach(function (name) {
    window.addEventListener(name, function (e) {
      if (!dropzone.contains(e.target)) e.preventDefault();
    });
  });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    if (busy) return;
    if (!currentFile) {
      showError('Choose a leaf photo first.');
      return;
    }
    clearError();
    setBusy(true);

    if (!cropper) {
      if (currentFile.size > MAX_UPLOAD_BYTES) {
        setBusy(false);
        showError('Choose a photo smaller than 10 MB.');
        return;
      }
      send(currentFile);
      return;
    }

    var canvas = cropper.getCroppedCanvas({
      maxWidth: 1024,
      maxHeight: 1024,
      fillColor: '#ffffff',
      imageSmoothingQuality: 'high'
    });
    if (!canvas) {
      setBusy(false);
      showError("The crop couldn't be created. Please adjust the box and try again.");
      return;
    }
    canvas.toBlob(function (blob) {
      if (!blob) {
        setBusy(false);
        showError("The crop couldn't be created. Please try again.");
        return;
      }
      send(new File([blob], 'leaf.jpg', { type: 'image/jpeg' }));
    }, 'image/jpeg', 0.92);
  });

  // Coming back via the browser's back button should not leave the page stuck "analyzing".
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
      clearError();
      resetUI();
    }
  });
})();
