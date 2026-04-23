import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import {
  BlocklistApi,
  type Block,
  type Candidate,
  type Options,
  type PendingRediscovery,
} from "./api-client";
import { LOADED_VERSION } from "./loaded-version";
import "./views/blocks-list";
import "./views/add-block-dialog";
import "./views/rediscovery-prompt";
import "./views/settings-view";

interface HomeAssistantLike {
  auth?: { accessToken: string };
}

@customElement("update-blocklist-panel")
export class UpdateBlocklistPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistantLike;
  @state() private _backendVersion: string | null = null;
  @property({ attribute: false }) loadedVersion: string | null = LOADED_VERSION;
  @state() private _blocks: Block[] = [];
  @state() private _pending: PendingRediscovery[] = [];
  @state() private _candidates: Candidate[] = [];
  @state() private _options: Options | null = null;
  @state() private _showAdd = false;
  @state() private _error: string | null = null;
  @state() private _version: string | null = null;

  private _api(): BlocklistApi {
    return new BlocklistApi(this.hass?.auth?.accessToken ?? "");
  }

  static styles = css`
    :host {
      display: block;
      padding: 16px;
      font-family: var(--primary-font-family, sans-serif);
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    h1 {
      margin: 0;
      font-size: 1.4em;
    }
    .title-group {
      display: flex;
      align-items: baseline;
      gap: 8px;
      flex-wrap: wrap;
    }
    .version {
      font-size: 0.8em;
      color: var(--secondary-text-color, #666);
      font-variant-numeric: tabular-nums;
    }
    button.primary {
      background: var(--primary-color, #03a9f4);
      color: white;
      border: 0;
      padding: 8px 14px;
      border-radius: 4px;
      cursor: pointer;
    }
    .error {
      color: var(--error-color, #d33);
      padding: 8px 0;
    }
    .overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.3);
      display: grid;
      place-items: center;
      padding: 16px;
      box-sizing: border-box;
      z-index: 10;
    }
    .dialog {
      background: var(--card-background-color, white);
      border-radius: 8px;
      box-sizing: border-box;
      width: min(400px, calc(100vw - 32px));
      max-width: calc(100vw - 32px);
      max-height: calc(100vh - 32px);
      overflow: auto;
    }
    .reload-banner {
      background: var(--warning-color, #f6a609);
      color: #111;
      padding: 10px 14px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }
    .reload-banner button {
      background: #111;
      color: #fff;
      border: 0;
      padding: 6px 12px;
      border-radius: 4px;
      cursor: pointer;
    }
  `;

  connectedCallback(): void {
    super.connectedCallback();
    this._refresh();
  }

  private async _refresh(): Promise<void> {
    try {
      const [list, opts, info] = await Promise.all([
        this._api().listBlocks(),
        this._api().getOptions(),
        this._api().getInfo(),
      ]);
      this._blocks = list.blocks;
      this._pending = list.pending_rediscovery;
      this._options = opts;
      this._version = info.version || null;
      this._backendVersion = info.version || null;
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private _isVersionMismatch(): boolean {
    return (
      this.loadedVersion !== null &&
      this._backendVersion !== null &&
      this.loadedVersion !== this._backendVersion
    );
  }

  private _reload(): void {
    window.location.reload();
  }

  private async _openAdd(): Promise<void> {
    try {
      const { candidates } = await this._api().listCandidates();
      this._candidates = candidates;
      this._showAdd = true;
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private async _onAdd(e: CustomEvent<{ device_id: string; reason: string }>): Promise<void> {
    try {
      await this._api().addBlock(e.detail.device_id, e.detail.reason);
      this._showAdd = false;
      await this._refresh();
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private async _onRemove(e: CustomEvent<{ block_id: string }>): Promise<void> {
    try {
      await this._api().removeBlock(e.detail.block_id);
      await this._refresh();
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  private async _onResolve(
    e: CustomEvent<{
      orphan_block_id: string;
      candidate_device_id: string;
      action: "accept" | "decline" | "dismiss";
    }>,
  ): Promise<void> {
    try {
      await this._api().resolveRediscovery(
        e.detail.orphan_block_id,
        e.detail.action,
        e.detail.candidate_device_id,
      );
      await this._refresh();
    } catch (err) {
      this._error = (err as Error).message;
    }
  }

  render() {
    return html`
      <header>
        <div class="title-group">
          <h1>Update Blocklist</h1>
          ${this._version ? html`<span class="version" data-test="panel-version">v${this._version}</span>` : html``}
        </div>
        <button class="primary" @click=${this._openAdd}>Add block</button>
      </header>
      ${this._isVersionMismatch()
        ? html`
            <div class="reload-banner" data-test="reload-banner" role="alert">
              <span>
                A new version of Update Blocklist is available
                (v${this._backendVersion}). Reload to update.
              </span>
              <button @click=${this._reload}>Reload</button>
            </div>
          `
        : html``}
      ${this._error ? html`<div class="error">${this._error}</div>` : html``}

      <rediscovery-prompt
        .pending=${this._pending}
        @resolve=${this._onResolve}
      ></rediscovery-prompt>

      <blocks-list .blocks=${this._blocks} @block-remove=${this._onRemove}></blocks-list>

      <settings-view .options=${this._options}></settings-view>

      ${this._showAdd
        ? html`
            <div class="overlay" @click=${() => (this._showAdd = false)}>
              <div class="dialog" @click=${(e: Event) => e.stopPropagation()}>
                <add-block-dialog
                  .candidates=${this._candidates}
                  @block-add=${this._onAdd}
                  @cancel=${() => (this._showAdd = false)}
                ></add-block-dialog>
              </div>
            </div>
          `
        : html``}
    `;
  }
}
