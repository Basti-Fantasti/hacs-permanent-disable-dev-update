import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { Candidate } from "../api-client";

@customElement("add-block-dialog")
export class AddBlockDialog extends LitElement {
  @property({ attribute: false }) candidates: Candidate[] = [];
  @state() private _deviceId = "";
  @state() private _reason = "";

  static styles = css`
    :host { display: block; padding: 16px; }
    form { display: flex; flex-direction: column; gap: 12px; }
    label { font-weight: 600; }
    select, textarea { padding: 8px; font: inherit; }
    .actions { display: flex; gap: 8px; justify-content: flex-end; }
  `;

  render() {
    return html`
      <form @submit=${this._onSubmit}>
        <label>
          Device to block
          <select @change=${(e: Event) => (this._deviceId = (e.target as HTMLSelectElement).value)}>
            <option value="">— select —</option>
            ${this.candidates.map(
              (c) =>
                html`<option value=${c.device_id}>${c.name} (${c.manufacturer ?? ""} ${c.model ?? ""})</option>`,
            )}
          </select>
        </label>
        <label>
          Reason (optional)
          <textarea
            rows="3"
            @input=${(e: Event) => (this._reason = (e.target as HTMLTextAreaElement).value)}
          ></textarea>
        </label>
        <div class="actions">
          <button type="button" @click=${this._cancel}>Cancel</button>
          <button type="submit" ?disabled=${!this._deviceId}>Add block</button>
        </div>
      </form>
    `;
  }

  private _onSubmit(e: Event) {
    e.preventDefault();
    if (!this._deviceId) return;
    this.dispatchEvent(
      new CustomEvent("block-add", {
        detail: { device_id: this._deviceId, reason: this._reason },
        bubbles: true,
        composed: true,
      }),
    );
  }

  private _cancel() {
    this.dispatchEvent(new CustomEvent("cancel", { bubbles: true, composed: true }));
  }
}
