import { LitElement, html, css } from "lit";
import { customElement, property } from "lit/decorators.js";
import type { PendingRediscovery } from "../api-client";

@customElement("rediscovery-prompt")
export class RediscoveryPrompt extends LitElement {
  @property({ attribute: false }) pending: PendingRediscovery[] = [];

  static styles = css`
    :host { display: block; }
    .item {
      background: var(--warning-color, #ffcc80);
      color: var(--primary-text-color, #000);
      padding: 12px; margin-bottom: 8px; border-radius: 4px;
    }
    .actions { margin-top: 8px; display: flex; gap: 8px; }
  `;

  render() {
    if (!this.pending.length) return html``;
    return html`
      ${this.pending.map(
        (p) => html`
          <div class="item">
            <div>
              <strong>Suspected re-pair.</strong>
              Blocked device appears to have returned as a new device
              (matched by ${p.match_type}). Re-apply block?
            </div>
            <div class="actions">
              <button data-action="accept" @click=${() => this._emit(p, "accept")}>
                Re-apply to this device
              </button>
              <button data-action="decline" @click=${() => this._emit(p, "decline")}>
                Delete block
              </button>
              <button data-action="dismiss" @click=${() => this._emit(p, "dismiss")}>
                Remind me later
              </button>
            </div>
          </div>
        `,
      )}
    `;
  }

  private _emit(p: PendingRediscovery, action: "accept" | "decline" | "dismiss") {
    this.dispatchEvent(
      new CustomEvent("resolve", {
        detail: {
          orphan_block_id: p.orphan_block_id,
          candidate_device_id: p.candidate_device_id,
          action,
        },
        bubbles: true,
        composed: true,
      }),
    );
  }
}
