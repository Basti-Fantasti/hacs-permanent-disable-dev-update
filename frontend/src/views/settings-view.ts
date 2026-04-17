import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { Options } from "../api-client";

@customElement("settings-view")
export class SettingsView extends LitElement {
  @property({ attribute: false }) options: Options | null = null;

  static styles = css`
    :host { display: block; padding: 16px; }
    dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 16px; }
    dt { font-weight: 600; }
    .hint { color: var(--secondary-text-color, #666); margin-top: 16px; }
  `;

  render() {
    if (!this.options) return html`<div>Loading…</div>`;
    return html`
      <dl>
        <dt>Scan window start</dt>
        <dd>${this.options.scan_start_time}</dd>
        <dt>Max duration (minutes)</dt>
        <dd>${this.options.scan_max_duration_minutes}</dd>
        <dt>Per-device timeout (seconds)</dt>
        <dd>${this.options.per_device_timeout_seconds}</dd>
      </dl>
      <div class="hint">
        Edit these values in Settings → Devices &amp; Services → Update Blocklist → Configure.
      </div>
    `;
  }
}
