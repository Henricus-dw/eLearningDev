(function () {
  // Run after DOM is ready
  document.addEventListener('DOMContentLoaded', function () {
    var audio       = document.getElementById('vo-audio');
    if (!audio) return;  // no audio gate on this page

    var playBtn     = document.getElementById('vo-play');
    var stopBtn     = document.getElementById('vo-stop');
    var statusLabel = document.getElementById('vo-status');
    var progressBar = document.getElementById('vo-progress');
    var continueBtn = document.getElementById('vo-continue');

    function setStatus(text) {
      if (statusLabel) {
        statusLabel.textContent = text;
      }
    }

    function lockContinue() {
      if (!continueBtn) return;
      continueBtn.style.pointerEvents = 'none';
      continueBtn.style.opacity = '.45';
      continueBtn.style.cursor = 'not-allowed';
      continueBtn.style.background = '#9ca3af';
      continueBtn.style.color = '#f9fafb';
    }

    function unlockContinue() {
      if (!continueBtn) return;
      continueBtn.style.pointerEvents = 'auto';
      continueBtn.style.opacity = '1';
      continueBtn.style.cursor = 'pointer';
      continueBtn.style.background = '#C7A434';
      continueBtn.style.color = '#111827';
    }

    lockContinue();

    if (playBtn) {
      playBtn.addEventListener('click', function () {
        audio.play().then(function () {
          setStatus('Status: Playing…');
        }).catch(function (err) {
          console.error('Audio play error:', err);
          setStatus('Status: Unable to play (check audio file).');
        });
      });
    }

    if (stopBtn) {
      stopBtn.addEventListener('click', function () {
        audio.pause();
        audio.currentTime = 0;
        setStatus('Status: Stopped.');
        if (progressBar) {
          progressBar.style.width = '0%';
        }
      });
    }

    audio.addEventListener('timeupdate', function () {
      if (!audio.duration || !isFinite(audio.duration)) return;
      if (!progressBar) return;
      var pct = (audio.currentTime / audio.duration) * 100;
      progressBar.style.width = pct + '%';
    });

    audio.addEventListener('ended', function () {
      setStatus('Status: Completed ✔ You may continue.');
      if (progressBar) {
        progressBar.style.width = '100%';
      }
      unlockContinue();
    });

    audio.addEventListener('pause', function () {
      if (audio.currentTime < audio.duration) {
        setStatus('Status: Paused.');
      }
    });
  });
})();
