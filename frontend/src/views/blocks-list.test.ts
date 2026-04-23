import { describe, it, expect } from "vitest";
import { fixture, html as tplHtml } from "@open-wc/testing-helpers";
import "./blocks-list";
import type { BlocksListView } from "./blocks-list";
import type { Block } from "../api-client";

function makeBlock(overrides: Partial<Block> = {}): Block {
  return {
    id: "b1",
    device_id: "d1",
    update_entity_ids: [],
    unique_ids: [],
    fingerprint: { manufacturer: "", model: "", name: "" },
    integration_domain: null,
    reason: "r",
    created_at: "",
    last_known_version: null,
    installed_version: null,
    last_scan_at: null,
    last_scan_status: "ok",
    status: "active",
    ...overrides,
  };
}

describe("<blocks-list>", () => {
  it("renders an empty state when no blocks", async () => {
    const el = await fixture<BlocksListView>(tplHtml`<blocks-list .blocks=${[]}></blocks-list>`);
    expect(el.shadowRoot!.textContent).toMatch(/No blocks/i);
  });

  it("renders one row per block", async () => {
    const blocks = [makeBlock({ reason: "r" })];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );
    const rows = el.shadowRoot!.querySelectorAll("[data-test='block-row']");
    expect(rows.length).toBe(1);
    expect(rows[0].textContent).toMatch(/r/);
  });

  it("dispatches remove event when remove button clicked", async () => {
    const blocks = [makeBlock()];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );

    const events: CustomEvent[] = [];
    el.addEventListener("block-remove", (e) => events.push(e as CustomEvent));

    (el.shadowRoot!.querySelector("[data-test='remove-btn']") as HTMLButtonElement).click();
    expect(events.length).toBe(1);
    expect(events[0].detail).toEqual({ block_id: "b1" });
  });

  it("renders a brand icon img when integration_domain is set", async () => {
    const blocks = [makeBlock({ integration_domain: "acme" })];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );
    const img = el.shadowRoot!.querySelector(
      "[data-test='brand-icon-img']",
    ) as HTMLImageElement;
    expect(img).not.toBeNull();
    expect(img.src).toBe("https://brands.home-assistant.io/_/acme/icon.png");
    expect(el.shadowRoot!.querySelector("[data-test='brand-icon-fallback']")).toBeNull();
  });

  it("renders the mdi:devices fallback icon when integration_domain is null", async () => {
    const blocks = [makeBlock({ integration_domain: null })];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );
    const fallback = el.shadowRoot!.querySelector(
      "[data-test='brand-icon-fallback']",
    ) as HTMLElement;
    expect(fallback).not.toBeNull();
    expect(fallback.getAttribute("icon")).toBe("mdi:devices");
    expect(el.shadowRoot!.querySelector("[data-test='brand-icon-img']")).toBeNull();
  });

  it("falls back to mdi:devices when the brand image fails to load", async () => {
    const blocks = [makeBlock({ integration_domain: "acme" })];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );
    const img = el.shadowRoot!.querySelector(
      "[data-test='brand-icon-img']",
    ) as HTMLImageElement;
    img.dispatchEvent(new Event("error"));
    await el.updateComplete;
    expect(el.shadowRoot!.querySelector("[data-test='brand-icon-img']")).toBeNull();
    const fallback = el.shadowRoot!.querySelector(
      "[data-test='brand-icon-fallback']",
    ) as HTMLElement;
    expect(fallback).not.toBeNull();
    expect(fallback.getAttribute("icon")).toBe("mdi:devices");
  });

  it("shows installed_version in the Pinned version column", async () => {
    const blocks = [makeBlock({ installed_version: "2.5.1" })];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );
    const cells = el.shadowRoot!.querySelectorAll(
      "[data-test='block-row'] td",
    );
    // Column order: icon, device, reason, pinned, last-known, last-scan, status, actions
    expect(cells[3].textContent?.trim()).toBe("2.5.1");
    expect(cells[4].textContent?.trim()).toBe("unknown");
  });

  it("shows 'unknown' when installed_version is null", async () => {
    const blocks = [makeBlock({ installed_version: null })];
    const el = await fixture<BlocksListView>(
      tplHtml`<blocks-list .blocks=${blocks}></blocks-list>`,
    );
    const cells = el.shadowRoot!.querySelectorAll(
      "[data-test='block-row'] td",
    );
    expect(cells[3].textContent?.trim()).toBe("unknown");
  });
});
