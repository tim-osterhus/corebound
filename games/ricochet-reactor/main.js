const requiredElements = {
  bootState: document.querySelector("#boot-state"),
  statusMessage: document.querySelector("#status-message"),
  arenaShell: document.querySelector("#arena-shell"),
  chargeValue: document.querySelector("#charge-value"),
  integrityValue: document.querySelector("#integrity-value"),
  chainValue: document.querySelector("#chain-value"),
  laneValue: document.querySelector("#lane-value"),
  directiveValue: document.querySelector("#directive-value"),
  arenaValue: document.querySelector("#arena-value"),
};

function bootShell() {
  const missing = Object.entries(requiredElements)
    .filter(([, element]) => !element)
    .map(([key]) => key);

  if (missing.length > 0) {
    const message = `Shell boot failed: missing ${missing.join(", ")}.`;
    if (requiredElements.statusMessage) {
      requiredElements.statusMessage.textContent = message;
    }
    console.error(message);
    return;
  }

  requiredElements.bootState.textContent = "Shell ready";
  requiredElements.statusMessage.textContent = "Shell ready. Arena conduit waiting for gameplay systems.";
  requiredElements.chargeValue.textContent = "00%";
  requiredElements.integrityValue.textContent = "Stable";
  requiredElements.chainValue.textContent = "x0";
  requiredElements.laneValue.textContent = "North rail online";
  requiredElements.directiveValue.textContent = "Await first playable systems";
  requiredElements.arenaValue.textContent = "Arena conduit aligned";
  requiredElements.arenaShell.classList.add("shell-ready");
  document.body.classList.add("shell-ready");
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootShell, { once: true });
} else {
  bootShell();
}
