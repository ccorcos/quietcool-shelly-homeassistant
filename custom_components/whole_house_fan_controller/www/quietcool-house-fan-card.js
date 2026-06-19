class QuietCoolHouseFanCard extends HTMLElement {
  constructor() {
    super();
    this._root = this.attachShadow({ mode: "open" });
  }

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
    if (!fan) {
      this._root.innerHTML = this.card(`
        <div style="color: var(--error-color, #db4437); padding: 16px;">
          Entity not found: ${this.escape(this.config.entity)}
        </div>
      `);
      return;
    }

    const duration = this._hass.states[this.config.duration_entity];
    const timedRun = this._hass.states[this.config.timed_run_entity];
    const remaining = this._hass.states[this.config.remaining_entity];
    const finishesAt = this._hass.states[this.config.finishes_at_entity];

    const fanOn = fan.state === "on";
    const timerActive = timedRun?.state === "on";
    const preset = fan.attributes?.preset_mode || "Low";
    const durationValue = duration?.state && duration.state !== "unknown" ? Number(duration.state) : undefined;
    const finishValue = this.formatFinishTime(finishesAt?.state);
    const title = this.config.name || fan.attributes?.friendly_name || "House Fan";

    const status = timerActive ? "Timed" : fanOn ? "On" : "Off";
    const primaryLabel = timerActive || fanOn ? "Remaining" : "Duration";
    const primaryValue = timerActive
      ? `${this.formatRemaining(remaining?.state)}${finishValue ? `, ends ${finishValue}` : ""}`
      : fanOn
        ? "∞"
        : this.durationInput(durationValue);
    const actionLabel = fanOn || timerActive ? "Stop" : "Start";
    const action = fanOn || timerActive ? "stop" : "start";

    this._root.innerHTML = this.card(`
      <div style="align-items: center; display: flex; gap: 12px; justify-content: space-between;">
        <div style="font-size: 1.15rem; font-weight: 600; line-height: 1.2;">
          ${this.escape(title)}
        </div>
        ${this.statusPill(status, timerActive, fanOn)}
      </div>

      <div style="display: grid; gap: 8px; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 16px 0;">
        ${["High", "Medium", "Low"].map((mode) => this.speedButton(mode, preset === mode)).join("")}
      </div>

      <div style="align-items: center; display: flex; gap: 12px; justify-content: space-between;">
        <div>
          <div style="color: var(--secondary-text-color); font-size: 0.75rem; letter-spacing: 0.04em; text-transform: uppercase;">
            ${primaryLabel}
          </div>
          <div style="align-items: baseline; display: flex; gap: 6px; min-height: 36px; padding-top: 2px;">
            ${primaryValue}
          </div>
        </div>
        ${this.actionButton(actionLabel, action)}
      </div>
    `);

    this.bindEvents();
  }

  card(content) {
    return `<ha-card><div style="padding: 16px;">${content}</div></ha-card>`;
  }

  statusPill(status, timerActive, fanOn) {
    const background = timerActive
      ? "rgba(var(--rgb-accent-color, 255, 152, 0), 0.18)"
      : fanOn
        ? "rgba(var(--rgb-primary-color, 3, 169, 244), 0.16)"
        : "var(--divider-color)";
    const color = timerActive
      ? "var(--accent-color)"
      : fanOn
        ? "var(--primary-color)"
        : "var(--secondary-text-color)";

    return `
      <div style="background: ${background}; border-radius: 999px; color: ${color}; font-size: 0.8rem; font-weight: 700; padding: 4px 10px;">
        ${status}
      </div>
    `;
  }

  speedButton(mode, selected) {
    return `
      <button
        data-preset="${mode}"
        style="background: ${selected ? "var(--primary-color)" : "var(--secondary-background-color)"}; border: 0; border-radius: 12px; color: ${selected ? "var(--text-primary-color, white)" : "var(--primary-text-color)"}; cursor: pointer; font: inherit; font-size: 1.05rem; font-weight: 700; min-height: 42px;"
      >
        ${mode[0]}
      </button>
    `;
  }

  actionButton(label, action) {
    return `
      <button
        data-action="${action}"
        style="background: ${action === "start" ? "var(--primary-color)" : "var(--error-color, #db4437)"}; border: 0; border-radius: 12px; color: white; cursor: pointer; font: inherit; font-weight: 700; min-height: 42px; min-width: 86px; padding: 0 18px;"
      >
        ${label}
      </button>
    `;
  }

  bindEvents() {
    this._root.querySelectorAll("button[data-preset]").forEach((button) => {
      button.addEventListener("click", () => this.setPreset(button.dataset.preset));
    });

    const action = this._root.querySelector("button[data-action]");
    action?.addEventListener("click", () => {
      if (action.dataset.action === "start") {
        this.callService("switch", "turn_on", this.config.timed_run_entity);
      } else {
        this.callService("fan", "turn_off", this.config.entity);
      }
    });

    const durationInput = this._root.querySelector("input[data-duration]");
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
      <input
        data-duration
        type="number"
        min="0.1"
        step="0.5"
        value="${safeValue}"
        style="background: var(--secondary-background-color); border: 1px solid var(--divider-color); border-radius: 10px; box-sizing: border-box; color: var(--primary-text-color); font: inherit; max-width: 92px; padding: 7px 9px;"
      >
      <span style="color: var(--secondary-text-color);">h</span>
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
