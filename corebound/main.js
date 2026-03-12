const WIDTH = 12;
const HEIGHT = 18;
const MAX_PRESSURE = 100;
const MOVE_COST = 1;
const MINE_COST = 4;
const RESOURCE_TYPES = {
  copper: { value: 4, label: "Copper shards" },
  amber: { value: 7, label: "Amber resin" },
  iridium: { value: 12, label: "Iridium cores" },
};

const elements = {
  grid: document.querySelector("#game-grid"),
  message: document.querySelector("#message"),
  depth: document.querySelector("#depth-value"),
  banked: document.querySelector("#banked-value"),
  pressure: document.querySelector("#pressure-value"),
  pressureDetail: document.querySelector("#pressure-detail"),
  pressureFill: document.querySelector("#pressure-fill"),
  cargoTotal: document.querySelector("#cargo-total"),
  cargoCopper: document.querySelector("#cargo-copper"),
  cargoAmber: document.querySelector("#cargo-amber"),
  cargoIridium: document.querySelector("#cargo-iridium"),
  restartButton: document.querySelector("#restart-button"),
  overlay: document.querySelector("#overlay"),
  overlayTitle: document.querySelector("#overlay-title"),
  overlayCopy: document.querySelector("#overlay-copy"),
  overlayRestart: document.querySelector("#overlay-restart"),
};

let bankedCurrency = 0;
let state = createRunState();

function createRunState() {
  return {
    grid: createGrid(),
    player: { x: 5, y: 0 },
    cargo: { copper: 0, amber: 0, iridium: 0 },
    pickups: [],
    pressure: MAX_PRESSURE,
    gameOver: false,
    statusMessage: "Mine downward, then return to the extractor to bank cargo.",
  };
}

function createGrid() {
  const grid = [];
  for (let y = 0; y < HEIGHT; y += 1) {
    const row = [];
    for (let x = 0; x < WIDTH; x += 1) {
      if (y === 0) {
        row.push(x === 5 ? "extractor" : "air");
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

function collectPickup(x, y) {
  const pickup = pickupAt(x, y);
  if (!pickup) {
    return;
  }
  state.pickups = state.pickups.filter((item) => item !== pickup);
  state.cargo[pickup.type] += 1;
  state.statusMessage = `Collected ${RESOURCE_TYPES[pickup.type].label}.`;
}

function totalCargo() {
  return Object.values(state.cargo).reduce((sum, amount) => sum + amount, 0);
}

function spendPressure(amount) {
  state.pressure = Math.max(0, state.pressure - amount);
  if (state.pressure === 0) {
    triggerFailure();
  }
}

function bankCargo() {
  const haul = Object.entries(state.cargo).reduce((sum, [type, amount]) => {
    return sum + amount * RESOURCE_TYPES[type].value;
  }, 0);

  if (haul === 0) {
    state.pressure = MAX_PRESSURE;
    state.statusMessage = "Extractor sealed. Pressure refreshed, but cargo hold is empty.";
    return;
  }

  bankedCurrency += haul;
  state.cargo = { copper: 0, amber: 0, iridium: 0 };
  state.pressure = MAX_PRESSURE;
  state.statusMessage = `Banked ${haul} credits and refreshed hull pressure.`;
}

function triggerFailure() {
  state.gameOver = true;
  state.cargo = { copper: 0, amber: 0, iridium: 0 };
  state.pickups = [];
  elements.overlayTitle.textContent = "Pressure failure";
  elements.overlayCopy.textContent = "Unbanked cargo was lost. Banked currency is still intact for this session.";
  elements.overlay.classList.remove("hidden");
  state.statusMessage = "Pressure collapsed. Restart to launch a fresh run.";
}

function restartRun() {
  state = createRunState();
  elements.overlay.classList.add("hidden");
  render();
}

function movePlayer(dx, dy) {
  if (state.gameOver) {
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
    spendPressure(MINE_COST);
    render();
    return;
  }

  state.player.x = nextX;
  state.player.y = nextY;
  spendPressure(MOVE_COST);
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

      if (state.player.x === x && state.player.y === y) {
        tile.classList.add("tile-player");
      }

      tile.setAttribute("role", "presentation");
      elements.grid.appendChild(tile);
    }
  }

  const depth = state.player.y * 12;
  const pressurePercent = Math.round((state.pressure / MAX_PRESSURE) * 100);
  elements.depth.textContent = `${depth} m`;
  elements.banked.textContent = `${bankedCurrency} cr`;
  elements.pressure.textContent = `${pressurePercent}%`;
  elements.pressureDetail.textContent = `${state.pressure} / ${MAX_PRESSURE}`;
  elements.pressureFill.style.transform = `scaleX(${state.pressure / MAX_PRESSURE})`;
  elements.cargoCopper.textContent = String(state.cargo.copper);
  elements.cargoAmber.textContent = String(state.cargo.amber);
  elements.cargoIridium.textContent = String(state.cargo.iridium);
  elements.cargoTotal.textContent = `${totalCargo()} units`;
  elements.message.textContent = state.statusMessage;
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

render();
