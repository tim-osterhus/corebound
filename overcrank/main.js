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
  gameCanvas: document.querySelector("#game-canvas"),
  gameOverlay: document.querySelector("#game-overlay"),
  overlayEyebrow: document.querySelector("#overlay-eyebrow"),
  overlayTitle: document.querySelector("#overlay-title"),
  overlayCopy: document.querySelector("#overlay-copy"),
};

const missingElements = Object.entries(shell)
  .filter(([, element]) => !element)
  .map(([key]) => key);

if (missingElements.length > 0) {
  throw new Error(`Overcrank shell is missing required elements: ${missingElements.join(", ")}`);
}

const config = {
  width: 360,
  height: 640,
  wallWidth: 34,
  floorY: 34,
  playerWidth: 28,
  playerHeight: 28,
  moveSpeed: 230,
  airControl: 0.16,
  jumpVelocity: 540,
  wallJumpX: 290,
  wallJumpY: 575,
  gravity: 1320,
  wallSlideSpeed: 190,
  maxFallSpeed: 760,
  cameraLead: 180,
  heatStart: -220,
  heatBaseSpeed: 36,
  heatRamp: 8,
};

const canvas = shell.gameCanvas;
const context = canvas.getContext("2d");

const state = {
  mode: "intro",
  cameraY: 0,
  highestY: config.floorY,
  heatY: config.heatStart,
  lastTime: 0,
  keys: {
    left: false,
    right: false,
  },
  player: createPlayer(),
};

function createPlayer() {
  return {
    x: config.width * 0.5 - config.playerWidth * 0.5,
    y: config.floorY,
    vx: 0,
    vy: 0,
    onGround: true,
    onWall: null,
  };
}

function setOverlay(eyebrow, title, copy) {
  shell.overlayEyebrow.textContent = eyebrow;
  shell.overlayTitle.textContent = title;
  shell.overlayCopy.textContent = copy;
}

function updateOverlay() {
  if (state.mode === "running") {
    shell.gameOverlay.classList.add("is-hidden");
    return;
  }

  shell.gameOverlay.classList.remove("is-hidden");

  if (state.mode === "intro") {
    setOverlay(
      "Start run",
      "Ignite the rig",
      "Press Space, W, Up, A, D, or the arrow keys to start. Reach a wall, kick away, and stay above the heat line."
    );
    return;
  }

  setOverlay(
    "Run failed",
    "Heat breach",
    "The room flashed over. Press any movement key or jump key to restart from a clean run."
  );
}

function updateHud() {
  const altitude = Math.max(0, Math.round((state.highestY - config.floorY) / 10));
  const heatGap = Math.max(0, state.player.y - state.heatY);
  const heatPercent = Math.max(0, Math.min(100, Math.round(100 - heatGap / 4.8)));

  shell.statusMessage.textContent =
    state.mode === "intro"
      ? "Stand by. One key press starts the climb."
      : state.mode === "running"
        ? "Climb clean and keep the heat below your boots."
        : "Heat contact detected. Any movement or jump key restarts.";
  shell.heatValue.textContent = `${heatPercent}%`;
  shell.torqueValue.textContent = Math.abs(state.player.vx) > 30 ? "Spooling" : "Centered";
  shell.pressureValue.textContent =
    state.mode === "gameover" ? "Breached" : state.mode === "running" ? `${altitude} m` : "Stand by";
  shell.cycleValue.textContent =
    state.mode === "intro" ? "Idle" : state.mode === "running" ? "Climbing" : "Tripped";
  shell.statusReadout.textContent =
    state.mode === "intro" ? "Awaiting ignition" : state.mode === "running" ? "Run active" : "Thermal shutdown";
  shell.viewportReadout.textContent =
    state.mode === "intro"
      ? "Press A/D or arrow keys to engage"
      : state.mode === "running"
        ? `Camera lock ${altitude} m above floor`
        : "Viewport reset pending";
  shell.milestoneReadout.textContent =
    state.mode === "running" ? `Peak climb ${altitude} m` : "Climb above the heat band";
  shell.gameViewport.dataset.mode = state.mode;
}

function resetRun(mode = "intro") {
  state.mode = mode;
  state.cameraY = 0;
  state.highestY = config.floorY;
  state.heatY = config.heatStart;
  state.lastTime = 0;
  state.keys.left = false;
  state.keys.right = false;
  state.player = createPlayer();
  updateOverlay();
  updateHud();
  draw();
}

function startRun() {
  resetRun("running");
  shell.bootState.textContent = "Run live";
  shell.viewportShell.dataset.boot = "running";
}

function failRun() {
  state.mode = "gameover";
  state.player.vx = 0;
  state.player.vy = 0;
  shell.bootState.textContent = "Overheat";
  updateOverlay();
  updateHud();
  draw();
}

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(config.width * ratio);
  canvas.height = Math.round(config.height * ratio);
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  draw();
}

function handleAction() {
  if (state.mode !== "running") {
    startRun();
    return;
  }

  if (state.player.onGround) {
    state.player.vy = config.jumpVelocity;
    state.player.onGround = false;
    return;
  }

  if (state.player.onWall === "left") {
    state.player.vx = config.wallJumpX;
    state.player.vy = config.wallJumpY;
    return;
  }

  if (state.player.onWall === "right") {
    state.player.vx = -config.wallJumpX;
    state.player.vy = config.wallJumpY;
  }
}

function onKeyChange(event, pressed) {
  const { code } = event;

  if (code === "ArrowLeft" || code === "KeyA") {
    state.keys.left = pressed;
  } else if (code === "ArrowRight" || code === "KeyD") {
    state.keys.right = pressed;
  } else if ((code === "Space" || code === "ArrowUp" || code === "KeyW") && pressed && !event.repeat) {
    event.preventDefault();
    handleAction();
  }

  if (pressed && !event.repeat && (code === "ArrowLeft" || code === "KeyA" || code === "ArrowRight" || code === "KeyD")) {
    handleAction();
  }
}

function update(dt) {
  const player = state.player;
  const input = (state.keys.right ? 1 : 0) - (state.keys.left ? 1 : 0);
  const targetVelocity = input * config.moveSpeed;
  const control = player.onGround ? 1 : config.airControl;

  player.vx += (targetVelocity - player.vx) * Math.min(1, control * 10 * dt);
  player.vy = Math.max(player.vy - config.gravity * dt, -config.maxFallSpeed);
  player.x += player.vx * dt;
  player.y += player.vy * dt;
  player.onGround = false;
  player.onWall = null;

  if (player.y <= config.floorY) {
    player.y = config.floorY;
    player.vy = 0;
    player.onGround = true;
  }

  const minX = config.wallWidth;
  const maxX = config.width - config.wallWidth - config.playerWidth;

  if (player.x <= minX) {
    player.x = minX;
    if (player.vx < 0) {
      player.vx = 0;
    }
    if (!player.onGround) {
      player.onWall = "left";
    }
  } else if (player.x >= maxX) {
    player.x = maxX;
    if (player.vx > 0) {
      player.vx = 0;
    }
    if (!player.onGround) {
      player.onWall = "right";
    }
  }

  if (player.onWall && player.vy < -config.wallSlideSpeed) {
    player.vy = -config.wallSlideSpeed;
  }

  state.highestY = Math.max(state.highestY, player.y);
  state.cameraY = Math.max(0, state.highestY - config.cameraLead);
  state.heatY += (config.heatBaseSpeed + state.cameraY / 220 * config.heatRamp) * dt;

  if (player.y <= state.heatY + 10) {
    failRun();
  }
}

function renderWorldY(worldY) {
  return config.height - (worldY - state.cameraY);
}

function draw() {
  context.clearRect(0, 0, config.width, config.height);

  const shaftTop = renderWorldY(state.cameraY + config.height + 100);
  const shaftBottom = renderWorldY(state.cameraY - 120);

  context.fillStyle = "#081018";
  context.fillRect(config.wallWidth, shaftTop, config.width - config.wallWidth * 2, shaftBottom - shaftTop);

  for (let i = -1; i < 12; i += 1) {
    const rungY = Math.floor(state.cameraY / 80 + i) * 80;
    const screenY = renderWorldY(rungY);
    context.strokeStyle = "rgba(255, 255, 255, 0.04)";
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(config.wallWidth + 10, screenY);
    context.lineTo(config.width - config.wallWidth - 10, screenY);
    context.stroke();
  }

  context.fillStyle = "#131a23";
  context.fillRect(0, 0, config.wallWidth, config.height);
  context.fillRect(config.width - config.wallWidth, 0, config.wallWidth, config.height);

  context.fillStyle = "rgba(116, 208, 255, 0.18)";
  for (let y = -40; y < config.height + 80; y += 110) {
    context.fillRect(12, y, 10, 44);
    context.fillRect(config.width - 22, y + 42, 10, 44);
  }

  const floorY = renderWorldY(config.floorY);
  context.fillStyle = "#202833";
  context.fillRect(config.wallWidth, floorY, config.width - config.wallWidth * 2, config.height - floorY);

  const heatY = renderWorldY(state.heatY);
  const heatGradient = context.createLinearGradient(0, heatY - 120, 0, heatY + 8);
  heatGradient.addColorStop(0, "rgba(255, 98, 56, 0)");
  heatGradient.addColorStop(1, "rgba(255, 98, 56, 0.44)");
  context.fillStyle = heatGradient;
  context.fillRect(config.wallWidth, heatY - 120, config.width - config.wallWidth * 2, 128);
  context.fillStyle = "#ff6238";
  context.fillRect(config.wallWidth, heatY - 4, config.width - config.wallWidth * 2, 6);

  const playerY = renderWorldY(state.player.y + config.playerHeight);
  context.fillStyle = "#d7ecff";
  context.fillRect(state.player.x, playerY, config.playerWidth, config.playerHeight);
  context.fillStyle = "#74d0ff";
  context.fillRect(state.player.x + 6, playerY + 6, config.playerWidth - 12, 8);
}

function tick(timestamp) {
  if (state.mode === "running") {
    if (!state.lastTime) {
      state.lastTime = timestamp;
    }

    const dt = Math.min(0.033, (timestamp - state.lastTime) / 1000);
    state.lastTime = timestamp;
    update(dt);
    updateHud();
    draw();
  }

  window.requestAnimationFrame(tick);
}

function bootShell() {
  shell.bootState.textContent = "Shell ready";
  shell.viewportShell.dataset.boot = "ready";
  resizeCanvas();
  resetRun("intro");
  window.requestAnimationFrame(tick);
}

window.addEventListener("resize", resizeCanvas);
window.addEventListener("keydown", (event) => onKeyChange(event, true));
window.addEventListener("keyup", (event) => onKeyChange(event, false));
shell.gameViewport.addEventListener("pointerdown", () => {
  if (state.mode !== "running") {
    startRun();
  }
});

window.__overcrank = {
  getState() {
    return {
      mode: state.mode,
      cameraY: state.cameraY,
      highestY: state.highestY,
      heatY: state.heatY,
      player: {
        x: state.player.x,
        y: state.player.y,
        vx: state.player.vx,
        vy: state.player.vy,
        onGround: state.player.onGround,
        onWall: state.player.onWall,
      },
    };
  },
  failRun,
  startRun,
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", bootShell, { once: true });
} else {
  bootShell();
}
