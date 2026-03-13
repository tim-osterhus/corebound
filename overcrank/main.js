const shell = {
  bootState: document.querySelector("#boot-state"),
  statusMessage: document.querySelector("#status-message"),
  heatValue: document.querySelector("#heat-value"),
  torqueValue: document.querySelector("#torque-value"),
  pressureValue: document.querySelector("#pressure-value"),
  cycleValue: document.querySelector("#cycle-value"),
  statusReadout: document.querySelector("#status-readout"),
  viewportReadout: document.querySelector("#viewport-readout"),
  milestoneReadout: document.querySelector("#milestone-readout"),
  viewportShell: document.querySelector("#viewport-shell"),
  gameViewport: document.querySelector("#game-viewport"),
};

const missingElements = Object.entries(shell)
  .filter(([, element]) => !element)
  .map(([key]) => key);

if (missingElements.length > 0) {
  throw new Error(`Overcrank shell is missing required elements: ${missingElements.join(", ")}`);
}

function bootShell() {
  shell.bootState.textContent = "Shell ready";
  shell.statusMessage.textContent = "Placeholder systems online. Gameplay runtime not installed.";
  shell.heatValue.textContent = "47%";
  shell.torqueValue.textContent = "Green band";
  shell.pressureValue.textContent = "Holding";
  shell.cycleValue.textContent = "Awaiting loop";
  shell.statusReadout.textContent = "Scaffold active";
  shell.viewportReadout.textContent = "Viewport container bound";
  shell.milestoneReadout.textContent = "Playable build pending";
  shell.viewportShell.dataset.boot = "ready";
  shell.gameViewport.dataset.mode = "placeholder";
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootShell, { once: true });
} else {
  bootShell();
}
