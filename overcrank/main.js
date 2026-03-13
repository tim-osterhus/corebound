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
  platformHeight: 12,
  segmentHeight: 180,
  generateAhead: 980,
  cleanupBelow: 320,
  coolantPush: 120,
  coolantSlowDuration: 3.6,
  ventTelegraph: 0.9,
  ventActive: 1.1,
};

const canvas = shell.gameCanvas;
const context = canvas.getContext("2d");

function createPlayer() {
  return {
    x: config.width * 0.5 - config.playerWidth * 0.5,
    y: config.floorY,
    vx: 0,
    vy: 0,
    onGround: true,
    onWall: null,
    platformId: null,
  };
}

const state = {
  mode: "intro",
  cameraY: 0,
  highestY: config.floorY,
  heatY: config.heatStart,
  lastTime: 0,
  nextEntityId: 1,
  segmentIndex: 0,
  generatedToY: config.floorY,
  keys: {
    left: false,
    right: false,
  },
  coolantSlowTimer: 0,
  coolantPulse: 0,
  platforms: [],
  vents: [],
  pickups: [],
  player: createPlayer(),
};

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
      "Press Space, W, Up, A, D, or the arrow keys to start. Ride lifts, avoid steam bursts, grab coolant, and stay above the heat line."
    );
    return;
  }

  setOverlay(
    "Run failed",
    "Heat breach",
    "The shaft flashed over. Press any movement key or jump key to restart with fresh hazards, lifts, and coolant pickups."
  );
}

function updateHud() {
  const altitude = Math.max(0, Math.round((state.highestY - config.floorY) / 10));
  const heatGap = Math.max(0, state.player.y - state.heatY);
  const heatPercent = Math.max(0, Math.min(100, Math.round(100 - heatGap / 4.8)));
  const coolantSeconds = Math.max(0, state.coolantSlowTimer);

  shell.statusMessage.textContent =
    state.mode === "intro"
      ? "Stand by. One key press starts the climb."
      : state.mode === "running"
        ? coolantSeconds > 0
          ? `Coolant surge live for ${coolantSeconds.toFixed(1)}s. The heat line is backing off.`
          : "Climb clean, read steam telegraphs, and keep the heat below your boots."
        : "Heat contact detected. Any movement or jump key restarts.";
  shell.heatValue.textContent = `${heatPercent}%`;
  shell.torqueValue.textContent =
    state.mode === "running"
      ? state.player.platformId && getPlatformById(state.player.platformId)?.type === "moving"
        ? "Lift engaged"
        : Math.abs(state.player.vx) > 30
          ? "Spooling"
          : "Centered"
      : "Stand by";
  shell.pressureValue.textContent =
    state.mode === "gameover" ? "Breached" : state.mode === "running" ? `${altitude} m` : "Stand by";
  shell.cycleValue.textContent =
    state.mode === "running"
      ? coolantSeconds > 0
        ? `Coolant ${coolantSeconds.toFixed(1)}s`
        : `${state.vents.filter((vent) => isVentActive(vent)).length} vents hot`
      : state.mode === "intro"
        ? "Idle"
        : "Tripped";
  shell.statusReadout.textContent =
    state.mode === "intro"
      ? "Awaiting ignition"
      : state.mode === "running"
        ? `${state.platforms.filter((platform) => platform.active !== false).length} supports live`
        : "Thermal shutdown";
  shell.viewportReadout.textContent =
    state.mode === "intro"
      ? "Press A/D or arrow keys to engage"
      : state.mode === "running"
        ? `Camera lock ${altitude} m above floor`
        : "Viewport reset pending";
  shell.milestoneReadout.textContent =
    state.mode === "running"
      ? cooldownReadout(altitude)
      : "Ride lifts, dodge steam, and chase coolant";
  shell.gameViewport.dataset.mode = state.mode;
}

function cooldownReadout(altitude) {
  if (state.coolantSlowTimer > 0) {
    return `Coolant shield holding for ${state.coolantSlowTimer.toFixed(1)}s`;
  }

  const nextPickup = state.pickups.find((pickup) => !pickup.collected && pickup.y > state.player.y);
  if (nextPickup) {
    return `Next coolant cache at ${Math.round((nextPickup.y - config.floorY) / 10)} m`;
  }

  return `Peak climb ${altitude} m`;
}

function nextId() {
  const id = state.nextEntityId;
  state.nextEntityId += 1;
  return id;
}

function getPlatformById(id) {
  return state.platforms.find((platform) => platform.id === id) || null;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function createPlatform(y, type, lane, width, extra = {}) {
  const minX = config.wallWidth + 6;
  const shaftWidth = config.width - config.wallWidth * 2 - 12;
  const x = minX + lane * shaftWidth;
  return {
    id: nextId(),
    type,
    x,
    y,
    width,
    height: config.platformHeight,
    active: true,
    crumbleTimer: extra.crumbleTimer ?? 0,
    movingRange: extra.movingRange ?? 0,
    movingSpeed: extra.movingSpeed ?? 0,
    movingPhase: extra.movingPhase ?? 0,
    baseX: extra.baseX ?? x,
    deltaX: 0,
    previousX: x,
  };
}

function createVent(y, side, extra = {}) {
  const width = 72;
  const x =
    side === "left"
      ? config.wallWidth + 6
      : config.width - config.wallWidth - width - 6;

  return {
    id: nextId(),
    x,
    y,
    width,
    plumeHeight: extra.plumeHeight ?? 108,
    cycleOffset: extra.cycleOffset ?? 0,
  };
}

function createPickup(y, lane, extra = {}) {
  const shaftWidth = config.width - config.wallWidth * 2 - 56;
  return {
    id: nextId(),
    x: config.wallWidth + 28 + lane * shaftWidth,
    y,
    radius: 10,
    collected: false,
    bobPhase: extra.bobPhase ?? 0,
  };
}

function addSegment(baseY, index) {
  const segmentBase = baseY;
  const pattern = index % 4;
  const laneA = (index % 3) * 0.18;
  const laneB = ((index + 1) % 3) * 0.2 + 0.36;
  const laneC = 0.68 - (index % 2) * 0.08;

  if (pattern === 0) {
    state.platforms.push(createPlatform(segmentBase + 46, "stable", laneA, 96));
    state.platforms.push(createPlatform(segmentBase + 104, "crumble", laneB, 80, { crumbleTimer: 0.55 }));
    state.platforms.push(createPlatform(segmentBase + 154, "stable", laneC, 92));
    state.vents.push(createVent(segmentBase + 42, index % 2 === 0 ? "right" : "left", { plumeHeight: 96, cycleOffset: 0.8 }));
    state.pickups.push(createPickup(segmentBase + 142, 0.46, { bobPhase: index * 0.7 }));
    return;
  }

  if (pattern === 1) {
    state.platforms.push(createPlatform(segmentBase + 40, "stable", laneC, 90));
    state.platforms.push(
      createPlatform(segmentBase + 96, "moving", 0.28, 84, {
        movingRange: 96,
        movingSpeed: 1.3,
        movingPhase: index * 0.9,
        baseX: config.wallWidth + 26,
      })
    );
    state.platforms.push(createPlatform(segmentBase + 152, "stable", 0.58, 88));
    state.pickups.push(createPickup(segmentBase + 120, 0.16, { bobPhase: index * 0.5 }));
    return;
  }

  if (pattern === 2) {
    state.platforms.push(createPlatform(segmentBase + 48, "crumble", 0.12, 84, { crumbleTimer: 0.42 }));
    state.platforms.push(createPlatform(segmentBase + 98, "stable", 0.52, 94));
    state.platforms.push(createPlatform(segmentBase + 150, "moving", 0.18, 82, {
      movingRange: 82,
      movingSpeed: 1.55,
      movingPhase: 1.4 + index * 0.4,
      baseX: config.wallWidth + 30,
    }));
    state.vents.push(createVent(segmentBase + 94, "right", { plumeHeight: 118, cycleOffset: 1.6 }));
    return;
  }

  state.platforms.push(createPlatform(segmentBase + 44, "stable", 0.62, 98));
  state.platforms.push(createPlatform(segmentBase + 102, "stable", 0.2, 90));
  state.platforms.push(createPlatform(segmentBase + 150, "crumble", 0.5, 76, { crumbleTimer: 0.5 }));
  state.vents.push(createVent(segmentBase + 40, "left", { plumeHeight: 86, cycleOffset: 0.2 }));
  state.pickups.push(createPickup(segmentBase + 162, 0.7, { bobPhase: index }));
}

function ensureContent(targetY) {
  while (state.generatedToY < targetY) {
    addSegment(state.generatedToY, state.segmentIndex);
    state.generatedToY += config.segmentHeight;
    state.segmentIndex += 1;
  }
}

function isVentActive(vent) {
  const cycle = config.ventTelegraph + config.ventActive + 1.4;
  const phase = (performance.now() / 1000 + vent.cycleOffset) % cycle;
  return phase >= config.ventTelegraph && phase < config.ventTelegraph + config.ventActive;
}

function isVentTelegraphing(vent) {
  const cycle = config.ventTelegraph + config.ventActive + 1.4;
  const phase = (performance.now() / 1000 + vent.cycleOffset) % cycle;
  return phase < config.ventTelegraph;
}

function resetRun(mode = "intro") {
  state.mode = mode;
  state.cameraY = 0;
  state.highestY = config.floorY;
  state.heatY = config.heatStart;
  state.lastTime = 0;
  state.nextEntityId = 1;
  state.segmentIndex = 0;
  state.generatedToY = config.floorY;
  state.coolantSlowTimer = 0;
  state.coolantPulse = 0;
  state.keys.left = false;
  state.keys.right = false;
  state.platforms = [];
  state.vents = [];
  state.pickups = [];
  state.player = createPlayer();
  ensureContent(config.height + config.generateAhead);
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
    state.player.platformId = null;
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

function updateMovingPlatforms(dt) {
  for (const platform of state.platforms) {
    if (platform.type !== "moving" || platform.active === false) {
      continue;
    }

    platform.previousX = platform.x;
    platform.movingPhase += dt * platform.movingSpeed;
    platform.x = platform.baseX + Math.sin(platform.movingPhase) * platform.movingRange;
    platform.x = clamp(platform.x, config.wallWidth + 6, config.width - config.wallWidth - platform.width - 6);
    platform.deltaX = platform.x - platform.previousX;
  }
}

function applyPlatformCarry() {
  const platform = getPlatformById(state.player.platformId);
  if (!platform || platform.type !== "moving" || platform.active === false) {
    return;
  }

  state.player.x += platform.deltaX;
}

function resolvePlatformLanding(prevY) {
  const player = state.player;
  if (player.vy > 0) {
    return;
  }

  for (const platform of state.platforms) {
    if (platform.active === false) {
      continue;
    }

    const topY = platform.y;
    const overlapX =
      player.x + config.playerWidth > platform.x + 4 && player.x < platform.x + platform.width - 4;

    if (!overlapX) {
      continue;
    }

    if (prevY >= topY && player.y <= topY) {
      player.y = topY;
      player.vy = 0;
      player.onGround = true;
      player.platformId = platform.id;

      if (platform.type === "crumble" && platform.crumbleTimer > 0) {
        platform.crumbleTimer -= 1 / 60;
      }

      return;
    }
  }
}

function updatePlatforms(dt) {
  for (const platform of state.platforms) {
    if (platform.type === "crumble" && platform.active !== false && platform.crumbleTimer <= 0) {
      platform.active = false;
      if (state.player.platformId === platform.id) {
        state.player.platformId = null;
        state.player.onGround = false;
      }
    }

    if (platform.type === "crumble" && platform.active !== false && state.player.platformId === platform.id) {
      platform.crumbleTimer -= dt;
    }
  }
}

function updateHazardsAndPickups(dt) {
  const playerLeft = state.player.x;
  const playerRight = state.player.x + config.playerWidth;
  const playerBottom = state.player.y;
  const playerTop = state.player.y + config.playerHeight;

  for (const vent of state.vents) {
    if (!isVentActive(vent)) {
      continue;
    }

    const plumeTop = vent.y + vent.plumeHeight;
    const overlapX = playerRight > vent.x && playerLeft < vent.x + vent.width;
    const overlapY = playerTop > vent.y && playerBottom < plumeTop;
    if (overlapX && overlapY) {
      failRun();
      return;
    }
  }

  for (const pickup of state.pickups) {
    if (pickup.collected) {
      continue;
    }

    const dx = state.player.x + config.playerWidth * 0.5 - pickup.x;
    const dy = state.player.y + config.playerHeight * 0.5 - pickup.y;
    if (dx * dx + dy * dy <= (pickup.radius + 14) * (pickup.radius + 14)) {
      pickup.collected = true;
      state.heatY -= config.coolantPush;
      state.coolantSlowTimer = Math.max(state.coolantSlowTimer, config.coolantSlowDuration);
      state.coolantPulse = 0.85;
    }
  }

  state.coolantSlowTimer = Math.max(0, state.coolantSlowTimer - dt);
  state.coolantPulse = Math.max(0, state.coolantPulse - dt);
}

function cleanupContent() {
  const threshold = state.cameraY - config.cleanupBelow;
  state.platforms = state.platforms.filter(
    (platform) => platform.y > threshold || platform.id === state.player.platformId
  );
  state.vents = state.vents.filter((vent) => vent.y + vent.plumeHeight > threshold);
  state.pickups = state.pickups.filter((pickup) => pickup.collected || pickup.y > threshold);
}

function update(dt) {
  const player = state.player;
  const prevY = player.y;
  const input = (state.keys.right ? 1 : 0) - (state.keys.left ? 1 : 0);
  const targetVelocity = input * config.moveSpeed;
  const control = player.onGround ? 1 : config.airControl;

  updateMovingPlatforms(dt);
  if (player.onGround) {
    applyPlatformCarry();
  }

  player.vx += (targetVelocity - player.vx) * Math.min(1, control * 10 * dt);
  player.vy = Math.max(player.vy - config.gravity * dt, -config.maxFallSpeed);
  player.x += player.vx * dt;
  player.y += player.vy * dt;
  player.onGround = false;
  player.onWall = null;
  player.platformId = null;

  if (player.y <= config.floorY) {
    player.y = config.floorY;
    player.vy = 0;
    player.onGround = true;
  }

  resolvePlatformLanding(prevY);

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

  updatePlatforms(dt);
  updateHazardsAndPickups(dt);
  if (state.mode !== "running") {
    return;
  }

  state.highestY = Math.max(state.highestY, player.y);
  state.cameraY = Math.max(0, state.highestY - config.cameraLead);
  ensureContent(state.highestY + config.generateAhead);
  cleanupContent();

  const heatSpeedMultiplier = state.coolantSlowTimer > 0 ? 0.42 : 1;
  state.heatY += (config.heatBaseSpeed + (state.cameraY / 220) * config.heatRamp) * dt * heatSpeedMultiplier;

  if (player.y <= state.heatY + 10) {
    failRun();
  }
}

function renderWorldY(worldY) {
  return config.height - (worldY - state.cameraY);
}

function drawPlatform(platform) {
  if (platform.active === false) {
    return;
  }

  const screenY = renderWorldY(platform.y);
  let fill = "#596b78";
  let stroke = "rgba(255, 255, 255, 0.08)";

  if (platform.type === "crumble") {
    const urgency = clamp(platform.crumbleTimer / 0.55, 0, 1);
    fill = `rgba(${Math.round(214 + (1 - urgency) * 22)}, ${Math.round(158 - (1 - urgency) * 60)}, 105, 0.95)`;
    stroke = "rgba(255, 220, 184, 0.26)";
  } else if (platform.type === "moving") {
    fill = "#74d0ff";
    stroke = "rgba(198, 239, 255, 0.32)";
  }

  context.fillStyle = fill;
  context.fillRect(platform.x, screenY - platform.height, platform.width, platform.height);
  context.strokeStyle = stroke;
  context.lineWidth = 2;
  context.strokeRect(platform.x, screenY - platform.height, platform.width, platform.height);

  if (platform.type === "moving") {
    context.strokeStyle = "rgba(116, 208, 255, 0.22)";
    context.setLineDash([6, 6]);
    context.beginPath();
    context.moveTo(platform.baseX, screenY - platform.height * 0.5);
    context.lineTo(platform.baseX + platform.movingRange, screenY - platform.height * 0.5);
    context.stroke();
    context.setLineDash([]);
  }
}

function drawVent(vent) {
  const baseY = renderWorldY(vent.y);
  const telegraph = isVentTelegraphing(vent);
  const active = isVentActive(vent);

  context.fillStyle = telegraph ? "rgba(255, 190, 120, 0.7)" : "rgba(255, 98, 56, 0.5)";
  context.fillRect(vent.x, baseY - 8, vent.width, 8);

  if (!telegraph && !active) {
    return;
  }

  const plumeTop = renderWorldY(vent.y + vent.plumeHeight);
  const gradient = context.createLinearGradient(0, plumeTop, 0, baseY);
  if (active) {
    gradient.addColorStop(0, "rgba(255, 190, 120, 0.04)");
    gradient.addColorStop(0.45, "rgba(255, 154, 92, 0.22)");
    gradient.addColorStop(1, "rgba(255, 98, 56, 0.72)");
  } else {
    gradient.addColorStop(0, "rgba(255, 230, 180, 0.02)");
    gradient.addColorStop(1, "rgba(255, 214, 163, 0.28)");
  }

  context.fillStyle = gradient;
  context.fillRect(vent.x, plumeTop, vent.width, baseY - plumeTop);
}

function drawPickup(pickup, time) {
  if (pickup.collected) {
    return;
  }

  const bob = Math.sin(time * 2.8 + pickup.bobPhase) * 4;
  const screenY = renderWorldY(pickup.y + bob);
  context.fillStyle = "rgba(116, 208, 255, 0.18)";
  context.beginPath();
  context.arc(pickup.x, screenY, pickup.radius + 6, 0, Math.PI * 2);
  context.fill();

  context.fillStyle = "#8fe7ff";
  context.beginPath();
  context.arc(pickup.x, screenY, pickup.radius, 0, Math.PI * 2);
  context.fill();

  context.strokeStyle = "rgba(255, 255, 255, 0.45)";
  context.lineWidth = 2;
  context.beginPath();
  context.moveTo(pickup.x, screenY - 6);
  context.lineTo(pickup.x, screenY + 6);
  context.moveTo(pickup.x - 6, screenY);
  context.lineTo(pickup.x + 6, screenY);
  context.stroke();
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

  const time = performance.now() / 1000;
  for (const vent of state.vents) {
    drawVent(vent);
  }

  for (const platform of state.platforms) {
    drawPlatform(platform);
  }

  for (const pickup of state.pickups) {
    drawPickup(pickup, time);
  }

  const heatY = renderWorldY(state.heatY);
  const heatGradient = context.createLinearGradient(0, heatY - 140, 0, heatY + 8);
  heatGradient.addColorStop(0, "rgba(255, 98, 56, 0)");
  heatGradient.addColorStop(1, state.coolantPulse > 0 ? "rgba(120, 216, 255, 0.26)" : "rgba(255, 98, 56, 0.44)");
  context.fillStyle = heatGradient;
  context.fillRect(config.wallWidth, heatY - 140, config.width - config.wallWidth * 2, 148);
  context.fillStyle = state.coolantPulse > 0 ? "#8fe7ff" : "#ff6238";
  context.fillRect(config.wallWidth, heatY - 4, config.width - config.wallWidth * 2, 6);

  const playerY = renderWorldY(state.player.y + config.playerHeight);
  context.fillStyle = "#d7ecff";
  context.fillRect(state.player.x, playerY, config.playerWidth, config.playerHeight);
  context.fillStyle = state.coolantSlowTimer > 0 ? "#8fe7ff" : "#74d0ff";
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
      coolantSlowTimer: state.coolantSlowTimer,
      platformCounts: state.platforms.reduce((counts, platform) => {
        const key = platform.type;
        counts[key] = (counts[key] || 0) + (platform.active === false ? 0 : 1);
        return counts;
      }, {}),
      ventCount: state.vents.length,
      pickupCount: state.pickups.filter((pickup) => !pickup.collected).length,
      player: {
        x: state.player.x,
        y: state.player.y,
        vx: state.player.vx,
        vy: state.player.vy,
        onGround: state.player.onGround,
        onWall: state.player.onWall,
        platformId: state.player.platformId,
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
