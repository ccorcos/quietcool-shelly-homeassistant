class QuietCoolHouseFanCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("quietcool-house-fan-card-editor");
  }

  static getStubConfig() {
    return {
      entity: "fan.house_fan",
      duration_entity: "number.house_fan_run_hours",
      timed_run_entity: "switch.house_fan_timed_run",
      remaining_entity: "sensor.house_fan_timer_remaining",
      finishes_at_entity: "sensor.house_fan_timer_finishes_at",
      name: "House Fan",
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error("quietcool-house-fan-card requires an entity");
    }

    this.config = {
      duration_entity: "number.house_fan_run_hours",
      timed_run_entity: "switch.house_fan_timed_run",
      remaining_entity: "sensor.house_fan_timer_remaining",
      finishes_at_entity: "sensor.house_fan_timer_finishes_at",
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 3;
  }

  render() {
    if (!this.config || !this._hass) return;

    const fan = this._hass.states[this.config.entity];
    const duration = this._hass.states[this.config.duration_entity];
    const timedRun = this._hass.states[this.config.timed_run_entity];
    const remaining = this._hass.states[this.config.remaining_entity];
    const finishesAt = this._hass.states[this.config.finishes_at_entity];

    if (!fan) {
      this.innerHTML = this.wrap(`
        <div class="error">Entity not found: ${this.escape(this.config.entity)}</div>
      `);
      return;
    }

    const fanOn = fan.state === "on";
    const timerActive = timedRun?.state === "on";
    const preset = fan.attributes?.preset_mode || "Low";
    const durationValue = duration?.state && duration.state !== "unknown" ? Number(duration.state) : undefined;
    const remainingValue = remaining?.state;
    const finishValue = this.formatFinishTime(finishesAt?.state);

    const title = this.config.name || fan.attributes?.friendly_name || "House Fan";
    const status = timerActive ? "Timed" : fanOn ? "On" : "Off";
    const statusClass = timerActive ? "timed" : fanOn ? "on" : "off";
    const primaryValue = timerActive
      ? `${this.formatRemaining(remainingValue)}${finishValue ? `, ends ${finishValue}` : ""}`
      : fanOn
        ? "∞"
        : this.durationInput(durationValue);
    const primaryLabel = timerActive || fanOn ? "Remaining" : "Duration";
    const actionLabel = fanOn || timerActive ? "Stop" : "Start";
    const actionClass = fanOn || timerActive ? "stop" : "start";

    this.innerHTML = this.wrap(`
      <div class="header">
        <div>
          <div class="name">${this.escape(title)}</div>
        </div>
        <div class="status ${statusClass}">${status}</div>
      </div>

      <div class="speed-row" role="group" aria-label="Fan speed">
        ${["High", "Medium", "Low"].map((mode) => `
          <button class="speed ${preset === mode ? "selected" : ""}" data-preset="${mode}">
            ${mode[0]}
          </button>
        `).join("")}
      </div>

      <div class="timer-row">
        <div>
          <div class="label">${primaryLabel}</div>
          <div class="value">${primaryValue}</div>
        </div>
        <button class="action ${actionClass}" data-action="${actionClass}">${actionLabel}</button>
      </div>
    `);

    this.bindEvents();
  }

  wrap(content) {
    return `
      <ha-card>
        <style>
          :host {
            display: block;
          }
          .card {
            padding: 16px;
          }
          .header,
          .timer-row {
            align-items: center;
            display: flex;
            gap: 12px;
            justify-content: space-between;
          }
          .name {
            font-size: 1.15rem;
            font-weight: 600;
            line-height: 1.2;
          }
          .subtle {
            color: var(--secondary-text-color);
            font-size: 0.8rem;
            margin-top: 2px;
          }
          .status {
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            padding: 4px 10px;
          }
          .status.off {
            background: var(--divider-color);
            color: var(--secondary-text-color);
          }
          .status.on {
            background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.16);
            color: var(--primary-color);
          }
          .status.timed {
            background: rgba(var(--rgb-accent-color, 255, 152, 0), 0.18);
            color: var(--accent-color);
          }
          .speed-row {
            display: grid;
            gap: 8px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin: 16px 0;
          }
          button {
            border: 0;
            border-radius: 12px;
            cursor: pointer;
            font: inherit;
            min-height: 42px;
          }
          button:disabled {
            cursor: not-allowed;
            opacity: 0.5;
          }
          .speed {
            background: var(--secondary-background-color);
            color: var(--primary-text-color);
            font-size: 1.05rem;
            font-weight: 700;
          }
          .speed.selected {
            background: var(--primary-color);
            color: var(--text-primary-color, white);
          }
          .label {
            color: var(--secondary-text-color);
            font-size: 0.75rem;
            letter-spacing: 0.04em;
            text-transform: uppercase;
          }
          .value {
            align-items: baseline;
            display: flex;
            gap: 6px;
            min-height: 36px;
            padding-top: 2px;
          }
          .duration-input {
            background: var(--secondary-background-color);
            border: 1px solid var(--divider-color);
            border-radius: 10px;
            box-sizing: border-box;
            color: var(--primary-text-color);
            font: inherit;
            max-width: 92px;
            padding: 7px 9px;
          }
          .unit {
            color: var(--secondary-text-color);
          }
          .action {
            color: white;
            font-weight: 700;
            min-width: 86px;
            padding: 0 18px;
          }
          .action.start {
            background: var(--primary-color);
          }
          .action.stop {
            background: var(--error-color, #db4437);
          }
          .error {
            color: var(--error-color, #db4437);
            padding: 16px;
          }
        </style>
        <div class="card">${content}</div>
      </ha-card>
    `;
  }

  bindEvents() {
    this.querySelectorAll("button[data-preset]").forEach((button) => {
      button.addEventListener("click", () => this.setPreset(button.dataset.preset));
    });

    const action = this.querySelector("button[data-action]");
    action?.addEventListener("click", () => {
      if (action.dataset.action === "start") {
        this.callService("switch", "turn_on", this.config.timed_run_entity);
      } else {
        this.callService("fan", "turn_off", this.config.entity);
      }
    });

    const durationInput = this.querySelector("input[data-duration]");
    durationInput?.addEventListener("change", () => {
      const value = Number(durationInput.value);
      if (Number.isFinite(value)) {
        this._hass.callService("number", "set_value", {
          entity_id: this.config.duration_entity,
          value,
        });
      }
    });
  }

  setPreset(presetMode) {
    this._hass.callService("fan", "set_preset_mode", {
      entity_id: this.config.entity,
      preset_mode: presetMode,
    });
  }

  callService(domain, service, entityId) {
    this._hass.callService(domain, service, { entity_id: entityId });
  }

  durationInput(value) {
    const safeValue = Number.isFinite(value) ? value : 4;
    return `
      <input data-duration class="duration-input" type="number" min="0.1" step="0.5" value="${safeValue}">
      <span class="unit">h</span>
    `;
  }

  formatRemaining(value) {
    if (!value || value === "unknown" || value === "unavailable") return "—";
    const minutes = Number(value);
    if (!Number.isFinite(minutes)) return this.escape(value);
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const mins = minutes % 60;
      return mins ? `${hours}h ${mins}m` : `${hours}h`;
    }
    return `${minutes}m`;
  }

  formatFinishTime(value) {
    if (!value || value === "unknown" || value === "unavailable") return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return this.escape(value);
    return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }

  escape(value) {
    return String(value).replace(/[&<>'"]/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "'": "&#39;",
      '"': "&quot;",
    })[char]);
  }
}

class QuietCoolHouseFanCardEditor extends HTMLElement {
  setConfig(config) {
    this.config = config;
  }
}

customElements.define("quietcool-house-fan-card", QuietCoolHouseFanCard);
customElements.define("quietcool-house-fan-card-editor", QuietCoolHouseFanCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "quietcool-house-fan-card",
  name: "QuietCool House Fan",
  description: "Compact speed and timer controls for a QuietCool/Shelly house fan.",
  preview: true,
});
