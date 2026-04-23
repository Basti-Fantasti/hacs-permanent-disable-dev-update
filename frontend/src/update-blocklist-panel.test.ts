import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import "./update-blocklist-panel";
import type { UpdateBlocklistPanel } from "./update-blocklist-panel";

function makeFetch(infoVersion: string) {
  return vi.fn(async (url: string) => {
    if (typeof url === "string" && url.endsWith("/info")) {
      return { ok: true, status: 200, json: async () => ({ version: infoVersion }) } as Response;
    }
    if (typeof url === "string" && url.endsWith("/blocks")) {
      return {
        ok: true,
        status: 200,
        json: async () => ({ blocks: [], pending_rediscovery: [] }),
      } as Response;
    }
    if (typeof url === "string" && url.endsWith("/options")) {
      return { ok: true, status: 200, json: async () => ({}) } as Response;
    }
    return { ok: true, status: 200, json: async () => ({}) } as Response;
  });
}

async function mountPanel(loadedVersion: string | null): Promise<UpdateBlocklistPanel> {
  const el = document.createElement("update-blocklist-panel") as UpdateBlocklistPanel;
  (el as unknown as { hass: unknown }).hass = { auth: { accessToken: "T" } };
  (el as unknown as { loadedVersion: string | null }).loadedVersion = loadedVersion;
  document.body.appendChild(el);
  await el.updateComplete;
  await new Promise((r) => setTimeout(r, 0));
  await el.updateComplete;
  return el;
}

describe("update-blocklist-panel reload banner", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the reload banner when loaded version differs from backend version", async () => {
    vi.stubGlobal("fetch", makeFetch("1.0.4"));
    const el = await mountPanel("1.0.3");
    const banner = el.shadowRoot!.querySelector('[data-test="reload-banner"]');
    expect(banner).not.toBeNull();
    expect(banner!.textContent).toContain("1.0.4");
  });

  it("does not render the banner when versions match", async () => {
    vi.stubGlobal("fetch", makeFetch("1.0.3"));
    const el = await mountPanel("1.0.3");
    expect(el.shadowRoot!.querySelector('[data-test="reload-banner"]')).toBeNull();
  });

  it("does not render the banner when loaded version is unknown", async () => {
    vi.stubGlobal("fetch", makeFetch("1.0.3"));
    const el = await mountPanel(null);
    expect(el.shadowRoot!.querySelector('[data-test="reload-banner"]')).toBeNull();
  });
});
