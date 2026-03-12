const WIDTH = 12;
const HEIGHT = 18;
const BASE_PRESSURE = 100;
const BASE_MOVE_COST = 1;
const BASE_MINE_COST = 4;
const SAVE_KEY = "corebound-save-v1";
const SURFACE_X = 5;

const RESOURCE_TYPES = {
  copper: { value: 4, label: "Copper shards" },
  amber: { value: 7, label: "Amber resin" },
  iridium: { value: 12, label: "Iridium cores" },
};

const UPGRADES = {
  servos: {
    label: "Servo Rails",
    description: "Traverse the shaft with less pressure loss on each movement step.",
    baseCost: 14,
    costStep: 10,
    maxLevel: 4,
    effect(level) {
      return `Move cost ${formatNumber(Math.max(0.4, BASE_MOVE_COST - level * 0.15))}`;
    },
  },
  drill: {
    label: "Resonant Drill",
    description: "Cuts ore veins cleaner, reducing the pressure cost of each mining hit.",
    baseCost: 18,
    costStep: 12,
    maxLevel: 4,
    effect(level) {
      return `Mine cost ${formatNumber(Math.max(1.5, BASE_MINE_COST - level * 0.65))}`;
    },
  },
  seals: {
    label: "Pressure Seals",
    description: "Adds reinforced hull buffering so every fresh run starts with more pressure.",
    baseCost: 16,
    costStep: 14,
    maxLevel: 4,
    effect(level) {
      return `${BASE_PRESSURE + level * 20} max pressure`;
    },
  },
};

const elements = {
  grid: document.querySelector("#game-grid"),
  feedbackLayer: document.querySelector("#feedback-layer"),
  message: document.querySelector("#message"),
  depth: document.querySelector("#depth-value"),
  banked: document.querySelector("#banked-value"),
  bankedCard: document.querySelector("#banked-card"),
  pressure: document.querySelector("#pressure-value"),
  pressureDetail: document.querySelector("#pressure-detail"),
  pressureFill: document.querySelector("#pressure-fill"),
  pressureBlock: document.querySelector("#pressure-block"),
  cargoTotal: document.querySelector("#cargo-total"),
  cargoCopper: document.querySelector("#cargo-copper"),
  cargoAmber: document.querySelector("#cargo-amber"),
  cargoIridium: document.querySelector("#cargo-iridium"),
  upgradeHint: document.querySelector("#upgrade-hint"),
  upgradeList: document.querySelector("#upgrade-list"),
  restartButton: document.querySelector("#restart-button"),
  overlay: document.querySelector("#overlay"),
  overlayTitle: document.querySelector("#overlay-title"),
  overlayCopy: document.querySelector("#overlay-copy"),
  overlayRestart: document.querySelector("#overlay-restart"),
  onboardingOverlay: document.querySelector("#onboarding-overlay"),
  onboardingDismiss: document.querySelector("#onboarding-dismiss"),
};

let saveState = loadSave();
let state = createRunState();
let nextFeedbackId = 1;

function defaultSave() {
  return {
    bankedCurrency: 0,
    upgrades: {
      servos: 0,
      drill: 0,
      seals: 0,
    },
    onboardingDismissed: false,
  };
}

function loadSave() {
  const fallback = defaultSave();
  try {
    const raw = window.localStorage.getItem(SAVE_KEY);
    if (!raw) {
      return fallback;
    }
    const parsed = JSON.parse(raw);
    return {
      bankedCurrency: Number.isFinite(parsed?.bankedCurrency) ? parsed.bankedCurrency : fallback.bankedCurrency,
      upgrades: {
        servos: sanitizeLevel(parsed?.upgrades?.servos, UPGRADES.servos.maxLevel),
        drill: sanitizeLevel(parsed?.upgrades?.drill, UPGRADES.drill.maxLevel),
        seals: sanitizeLevel(parsed?.upgrades?.seals, UPGRADES.seals.maxLevel),
      },
      onboardingDismissed: Boolean(parsed?.onboardingDismissed),
    };
  } catch (error) {
    return fallback;
  }
}

function sanitizeLevel(value, maxLevel) {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(maxLevel, Math.floor(value)));
}

function persistSave() {
  window.localStorage.setItem(SAVE_KEY, JSON.stringify(saveState));
}

function formatNumber(value) {
  if (Number.isInteger(value)) {
    return String(value);
  }
  return value.toFixed(1);
}

function currentMaxPressure() {
  return BASE_PRESSURE + saveState.upgrades.seals * 20;
}

function currentMoveCost() {
  return Math.max(0.4, BASE_MOVE_COST - saveState.upgrades.servos * 0.15);
}

function currentMineCost() {
  return Math.max(1.5, BASE_MINE_COST - saveState.upgrades.drill * 0.65);
}

function createRunState() {
  const maxPressure = currentMaxPressure();
  return {
    grid: createGrid(),
    player: { x: SURFACE_X, y: 0 },
    cargo: { copper: 0, amber: 0, iridium: 0 },
    pickups: [],
    pressure: maxPressure,
    maxPressure,
    gameOver: false,
    statusMessage: "Mine downward, then return to the extractor to bank cargo.",
    floatingFeedback: [],
    tileFeedback: [],
  };
}

function createGrid() {
  const grid = [];
  for (let y = 0; y < HEIGHT; y += 1) {
    const row = [];
    for (let x = 0; x < WIDTH; x += 1) {
      if (y === 0) {
        row.push(x === SURFACE_X ? "extractor" : "air");
        continue;
      }

      const depthBias = y / HEIGHT;
      const roll = ((x * 17 + y * 31) % 100) / 100;
      let tile = "rock";
      if (roll < 0.16 + depthBias * 0.18) {
        tile = "copper";
      }
      if (roll < 0.1 + depthBias * 0.14) {
        tile = "amber";
      }
      if (roll < 0.05 + depthBias * 0.12) {
        tile = "iridium";
      }
      row.push(tile);
    }
    grid.push(row);
  }
  return grid;
}

function getTile(x, y) {
  if (x < 0 || x >= WIDTH || y < 0 || y >= HEIGHT) {
    return "void";
  }
  return state.grid[y][x];
}

function setTile(x, y, tile) {
  state.grid[y][x] = tile;
}

function pickupAt(x, y) {
  return state.pickups.find((pickup) => pickup.x === x && pickup.y === y) || null;
}

function tileFeedbackAt(x, y) {
  return state.tileFeedback.find((feedback) => feedback.x === x && feedback.y === y) || null;
}

function removeFeedback(collectionName, id) {
  state[collectionName] = state[collectionName].filter((entry) => entry.id !== id);
  render();
}

function addFloatingFeedback(text, x, y, kind) {
  const id = nextFeedbackId;
  nextFeedbackId += 1;
  state.floatingFeedback.push({ id, text, x, y, kind });
  render();
  window.setTimeout(() => removeFeedback("floatingFeedback", id), 900);
}

function addTileFeedback(x, y, kind) {
  const id = nextFeedbackId;
  nextFeedbackId += 1;
  state.tileFeedback.push({ id, x, y, kind });
  render();
  window.setTimeout(() => removeFeedback("tileFeedback", id), 420);
}

function pulseElement(element, className, duration = 650) {
  element.classList.remove(className);
  void element.offsetWidth;
  element.classList.add(className);
  window.setTimeout(() => {
    element.classList.remove(className);
  }, duration);
}

function totalCargo() {
  return Object.values(state.cargo).reduce((sum, amount) => sum + amount, 0);
}

function bankedCurrency() {
  return saveState.bankedCurrency;
}

function betweenRuns() {
  return state.gameOver || (state.player.x === SURFACE_X && state.player.y === 0 && totalCargo() === 0);
}

function spendPressure(amount, reason, focusX = state.player.x, focusY = state.player.y) {
  state.pressure = Math.max(0, state.pressure - amount);
  if (reason === "mine" || reason === "damage") {
    pulseElement(elements.pressureBlock, "is-damaged", 450);
    addFloatingFeedback(`-${formatNumber(amount)} pressure`, focusX + 0.5, focusY + 0.45, "damage");
  }
  if (state.pressure === 0) {
    triggerFailure();
  }
}

function collectPickup(x, y) {
  const pickup = pickupAt(x, y);
  if (!pickup) {
    return;
  }
  state.pickups = state.pickups.filter((item) => item !== pickup);
  state.cargo[pickup.type] += 1;
  state.statusMessage = `Collected ${RESOURCE_TYPES[pickup.type].label}.`;
  addTileFeedback(x, y, "pickup");
  addFloatingFeedback(`+1 ${pickup.type}`, x + 0.5, y + 0.5, "pickup");
}

function bankCargo() {
  const haul = Object.entries(state.cargo).reduce((sum, [type, amount]) => {
    return sum + amount * RESOURCE_TYPES[type].value;
  }, 0);

  state.cargo = { copper: 0, amber: 0, iridium: 0 };
  state.pressure = state.maxPressure;

  if (haul === 0) {
    state.statusMessage = "Extractor sealed. Pressure refreshed, but cargo hold is empty.";
    addTileFeedback(SURFACE_X, 0, "bank");
    render();
    return;
  }

  saveState.bankedCurrency += haul;
  persistSave();
  state.statusMessage = `Banked ${haul} credits and refreshed hull pressure.`;
  addTileFeedback(SURFACE_X, 0, "bank");
  addFloatingFeedback(`+${haul} cr`, SURFACE_X + 0.5, 0.55, "bank");
  pulseElement(elements.bankedCard, "is-banked");
}

function triggerFailure() {
  state.gameOver = true;
  state.cargo = { copper: 0, amber: 0, iridium: 0 };
  state.pickups = [];
  elements.overlayTitle.textContent = "Pressure failure";
  elements.overlayCopy.textContent = "Unbanked cargo was lost. Banked currency and purchased upgrades persist.";
  elements.overlay.classList.remove("hidden");
  state.statusMessage = "Pressure collapsed. Restart to launch a fresh run.";
}

function restartRun() {
  state = createRunState();
  elements.overlay.classList.add("hidden");
  render();
}

function upgradeCost(upgradeId) {
  const upgrade = UPGRADES[upgradeId];
  const level = saveState.upgrades[upgradeId];
  return upgrade.baseCost + level * upgrade.costStep;
}

function tryPurchaseUpgrade(upgradeId) {
  if (!betweenRuns()) {
    state.statusMessage = "Upgrades can only be installed at the extractor between runs.";
    render();
    return;
  }

  const upgrade = UPGRADES[upgradeId];
  const level = saveState.upgrades[upgradeId];
  if (level >= upgrade.maxLevel) {
    state.statusMessage = `${upgrade.label} is already maxed out.`;
    render();
    return;
  }

  const cost = upgradeCost(upgradeId);
  if (saveState.bankedCurrency < cost) {
    state.statusMessage = `Need ${cost} credits for ${upgrade.label}.`;
    render();
    return;
  }

  saveState.bankedCurrency -= cost;
  saveState.upgrades[upgradeId] += 1;
  persistSave();
  state.maxPressure = currentMaxPressure();
  if (state.player.x === SURFACE_X && state.player.y === 0) {
    state.pressure = state.maxPressure;
  } else {
    state.pressure = Math.min(state.pressure, state.maxPressure);
  }
  state.statusMessage = `${upgrade.label} upgraded to level ${saveState.upgrades[upgradeId]}.`;
  addFloatingFeedback(`-${cost} cr`, SURFACE_X + 0.5, 0.55, "damage");
  pulseElement(elements.bankedCard, "is-banked");
  render();
}

function dismissOnboarding() {
  saveState.onboardingDismissed = true;
  persistSave();
  elements.onboardingOverlay.classList.add("hidden");
}

function movePlayer(dx, dy) {
  if (state.gameOver || !elements.onboardingOverlay.classList.contains("hidden")) {
    return;
  }

  const nextX = state.player.x + dx;
  const nextY = state.player.y + dy;
  const tile = getTile(nextX, nextY);
  if (tile === "void") {
    state.statusMessage = "The rig cannot move beyond the mine boundary.";
    render();
    return;
  }

  if (tile === "rock" || RESOURCE_TYPES[tile]) {
    if (tile !== "rock") {
      state.pickups.push({ x: nextX, y: nextY, type: tile });
      state.statusMessage = `${RESOURCE_TYPES[tile].label} exposed. Move onto the drop to collect it.`;
    } else {
      state.statusMessage = "Rock wall broken open.";
    }
    setTile(nextX, nextY, "air");
    addTileFeedback(nextX, nextY, "mine");
    addFloatingFeedback("Crack", nextX + 0.5, nextY + 0.5, "damage");
    spendPressure(currentMineCost(), "mine", nextX, nextY);
    render();
    return;
  }

  state.player.x = nextX;
  state.player.y = nextY;
  spendPressure(currentMoveCost(), "move");
  if (state.gameOver) {
    render();
    return;
  }
  collectPickup(nextX, nextY);
  if (getTile(nextX, nextY) === "extractor") {
    bankCargo();
  }
  render();
}

function renderUpgradePanel() {
  elements.upgradeList.innerHTML = "";
  const canBuy = betweenRuns();
  elements.upgradeHint.textContent = canBuy
    ? "Available now at the extractor."
    : "Return to the extractor with an empty hold to install upgrades.";

  Object.entries(UPGRADES).forEach(([upgradeId, upgrade]) => {
    const level = saveState.upgrades[upgradeId];
    const cost = upgradeCost(upgradeId);
    const button = document.createElement("button");
    button.className = "button secondary";
    button.type = "button";
    button.textContent = level >= upgrade.maxLevel ? "Maxed" : `Buy ${cost} cr`;
    button.disabled = !canBuy || level >= upgrade.maxLevel || saveState.bankedCurrency < cost;
    button.addEventListener("click", () => tryPurchaseUpgrade(upgradeId));

    const card = document.createElement("article");
    card.className = "upgrade-card";
    card.innerHTML = `
      <div class="upgrade-top">
        <div>
          <h3>${upgrade.label}</h3>
          <p class="upgrade-copy">${upgrade.description}</p>
        </div>
        <strong>Lv ${level}/${upgrade.maxLevel}</strong>
      </div>
      <div class="upgrade-meta">
        <span>${upgrade.effect(level + 1 > upgrade.maxLevel ? level : level + 1)}</span>
        <span>${level >= upgrade.maxLevel ? "Installed" : `Next cost ${cost} cr`}</span>
      </div>
    `;
    card.appendChild(button);
    elements.upgradeList.appendChild(card);
  });
}

function renderFeedback() {
  elements.feedbackLayer.innerHTML = "";
  state.floatingFeedback.forEach((feedback) => {
    const item = document.createElement("div");
    item.className = `floating-feedback ${feedback.kind}`;
    item.textContent = feedback.text;
    item.style.setProperty("--grid-x", String(feedback.x / WIDTH));
    item.style.setProperty("--grid-y", String(feedback.y / HEIGHT));
    elements.feedbackLayer.appendChild(item);
  });
}

function render() {
  elements.grid.innerHTML = "";
  for (let y = 0; y < HEIGHT; y += 1) {
    for (let x = 0; x < WIDTH; x += 1) {
      const tile = document.createElement("div");
      const baseTile = getTile(x, y);
      tile.className = `tile tile-${baseTile}`;

      const pickup = pickupAt(x, y);
      if (pickup) {
        tile.classList.add("tile-pickup", `pickup-${pickup.type}`);
      }

      const feedback = tileFeedbackAt(x, y);
      if (feedback) {
        tile.classList.add(`tile-feedback-${feedback.kind}`);
      }

      if (state.player.x === x && state.player.y === y) {
        tile.classList.add("tile-player");
      }

      tile.setAttribute("role", "presentation");
      elements.grid.appendChild(tile);
    }
  }

  const depth = state.player.y * 12;
  const pressurePercent = Math.round((state.pressure / state.maxPressure) * 100);
  elements.depth.textContent = `${depth} m`;
  elements.banked.textContent = `${bankedCurrency()} cr`;
  elements.pressure.textContent = `${pressurePercent}%`;
  elements.pressureDetail.textContent = `${formatNumber(state.pressure)} / ${state.maxPressure}`;
  elements.pressureFill.style.transform = `scaleX(${state.pressure / state.maxPressure})`;
  elements.cargoCopper.textContent = String(state.cargo.copper);
  elements.cargoAmber.textContent = String(state.cargo.amber);
  elements.cargoIridium.textContent = String(state.cargo.iridium);
  elements.cargoTotal.textContent = `${totalCargo()} units`;
  elements.message.textContent = state.statusMessage;
  elements.message.classList.toggle("is-emphasis", state.statusMessage.includes("Banked") || state.statusMessage.includes("Collected"));
  renderUpgradePanel();
  renderFeedback();
}

function handleKeydown(event) {
  const key = event.key.toLowerCase();
  const directions = {
    arrowup: [0, -1],
    w: [0, -1],
    arrowdown: [0, 1],
    s: [0, 1],
    arrowleft: [-1, 0],
    a: [-1, 0],
    arrowright: [1, 0],
    d: [1, 0],
  };
  const direction = directions[key];
  if (!direction) {
    return;
  }
  event.preventDefault();
  movePlayer(direction[0], direction[1]);
}

document.addEventListener("keydown", handleKeydown);
elements.restartButton.addEventListener("click", restartRun);
elements.overlayRestart.addEventListener("click", restartRun);
elements.onboardingDismiss.addEventListener("click", dismissOnboarding);

if (!saveState.onboardingDismissed) {
  elements.onboardingOverlay.classList.remove("hidden");
}

render();
